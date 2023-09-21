from discord.ext import commands
import discord

class General(commands.Cog):
    def __init__(self, bot: commands.Bot):
        super().__init__()
        self.bot = bot

    @commands.command(
        name="come",
        description="Can I come into your vc?",
        usage="!come",
        brief="Invites Bocchi into your voice channel.",
        help="Invites Bocchi into your voice channel."
    )
    async def come(self, ctx: commands.Context):
        sender_voice = ctx.author.voice
        bocchi_voice = ctx.voice_client
        if sender_voice is None:
            await ctx.reply("You are not in any voice channel.", mention_author=False)
            return
        sender_vc = sender_voice.channel
        if bocchi_voice is not None:
            await bocchi_voice.disconnect()
        await sender_vc.connect()
        await ctx.message.add_reaction('✅')
    
    @commands.command(
        name="speak",
        description="Anoo...",
        usage="!speak [what to speak]",
        brief="Bocchi will say what you send.",
        help="Bocchi will say what you send."
    )
    async def speak(self, ctx: commands.Context, *, text: str = "Hi"):
        bocchi_voice: discord.VoiceClient = ctx.voice_client
        if bocchi_voice is None:
            await ctx.reply("Invite me into a voice chat first.", mention_author=False)
            return
        audio_file = "audio/hello.mp3"
        print(bocchi_voice.average_latency)
        bocchi_voice.play(discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(audio_file)), after=lambda e: print(f'Player error: {e}') if e else None)
        await ctx.channel.send(f"Playing: {audio_file}")
        await ctx.message.add_reaction('✅')
