import discord, logging
from discord.ext import commands
from yt_dlp import YoutubeDL
from utils.general import padded_intstring

class Music(commands.Cog):
    def __init__(self, bot: commands.Bot):
        super().__init__()
        self.bot = bot
        self.voice_channel = None
        self.repeat = False
        self.song_queue: list[dict[str, str]] = []
        self.ytdl_options = { "noplaylist" : True }
        self.ffmpeg_options = { "before_options": "-reconnect 2 -reconnect_streamed 2 -reconnect_delay_max 5" }

    def search_song(self, query: str) -> dict[str, str]:
        song = {"title": "", "url": ""}
        try:
            # assuming query is url
            video = YoutubeDL(params=self.ytdl_options).extract_info(query, download=False)
            info = video
        except Exception:
            # assuming it's a normal search query
            try:
                videos = YoutubeDL(params=self.ytdl_options).extract_info(f"ytsearch:{query}", download=False)
                if len(videos["entries"]) == 0:
                    return {}
                info = videos["entries"][0]
            except Exception as e:
                # something else happened
                logging.error(e)
                return {}
        song["title"] = info["title"]
        song["url"] = info["formats"][0]["url"]
        max_acodec = ""
        for format in info["formats"]:
            if "acodec" in format and "vcodec" in format and "ext" in format and format["vcodec"] == "none" and format["ext"] == "m4a":
                if format["acodec"] >= max_acodec:
                    max_acodec = format["acodec"]
                    song["url"] = format["url"]
        return song

    def add_song(self, query: str) -> bool:
        song = self.search_song(query)
        if song:
            self.song_queue.append(song)
            return True
        else:
            return False
        
    def play_song(self, url: str):
        if self.voice_channel:
            if self.voice_channel.is_playing():
                self.voice_channel.stop()
            after_function = lambda: self.next(url)
            if self.repeat:
                self.voice_channel.play(discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(
                    url,
                    before_options=self.ffmpeg_options,
                    options="-vn"
                )), after=lambda: self.play(url))
            self.voice_channel.play(discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(
                url,
                before_options=self.ffmpeg_options,
                options="-vn"
            )))

    @commands.command(
        name="play",
        brief="Okay let me play this song."
    )
    async def play(self, ctx: commands.Context, *, song: str = None):
        if ctx.author.voice is None:
            await ctx.reply("You are not in any voice channel.", mention_author=False)
            return
        elif ctx.voice_client is None:
            self.voice_channel = await ctx.author.voice.channel.connect()
        if song is not None:
            song = self.search_song(song)
        elif len(self.song_queue) == 0:
            await ctx.reply("No songs in the queue.", mention_author=False)
            return
        else:
            song = self.song_queue[0]
        song_title = song["title"]
        song_url = song["url"]
        self.song_queue.append(song)
        await ctx.reply(f"Playing {song_title} now.", mention_author=False)
        await self.play_song(song_url)
        await ctx.message.add_reaction('✅')

    @commands.command(
            name = "next",
            brief = "I'll play the next song then."
    )
    async def next(self, ctx: commands.Context):
        if len(self.song_queue) == 0:
            await ctx.reply("No songs in the queue.", mention_author=False)
            return
        elif len(self.song_queue) == 1:
            await ctx.reply("No songs left to play.", mention_author=False)
            self.song_queue.pop(0)
            return
        self.song_queue.pop(0)
        await self.play(self.song_queue[0]['url'])
        
    @commands.command(
            name="stop",
            brief="Okay I will stop that song."
    )
    async def stop(self, ctx: commands.Context):
        if self.voice_channel is None:
            await ctx.reply("I am not in any voice channel.", mention_author=False)
            return
        await self.voice_channel.disconnect()
        self.voice_channel = None
        await ctx.message.add_reaction('✅')

    @commands.command(
            name = "repeat",
            brief = "Toggle repeat."
    )
    async def repeat(self, ctx: commands.Context):
        self.repeat = not self.repeat
    
    @commands.command(
        name="queue",
        brief="This song will be eventually played."
    )
    async def queue(self, ctx: commands.Context, *, query: str = None):
        if query is not None:
            self.add_song(query)
            await ctx.message.reply(f"Added {self.song_queue[-1]['title']}.", mention_author=False)
        max_int_length = len(str(len(self.song_queue)))
        queue_embeds = []
        if len(self.song_queue) == 0:
            await ctx.reply("Empty queue.", mention_author=False)
            return
        for i in range(len(self.song_queue)):
            embed = discord.Embed(
                description=f"{padded_intstring(i+1, max_int_length)}. {self.song_queue[i]['title']}", 
                url=self.song_queue[i]['url'],
                color=discord.Color.pink()
            )
            queue_embeds.append(embed)
        await ctx.send(embeds=queue_embeds)
