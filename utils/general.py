import os, random, logging
from gtts import tts
from discord import Embed, Color

def padded_int_string(number: int, max_length: int = 10) -> str:
    int_string = str(number)
    return (max_length-len(int_string))*'0' + int_string

def get_filename(folder: str, extension: str, create_file: bool = True):
    # returns just the directory if create file is False
    # else returns the filename
    download_dir = "downloads"
    if not os.path.isdir(download_dir):
        os.mkdir(download_dir)
    file_dir = os.path.join(download_dir, folder)
    if not os.path.isdir(file_dir):
        os.mkdir(file_dir)
    if not create_file: return file_dir
    index = 0
    filename = os.path.join(file_dir, f"{folder}_{padded_int_string(index)}.{extension}")
    while os.path.isfile(filename):
        index += 1
        filename = os.path.join(file_dir, f"{folder}_{padded_int_string(index)}.{extension}")
    # creating empty file
    empty = open(filename, "wb")
    empty.close()
    return filename

def is_language(lang: str) -> str | None:
    langs = tts.tts_langs()
    if lang in langs:
        return langs[lang]
    
def get_random_clip():
    clip_dir = os.path.join("downloads", "preloaded", "clips")
    clip_ext = ".mp4"
    clips = []
    for file in os.listdir(clip_dir):
        filepath = os.path.join(clip_dir, file)
        if os.path.isfile(filepath) and filepath.endswith(clip_ext):
            clips.append(filepath)
    return random.choice(clips)

def get_language_embeds() -> list[Embed]:
    available_langs = list(tts.tts_langs().items())
    if len(available_langs) == 0:
        logging.warning("No tts language found.")
        return
    max_field = 24
    embeds = []
    index = 0
    for i in range(len(available_langs)//max_field):
        lang_embed = Embed(color=Color.pink())
        for j in range(max_field):
            lang_embed.add_field(
                name=f"*#{index+1}* **/ {len(available_langs)}**", 
                value=f"{available_langs[index][0]}\n{available_langs[index][1]}"
            )
            index += 1
        embeds.append(lang_embed)
    if len(available_langs) % max_field == 0:
        return embeds
    lang_embed = Embed(color=Color.pink())
    for i in range(len(available_langs)%max_field):
        lang_embed.add_field(
            name=f"*#{index+1}* **/ {len(available_langs)}**", 
            value=f"{available_langs[index][0]}\n{available_langs[index][1]}"
        )
        index += 1
    embeds.append(lang_embed)
    return embeds
