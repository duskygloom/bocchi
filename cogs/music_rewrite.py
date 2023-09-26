from discord.ext import commands
from bot import VoiceBot
from utils.music import async_downloader, ffmpeg_path
import typing, logging, asyncio, discord

class Music(commands.Cog):
    def __init__(self, bot: VoiceBot):
        super().__init__()
        self.bot = bot
        self.ffmpeg_options = {
            "before_options": "",
            "options": "-vn"
        }
        self._ongoing = False
        self._repeat = False
        self._volume = 90
        self._playing = False
        self.song_queue = []

    def set_ongoing(self, status: bool = True):
        self._ongoing = status

    @commands.command(
        name = "play",
        brief = "Bocchi plays a song."
    )
    async def play(self, ctx: commands.Context, *, song: typing.Optional[str] = ""):
        if not song and len(self.song_queue) == 0:
            await ctx.reply("No songs in the queue.", mention_author=False)
            return
        # prepends the song if provided
        elif song:
            info = await async_downloader(ctx, song=song)
            if not info: return
            self.song_queue.insert(0, info)
        # plays song from queue
        else:
            info = self.song_queue[0]
        # getting and checking client
        if not self.bot.current_client:
            await ctx.reply("Invite me into a voice channel first.", mention_author=False)
            return
        # playing song
        await ctx.message.add_reaction('⏳')
        finish = lambda e: (logging.error(e), self.set_ongoing(False))
        self._playing = True
        self.set_ongoing()
        self.bot.current_client.play(
            discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(info.get("path"), **self.ffmpeg_options, executable=ffmpeg_path), volume=self._volume/100), 
            after=finish
        )
        await self.current(ctx)
        while self._ongoing:
            await asyncio.sleep(1)
        await ctx.message.remove_reaction('⏳', self.bot.user)
        if self._playing and self._repeat:
            await self.play(ctx)
        elif self._playing and not self._repeat:
            await self.next(ctx)

    @commands.command(
        name = "next",
        brief = "Bocchi plays the next song in queue."
    )
    async def next(self, ctx: commands.Context):
        if len(self.song_queue) == 0:
            await ctx.reply("Empty queue.", mention_author=False)
            return
        elif len(self.song_queue) == 1:
            await ctx.reply("No more songs in the queue.", mention_author=False)
            self.song_queue.pop(0)
            return
        self.song_queue.pop(0)
        await self.play(ctx)

    @commands.command(
        name = "pause",
        brief = "Bocchi pauses the song."
    )
    async def pause(self, ctx: commands.Context):
        if not self.bot.current_client:
            await ctx.reply("Invite me into a voice channel first.", mention_author=False)
            return
        self.bot.current_client.pause()
        self._playing = False
        await ctx.message.add_reaction('✅')
    
    @commands.command(
        name = "resume",
        brief = "Bocchi resumes the song."
    )
    async def resume(self, ctx: commands.Context):
        if not self.bot.current_client:
            await ctx.reply("Invite me into a voice channel first.", mention_author=False)
            return
        self.bot.current_client.resume()
        self._playing = True
        await ctx.message.add_reaction('✅')

    @commands.command(
        name = "repeat",
        brief = "Bocchi plays the next song in repeat."
    )
    async def repeat(self, ctx: commands.Context):
        self._repeat = not self._repeat
        await ctx.reply(f"Repeat mode: {self._repeat}", mention_author=False)

    @commands.command(
        name = "volume",
        brief = "Bocchi changes the volume of the song.",
        description = "The volume of the current song can only be decreased."
    )
    async def volume(self, ctx: commands.Context, volume: int = 90):
        if not self.bot.current_client:
            await ctx.reply("Invite me into a voice channel first.", mention_author=False)
            return
        elif volume > 100 or volume < 0:
            await ctx.reply("Volume must be between 0 and 100.", mention_author=False)
        else:
            self._volume = volume
            source = self.bot.current_client.source
            if source and self.bot.current_client.is_playing():
                self.bot.current_client.source = discord.PCMVolumeTransformer(source, volume/100)
            await ctx.message.add_reaction('✅')

    @commands.command(
        name = "queue",
        brief = "Bocchi adds the song to the queue."
    )
    async def queue(self, ctx: commands.Context, *, song: typing.Optional[str] = ""):
        # appends the song if provided
        if song:
            info = await async_downloader(ctx, song=song)
            if not info: return
            self.song_queue.append(info)
            await ctx.reply(f"Added to queue: {info.get('title')}", mention_author=False)
            return
        # displays queue
        async with ctx.typing():
            index = 1
            for info in self.song_queue:
                info_embed = discord.Embed(color=discord.Color.pink(), title=f"Song #{index}")
                info_embed.add_field(name="Title", value=info.get("title"))
                info_embed.add_field(name="Artist", value=info.get("uploader"))
                info_embed.set_thumbnail(url=info.get("thumbnail"))
                await ctx.send(embed=info_embed)
                index += 1

    @commands.command(
        name = "current",
        brief = "Bocchi sends info about the current song."
    )
    async def current(self, ctx: commands.Context):
        if not self._playing:
            await ctx.reply("No song is currently being played.", mention_author=False)
            return
        elif len(self.song_queue) < 1:
            await ctx.reply("Song queue is empty.", mention_author=False)
            return
        embed = discord.Embed(title="**Now playing**", color=discord.Color.green(), description=f"**{self.song_queue[0].get('title')}**")
        embed.url = self.song_queue[0].get("url")
        embed.add_field(name="Artist", value=self.song_queue[0].get("uploader"))
        duration_seconds = self.song_queue[0].get("duration")
        embed.add_field(name="Duration", value=f"{duration_seconds//60} minutes {duration_seconds%60} seconds")
        embed.set_image(url=self.song_queue[0].get('thumbnail'))
        await ctx.send(embed=embed)
    @commands.command(
        name = "clear",
        brief = "Bocchi clears the song queue."
    )
    async def clear(self, ctx: commands.Context):
        self.song_queue.clear()
        await ctx.message.add_reaction('✅')
