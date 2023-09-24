from discord.ext import commands
from bot import VoiceBot
from gtts import gTTS
from utils.general import get_filename, is_language, generate_lang_help, get_random_clip
import discord, os, asyncio, logging

class General(commands.Cog):
    def __init__(self, bot: VoiceBot):
        super().__init__()
        self.bot = bot
        self.language = "ja"
        self.ongoing = False
        self.ffmpeg_options = {
            # "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
            "before_options": "",
            "options": "-vn"
        }

    def set_ongoing(self, status: bool = True):
        self.ongoing = status

    @commands.command(
            name="greet",
            brief="Bocchi says hi."
    )
    async def greet(self, ctx: commands.Context):
        await self.bot.get_author_voice_client(ctx.author)
        if not self.bot.current_client:
            await ctx.reply("You are not in any voice channel.", mention_author=False)
            return
        greet_audio = os.path.join("downloads", "preloaded", "hello.m4a")
        if not os.path.isfile(greet_audio):
            await self.speak(ctx)
            return
        await ctx.message.add_reaction('⏳')
        self.ongoing = True
        finish = lambda e: (logging.error(e), self.set_ongoing(False))
        self.bot.current_client.play(discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(greet_audio, **self.ffmpeg_options)), after=finish)
        while self.ongoing:
            await asyncio.sleep(1)
        self.ongoing = True
        await ctx.message.remove_reaction('⏳', self.bot.user)
        await ctx.message.add_reaction('✅')

    @commands.command(
            name = "speak",
            brief = "Random Bocchi lines from the anime."
    )
    async def speak(self, ctx: commands.Context, send_clip: bool = False):
        await self.bot.get_author_voice_client(ctx.author)
        if not self.bot.current_client:
            await ctx.reply("You are not in any voice channel.", mention_author=False)
            return
        clip = get_random_clip()
        await ctx.message.add_reaction('⏳')
        self.ongoing = True
        finish = lambda e: (logging.error(e), self.set_ongoing(False))
        self.bot.current_client.play(discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(clip, **self.ffmpeg_options)), after=finish)
        while self.ongoing:
            await asyncio.sleep(1)
        await ctx.message.remove_reaction('⏳', self.bot.user)
        await ctx.message.add_reaction('✅')
        if send_clip:
            async with ctx.typing():
                await ctx.reply(file=clip, mention_author=False)
    
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
            except StopIteration:
                break
        await ctx.message.add_reaction('✅')

    @commands.command(
        name="google",
        brief="Google like tts."
    )
    async def google(self, ctx: commands.Context, *, text: str = "hi"):
        await self.bot.get_author_voice_client(ctx.author)
        if not self.bot.current_client:
            await ctx.reply("You are not in any voice channel.", mention_author=False)
            return
        text = text.lower()
        await ctx.message.add_reaction('⏳')
        speech = gTTS(text, lang=self.language)
        ttsfile = get_filename("tts", "wav")
        speech.save(ttsfile)
        self.ongoing = True
        finish = lambda e: (logging.error(e), self.set_ongoing(False))
        self.bot.current_client.play(discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(ttsfile, **self.ffmpeg_options)), after=finish)
        while self.ongoing:
            await asyncio.sleep(1)
        await ctx.message.remove_reaction('⏳', self.bot.user)
        await ctx.message.add_reaction('✅')

    @commands.command(
        name = "come",
        brief = "Bocchi comes into your voice chat."
    )
    async def come(self, ctx: commands.Context):
        await self.bot.get_author_voice_client(ctx.author)
        if self.bot.current_client:
            await ctx.message.add_reaction('✅')
        else:
            await ctx.reply("You are not in any voice channel.", mention_author=False)

    @commands.command(
        name = "go",
        brief = "Bocchi goes out of your voice chat."
    )
    async def go(self, ctx: commands.Context):
        await self.bot.current_client.disconnect()
        self.bot.current_client = None
        await ctx.message.add_reaction('✅')
