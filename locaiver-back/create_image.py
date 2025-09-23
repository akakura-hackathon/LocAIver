import os
import scene
import translate
import make_scene_prompt
import make_character_prompt
import generate_character
import generate_scene_image
import gcs_utils


BUCKET_NAME = os.getenv("BUCKET_NAME")


def create_image_with_character(bucket_name, story_ja_path, story_en_path, character_ja_path, character_en_path, \
        scene_ja_path, scene_en_path, user_input_ja_path, user_input_en_path,\
        img_dir, save_img_name):
    # ストーリー(日本語) → シーン(日本語)
    scene.generate_scenes_from_story(bucket_name, story_ja_path, scene_ja_path)

    # シーン(日本語) → シーン(英語)
    translate.translate_json(bucket_name, scene_ja_path, scene_en_path)

    # キャラクターjsonからプロンプト生成
    character_prompt = make_character_prompt.generate_charcater_prompt_from_json(bucket_name, character_en_path)

    # キャラクターjsonを読み込み、name を取得
    # gcs
    character_data = gcs_utils.read_json(bucket_name, character_en_path)

    name = character_data.get("name", "unknown")
    # 名前被りを避ける方法を考える
    save_path = img_dir + name + ".png"
    
    # キャラクター画像生成
    generate_character.init_vertex()
    generate_character.generate_image(bucket_name, character_prompt, save_path, user_input_ja_path)

    #シーン(英語)のjsonから画像生成用のプロンプトにする
    scene_prompt = make_scene_prompt.generate_scene_prompts_from_json(bucket_name, scene_en_path, story_en_path, user_input_ja_path)

    #シーン(英語)＋キャラクター画像からシーン画像生成
    for i in range(len(scene_prompt)):
        prompt = scene_prompt[i]
        img_path = save_path
        print(f"--- Prompt for Scene {i+1} ---")
        print(prompt)
        print("-" * 25)
        generate_scene_image.safe_generate_image(bucket_name, prompt, \
            img_path, img_dir, i, save_img_name)
    
    print("---finish!!---")


def create_image_no_character(BUCKET_NAME, story_ja_path, story_en_path, character_ja_path, character_en_path, \
    scene_ja_path, scene_en_path, user_input_ja_path, user_input_en_path,\
    img_dir, save_img_name):

    # ストーリー(日本語) → シーン(日本語)
    scene.generate_scenes_from_story(BUCKET_NAME, story_ja_path, scene_ja_path)

    # シーン(日本語) → シーン(英語)
    translate.translate_json(BUCKET_NAME, scene_ja_path, scene_en_path)
    
    #シーン(英語)のjsonから画像生成用のプロンプトにする
    scene_prompt = make_scene_prompt.generate_scene_prompts_from_json(BUCKET_NAME, scene_en_path, story_en_path, user_input_ja_path)

    #シーン(英語)＋キャラクター画像からシーン画像生成
    for i in range(len(scene_prompt)):
        prompt = scene_prompt[i]
        
        print(f"--- Prompt for Scene {i+1} ---")
        print(prompt)
        print("-" * 25)
        generate_scene_image.safe_generate_image_no_character(BUCKET_NAME, prompt, \
            img_dir, i, save_img_name, user_input_ja_path)

    print("---finish!!---")


def display_scenes_from_json(bucket_name, scene_file_path):
    
    scene_data = gcs_utils.read_json(bucket_name, scene_file_path)

    # 'scenes'キーが存在するか確認
    scenes = scene_data.get("scenes", [])
    if not scenes:
        print("JSONファイルに'scenes'データが見つかりませんでした。")
        return

    # 各シーンをループして情報を表示
    for scene in scenes:
        scene_id = scene.get("scene_id")
        depiction = scene.get("depiction")
        composition = scene.get("composition", {})
        dialogue = scene.get("dialogue", [])
        other_info = scene.get("other_infomation", "なし")

        print(f"--- シーン {scene_id} ---")
        print(f"描写: {depiction}")
        
        print("\n- 構図情報:")
        for key, value in composition.items():
            print(f"  - {key}: {value}")

        if dialogue:
            print("\n- 会話:")
            for line in dialogue:
                character = line.get("character")
                text = line.get("line")
                print(f"  - {character}: 「{text}」")
        else:
            print("\n- 会話: なし")

        print(f"\n- その他情報: {other_info}")
        print("-" * 30)
        print("\n")


def edit_image(project_folder,story_ja_path, scene_ja_path, scene_en_path, story_en_path, user_input_ja_path, character_en_path, img_dir, revision_count,fix,input_fix):
    revised_scene_id = []
    for i, val in enumerate(fix):
        if val == "Y":
            scene_ja_path = scene.fix_slected_scene_from_story(BUCKET_NAME, i, story_ja_path, scene_ja_path, revision_count, input_fix[i], project_folder)
            output_scene_en_path = project_folder + f"json/scene_akakura_en_v{revision_count}.json"
            translate.translate_json(BUCKET_NAME, scene_ja_path, output_scene_en_path)
            revised_scene_id.append(i)

            continue
        else:
            continue
    print("修正点を受け付けました。絵コンテを再生成します")
    
    scene_prompt = make_scene_prompt.generate_scene_prompts_from_json(BUCKET_NAME, output_scene_en_path, story_en_path, user_input_ja_path)
    print(scene_prompt)
    save_img_name = "akakuraPR" + f"_v{revision_count}"
    
    data = gcs_utils.read_json(BUCKET_NAME, user_input_ja_path)
    progression = data.get("progression")
    
    if "登場人物型" == progression:
        print("登場人物型で画像修正を開始")
        character_data = gcs_utils.read_json(BUCKET_NAME, character_en_path)

        name = character_data.get("name", "unknown")

        save_path = img_dir + name + ".png"

        for j in range(len(scene_prompt)):
            # 修正したシーンだけ修正するように
            for k in range(len(revised_scene_id)):
                if (revised_scene_id[k] == j):
                    # 修正したシーンだけの処理はここ
                    prompt = scene_prompt[j]
                    img_path = save_path
                    print(f"--- Prompt for Scene {j+1} ---")
                    print(prompt)
                    print("-" * 25)
                    generate_scene_image.safe_generate_image(BUCKET_NAME, prompt, \
                        img_path, img_dir, j, save_img_name)
                else:
                    continue
            continue
        
    elif "ナレーション型" == progression:
        print("ナレーション型で画像修正を開始")
        for j in range(len(scene_prompt)):
            # 修正したシーンだけ修正するように
            for k in range(len(revised_scene_id)):
                if (revised_scene_id[k] == j):
                    # 修正したシーンだけの処理はここ
                    prompt = scene_prompt[j]
                    print(f"--- Prompt for Scene {j+1} ---")
                    print(prompt)
                    print("-" * 25)
                    generate_scene_image.safe_generate_image_no_character(BUCKET_NAME, prompt, img_dir, j, save_img_name, user_input_ja_path)
                else:
                    continue
            continue

    print("絵コンテ修正を終了します")


def main(project_folder):
    story_ja_path = project_folder + "json/story_script_akakura_ja.json"
    story_en_path = project_folder + "json/story_script_akakura_en.json"
    character_ja_path = project_folder + "json/character_akakura_ja.json"
    character_en_path = project_folder + "json/character_akakura_en.json"
    user_input_ja_path = project_folder + "json/user_input_akakura_ja.json"
    user_input_en_path = project_folder + "json/user_input_akakura_en.json"
    scene_ja_path = project_folder + "json/scene_akakura_ja.json"
    scene_en_path = project_folder + "json/scene_akakura_en.json"

    img_dir = project_folder + "images/"

    save_img_name = "akakuraPR"
    
    print("キャラクターとシーンを生成します")
    
    data =  gcs_utils.read_json(BUCKET_NAME, user_input_ja_path)
    progression =  data.get("progression")
    if "登場人物型" == progression:
        create_image_with_character(BUCKET_NAME, story_ja_path, story_en_path, character_ja_path, character_en_path, \
        scene_ja_path, scene_en_path, user_input_ja_path, user_input_en_path,\
        img_dir, save_img_name)
    elif "ナレーション型" == progression:
        create_image_no_character(BUCKET_NAME, story_ja_path, story_en_path, character_ja_path, character_en_path, \
        scene_ja_path, scene_en_path, user_input_ja_path, user_input_en_path,\
        img_dir, save_img_name)
    else:
        create_image_with_character(BUCKET_NAME, story_ja_path, story_en_path, character_ja_path, character_en_path, \
        scene_ja_path, scene_en_path, user_input_ja_path, user_input_en_path,\
        img_dir, save_img_name)


    display_scenes_from_json(BUCKET_NAME, scene_ja_path)