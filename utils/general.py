import os, math, random
from gtts import tts

def padded_intstring(number: int, max_length: int = 10) -> str:
    intstring = str(number)
    return (max_length-len(intstring))*'0' + intstring

def get_filename(folder: str, extension: str):
    file_dir = os.path.join("downloads", folder)
    index = 0
    filename = os.path.join(file_dir, f"{folder}_{padded_intstring(index)}.{extension}")
    while os.path.isfile(filename):
        index += 1
        filename = os.path.join(file_dir, f"{folder}_{padded_intstring(index)}.{extension}")
    return filename

def get_ytdl_options() -> (dict, str):
    '''returns ytdl options and the output filename used'''
    output_file = get_filename("audio", "mp4")
    ytdl_options = {
        'format': 'm4a/bestaudio/best',
        # 'extractaudio': True,
        # 'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
        'outtmpl': output_file,
        # 'restrictfilenames': True,
        'noplaylist': True,
        # 'nocheckcertificate': True,
        # 'ignoreerrors': False,
        # 'logtostderr': False,
        # 'quiet': True,
        # 'no_warnings': True,
        # 'default_search': 'ytsearch',
        # 'source_address': '0.0.0.0',
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
            help_text += f"{index+1}. **{available_langs[index][0]}** - {available_langs[index][1]}\n"
        yield help_text.rstrip()
