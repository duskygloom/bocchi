import discord, logging, os, asyncio
from discord.ext import commands
from yt_dlp import YoutubeDL
from utils.general import get_filename
from functools import partial
from gtts import gTTS

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
ffmpeg_path = None
if os.path.isdir(ffmpeg_dir):
    ffmpeg_path = os.path.join(ffmpeg_dir, "bin", "ffmpeg.exe")
    
async def async_downloader(ctx: commands.Context, song: str = None, tts_args: dict = None) -> dict | str:
    '''
        returns info dict if song
        else returns file name of tts
    '''
    async with ctx.typing():
        await ctx.message.add_reaction('⬇️')
        if song:
            download_function = partial(download_song, song)
            info = await ctx.bot.loop.run_in_executor(None, download_function)
            if not info:
                await ctx.reply(f"Could not find any song: {song}", mention_author=False)
            await ctx.message.remove_reaction('⬇️', ctx.bot.user)
            return info
        elif tts_args:
            download_function = partial(download_speech, tts_args)
            ttsfile = await ctx.bot.loop.run_in_executor(None, download_function)
            if not ttsfile:
                await ctx.reply(f"Could not generate speech: {tts_args['text']}", mention_author=False)
            await ctx.message.remove_reaction('⬇️', ctx.bot.user)
            return ttsfile

def download_song(query: str):
    '''returns info as output'''
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
    if info:
        info["path"] = os.path.join(audio_dir, f"{info.get('id')}.m4a")
    return info

def download_speech(tts_args: dict) -> str:
    try:
        speech = gTTS(tts_args["text"], lang=tts_args["lang"])
        ttsfile = get_filename("tts", "wav")
        speech.save(ttsfile)
        return ttsfile
    except Exception as e:
        logging.error(e)
