import os
import json
import google.generativeai as genai
import gcs_utils


GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")


def generate_scenes_from_story(bucket_name, story_ja_path, scene_ja_path): 
    
    genai.configure(api_key=GOOGLE_API_KEY)

    scene_data = gcs_utils.read_json(bucket_name, story_ja_path)

    # 物語の本文（storyキーを想定）
    story_text = scene_data.get("story", "")
    if not story_text:
        raise ValueError("JSONに 'story' キーが見つかりません")

    # 3. AIへのプロンプトを作成
    PROMPT = f"""
    あなたの役割は、与えられた日本語の物語をもとに、4つのシーンに分割し、指定されたJSON形式で出力することです。

    厳守事項:
    - 出力はJSON形式のみで、余計な文字・説明を絶対に含めないこと。
    - 各シーンには以下のキーを必ず含めること。
    - scene_id: 1から始まる連番
    - depiction: シーン全体の描写（自然な文章）、ここに「子供」や「孫」、といったワードを含めることは許されない
    - composition: カメラ的な構図情報を含むオブジェクト
        - camera_angle
        - view
        - focal_length
        - lighting
        - focus
    - dialogue: 会話がある場合は配列形式で {{"character": "", "line": "" }} を複数入れる。会話がない場合は空配列。
    - other_information: 必ず文字列のみを値とし、リストや別オブジェクトは禁止。

    足りない情報は物語の文脈に合うように自然に補完してください。

    出力フォーマット（厳守）:
    {{
    "scenes": [
        {{
        "scene_id": 1,
        "depiction": "",
        "composition": {{
            "camera_angle": "",
            "view": "",
            "focal_length": "",
            "lighting": "",
            "focus": ""
        }},
        "dialogue": [
            {{
            "character": "",
            "line": ""
            }}
        ],
        "other_information": ""
        }},
        ...
    ]
    }}

    物語本文:
    ---
    {story_text}
    ---

    """

    # 4. モデルを指定して呼び出し
    model = genai.GenerativeModel("gemini-2.5-pro")
    response = model.generate_content(PROMPT)

    # 5. 応答を取得
    text = response.text

    # JSONとしてパースできるよう整形
    try:
        cleaned = text.strip().strip("```").replace("json", "").strip()
        scenes_json = json.loads(cleaned)
    except Exception as e:
        print("AIの出力をJSONとしてパースできませんでした。生テキストを表示します:")
        print(text)
        raise e

    # 6. 結果をファイルに保存
    # gcsに保存
    gcs_utils.write_json(bucket_name, scenes_json, scene_ja_path)

    print(f"シーン情報を {scene_ja_path} に保存しました")

    return scenes_json


def fix_slected_scene_from_story(bucket_name, scene_id, story_ja_path, scene_ja_path, revision_count, revision_contents, project_folder):
    
    output_path = project_folder + f"json/scene_akakura_ja_v{revision_count}.json"

    genai.configure(api_key=GOOGLE_API_KEY)

    # 2. JSONファイルを読み込む
    # gcs_utilsの利用
    story_data = gcs_utils.read_json(bucket_name, story_ja_path)
    scene_data = gcs_utils.read_json(bucket_name, scene_ja_path)

    # 物語の本文（storyキーを想定）
    story_text = story_data.get("story", "")
    if not story_text:
        raise ValueError("JSONに 'story' キーが見つかりません")

    # 3. AIへのプロンプトを作成
    PROMPT = f"""
    あなたの役割は、入力されたJSONデータのうち、scene_id が {scene_id+1} のシーンを修正することです。  

    厳守事項:
    - 出力は入力JSON全体を返してください（修正対象以外のシーンもそのまま含めてください）。
    - JSON以外の文字、説明文、記号を絶対に含めないでください。
    - JSONの構造は保持してください。不要な削除や追加は行わず、必要な修正のみを加えてください。
    - 修正内容は「revision_contents」を解釈し、どのキーに対応するかを自律的に判断してください。
    - 修正は物語全体の文脈を考慮し、一貫性を保ってください。

    入力JSON:
    ---
    {scene_data}
    ---

    修正内容（revision_contents）:
    ---
    {revision_contents}
    ---

    出力:
    修正済みのJSON全体（入力と同じフォーマットの完全なJSON）を返してください。

    """

    # 4. モデルを指定して呼び出し
    model = genai.GenerativeModel("gemini-2.5-pro")
    response = model.generate_content(PROMPT)

    # 5. 応答を取得
    text = response.text

    # JSONとしてパースできるよう整形
    try:
        cleaned = text.strip().strip("```").replace("json", "").strip()
        scenes_json = json.loads(cleaned)
    except Exception as e:
        print("AIの出力をJSONとしてパースできませんでした。生テキストを表示します:")
        print(text)
        raise e

    # 6. 結果をファイルに保存
    # gcsに保存
    gcs_utils.write_json(bucket_name, scenes_json, output_path)
    print(f"シーン情報を {output_path} に保存しました")

    return output_path