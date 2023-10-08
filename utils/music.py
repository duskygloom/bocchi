import logging, os, platform, asyncio
from async_timeout import timeout
from discord.ext import commands
from utils.general import get_filename
from functools import partial
from gtts import gTTS
from yt_dlp import YoutubeDL, utils as yt_utils
import aiohttp

audio_dir = os.path.join("downloads", "audio")
max_song_duration = 1800
song_extension = "m4a"
song_quality = "medium"
max_download_size = 200_000_000

ytdl_options = {
    "format": f"{song_extension}/{song_quality}",
    "outtmpl": f"{audio_dir}/%(id)s.{song_extension}",
    "noplaylist": True,
}

ffmpeg_options = {
    "before_options": "",
    "options": "-vn"
}

ffmpeg_dir = "ffmpeg-essentials"
ffmpeg_path = "ffmpeg"
if os.path.isdir(ffmpeg_dir) and platform.system() == "Windows":
    ffmpeg_path = os.path.join(ffmpeg_dir, "bin", "ffmpeg.exe")

class Song:
    def __init__(self, result_raw: dict, complete: bool = False):
        self.id = result_raw.get("id")
        self.url = result_raw.get("url") or result_raw("original_url")
        self.title = result_raw.get("title")
        self.duration = result_raw.get("duration")
        self.artist = result_raw.get("channel")
        self.cover = result_raw.get("thumbnails")[-1].get("url")
        self.source = os.path.join(audio_dir, f"{self.id}.{song_extension}")
        self.source_url = None
        if complete:
            self.source_url = get_audio_url(result_raw)
        
    def clear_downloads(self):
        total_size = 0
        for file in os.listdir(audio_dir):
            path = os.path.join(audio_dir, file)
            if os.path.isfile(path):
                total_size += os.path.getsize(path)
        if total_size > max_download_size:
            for file in os.listdir(audio_dir):
                path = os.path.join(audio_dir, file)
                if os.path.isfile(path):
                    os.remove(os.path.join(audio_dir, file))
                    logging.warning(f"Deleted: {path}")

    async def download(self):
        self.clear_downloads()
        YoutubeDL(ytdl_options).download(self.url)

    def duration_str(self) -> str:
        text = f"{int(self.duration//60)} mins {int(self.duration%60)} secs"
        return text

    def exists(self) -> bool:
        return os.path.exists(self.source)
    
async def get_songs(ctx: commands.Context, query: str) -> list[Song]:
    search_function = partial(search_youtube, query)
    async with ctx.typing():
        await ctx.message.add_reaction('⏳')
        search_results: list[Song] = await ctx.bot.loop.run_in_executor(None, search_function)
        await ctx.message.remove_reaction('⏳', ctx.bot.user)
        return search_results

async def download_song(ctx: commands.Context, song: Song) -> bool:
    if song.duration > max_song_duration:
        return False
    elif os.path.isfile(os.path.join(audio_dir, f"{song.id}.{song_extension}")):
        logging.warning(f"Already downloaded: {song.id}.{song_extension}")
        return True
    async with ctx.typing():
        await ctx.message.add_reaction('⬇️')
        await song.download()
        await ctx.message.remove_reaction('⬇️', ctx.bot.user)
        return True

def get_audio_url(info: dict) -> str:
    '''
        returns download url of the audio
        or returns empty string if not found
    '''
    for format in info.get("formats"):
        if format.get("acodec") != "none" and format.get("vcodec") == "none" and format.get("ext") == song_extension and format.get("format_note") == song_quality:
            return format.get("url")
    return ""

def search_youtube(query: str) -> list[Song]:
    max_results = 1
    results = []
    try:
        # assuming query is a youtube link
        info = YoutubeDL().extract_info(
            url=query, 
            download=False,
            process=False
        )
        if info.get("webpage_url_basename") == "playlist":
            for entry in info.get("entries"):
                results.append(Song(entry))
        else:
            results.append(Song(info, True))
    except Exception as e:
        logging.warning(e)
        # error means the youtube link was not found
        results_raw = YoutubeDL().extract_info(
            url=f"ytsearch{max_results}:{query}", 
            download=False, 
            process=False
        )
        for result in results_raw.get("entries"):
            try:
                results.append(Song(result))
            except TypeError as e:
                logging.error(e)
    return results

async def download_tts(ctx: commands.Context, tts_args: dict) -> str:
    async with ctx.typing():
        await ctx.message.add_reaction('⬇️')
        download_function = partial(download_speech, tts_args)
        ttsfile = await ctx.bot.loop.run_in_executor(None, download_function)
        if not ttsfile:
            await ctx.reply(f"Could not generate speech: {tts_args['text']}", mention_author=False)
        await ctx.message.remove_reaction('⬇️', ctx.bot.user)
    return ttsfile

def download_speech(tts_args: dict) -> str:
    try:
        speech = gTTS(tts_args["text"], lang=tts_args["lang"])
        ttsfile = get_filename("tts", "wav")
        speech.save(ttsfile)
        return ttsfile
    except Exception as e:
        logging.error(e)
        return ""
