import discord
from discord.ext import commands
from cogs.music import Music

async def create_bot(
        cmd_prefex: str = "!",
        intents: discord.Intents = discord.Intents().all(),
        activity: str = "...",
        status: discord.Status = discord.Status.idle
):
    bot = commands.Bot(
        command_prefix=cmd_prefex,
        intents=intents
    )
    bot.activity = discord.CustomActivity(name=activity)
    bot.status = status
    await load_cogs(bot)
    return bot

async def load_cogs(bot: commands.Bot):
    await bot.add_cog(Music(bot))
