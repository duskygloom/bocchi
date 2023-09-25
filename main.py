import asyncio, logging, os, discord
from bot import VoiceBot
from cogs.music_rewrite import Music
from cogs.general import General

try:
    from secret import bot_token
except ModuleNotFoundError:
    bot_token = os.getenv("DISCORD_TOKEN")

if __name__ == "__main__":
    try:
        bot = VoiceBot()
        @bot.event
        async def on_ready():
            for guild in bot.guilds:
                await guild.system_channel.send("Rock youuu!")
        asyncio.run(bot.add_cog(General(bot)))
        asyncio.run(bot.add_cog(Music(bot)))
        bot.run(bot_token)
    except Exception as e:
        logging.error(e)
