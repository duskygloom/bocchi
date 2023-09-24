from discord.ext import commands
from gtts import gTTS
from utils.general import get_filename, is_language, generate_lang_help, get_random_clip
from utils.music import get_voice_client, disconnect_client
import discord, os, asyncio

class General(commands.Cog):
    def __init__(self, bot: commands.Bot):
        super().__init__()
        self.bot = bot
        self.language = "ja"
        self.ffmpeg_options = {
            # "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
            "before_options": "",
            "options": "-vn"
        }

    @commands.command(
            name="greet",
            brief="Bocchi says hi."
    )
    async def greet(self, ctx: commands.Context):
        voice_client = await get_voice_client(ctx)
        greet_audio = os.path.join("downloads", "preloaded", "hello.m4a")
        if not os.path.isfile(greet_audio):
            await self.speak(ctx)
        voice_client.play(discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(greet_audio, **self.ffmpeg_options)))

    @commands.command(
            name = "speak",
            brief = "Random Bocchi lines from the anime."
    )
    async def speak(self, ctx: commands.Context):
        voice_client = await get_voice_client(ctx)
        if not voice_client: return
        clip = get_random_clip()
        voice_client.play(discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(clip, **self.ffmpeg_options)))
        await ctx.message.add_reaction('✅')
    
    @commands.command(
        name = "language",
        brief = "Changes language of google."
    )
    async def language(self, ctx: commands.Context, language: str = ""):
        lang = is_language(language)
        if lang:
            self.language = language
            await ctx.reply(f"Language set: {lang}", mention_author=False)
            await ctx.message.add_reaction('✅')
            return
        await ctx.reply(f"Language not found: {language}", mention_author=False)
        generator = generate_lang_help()
        while True:
            try:
                await ctx.send(next(generator))
                # await asyncio.sleep(1)
            except StopIteration:
                break
        await ctx.message.add_reaction('✅')

    @commands.command(
        name="google",
        brief="Google like tts."
    )
    async def google(self, ctx: commands.Context, *, text: str = "hi"):
        voice_client = await get_voice_client(ctx)
        if not voice_client:
            return
        text = text.lower()
        speech = gTTS(text, lang=self.language)
        ttsfile = get_filename("tts", "wav")
        speech.save(ttsfile)
        voice_client.play(discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(ttsfile, **self.ffmpeg_options)), after=lambda e: os.remove(ttsfile))
        await ctx.message.add_reaction('✅')
        # while voice_client.is_playing():
        #     await asyncio.sleep(1)
        # os.remove(ttsfile)

    @commands.command(
        name = "come",
        brief = "Bocchi comes into your voice chat."
    )
    async def come(self, ctx: commands.Context):
        voice_client = await get_voice_client(ctx)
        if voice_client:
            await ctx.message.add_reaction('✅')

    @commands.command(
        name = "go",
        brief = "Bocchi goes out of your voice chat."
    )
    async def go(self, ctx: commands.Context):
        await disconnect_client(ctx)
        self.voice_client = None
        await ctx.message.add_reaction('✅')
