import json
import os
from io import BytesIO
from google.cloud import storage
from google.oauth2 import service_account
from PIL import Image
from datetime import timedelta
import re
from google.api_core.retry import Retry


key_json_str = os.environ.get("GCS_KEY_JSON")
if not key_json_str:
    raise RuntimeError("環境変数 GCS_KEY_JSON が設定されていません")
key_dict = json.loads(key_json_str)
credentials = service_account.Credentials.from_service_account_info(key_dict)
client = storage.Client(credentials=credentials)


BUCKET_NAME = os.getenv("BUCKET_NAME")


def read_json(bucket_name: str, gcs_path: str):
    """GCS から JSON を読み込む"""
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(gcs_path)
    data = blob.download_as_bytes()
    return json.loads(data.decode("utf-8"))


def write_json(bucket_name: str, data: dict, gcs_path: str):
    """JSON データを GCS に保存"""
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(gcs_path)
    blob.upload_from_string(
        json.dumps(data, ensure_ascii=False, indent=2),
        content_type="application/json"
    )
    print(f"[GCS] JSON Uploaded -> gs://{bucket_name}/{gcs_path}")


def upload_image(bucket_name: str, img, gcs_path: str):
    """画像を GCS にアップロード (GeneratedImage / PIL.Image 双方対応)"""
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(gcs_path)

    # GeneratedImage の場合
    if hasattr(img, "_image_bytes"):
        image_bytes = img._image_bytes
        blob.upload_from_string(image_bytes, content_type="image/png")

    # PIL.Image の場合
    elif isinstance(img, Image.Image):
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)
        blob.upload_from_file(buffer, content_type="image/png")

    else:
        raise TypeError(f"Unsupported image type: {type(img)}")

    print(f"Image uploaded to gs://{bucket_name}/{gcs_path}")
    return f"gs://{bucket_name}/{gcs_path}"


def read_image(bucket_name: str, gcs_path: str):
    """GCS から PNG/JPG 画像を読み込んで PIL Image を返す"""
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(gcs_path)
    data = blob.download_as_bytes()
    img = Image.open(BytesIO(data))
    return img


def upload_to_gcs(bucket_name, source_file, destination_blob):
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(destination_blob)
    blob.upload_from_filename(source_file)
    print(f"Uploaded {source_file} → gs://{bucket_name}/{destination_blob}")
    
    
def generate_signed_url(blob_path, expiration_minutes):
    bucket = client.bucket(BUCKET_NAME)
    blob = bucket.blob(blob_path)
    
    url = blob.generate_signed_url(
        version="v4",
        expiration=timedelta(minutes=expiration_minutes),
        method="GET",
    )
    return url


def create_next_project_folder():
    bucket = client.bucket(BUCKET_NAME)

    # 既存の Project-XXX フォルダを取得
    blobs = client.list_blobs(BUCKET_NAME, prefix="Project-")

    project_numbers = []
    for blob in blobs:
        # "Project-001/" のようなプレフィックスを抽出
        match = re.match(r"Project-(\d{3})/", blob.name)
        if match:
            project_numbers.append(int(match.group(1)))

    # 次の番号を決定
    next_number = max(project_numbers, default=0) + 1
    base_folder = f"Project-{next_number:03d}/"

    # まずベースフォルダを作成
    bucket.blob(base_folder).upload_from_string("")

    # サブフォルダを作成
    subfolders = ["images/", "json/", "result/", "videos/"]
    for sub in subfolders:
        folder_path = base_folder + sub
        bucket.blob(folder_path).upload_from_string("")  # 空ファイルでフォルダを作成
        print(f"Created subfolder: {folder_path}")

    print(f"Created project folder with subfolders under: {base_folder}")
    return base_folder


def download_videos(bucket_name, video_files, local_dir="videos"):
    bucket = client.bucket(bucket_name)

    if not os.path.exists(local_dir):
        os.makedirs(local_dir)

    local_paths = []
    for file in video_files:
        blob = bucket.blob(file)
        local_path = os.path.join(local_dir, os.path.basename(file))
        blob.download_to_filename(local_path)
        print(f"Downloaded {file} → {local_path}")
        local_paths.append(local_path)

    return local_paths


def move_and_cleanup(gcs_uri, target_prefix, new_filename):
    # 元のバケットとパス
    bucket_name, blob_path = gcs_uri[5:].split("/", 1)
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(blob_path)

    # ファイル名を決定
    file_name = new_filename or blob_path.split("/")[-1]

    if not target_prefix.endswith("/"):
        target_prefix += "/"

    # コピー先 blob
    new_blob_path = f"{target_prefix}{file_name}"

    # rewrite ではなく copy_blob を使用
    retry = Retry(deadline=300)  # 最大 5 分待機
    bucket.copy_blob(blob, bucket, new_blob_path, retry=retry)

    # 元を削除
    blob.delete()

    print(f"Moved: {gcs_uri} → gs://{bucket_name}/{new_blob_path}")

    # 疑似フォルダのクリーンアップは任意
    return f"gs://{bucket_name}/{new_blob_path}"


def list_images_in_folder(bucket_name: str, folder_prefix: str):
    bucket = client.bucket(bucket_name)
    
    # 指定フォルダ（プレフィックス）のファイルを取得
    blobs = bucket.list_blobs(prefix=folder_prefix)
    
    # 拡張子が画像のものだけを抽出
    images = [
        blob.name.split("/")[-1]  # フォルダ部分を除いたファイル名
        for blob in blobs
        if blob.name.lower().endswith((".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp"))
    ]
    
    candidates = {}
    pattern = re.compile(r"(?:v(\d+)_)?(\d+)\.png$")

    for img in images:
        match = pattern.search(img)
        if not match:
            continue

        v_num = int(match.group(1)) if match.group(1) else 0
        num = int(match.group(2))

        # 1〜4 のみ対象
        if 1 <= num <= 4:
            # すでに候補があるなら v が大きい方を残す
            if num not in candidates or v_num > candidates[num][0]:
                candidates[num] = (v_num, img)
                
    return [candidates[n][1] for n in sorted(candidates.keys())]


def get_latest_version_file(project_folder):
    client = storage.Client()
    bucket = client.bucket(BUCKET_NAME)

    # 指定prefixで始まるファイルを取得
    blobs = bucket.list_blobs(prefix = f"{project_folder}json/")

    # バージョン番号を抽出して管理
    versioned_files = []
    pattern = re.compile(rf"^{"scene_akakura_en"}(?:_v(\d+))?\.json$")

    for blob in blobs:
        filename = blob.name.split("/")[-1]  # ファイル名のみ
        match = pattern.match(filename)
        if match:
            version = int(match.group(1)) if match.group(1) else 0
            versioned_files.append((version, filename))

    if not versioned_files:
        return None

    # バージョン最大のファイルを返す
    latest_file = max(versioned_files, key=lambda x: x[0])
    return latest_file[1]