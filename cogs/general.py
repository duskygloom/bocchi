from discord.ext import commands
from bot import VoiceBot
from utils.general import is_language, get_language_embeds, get_random_clip
from utils.music import download_tts, ffmpeg_path
from datetime import datetime
import discord, os, asyncio, logging, typing

class General(commands.Cog):
    def __init__(self, bot: VoiceBot):
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
        if not self.bot.current_client:
            await ctx.reply("Invite me into a voice channel first.", mention_author=False)
            return
        greet_audio = os.path.join("downloads", "preloaded", "hello.m4a")
        if not os.path.isfile(greet_audio):
            await self.clip(ctx)
            return
        await ctx.message.add_reaction('⏳')
        if self.bot.current_client.is_playing():
            self.bot.current_client.pause()
        def finish(error, ctx: commands.Context):
            logging.error(error)
            asyncio.run_coroutine_threadsafe(ctx.message.remove_reaction('⏳', self.bot.user), ctx.bot.loop)
            asyncio.run_coroutine_threadsafe(ctx.message.add_reaction('✅'), ctx.bot.loop)
        self.bot.current_client.play(discord.PCMVolumeTransformer(
            discord.FFmpegPCMAudio(greet_audio, **self.ffmpeg_options, executable=ffmpeg_path)), 
            after = lambda e: finish(e, ctx)
        )

    @commands.command(
            name = "clip",
            brief = "Random clips."
    )
    async def clip(self, ctx: commands.Context, send: typing.Optional[bool], *, clip_name: typing.Optional[str]):
        # checking client
        if not self.bot.current_client:
            await ctx.reply("Invite me into a voice channel first.", mention_author=False)
            return
        # selects clip
        elif clip_name:
            clip = os.path.join("downloads",  "preloaded", "clips", f"{clip_name}.mp4")
        else:
            clip = get_random_clip()
        if not os.path.isfile(clip):
            await ctx.reply(f"Could not find clip: {clip_name}", mention_author=False)
            clip = get_random_clip()
        await ctx.message.add_reaction('⏳')
        # plays clip
        if self.bot.current_client.is_playing():
            self.bot.current_client.pause()
        def finish(error, ctx: commands.Context):
            logging.error(error)
            asyncio.run_coroutine_threadsafe(ctx.message.remove_reaction('⏳', self.bot.user), ctx.bot.loop)
            asyncio.run_coroutine_threadsafe(ctx.message.add_reaction('✅'), ctx.bot.loop)
        self.bot.current_client.play(discord.PCMVolumeTransformer(
            discord.FFmpegPCMAudio(clip, **self.ffmpeg_options, executable=ffmpeg_path)), 
            after = lambda e: finish(e, ctx)
        )
        # sends clip
        if send:
            async with ctx.typing():
                await ctx.reply(f"{os.path.basename(clip)[:-4]}", file=discord.File(clip), mention_author=False)
        
    
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
        lang_embeds = get_language_embeds()
        for embed in lang_embeds:
            await ctx.send(embed=embed, delete_after=45)
        await ctx.message.add_reaction('✅')

    @commands.command(
        name="google",
        brief="Google like tts."
    )
    async def google(self, ctx: commands.Context, *, text: str = "hi"):
        # checking client
        if not self.bot.current_client:
            await ctx.reply("Invite me into a voice channel first.", mention_author=False)
            return
        # getting speech
        text = text.lower()
        ttsfile = await download_tts(ctx, tts_args={"text": text, "lang": self.language})
        # playing speech
        if self.bot.current_client and self.bot.current_client.is_playing():
            self.bot.current_client.pause()
        def finish(error, ctx: commands.Context):
            logging.error(error)
            os.remove(ttsfile)
            asyncio.run_coroutine_threadsafe(ctx.message.remove_reaction('⏳', self.bot.user), ctx.bot.loop)
            asyncio.run_coroutine_threadsafe(ctx.message.add_reaction('✅'), ctx.bot.loop)
        self.bot.current_client.play(discord.PCMVolumeTransformer(
            discord.FFmpegPCMAudio(ttsfile, **self.ffmpeg_options, executable=ffmpeg_path)), 
            after = lambda e: finish(e, ctx)
        )

    @commands.command(
        name = "come",
        brief = "Bocchi comes into your voice chat."
    )
    async def come(self, ctx: commands.Context):
        if not ctx.author.voice:
            await ctx.reply("You are not in any voice channel.", mention_author=False)
            return
        elif ctx.voice_client:
            if not self.bot.current_client:
                self.bot.current_client = await ctx.voice_client.connect(timeout=180, reconnect=True)
            await self.bot.current_client.move_to(ctx.author.voice.channel)
        else:
            self.bot.current_client = await ctx.author.voice.channel.connect()
        await ctx.message.add_reaction('✅')

    @commands.command(
        name = "go",
        brief = "Bocchi goes out of your voice chat."
    )
    async def go(self, ctx: commands.Context):
        if self.bot.current_client and self.bot.current_client.is_playing():
            self.bot.current_client.pause()
        if ctx.voice_client:
            await ctx.voice_client.disconnect()
        self.bot.current_client = None
        await ctx.message.add_reaction('✅')

    @commands.command(
        name = "sleep",
        brief = "Bocchi shuts down.",
        alias = ["off", "shutdown"]
    )
    async def sleep(self, ctx: commands.Context, *, reason: str = "No reason specified."):
        if ctx.author.guild_permissions.administrator:
            with open("sleep_reason.txt", "w") as f:
                f.write(f"{datetime.now().isoformat()} -> {ctx.author}: {reason}")
            await ctx.reply("Bye bye.", mention_author=False)
            await ctx.bot.close()
        else:
            await ctx.reply("You are not an administrator.", mention_author=False)
