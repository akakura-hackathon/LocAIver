import json
import google.generativeai as genai
import gcs_utils
import os


GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")


def translate_json(bucket_name, input_path: str, output_path: str):
    
    genai.configure(api_key=GOOGLE_API_KEY)

    # 2. JSONファイルを読み込む
    # gcsとのやり取りに変える
    story_data = gcs_utils.read_json(bucket_name, input_path)

    # 物語の本文（storyキーを想定）

    # 3. AIへのプロンプトを作成
    PROMPT = f"""
    以下のjsonの値を英語に翻訳して出力してください

    json本体:
    ---
    {story_data}
    ---
    
    返すのはjsonのフォーマットで、そのデータだけを返してください。
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
    # gcs
    gcs_utils.write_json(bucket_name, scenes_json, output_path)

    print(f"翻訳結果を {output_path} に保存しました")

    return scenes_json