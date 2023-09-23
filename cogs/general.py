from discord.ext import commands
from gtts import gTTS
from utils.general import padded_intstring
from utils.music import get_voice_client
import discord, os

class General(commands.Cog):
    def __init__(self, bot: commands.Bot):
        super().__init__()
        self.bot = bot
        self.voice_client: discord.VoiceClient = None

    @commands.command(
            name="greet",
            brief="Bocchi says hi."
    )
    async def greet(self, ctx: commands.Context):
        self.voice_client = await get_voice_client(ctx, self.voice_client)
        greet_audio = "audio/hello.m4a"
        if not os.path.isfile(greet_audio):
            await self.speak(ctx)
        self.voice_client.play(discord.FFmpegPCMAudio(greet_audio))

    @commands.command(
            name = "speak",
            brief = "Random Bocchi lines from the anime."
    )
    async def speak(self, ctx: commands.Context):
        self.voice_client = await get_voice_client(ctx, self.voice_client)
        clip_dir = "clips"
        clip_ext = ".m4a"
        clip_files = []
        for file in clip_dir:
            filepath = os.path.join(clip_dir, file)
            if os.path.isfile(filepath) and filepath.endswith(clip_ext):
                clip_files.append(filepath)
    
    @commands.command(
        name="google",
        brief="Google translate like tts."
    )
    async def google(self, ctx: commands.Context, *, text: str = "hi"):
        self.voice_client = await get_voice_client(ctx, self.voice_client)
        tts_location = os.path.join("audio", "gtts")
        tts_file = "bocchi_tts_"
        index = 0
        while os.path.isfile(os.path.join(tts_location, f"{tts_file}{padded_intstring(index)}.wav")):
            index += 1
        tts_file = os.path.join(tts_location, f"{tts_file}{padded_intstring(index)}.wav")
        if not os.path.isdir(tts_location):
            os.mkdir(tts_location)
        text = text.lower()
        sound = gTTS(text)
        sound.save(tts_file)
        self.voice_client.play(discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(tts_file)))
        os.remove(tts_file)

    @commands.command(
        name = "come",
        brief = "Bocchi comes into your voice chat."
    )
    async def come(self, ctx: commands.Context):
        self.voice_client = await get_voice_client(ctx, self.voice_client)
        await ctx.message.add_reaction('✅')

    @commands.command(
        name = "go",
        brief = "Bocchi goes out of your voice chat."
    )
    async def go(self, ctx: commands.Context):
        if ctx.voice_client:
            await ctx.voice_client.disconnect()
        self.voice_client = None
        await ctx.message.add_reaction('✅')