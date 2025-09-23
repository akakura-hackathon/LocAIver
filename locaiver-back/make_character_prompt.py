import gcs_utils


def generate_charcater_prompt_from_json(bucket_name, file_path):

    data = gcs_utils.read_json(bucket_name, file_path)
    # Extracting data from the JSON
    name = data.get("name", "")
    sex = data.get("sex", "")
    age = data.get("age", "")
    description = data.get("description", "")
    personality = data.get("personality", "")
    
    visual_design = data.get("visual_design", {})
    height = visual_design.get("height", "")
    build = visual_design.get("build", "")
    hair_style = visual_design.get("hair_style", "")
    eye_color = visual_design.get("eye_color", "")
    clothing_style = visual_design.get("clothing_style", "")
    
    key_item = data.get("key_item", "")
    style = data.get("style", "")
    composition = data.get("character_composition", "")

    # Constructing the prompt string
    prompt = (
        f"An {style} {composition} shot of a {age} {sex} named {name}, {description}. "
        f"this person is {personality}. "
        f"this person has a height of {height} with a {build} build, {hair_style} hair, and {eye_color}. "
        f"this person is wearing a {clothing_style} and carrying {key_item}. "
        f"Do not create multiple frames or collage-style images, generate only one single coherent scene."
    )

    return prompt