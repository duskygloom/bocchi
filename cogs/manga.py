import requests, json
from discord.ext import commands

class Manga(commands.Cog):
    def __init__(self, bot: commands.Bot):
        super().__init__()
        self.bot = bot

homepage = "https://mangasee123.com"

def generate_manga_id():
    r = requests.get(f"{homepage}/_search.php")
    json.loads()
