from discord.ext import commands
from bot import VoiceBot
from utils.music import get_songs, download_song, ffmpeg_path, Song
import typing, logging, asyncio, discord

class Music(commands.Cog):
    def __init__(self, bot: VoiceBot):
        super().__init__()
        self.bot = bot
        self.ffmpeg_options = {
            "before_options": "",
            "options": "-vn"
        }
        self._repeat = False
        self._loop = False
        self._volume = 90
        self._playing = False
        self._index = 1                         # this index is the real index + 1
        self._queue: list[Song] = []

    def finish(self, error, ctx):
        logging.error(error)
        if self._repeat:
            asyncio.run_coroutine_threadsafe(self.play(ctx), self.bot.loop)
        else:
            asyncio.run_coroutine_threadsafe(self.next(ctx), self.bot.loop)

    @commands.command(
        name = "play",
        brief = "Bocchi plays a song."
    )
    async def play(self, ctx: commands.Context, *, query: typing.Optional[str] = ""):
        # getting and checking client
        if not self.bot.current_client:
            await ctx.reply("Invite me into a voice channel first.", mention_author=False)
            return
        # prepends the song if provided
        if query:
            songs = await get_songs(ctx, query)
            if len(songs) == 0:
                await ctx.reply(f"Could not find any song: {query}", mention_author=False)
                return
            self._queue = self._queue[:self._index-1] + songs + self._queue[self._index-1:]
        # checking if there's song in the queue
        if len(self._queue) == 0:
            await ctx.reply("No songs in the queue.", mention_author=False)
            return
        # download song
        status = await self.load_source(ctx, self._index)
        if not status: return
        # playing song
        if self.bot.current_client.is_playing():
            self.bot.current_client.pause()
        self._playing = True
        self.bot.current_client.play(
            discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(self._queue[self._index-1].source, **self.ffmpeg_options, executable=ffmpeg_path), volume=self._volume/100), 
            after=lambda e: self.finish(e, ctx)
        )
        await self.current(ctx)
        # download next song in advance
        if self._index < len(self._queue):
            await self.load_source(ctx, self._index+1)

    async def load_source(self, ctx: commands.Context, index: int) -> bool:
        if not index > 0 and index <= len(self._queue):
            await ctx.reply(f"Unexpected index: {index}", mention_author=False)
            return False
        currsong = self._queue[index-1]
        status = await download_song(ctx, currsong)
        while not status:
            await ctx.reply(f"Cannot download {currsong.title}.", mention_author=False)
            self._queue.pop(index)
            if self._index > len(self._queue):
                self._index = len(self._queue)
            if len(self._queue) == 0:
                break
            status = await download_song(ctx, currsong)
        if not currsong.exists():
            await ctx.reply(f"Source does not exist: {currsong.title}.", mention_author=False)
            return False
        return True

    @commands.command(
        name = "next",
        brief = "Bocchi plays the next song in queue.",
        aliases = ["skip"]
    )
    async def next(self, ctx: commands.Context):
        if len(self._queue) == 0:
            await ctx.reply("Empty queue.", mention_author=False)
            return
        # if not loop, stops playing songs
        if len(self._queue) == self._index and not self._loop:
            await ctx.reply("No more songs in the queue.", mention_author=False)
            return
        # if loop, index changed to 0
        elif len(self._queue) == self._index:
            self._index = 0
        self._index += 1
        await self.play(ctx)
    
    @commands.command(
        name = "prev",
        brief = "Bocchi plays the previous song in queue.",
    )
    async def prev(self, ctx: commands.Context):
        if len(self._queue) == 0:
            await ctx.reply("Empty queue.", mention_author=False)
            return
        # if not loop, stops playing songs
        if self._index == 1 and not self._loop:
            await ctx.reply("No more songs in the queue.", mention_author=False)
            return
        # if loop, index changed to last song
        elif self._index == 1:
            self._index = len(self._queue) + 1
        self._index -= 1
        await self.play(ctx)

    @commands.command(
        name = "goto",
        brief = "Bocchi goes to the particaular song.",
        aliases = ["index"]
    )
    async def goto(self, ctx: commands.Context, index: int):
        if index <= 0 or index > len(self._queue):
            await ctx.reply(f"Unexpected index: {index}", mention_author=False)
            return
        self._index = index
        await self.play(ctx)
        await ctx.message.add_reaction('✅')

    @commands.command(
        name = "remove",
        brief = "Bocchi removes the particular song.",
        aliases = ["delete"]
    )
    async def remove(self, ctx: commands.Context, index: int):
        if index <= 0 or index > len(self._queue):
            await ctx.reply(f"Unexpected index: {index}", mention_author=False)
            return
        self._queue.pop(index-1)
        if self._index == index:
            await self.bot.current_client.pause()
            await self.play()
        await ctx.message.add_reaction('✅')

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
        description = "The volume of the current song can only be decreased.",
        aliases = ["vol"]
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
        brief = "Bocchi adds the song to the queue.",
        aliases = ["list"]
    )
    async def queue(self, ctx: commands.Context, *, query: typing.Optional[str] = ""):
        # appends the song if provided
        if query:
            songs = await get_songs(ctx, query)
            if len(songs) == 0:
                await ctx.reply(f"Could not find any song: {query}", mention_author=False)
                return
            self._queue.extend(songs)
            return
        # displays queue
        if len(self._queue) == 0:
            await ctx.reply("No songs in the queue.", mention_author=False)
            return
        max_field = 24
        async with ctx.typing():
            index = 0
            for i in range(len(self._queue)//max_field):
                info_embed = discord.Embed(color=discord.Color.pink())
                for j in range(max_field):
                    song = self._queue[index]
                    info_embed.add_field(name=f"*#{index+1}* **/ 0{len(self._queue)}**", value=f"**{song.title}**\nBy **{song.artist}**\n**Duration:** {song.duration_str()}")
                    index += 1
                await ctx.send(embed=info_embed, delete_after=45)
            if len(self._queue) % max_field == 0:
                return
            info_embed = discord.Embed(color=discord.Color.pink())
            for i in range(len(self._queue)%max_field):
                song = self._queue[index]
                info_embed.add_field(name=f"*#{index+1}* **/ 0{len(self._queue)}**", value=f"**{song.title}**\nBy **{song.artist}**\n**Duration:** {song.duration_str()}")
                index += 1
            await ctx.send(embed=info_embed, delete_after=45)

    @commands.command(
        name = "current",
        brief = "Bocchi sends info about the current song.",
        aliases = ["now"]
    )
    async def current(self, ctx: commands.Context):
        if not self._playing:
            await ctx.reply("No song is currently being played.", mention_author=False)
            return
        elif len(self._queue) == 0:
            await ctx.reply("Song queue is empty.", mention_author=False)
            return
        currsong = self._queue[self._index-1]
        embed = discord.Embed(title="**Now playing**", color=discord.Color.green(), description=f"**{currsong.title}**")
        embed.url = currsong.url
        embed.add_field(name="Artist", value=currsong.artist)
        embed.add_field(name="Duration", value=currsong.duration_str())
        embed.set_image(url=currsong.cover)
        await ctx.send(embed=embed, delete_after=45)

    @commands.command(
        name = "stop",
        brief = "Bocchi clears the song queue.",
        aliases = ["clear", "quit"]
    )
    async def stop(self, ctx: commands.Context):
        self._queue.clear()
        self._index = 1
        if self.bot.current_client:
            self.bot.current_client.stop()
        self._playing = False
        await ctx.message.add_reaction('✅')
