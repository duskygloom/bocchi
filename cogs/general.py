from discord.ext import commands
from gtts import gTTS
import discord, os

class General(commands.Cog):
    def __init__(self, bot: commands.Bot):
        super().__init__()
        self.bot = bot
        self.bocchi_vc: discord.VoiceClient = None

    @commands.command(
        name="greet",
        brief="Hi user!",
        description="Bocchi greets you in the voice chat.",
        usage="!greet",
        help="Bocchi greets you in the voice chat."
    )
    async def greet(self, ctx: commands.Context):
        if ctx.author.voice is None:
            await ctx.reply("You are not in any voice channel.", mention_author=False)
            return
        if ctx.voice_client is None or self.bocchi_vc is None:
            self.bocchi_vc = await ctx.author.voice.channel.connect()
        greet_audio = "audio/hello.m4a"
        self.bocchi_vc.play(discord.FFmpegPCMAudio(greet_audio))
    
    @commands.command(
        name="say",
        brief="I say what you send.",
        description="Bocchi repeats after you in the voice chat.",
        usage="!say [what to say]",
        help="Bocchi repeats after you in the voice chat."
    )
    async def say(self, ctx: commands.Context, *, text: str = "hi"):
        if ctx.author.voice is None:
            await ctx.reply("You are not in any voice channel.", mention_author=False)
            return
        if ctx.voice_client is None or self.bocchi_vc is None:
            self.bocchi_vc = await ctx.author.voice.channel.connect()
        tts_location = os.path.join("audio", "gtts")
        if not os.path.isdir(tts_location):
            os.mkdir(tts_location)
        text = text.lower()
        tts_location = os.path.join(tts_location, text+'.wav')
        if not os.path.isfile(tts_location):
            sound = gTTS(text)
            sound.save(tts_location)
        self.bocchi_vc.play(discord.FFmpegPCMAudio(tts_location))
