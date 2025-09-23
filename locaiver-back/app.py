import json
from flask import Flask, jsonify, request
from google.cloud import storage
import create_image
import veo_utils
from google.oauth2 import service_account
import os
import translate
import create_story
import gcs_utils


key_json_str = os.environ.get("GCS_KEY_JSON")
if not key_json_str:
    raise RuntimeError("環境変数 GCS_KEY_JSON が設定されていません")
key_dict = json.loads(key_json_str)
credentials = service_account.Credentials.from_service_account_info(key_dict)
client = storage.Client(credentials=credentials)


BUCKET_NAME = os.getenv("BUCKET_NAME")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")


app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "a3f5c2b9e7d44c7a8e5b6f3f28c9a412")


@app.post("/form")
def form():
    print("フォーム入力を受け付けました")
    project_folder = gcs_utils.create_next_project_folder()
    
    json_folder = project_folder + "json/"
    data = request.get_json(silent=True) or {}
    filename = f"user_input_akakura_ja.json"
    gcs_path = json_folder + filename
    user_input_en_path = json_folder + "user_input_akakura_en.json"
    # GCS にアップロード
    client = storage.Client()
    bucket = client.bucket(BUCKET_NAME)
    blob = bucket.blob(gcs_path)
    blob.upload_from_string(json.dumps(data, ensure_ascii=False, indent=2), content_type="application/json")
    translate.translate_json(BUCKET_NAME, gcs_path, user_input_en_path)
    reply = create_story.first(data)
    
    return {"reply": reply, "project_folder": project_folder}


@app.post("/chat")
def chat():
    data = request.get_json(silent=True) or {}

    # 送信形式の違いを吸収
    message = data.get("message") or data.get("input")
    if not message and isinstance(data.get("messages"), list):
        for m in reversed(data["messages"]):
            if m and m.get("role") == "user":
                message = m.get("text")
                break
    message = (message or "").strip()

    # ---- 会話履歴をプロンプトに明示的に埋め込む ----
    # モデルが理解しやすいように英語ラベル "User"/"Assistant" を使用
    history_lines = []
    if isinstance(data.get("messages"), list):
        last = data["messages"][-8:]  # 直近8件くらいまで
        for m in last:
            role = m.get("role", "")
            text = (m.get("text") or m.get("content") or "").strip()
            if not text:
                continue
            if role == "user":
                history_lines.append(f"User: {text}")
            else:
                # 'assistant' 以外の表記（bot/システム等）も assistant として扱う
                history_lines.append(f"Assistant: {text}")

    # 直近ユーザー入力を最後にもう一度明示
    if message:
        history_lines.append(f"User: {message}")
        
    print("ユーザ：" + message)

    # suffix を履歴＋最新発話のドキュメントとして注入
    suffix = ""
    if history_lines:
        suffix = (
            "【会話履歴（古い→新しい）】\n"
            + "\n".join(history_lines)
            + "\n\n【指示】上の履歴の直近の流れを踏まえて、次の一手を出力してください。"
        )
    else:
        # 履歴が無い初回
        suffix = "【会話履歴】(なし)\n\n【指示】初回の質問から開始してください。"

    reply_text = create_story.generate_lyrics(suffix)
    return jsonify({"reply": reply_text})


@app.post("/chat-fin")
def image():
    
    data = request.get_json(silent=True) or {}
    
    project_folder = data.get("project_folder", "")
    messages = data.get("messages", [])
    print("messages:", messages)

    json_folder = project_folder + "json/"
    filename1 = f"story_script_akakura_ja.json"
    filename2 = f"character_akakura_ja.json"
    story_ja_path = json_folder + filename1
    character_ja_path = json_folder + filename2
    story_en_path = json_folder + "story_script_akakura_en.json"
    character_en_path = json_folder + "character_akakura_en.json"
    user_input_ja_path = json_folder + "user_input_akakura_ja.json"
    
    data = gcs_utils.read_json(BUCKET_NAME, user_input_ja_path)
    progression = data.get("progression")
    if "登場人物型" == progression:
        story_json = create_story.make_story(messages,story_ja_path)
        create_story.meke_character(story_json,character_ja_path)
        translate.translate_json(BUCKET_NAME, story_ja_path, story_en_path)
        translate.translate_json(BUCKET_NAME, character_ja_path, character_en_path)
        
    elif "ナレーション型" == progression:
        story_json = create_story.make_story_no_character(messages,story_ja_path)
        translate.translate_json(BUCKET_NAME, story_ja_path, story_en_path)
    
    else:
        story_json = create_story.make_story(messages,story_ja_path)
        create_story.meke_character(story_json,character_ja_path)
        translate.translate_json(BUCKET_NAME, story_ja_path, story_en_path)
        translate.translate_json(BUCKET_NAME, character_ja_path, character_en_path)

    print("create_image start")
    create_image.main(project_folder)
    print("create_image end")

    data = gcs_utils.read_json(BUCKET_NAME, project_folder + "json/scene_akakura_ja.json")
    for scene in data["scenes"]:
        scene_id = scene["scene_id"]
        scene["url"] = gcs_utils.generate_signed_url(project_folder + "images/akakuraPR_" + str(scene_id) + ".png", 60)
    return json.dumps(data, ensure_ascii=False, indent=2)


@app.post("/edit")
def edit():
    data = request.get_json(silent=True) or {}
    print(data)
    
    project_folder = data.get("project_folder", "")
    revision_count = data.get("counter", "")
    print("count"+ revision_count)

    fix = [scene["fix"] for scene in data["scenes"]]
    input_fix = [scene["input_fix"] for scene in data["scenes"]]
    print(fix)
    print(input_fix)

    story_ja_path = project_folder + "json/story_script_akakura_ja.json"
    story_en_path = project_folder + "json/story_script_akakura_en.json"
    character_en_path = project_folder + "json/character_akakura_en.json"
    user_input_ja_path = project_folder + "json/user_input_akakura_ja.json"
    scene_ja_path = project_folder + "json/scene_akakura_ja.json"
    scene_en_path = project_folder + "json/scene_akakura_en.json"
    img_dir = project_folder + "images/"

    create_image.edit_image(
        project_folder,story_ja_path, scene_ja_path, scene_en_path,
        story_en_path, user_input_ja_path, character_en_path,
        img_dir, revision_count, fix, input_fix
    )

    image_files = gcs_utils.list_images_in_folder(BUCKET_NAME, project_folder +  "images/")
    data = gcs_utils.read_json(BUCKET_NAME, project_folder + f"json/scene_akakura_ja_v{revision_count}.json")

    for scene in data["scenes"]:
        scene_id = scene["scene_id"]
        scene["url"] = gcs_utils.generate_signed_url(project_folder + "images/" + image_files[scene_id-1], 60)
    print(data)
    return json.dumps(data, ensure_ascii=False, indent=2)


@app.post("/video")
def video():
    data = request.get_json(silent=True) or {}
    
    project_folder = data.get("project_folder", "")

    print("create_video start")
    veo_utils.main(project_folder)
    print("create_video end")

    return gcs_utils.generate_signed_url(project_folder + "result/result.mp4",60)


if __name__ == "__main__":
    port = 8080
    app.run(host="0.0.0.0", port=port, debug=True, use_reloader=False, threaded=True)