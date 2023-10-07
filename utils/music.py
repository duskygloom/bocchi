import logging, os, platform, asyncio
from async_timeout import timeout
from discord.ext import commands
from utils.general import get_filename
from functools import partial
from gtts import gTTS
from yt_dlp import YoutubeDL

audio_dir = get_filename("audio", "m4a", create_file=False)
ytdl_options = {
    "format": "m4a/bestaudio",
    "outtmpl": f"{audio_dir}/%(id)s.m4a",
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
    def __init__(
            self,
            title: str = "",
            artist: str = "",
            url: str = "",
            path: str = "",
            cover: str = "",
            duration: int = 0
    ):
        self.title = title or ""
        self.artist = artist or ""
        self.url = url or ""
        self.path = path or ""
        self.cover = cover or ""
        self.duration = duration or 0

    def duration_str(self) -> str:
        duration = f"{self.duration//60} minutes {self.duration%60} seconds"
        return duration

    def exists(self) -> bool:
        return os.path.isfile(self.path)

async def async_downloader(ctx: commands.Context, song: str = None, tts_args: dict = None) -> Song | str:
    '''
        returns Song object if song
        else returns file name of tts
    '''
    async with ctx.typing():
        await ctx.message.add_reaction('⬇️')
        download_task = None
        if song:
            download_function = partial(download_song, song)
            recieved = await ctx.bot.loop.run_in_executor(None, download_function)
            await ctx.message.remove_reaction('⬇️', ctx.bot.user)
            return recieved
        elif tts_args:
            download_function = partial(download_speech, tts_args)
            ttsfile = await ctx.bot.loop.run_in_executor(None, download_function)
            if not ttsfile:
                await ctx.reply(f"Could not generate speech: {tts_args['text']}", mention_author=False)
            await ctx.message.remove_reaction('⬇️', ctx.bot.user)
            return ttsfile
        

def download_song(query: str) -> Song:
    '''returns info as output'''
    # clears folder if too many stuff
    max_download_size = 500_000_000
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
    # downloading part
    info = {}
    try:
        info = YoutubeDL(ytdl_options).extract_info(query)
    except Exception:
        try:
            results = YoutubeDL(ytdl_options).extract_info(f"ytsearch:{query}")
            if len(results["entries"]) == 0:
                logging.error(f"Song not found: {query}")
            info = results["entries"][0]
        except Exception as e:
            logging.error(e)
    if not info:
        return Song()
    return Song(
        title = info.get("title"),
        artist = info.get("uploader"),
        url = info.get("original_url"),
        path = os.path.join(audio_dir, f"{info.get('id')}.m4a"),
        cover = info.get("thumbnail"),
        duration = info.get("duration")
    )

def download_speech(tts_args: dict) -> str:
    try:
        speech = gTTS(tts_args["text"], lang=tts_args["lang"])
        ttsfile = get_filename("tts", "wav")
        speech.save(ttsfile)
        return ttsfile
    except Exception as e:
        logging.error(e)
