from discord.ext import commands
import discord

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
