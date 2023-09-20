import asyncio, secret, logging
from bot import create_bot

if __name__ == "__main__":
    try:
        bot = asyncio.run(create_bot())
        bot.run(secret.bot_token)
    except Exception as e:
        logging.error(e)
