import os, math, random
from gtts import tts

def padded_int_string(number: int, max_length: int = 10) -> str:
    int_string = str(number)
    return (max_length-len(int_string))*'0' + int_string

def get_filename(folder: str, extension: str):
    download_dir = "downloads"
    if not os.path.isdir(download_dir):
        os.mkdir(download_dir)
    file_dir = os.path.join(download_dir, folder)
    if not os.path.isdir(file_dir):
        os.mkdir(file_dir)
    index = 0
    filename = os.path.join(file_dir, f"{folder}_{padded_int_string(index)}.{extension}")
    while os.path.isfile(filename):
        index += 1
        filename = os.path.join(file_dir, f"{folder}_{padded_int_string(index)}.{extension}")
    # creating empty file
    empty = open(filename, "wb")
    empty.close()
    return filename

def get_ytdl_options() -> (dict, str):
    '''returns ytdl options and the output filename used'''
    output_file = get_filename("audio", "m4a")
    ytdl_options = {
        "format": "m4a/bestaudio/best",
        "outtmpl": output_file,
        "noplaylist": True,
    }
    return ytdl_options, output_file

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

def generate_lang_help():
    available_langs = list(tts.tts_langs().items())
    langs_per_help = 20
    for i in range(math.ceil(len(available_langs)/langs_per_help)):
        help_text = ""
        for j in range(langs_per_help):
            index = i*langs_per_help + j
            if index < len(available_langs):
                help_text += f"{index+1}. **{available_langs[index][0]}** - {available_langs[index][1]}\n"
        yield help_text.rstrip()
