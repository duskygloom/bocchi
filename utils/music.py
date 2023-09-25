import discord, logging, os, asyncio
from discord.ext import commands
from yt_dlp import YoutubeDL
from utils.general import get_filename
from functools import partial
from gtts import gTTS

voice_client: discord.VoiceClient = None

audio_dir = get_filename("audio", "m4a", create_file=False)
ytdl_options = {
    "format": "m4a/bestaudio",
    "outtmpl": f"{audio_dir}/%(id)s.m4a",
    "noplaylist": True,
}

async def get_voice_client(ctx: commands.Context) -> discord.VoiceClient | None:
    '''
        returns None if author is not connected to voice
        else returns client
    '''
    global voice_client
    if not ctx.author.voice:
        # does not return client if author is not connected to voice
        await ctx.reply("You are not in any voice channel.", mention_author=False)
        return
    elif ctx.voice_client and voice_client:
        # if client exists, moves to author's channel
        await voice_client.move_to(ctx.author.voice.channel)
        return voice_client
    elif ctx.voice_client and not voice_client:
        # disconnects if has an unsaved client
        await ctx.voice_client.disconnect()
    voice_client = await ctx.author.voice.channel.connect()
    return voice_client

async def disconnect_client(ctx: commands.Context):
    global voice_client
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
    voice_client = None

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
            return info
        elif tts_args:
            download_function = partial(download_speech, tts_args)
            ttsfile = await ctx.bot.loop.run_in_executor(None, download_function)
            if not ttsfile:
                await ctx.reply(f"Could not generate speech: {tts_args['text']}", mention_author=False)
            return ttsfile
        ctx.message.remove_reaction('⬇️', ctx.bot.user)

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
