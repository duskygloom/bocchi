import asyncio, logging, os, discord
from bot import create_bot
# from ctypes.util import find_library

# opus_so_name = find_library("opus")
# logging.warning(f"opus shared object: {opus_so_name}")
# os.system("ls /usr/lib/x86_64-linux-gnu | grep libopus")
# if not discord.opus.is_loaded():
#     discord.opus.load_opus(opus_so_name)

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
