from google import genai
from PIL import Image
from io import BytesIO
import gcs_utils
import os
import time
from google.genai import errors
from google.cloud import aiplatform
from vertexai.preview.vision_models import ImageGenerationModel
import gcs_utils
import os
import time


GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GOOGLE_CLOUD_PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT")
GOOGLE_CLOUD_REGION = os.getenv("GOOGLE_CLOUD_REGION")


# キャラクターあり
def safe_generate_image(bucket_name, prompt, read_img_path, output_directory, i, save_img_name):

    client = genai.Client(api_key=GOOGLE_API_KEY)
    image = gcs_utils.read_image(bucket_name, read_img_path)

    max_retries = 7
    attempt = 0
    success = False
    backoff = 2

    if not output_directory.endswith('/'):
        output_directory += '/'

    while attempt < max_retries and not success:
        attempt += 1
        print(f"Attempt {attempt}...", flush=True)

        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash-image-preview",
                contents=[prompt, image],
            )

            image_generated = False
            for part in response.candidates[0].content.parts:
                if part.inline_data is not None:
                    image_obj = Image.open(BytesIO(part.inline_data.data))
                    save_image_name_individual = f"{save_img_name}_{i + 1}.png"
                    save_path = output_directory + save_image_name_individual
                    gcs_utils.upload_image(bucket_name, image_obj, save_path)
                    print(f"Saved image {save_image_name_individual}", flush=True)
                    image_generated = True

            if image_generated:
                success = True
            else:
                print(f"No image returned, retrying in {backoff}s...", flush=True)
                time.sleep(backoff)
                backoff *= 2

        except (errors.ServerError, Exception) as e:
            print(f"Error: {e}, retrying in {backoff}s...", flush=True)
            time.sleep(backoff)
            backoff *= 2

    if not success:
        raise RuntimeError("Failed to generate image after maximum retries")

    return save_path


# キャラクターなし
def init_vertex():
    aiplatform.init(project=GOOGLE_CLOUD_PROJECT, location=GOOGLE_CLOUD_REGION)

# キャラクターなし
def safe_generate_image_no_character(bucket_name, prompt, output_directory, i, save_img_name, user_input_ja_path):

    init_vertex()
    model = ImageGenerationModel.from_pretrained("imagen-4.0-generate-001")

    # アスペクト比を JSON から取得
    aspect_ratio = gcs_utils.read_json(bucket_name, user_input_ja_path).get("format")
    if aspect_ratio == "縦":
        aspect_ratio = "9:16"
    elif aspect_ratio == "横":
        aspect_ratio = "16:9"
    else:
        aspect_ratio = "1:1"  # デフォルト（正方形）

    negative_prompt = "collage, split screen, border, frame, duplicate, child, children"

    max_retries = 7
    attempt = 0
    success = False
    backoff = 2

    if not output_directory.endswith('/'):
        output_directory += '/'

    save_path = None

    while attempt < max_retries and not success:
        attempt += 1
        print(f"Attempt {attempt}...", flush=True)

        try:
            result = model.generate_images(
                prompt=prompt,
                negative_prompt=negative_prompt,
                number_of_images=1,
                aspect_ratio=aspect_ratio,
                add_watermark=False
            )

            # 1枚だけ生成するので result[0]
            img = result[0]

            save_image_name_individual = f"{save_img_name}_{i + 1}.png"
            save_path = output_directory + save_image_name_individual

            gcs_utils.upload_image(bucket_name, img, save_path)
            print(f"Saved image {save_image_name_individual}", flush=True)

            success = True

        except Exception as e:
            print(f"Error: {e}, retrying in {backoff}s...", flush=True)
            time.sleep(backoff)
            backoff *= 2

    if not success:
        raise RuntimeError("Failed to generate image with Imagen after maximum retries")

    return save_path