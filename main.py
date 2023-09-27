import asyncio, logging, os, sys
from bot import VoiceBot
from discord.ext import commands
from cogs.music_rewrite import Music
from cogs.general import General

try:
    from secret import bot_token
except ModuleNotFoundError:
    token_env = "BOCCHI_DISCORD_TOKEN"
    bot_token = os.getenv(token_env)
    if bot_token is None:
        logging.error(f"Token not found. Try setting the value of {token_env} environment variable.")
        sys.exit(0)

if __name__ == "__main__":
    try:
        bot = VoiceBot()
        # startup event
        @bot.event
        async def on_ready():
            for guild in bot.guilds:
                await guild.system_channel.send("Rock youuu!")
        @bot.event
        async def on_command_error(ctx: commands.Context, error: commands.CommandError):
            await ctx.reply(f"Error: {error}", mention_author=False)
        # loading cog
        asyncio.run(bot.add_cog(General(bot)))
        asyncio.run(bot.add_cog(Music(bot)))
        bot.run(bot_token)
    except Exception as e:
        logging.error(e)
