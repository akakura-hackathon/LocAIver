import requests
import base64
import gcs_utils
import os
import json
from google.oauth2 import service_account
from google.auth.transport.requests import Request


BUCKET_NAME = os.getenv("BUCKET_NAME")
URL = os.getenv("URL")


def get_access_token():
    key_json_str = os.environ.get("VERTEX_KEY_JSON")
    if not key_json_str:
        raise RuntimeError("環境変数 VERTEX_KEY_JSON が設定されていません")

    key_dict = json.loads(key_json_str)
    credentials = service_account.Credentials.from_service_account_info(
        key_dict,
        scopes=["https://www.googleapis.com/auth/cloud-platform"]
    )
    credentials.refresh(Request())
    return credentials.token


def lyria(project_folder, prompt, negative_prompt):
    token = get_access_token()
    
    # ヘッダー
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    # リクエストボディ
    data = {
        "instances": [
            {
                "prompt": prompt,
                "negative_prompt": negative_prompt,
                "seed": 98765
            }
        ],
        "parameters": {}
    }

    # POSTリクエスト送信
    response = requests.post(URL, headers=headers, json=data)

    if response.status_code == 200:
        # JSONにパース
        response_json = response.json()

        # Base64の音声データを抽出
        audio_b64 = response_json["predictions"][0]["bytesBase64Encoded"]
        audio_bytes = base64.b64decode(audio_b64)

        # 音声ファイルとして保存 (wav想定)
        with open("bgm.wav", "wb") as f:
            f.write(audio_bytes)
        print("音声ファイルを 'bgm.wav' として保存しました")
        
        gcs_utils.upload_to_gcs(BUCKET_NAME, "bgm.wav", project_folder + "result/bgm.wav")

    else:
        print("エラー:", response.text)