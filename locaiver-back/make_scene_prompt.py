import gcs_utils


def generate_scene_prompts_from_json(bucket_name, scene_en_path, story_en_path, user_input_ja_path):

    scene_data = gcs_utils.read_json(bucket_name, scene_en_path)
    story_data = gcs_utils.read_json(bucket_name, story_en_path)
    user_input = gcs_utils.read_json(bucket_name, user_input_ja_path)
    
    # グローバルスタイルと動画フォーマットを取得
    style = story_data.get("style", "")
    video_format = user_input.get("video_format", "縦")

    # アスペクト比の設定
    if video_format == "縦":
        aspect_ratio = "9:16" 
    else:
        aspect_ratio = "16:9"

    prompts = []
    for scene in scene_data.get("scenes", []):
        depiction = scene.get("depiction", "")
        composition = scene.get("composition", {})
        other_info = scene.get("other_infomation", "")

        # 構図情報
        camera_angle = composition.get("camera_angle", "")
        view = composition.get("view", "")
        focal_length = composition.get("focal_length", "")
        lighting = composition.get("lighting", "")
        focus = composition.get("focus", "")

        # プロンプト組み立て
        composition_prompt = (
            f"The scene is captured with {view} from a {camera_angle}. "
            f"The lighting is {lighting}, and a {focal_length} mm lens is used. "
            f"The camera's focus is on {focus}. "
            f"The image style is {style}. "
            f"The image should be in a {aspect_ratio} format."
            f"Absolutely no individuals who appear under 21 years old. Exclude children and teenagers entirely. Only depict adults with a clear, mature, unmistakable age of 21 or older."
        )

        final_prompt = f"{depiction}. {composition_prompt} {other_info}".strip()
        prompts.append(final_prompt)
    
    return prompts