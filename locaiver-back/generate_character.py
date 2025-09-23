from google.cloud import aiplatform
from vertexai.preview.vision_models import ImageGenerationModel
import gcs_utils
import os


GOOGLE_CLOUD_PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT")
GOOGLE_CLOUD_REGION = os.getenv("GOOGLE_CLOUD_REGION")


def init_vertex():
    aiplatform.init(project=GOOGLE_CLOUD_PROJECT, location=GOOGLE_CLOUD_REGION)


def generate_image(bucket_name, prompt: str, output_path: str, user_input_ja_path):
    init_vertex()
    model = ImageGenerationModel.from_pretrained("imagen-4.0-generate-001")
    
    aspect_ratio = gcs_utils.read_json(bucket_name, user_input_ja_path).get("format")
    
    if aspect_ratio == "縦":
        aspect_ratio = "9:16"
    elif aspect_ratio == "横":
        aspect_ratio = "16:9"
        
    negative_prompt = "multipul angle, split view, two shot, grid view"

    # 画像生成
    result = model.generate_images(
        prompt=prompt,
        negative_prompt=negative_prompt,  
        number_of_images=1,
        aspect_ratio=aspect_ratio,
        add_watermark=False
    )

    img = result[0]

    gcs_utils.upload_image(bucket_name, img, output_path)

    print(f"Image saved to: {output_path}")