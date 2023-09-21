import asyncio, logging, os, discord
from bot import create_bot

discord.opus.load_opus("libopus.so.0")
if not discord.opus.is_loaded():
    logging.warning("opus not loaded.")

try:
    from secret import bot_token
except ModuleNotFoundError:
    bot_token = os.getenv("DISCORD_TOKEN")

if __name__ == "__main__":
    try:
        bot = asyncio.run(create_bot())
        bot.run(bot_token)
    except Exception as e:
        logging.error(e)
