import discord
from discord.ext import commands

class VoiceBot(commands.Bot):
    def __init__(
            self,
            cmd_prefex: str = "!",
            intents: discord.Intents = discord.Intents().all(),
            activity: str = "...",
            status: discord.Status = discord.Status.idle
    ):
        super().__init__(command_prefix=cmd_prefex, intents=intents)
        self.activity = discord.CustomActivity(activity)
        self.status = status
        self.current_client: discord.VoiceClient = None

    async def get_author_voice_client(self, ctx: commands.Context):
        if not ctx.author.voice:
            await ctx.reply("You are not connected to any voice channel.", mention_author=False)
            return
        elif self.current_client and ctx.voice_client:
            await self.current_client.move_to(ctx.author.voice.channel)
        elif self.current_client:
            self.current_client = None
            return
        else:
            self.current_client = await ctx.author.voice.channel.connect()

    async def disconnect_voice(self, ctx: commands.Context):
        if not ctx.voice_client:
            await ctx.reply("I am not in any voice channel.", mention_author=False)
        else:
            await ctx.voice_client.disconnect()
        self.current_client = None
