import asyncio, logging, os
from bot import create_bot

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
