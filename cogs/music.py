from discord.ext import commands
from bot import VoiceBot
from utils.music import get_songs, download_song, ffmpeg_path, Song, max_song_duration
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
        self._volume = 90
        self._playing = False
        self.song_queue: list[Song] = []

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
            self.song_queue.insert(0, songs[0])
        # checking if there's song in the queue
        if len(self.song_queue) == 0:
            await ctx.reply("No songs in the queue.", mention_author=False)
            return
        # download song
        status = await download_song(ctx, self.song_queue[0])
        while not status:
            await ctx.reply(f"Cannot download {self.song_queue[0].title}.", mention_author=False)
            self.song_queue.pop(0)
            print("popped")
            if len(self.song_queue) == 0:
                print("broken")
                break
            print("not broken")
            status = await download_song(ctx, self.song_queue[0])
        # playing song
        if self.bot.current_client.is_playing():
            self.bot.current_client.pause()
        self._playing = True
        self.bot.current_client.play(
            discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(self.song_queue[0].source, **self.ffmpeg_options, executable=ffmpeg_path), volume=self._volume/100), 
            after=lambda e: self.finish(e, ctx)
        )
        await self.current(ctx)

    @commands.command(
        name = "next",
        brief = "Bocchi plays the next song in queue.",
        aliases = ["skip"]
    )
    async def next(self, ctx: commands.Context):
        if len(self.song_queue) == 0:
            await ctx.reply("Empty queue.", mention_author=False)
            return
        elif len(self.song_queue) == 1:
            self.song_queue.pop()
            await ctx.reply("No more songs in the queue.", mention_author=False)
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
            for song in songs:
                self.song_queue.append(song)
            return
        # displays queue
        if len(self.song_queue) == 0:
            await ctx.reply("No songs in the queue.", mention_author=False)
            return
        max_field = 24
        async with ctx.typing():
            index = 0
            for i in range(len(self.song_queue)//max_field):
                info_embed = discord.Embed(color=discord.Color.pink())
                for j in range(max_field):
                    song = self.song_queue[index]
                    info_embed.add_field(name=f"*#{index+1}* **/ 0{len(self.song_queue)}**", value=f"**{song.title}**\nBy **{song.artist}**\n**Duration:** {song.duration_str()}")
                    index += 1
                await ctx.send(embed=info_embed)
            if len(self.song_queue) % max_field == 0:
                return
            info_embed = discord.Embed(color=discord.Color.pink())
            for i in range(len(self.song_queue)%max_field):
                song = self.song_queue[index]
                info_embed.add_field(name=f"*#{index+1}* **/ 0{len(self.song_queue)}**", value=f"**{song.title}**\nBy **{song.artist}**\n**Duration:** {song.duration_str()}")
                index += 1
            await ctx.send(embed=info_embed)

    @commands.command(
        name = "current",
        brief = "Bocchi sends info about the current song.",
        aliases = ["now"]
    )
    async def current(self, ctx: commands.Context):
        if not self._playing:
            await ctx.reply("No song is currently being played.", mention_author=False)
            return
        elif len(self.song_queue) < 1:
            await ctx.reply("Song queue is empty.", mention_author=False)
            return
        embed = discord.Embed(title="**Now playing**", color=discord.Color.green(), description=f"**{self.song_queue[0].title}**")
        embed.url = self.song_queue[0].url
        embed.add_field(name="Artist", value=self.song_queue[0].artist)
        embed.add_field(name="Duration", value=self.song_queue[0].duration_str())
        embed.set_image(url=self.song_queue[0].cover)
        await ctx.send(embed=embed)

    @commands.command(
        name = "stop",
        brief = "Bocchi clears the song queue.",
        aliases = ["clear", "quit"]
    )
    async def stop(self, ctx: commands.Context):
        self.song_queue.clear()
        if self.bot.current_client:
            self.bot.current_client.stop()
        await ctx.message.add_reaction('✅')
