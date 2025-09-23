import google.generativeai as genai
import os
import gcs_utils


GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")


def make_prompt(bucket_name, input_path):
    genai.configure(api_key=GOOGLE_API_KEY)

    data = gcs_utils.read_json(bucket_name, input_path)
    
    story_text = data["story"]
    
    prompt = f"""
    You are a creative assistant that generates prompts for AI music generation models. 
    Your task is not to create music directly, but to create detailed instructions that a music generation AI can understand.
    
    Instructions:
    1. Read the input text carefully.
    2. Identify the key emotions, setting, and important events.
    3. Convert these elements into a clear, concise, and creative instruction for a music AI.
    4. Include any details that help the AI generate the appropriate music (tempo, instrumentation, mood).
    5. Do not generate actual music, only the prompt text.

    Input: A short story, scene description, or mood description.
    Output: A music generation prompt that includes:
    - The emotional tone or atmosphere (e.g., calm, cheerful, dramatic)
    - The scene or setting
    - Suggested instruments or musical style (optional)

    Example:
        Input: "A sunset on a quiet beach, waves gently hitting the shore, a lone figure watching the horizon."
        Output: "An uplifting and hopeful orchestral piece with a soaring string melody and triumphant brass."
        
    Input:{story_text}
    """

    # 4. モデルを指定して呼び出し
    model = genai.GenerativeModel("gemini-2.5-pro")
    response = model.generate_content(prompt)

    return response.text