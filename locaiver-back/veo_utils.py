import time
from google import genai
from google.genai import types
from google.cloud import storage
import vertexai
import os
import gcs_utils
import subprocess
import imageio_ffmpeg as ffmpeg
import generate_bgm
import make_bgm_prompt


GOOGLE_CLOUD_PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT")
GOOGLE_CLOUD_REGION = os.getenv("GOOGLE_CLOUD_REGION")
BUCKET_NAME = os.getenv("BUCKET_NAME")
MODEL = "veo-3.0-fast-generate-001" 


# ===== プロンプトを安全に言い換え =====
def sanitize_prompt_with_gemini(prompt: str) -> str:
    from vertexai.generative_models import GenerativeModel

    model = GenerativeModel("gemini-2.5-pro")

    """
    Gemini を用いて NG ワードを徹底的に除去し、
    映像生成に必ず通る安全な表現に書き換える関数
    """
    system_instruction = (
        "You are a strict safety filter for video generation prompts.\n"
        "Rewrite the input so it is ALWAYS safe and compliant.\n\n"
        "Rules:\n"
        "1. Detect and remove ALL sensitive, unsafe, or restricted content "
        "(violence, sex, drugs, crime, medical, politics, religion, discrimination, etc.).\n"
        "2. Replace them with safe, neutral, and family-friendly alternatives "
        "such as nature, landscapes, objects, weather, abstract visuals, or daily life scenes.\n"
        "3. Do NOT include emotional, psychological, or subjective descriptions.\n"
        "4. Keep only concrete, visual, cinematic instructions that are guaranteed safe.\n"
        "5. If the input is too unsafe, IGNORE it and instead return a generic safe prompt "
        "like 'A calm scene of nature with mountains and a river under a clear sky.'\n"
        "6. Output ONLY the safe rewritten text, nothing else."
    )

    response = model.generate_content(
        [system_instruction, prompt],
        generation_config={"temperature": 0.0, "max_output_tokens": 256},
    )

    return response.text.strip()


# ===== 動画を結合 =====
def merge_videos(video_paths, output_file):
    list_file = "videos.txt"
    with open(list_file, "w", encoding="utf-8") as f:
        for path in video_paths:
            f.write(f"file '{path}'\n")

    cmd = [
        ffmpeg.get_ffmpeg_exe(),  # pip で入れた ffmpeg バイナリ
        "-y",
        "-f", "concat", "-safe", "0",
        "-i", list_file,
        "-c:v", "copy",  # 映像は再エンコードせずコピー
        "-an",           # 音声を削除（無音化）
        output_file
    ]
    subprocess.run(cmd, check=True)
    print(f"無音動画を保存しました → {output_file}")
    
    
# ===== 動画にbgmを追加 =====
def merge_bgm(video_path, bgm_path, output_path):
    ffmpeg_path = ffmpeg.get_ffmpeg_exe()

    cmd = [
        ffmpeg_path,   # "ffmpeg" ではなく、このパスを渡す
        "-y",
        "-i", video_path,
        "-i", bgm_path,
        "-c:v", "copy",
        "-c:a", "aac",
        "-map", "0:v:0",
        "-map", "1:a:0",
        "-shortest",
        output_path
    ]
    subprocess.run(cmd, check=True)
    print(f"Final video with BGM saved: {output_path}")
    return output_path


# ===== 動画生成 =====
def generate_video_with_retry(i, input_image, prompt, output_gcs_uri, project_folder, genai_client):
    
    retry = 5
    attempt = 0
    current_prompt = prompt
    aspect_ratio = gcs_utils.read_json(BUCKET_NAME, project_folder + "json/user_input_akakura_ja.json").get("format")
    if aspect_ratio == "縦":
        aspect_ratio = "9:16"
    elif aspect_ratio == "横":
        aspect_ratio = "16:9"
        
    seconds = gcs_utils.read_json(BUCKET_NAME, project_folder + "json/user_input_akakura_ja.json").get("seconds")
    if seconds == 16:
        duration_seconds = 4
    elif seconds == 24:
        duration_seconds = 6
    elif seconds == 32:
        duration_seconds = 8
    
    while attempt < retry:
        attempt += 1
        print(f"No.{i} 動画生成試行 {attempt} 回目…")
        print("使用プロンプト:", current_prompt)

        operation = genai_client.models.generate_videos(
            model=MODEL,
            prompt=current_prompt,
            config=types.GenerateVideosConfig(
                aspect_ratio=aspect_ratio,
                output_gcs_uri=output_gcs_uri,
                number_of_videos=1,
                duration_seconds=duration_seconds,
                person_generation="allow_all",
                enhance_prompt=True,
            ),
            image={"gcsUri": input_image, "mimeType": "image/png"},
        )

        # -------------------------
        # 処理完了まで待機
        # -------------------------
        while not operation.done:
            time.sleep(10)
            operation = genai_client.operations.get(operation)

        # -------------------------
        # 結果確認
        # -------------------------
        videos = None
        if getattr(operation, "result", None) and getattr(operation.result, "generated_videos", None):
            videos = operation.result.generated_videos
        elif getattr(operation, "response", None) and getattr(operation.response, "generated_videos", None):
            videos = operation.response.generated_videos

        final_path = None
        if videos:
            for idx, video in enumerate(operation.result.generated_videos, start=1):
                gcs_uri = video.video.uri
                new_filename = f"{i}.mp4"
                success = False
                for _ in range(3):
                    try:
                        final_path = gcs_utils.move_and_cleanup(gcs_uri, project_folder+"videos/", new_filename)
                        success = True
                        break
                    except Exception as e:
                        print("GCS move failed, retrying...", e)
                        time.sleep(5)

                if not success:
                    print("Failed to move video after retries, skipping")
                print("Final saved:", final_path)
            return True  # 成功
        else:
            print(f"動画生成に失敗しました: {operation.error}")
            # プロンプトを安全化して再試行
            current_prompt = sanitize_prompt_with_gemini(current_prompt)

    # すべて失敗した場合
    print(f"No.{i} は全ての試行で失敗しました。スキップします。")
    return False


# ===== main =====
def main(project_folder):
    bucket_name = BUCKET_NAME
    project = GOOGLE_CLOUD_PROJECT
    location = "us-central1"

    # -------------------------
    # Vertex AI クライアント初期化
    # -------------------------
    genai_client = genai.Client(vertexai=True, project=project, location=location)
    vertexai.init(project=project, location=location)

    latest_version = gcs_utils.get_latest_version_file(project_folder)
    json_content = gcs_utils.read_json(bucket_name, project_folder + "json/" + latest_version)
    scenes = json_content["scenes"]
    prompts = []
    for scene in scenes:
        prompt = (
        f"Scene {scene['scene_id']}: {scene['depiction']} "
        f"Composition details: {scene['composition']['camera_angle']}, "
        f"{scene['composition']['view']}, "
        f"shot with {scene['composition']['focal_length']} lens, "
        f"lighting: {scene['composition']['lighting']}, "
        f"focus: {scene['composition']['focus']}.")
        prompts.append(prompt)
        
    image_files = gcs_utils.list_images_in_folder(bucket_name, project_folder + "images/")
    for i, filename in enumerate(image_files, start=1):
        output_gcs_uri = "gs://" + bucket_name + "/" + project_folder + "videos/"
        input_image = "gs://" + bucket_name + "/" + project_folder + "images/" + filename
        generate_video_with_retry(i, input_image, prompts[i-1], output_gcs_uri, project_folder, genai_client)
    
    # 1. GCSから動画を取得
    # 入力動画
    VIDEO_FILES = [
        project_folder + "videos/1.mp4",
        project_folder + "videos/2.mp4",
        project_folder + "videos/3.mp4",
        project_folder + "videos/4.mp4"
    ]
    local_video_paths = gcs_utils.download_videos(bucket_name, VIDEO_FILES)

    # 2. 動画を結合
    merge_videos(local_video_paths, "no_bgm.mp4")
    gcs_utils.upload_to_gcs(bucket_name, "no_bgm.mp4", project_folder + "result/no_bgm.mp4")
    
    # 3. bgmを生成
    print("create_bgm start")
    prompt = make_bgm_prompt.make_prompt(bucket_name, project_folder + "json/story_script_akakura_en.json")
    print(prompt)
    generate_bgm.lyria(project_folder, prompt, "")
    print("create_bgm end")
    
    # 4. bgmをマージ
    print("merge bgm start")
    merge_bgm("no_bgm.mp4", "bgm.wav", "result.mp4")
    print("merge bgm end")

    # 5. 結果をGCSにアップロード
    gcs_utils.upload_to_gcs(bucket_name, "result.mp4", project_folder + "result/result.mp4")