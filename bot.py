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

    async def get_author_voice_client(self, author: discord.Member):
        if not author.voice: return
        elif self.current_client:
            self.current_client.move_to(author.voice.channel)
        else:
            self.current_client = await author.voice.channel.connect()

# async def load_cogs(bot: commands.Bot):
#     # await bot.add_cog(Music(bot))
#     await bot.add_cog(General(bot))
