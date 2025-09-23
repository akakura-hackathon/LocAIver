import os
import google.generativeai as genai
import vertexai
from vertexai.generative_models import GenerativeModel
import json
import gcs_utils


GOOGLE_CLOUD_PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
BUCKET_NAME = os.getenv("BUCKET_NAME")


def get_model():
    genai.configure(api_key=GOOGLE_API_KEY)
    return genai.GenerativeModel("gemini-2.5-pro")


def first(data) -> str:
    
    model = get_model()
    
    seconds = data.get("seconds")
    highlight = data.get("highlight")
    
    system_instruction = f"""
    あなたは「地域紹介の{seconds}秒映像」を作るためのインタビュアーです。
    映像制作に詳しくないユーザーの想像力を引き出し、彼らが本当に作りたい映像を言語化する手助けをします。
    ユーザーは「{highlight}」をプロモーションしたいと思っているが、映像制作の方向性がわかっていない状態です。

    対話の進め方
    目的の共有: 会話の最初に、これから一緒に作り上げる映像の方向性を決めるために、いくつかの質問をすること、そして質問項目（題材、ストーリー、スタイル、質感、避けたい要素）をユーザーに伝えます。

    対話の流れ: ユーザーの回答に合わせて、柔軟に質問を組み立ててください。ただし、一度に複数の質問をしないようにしてください。

    具体的な例示: ユーザーの回答が曖昧な場合やアイデアに行き詰まっている場合は、具体的な映像表現の例を3つ以上提示してください。単なる単語ではなく、「ドキュメンタリータッチで街の人々の日常を追う」のように、具体的な描写を加えることで、より豊かなアイデアを引き出します。

    厳守事項：ストーリーに「子供」や「孫」などのワードを絶対に含めてはいけないので、そこに注意しながら対話を進めてください。
    
    ユーザーに提示する文字数：200文字以内には収めるようにしてください。

    収集項目の管理: 以下のJSON形式で収集項目を管理してください。
    {{"subject": "...", "story": "...", "style": "...", "quality_modifiers": "...", "negative_prompt": "..." }}

    最終確認: 収集が完了したら、これまでの回答をまとめた上で、「これで確定しますか？確定する場合は会話終了と返信してください」と1行でユーザーに再確認を促してください。

    以上のルールに基づき、日本語で自然な会話を心がけてください。ユーザーとの対話を通じて、「{highlight}」をプロモーションするための最高の{seconds}秒映像のアイデアを一緒に見つけましょう。

    まず、ユーザに最初の質問を提示するところからスタートです。
    """
    
    resp = model.generate_content(system_instruction)
    
    print("システム：" + getattr(resp, "text", None))
    
    return getattr(resp, "text", None) or "（生成結果なし）"


def generate_lyrics(prompt_suffix):
    vertexai.init(project=GOOGLE_CLOUD_PROJECT, location="us-central1")

    model = GenerativeModel(
        model_name="gemini-2.5-pro",
        system_instruction=[
            """あなたは「地域紹介映像」を作るためのインタビュアーです。
            映像制作に詳しくないユーザーの想像力を引き出し、彼らが本当に作りたい映像を言語化する手助けをします。

            対話の進め方
            目的の共有: 会話の最初に、これから一緒に作り上げる映像の方向性を決めるために、いくつかの質問をすること、そして質問項目（題材、ストーリー、スタイル、質感、避けたい要素）をユーザーに伝えます。

            対話の流れ: ユーザーの回答に合わせて、柔軟に質問を組み立ててください。ただし、一度に複数の質問をしないようにしてください。

            具体的な例示: ユーザーの回答が曖昧な場合やアイデアに行き詰まっている場合は、具体的な映像表現の例を3つ以上提示してください。単なる単語ではなく、「ドキュメンタリータッチで街の人々の日常を追う」のように、具体的な描写を加えることで、より豊かなアイデアを引き出します。

            収集項目の管理: 以下のJSON形式で収集項目を管理してください。
            {   "subject": "...",   "story": "...",   "style": "...",   "quality_modifiers": "...",   "negative_prompt": "..." }

            最終確認: 収集が完了したら、これまでの回答をまとめた上で、「この内容で確定しますか？もし問題なければ「会話終了」と返信してください。」とユーザーに再確認を促してください。

            以上のルールに基づき、日本語で自然な会話を心がけてください。ユーザーとの対話を通じて、最高の「地域紹介20秒映像」のアイデアを一緒に見つけましょう。
            """
        ],
    )

    prompt = prompt_suffix
    response = model.generate_content([prompt])
    print(response.text)
    return response.text


def make_story(messages,story_ja_path):
    model = get_model()
    
    PROMPT = f"""
    あなたはプロの地方創生映像プロデューサーです。  
    以下にユーザとの会話履歴があります。この会話は、ユーザがどのような地方創生映像を作りたいかについての相談内容です。  

    タスク:  
    会話履歴を読み取り、ユーザが希望する地方創生映像のコンセプトを抽出する。  
    抽出した内容を必ず有効なJSON形式に変換し、前後に解説文や補足を加えず出力する。  
    このJSONは絵コンテ生成のベースとして直接利用されるため、映像イメージが具体的に想起できるように記述すること。  
    会話から情報が不足している場合は、文脈に沿った plausible（もっともらしい）内容を補完して埋めること。  
    各フィールドは必ず出力すること。  
    
    厳守事項：
    "story"の値に「子供」や「孫」などのワードを絶対に含めてはいけない。

    出力フォーマット:
    {{
        "subject": "映像の主題やテーマを簡潔に記述（20文字以内）",
        "story": "映像全体の物語やコンセプトを100〜200文字程度でまとめ、絵コンテ化しやすい具体性を持たせる",
        "style": "映像の表現スタイルを5〜15文字程度で記述（例: ドキュメンタリー風、シネマティックなど）",
        "quality_modifiers": "演出強調要素をカンマ区切りで3〜5個列挙（例: 温かみのある光、ドローン空撮など）",
        "negative_prompt": "避けるべき要素やNGな表現を簡潔に記述（例: ネガティブな描写、都会的すぎる映像）"
    }}

    入力: {messages} 
    出力: JSON
    """
    
    response = model.generate_content(PROMPT)
    text = response.text

    try:
        cleaned = text.strip().strip("```").replace("json", "").strip()
        story_json = json.loads(cleaned)
    except Exception as e:
        print("AIの出力をJSONとしてパースできませんでした。生テキストを表示します:")
        print(text)
        raise e

    gcs_utils.write_json(BUCKET_NAME, story_json, story_ja_path)

    print(f"ストーリー情報を {story_ja_path} に保存しました")

    return story_json


def make_story_no_character(messages,story_ja_path):
    model = get_model()
    
    PROMPT = f"""
    あなたはプロの地方創生映像プロデューサーです。  
    以下にユーザとの会話履歴があります。この会話は、ユーザがどのような地方創生映像を作りたいかについての相談内容です。  

    タスク:  
    会話履歴を読み取り、ユーザが希望する地方創生映像のコンセプトを抽出する。  
    抽出した内容を必ず有効なJSON形式に変換し、前後に解説文や補足を加えず出力する。  
    このJSONは絵コンテ生成のベースとして直接利用されるため、映像イメージが具体的に想起できるように記述すること。  
    会話から情報が不足している場合は、文脈に沿った plausible（もっともらしい）内容を補完して埋めること。  
    storyには絶対に登場人物を登場させてはいけない。
    各フィールドは必ず出力すること。 
    
    厳守事項：
    "story"の値に「子供」や「孫」などのワードを絶対に含めてはいけない。

    出力フォーマット:
    {{
        "subject": "映像の主題やテーマを簡潔に記述（20文字以内）",
        "story": "映像全体の物語やコンセプトを100〜200文字程度でまとめ、絵コンテ化しやすい具体性を持たせる",
        "style": "映像の表現スタイルを5〜15文字程度で記述（例: ドキュメンタリー風、シネマティックなど）",
        "quality_modifiers": "演出強調要素をカンマ区切りで3〜5個列挙（例: 温かみのある光、ドローン空撮など）",
        "negative_prompt": "避けるべき要素やNGな表現を簡潔に記述（例: ネガティブな描写、都会的すぎる映像）"
    }}

    入力: {messages} 
    出力: JSON
    """
    
    response = model.generate_content(PROMPT)
    text = response.text

    try:
        cleaned = text.strip().strip("```").replace("json", "").strip()
        story_json = json.loads(cleaned)
    except Exception as e:
        print("AIの出力をJSONとしてパースできませんでした。生テキストを表示します:")
        print(text)
        raise e

    gcs_utils.write_json(BUCKET_NAME, story_json, story_ja_path)

    print(f"ストーリー情報を {story_ja_path} に保存しました")

    return story_json


def meke_character(story,character_ja_path):
    model = get_model()
    
    PROMPT = f"""
    あなたはプロのキャラクターデザイナー兼ストーリープロデューサーです。  
    以下に地方創生映像のストーリーを含むJSON（subject, story, style, …）があります。  
    そのストーリーに登場する「主要人物」を一人特定し、人物像を整理して以下のJSON形式で出力してください。  

    タスク:  
    - 必ず一人の人物だけを出力すること。  
    - 出力は有効なJSON形式とし、前後に説明文や補足を加えないこと。  
    - 各フィールドは必ず埋めること。不足がある場合は plausible（もっともらしい）情報を補完して埋めること。  
    - このJSONは絵コンテやビジュアルデザインに直接利用されるため、映像イメージが想起できる具体性を持たせること。  
    - "age": "年齢" は必ず20以上にすること。

    厳守事項：
    - "age": "年齢" は必ず20以上の値にすること。

    出力フォーマット:
    {{
    "name": "人物名（日本語）",
    "sex": "性別",
    "age": "年齢",
    "description": "人物の背景や役割を簡潔に記述",
    "personality": "性格や価値観を簡潔に記述",
    "visual_design": {{
        "height": "身長",
        "build": "体格",
        "hair_style": "髪型",
        "eye_color": "瞳の色",
        "clothing_style": "服装"
    }},
    "key_item": "人物に紐づく象徴的なアイテム",
    "style": "ビジュアルスタイル（例: アニメ、リアル調など）",
    "character_composition": "絵コンテ用の構図（例: 全身、バストアップ、顔アップなど）"
    }}

    入力: {story}  
    出力: 単一の人物像を表すJSON

    """
    
    response = model.generate_content(PROMPT)
    text = response.text

    try:
        cleaned = text.strip().strip("```").replace("json", "").strip()
        character_json = json.loads(cleaned)
    except Exception as e:
        print("AIの出力をJSONとしてパースできませんでした。生テキストを表示します:")
        print(text)
        raise e

    gcs_utils.write_json(BUCKET_NAME, character_json, character_ja_path)

    print(f"キャラクター情報を {character_ja_path} に保存しました")

    return character_json