import discord, logging, typing, os
from discord.ext import commands
from yt_dlp import YoutubeDL
from bot import VoiceBot
from utils.general import get_ytdl_options, padded_int_string
from utils.music import get_voice_client, disconnect_client

class Music(commands.Cog):
    def __init__(self, bot: VoiceBot):
        super().__init__()
        self.bot = bot
        self.repeat = False
        self.volume = 90
        self.song_queue: list[dict[str, str]] = []
        self.ffmpeg_options = {"before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5 +discardcorrupt" }

    def search_song(self, query: str) -> dict[str, str]:
        song = {"title": "", "url": "", "uploader": "", "thumbnail": "", "duration": "", "path": ""}
        try:
            ytdl_options, output_file = get_ytdl_options()
            # assuming query is url
            video = YoutubeDL(params=ytdl_options).extract_info(query, download=True)
            info = video
        except Exception:
            # assuming it's a normal search query
            try:
                videos = YoutubeDL(params=ytdl_options).extract_info(f"ytsearch:{query}", download=True)
                if len(videos["entries"]) == 0:
                    return {}
                info = videos["entries"][0]
            except Exception as e:
                # something else happened
                logging.error(e)
                return {}
        for key in song:
            if key in info:
                song[key] = info[key]
        song["path"] = output_file
        return song
        
    def play_next(self, ctx: commands.Context, previous_song: str, error: Exception = None):
        # firstly logging if any error generated
        if error:
            logging.error(error)
        # removes the previous song
        os.remove(previous_song)
        # checking if voice client is ok
        if not self.bot.current_client:
            return
        elif self.bot.current_client.is_playing():
            self.bot.current_client.pause()
        # dequeue and play
        if len(self.song_queue) == 0:
            return
        elif len(self.song_queue) == 1:
            self.song_queue.pop(0)
            return
        self.song_queue.pop(0)
        self.play_song(ctx)
        
    def play_song(self, ctx: commands.Context, error: Exception = None):
        '''just plays songs'''
        if error:
            logging.error(error)
        if not self.bot.current_client:
            return
        elif self.bot.current_client.is_playing():
            self.bot.current_client.pause()
        elif len(self.song_queue) < 1:
            return
        if self.repeat:
            after = lambda e: self.play_song(ctx, e)
        else:
            after = lambda e: self.play_next(ctx, self.song_queue[0]["path"], e)
        self.bot.current_client.play(discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(
            self.song_queue[0]["path"],
            before_options=self.ffmpeg_options,
            options="-vn"
        ), volume=self.volume/100), after=after)

    @commands.command(
        name="play",
        brief="Plays the song specified or the first song in the queue."
    )
    async def play(self, ctx: commands.Context, *, song: str = None):
        self.bot.current_client = await get_voice_client(ctx)
        if not self.bot.current_client: return
        if song:
            await ctx.message.add_reaction('⏳')
            async with ctx.typing():
                song = self.search_song(song)
            await ctx.message.remove_reaction('⏳', self.bot.user)
            if not song:
                await ctx.reply(f"Could not find the song: {song}", mention_author=False)
                return
            self.song_queue.insert(0, song)
        elif len(self.song_queue) == 0:
            await ctx.reply("No songs in the queue.", mention_author=False)
            await ctx.message.add_reaction('✅')
            return
        try:
            await ctx.reply(f"Playing {song['title']} now.", mention_author=False)
            self.play_song(ctx)
            await ctx.message.add_reaction('✅')
            await self.queue(ctx)
        except Exception as e:
            logging.error(f"Could not play the song: {song}")
            await ctx.reply(f"Error while playing the song: {song}\nRemoving it from queue.")
            await self.next(ctx)

    @commands.command(
            name = "next",
            brief = "Proceeds to the next song."
    )
    async def next(self, ctx: commands.Context):
        self.bot.current_client = await get_voice_client(ctx)
        if not self.bot.current_client:
            return
        if len(self.song_queue) == 0:
            await ctx.reply("No songs in the queue.", mention_author=False)
            await disconnect_client(ctx)
            self.bot.current_client = await get_voice_client(ctx)
            return
        elif len(self.song_queue) == 1:
            await ctx.reply("No songs left to play.", mention_author=False)
            self.song_queue.pop(0)
            await disconnect_client(ctx)
            self.bot.current_client = await get_voice_client(ctx)
            return
        self.song_queue.pop(0)
        await self.play(ctx, song=self.song_queue[0]["path"])
        
    @commands.command(
            name="stop",
            brief="Okay I will stop that song."
    )
    async def stop(self, ctx: commands.Context):
        self.bot.current_client = await get_voice_client(ctx)
        if not self.bot.current_client:
            await ctx.reply("I am not in any voice channel.", mention_author=False)
            return
        await disconnect_client(ctx)
        self.bot.current_client = await get_voice_client(ctx)
        await ctx.message.add_reaction('✅')

    @commands.command(
            name = "clear",
            brief = "Clears the music queue."
    )
    async def clear(self, ctx: commands.Context):
        self.song_queue.clear()
        await ctx.message.add_reaction('✅')

    @commands.command(
            name = "repeat",
            brief = "Toggle repeat."
    )
    async def repeat(self, ctx: commands.Context):
        self.repeat = not self.repeat
        if self.repeat:
            await ctx.reply("Repeating mode: On", mention_author=False)
        else:
            await ctx.reply("Repeating mode: Off", mention_author=False)
        await ctx.message.add_reaction('✅')
    
    @commands.command(
            name = "pause",
            brief = "Pauses the song."
    )
    async def pause(self, ctx: commands.Context):
        self.bot.current_client = await get_voice_client(ctx)
        if ctx.voice_client and self.bot.current_client and self.bot.current_client.is_playing():
            self.bot.current_client.pause()
        else:
            await ctx.reply("No song is being played.", mention_author=False)
        await ctx.message.add_reaction('✅')
    
    @commands.command(
            name = "resume",
            brief = "Resumes the song."
    )
    async def resume(self, ctx: commands.Context):
        self.bot.current_client = await get_voice_client(ctx)
        if ctx.voice_client and self.bot.current_client and self.bot.current_client.is_paused():
            self.bot.current_client.resume()
        else:
            await ctx.reply("No song was paused.", mention_author=False)
        await ctx.message.add_reaction('✅')
    
    @commands.command(
            name = "volume",
            brief = "Changes volume for the song."
    )
    async def volume(self, ctx: commands.Context, volume: float = 90):
        if not self.bot.current_client:
            await ctx.reply("I am not in any voice channel.", mention_author=False)
            return
        self.volume = volume
        source = self.bot.current_client.source
        if source and self.bot.current_client and self.bot.current_client.is_playing():
            self.bot.current_client.source = discord.PCMVolumeTransformer(source, volume/100)
        await ctx.message.add_reaction('✅')
    
    @commands.command(
            name="queue",
            brief="This song will be eventually played."
    )
    async def queue(self, ctx: commands.Context, *, query: typing.Optional[str] = None):
        # adding any song if provided
        if query:
            await ctx.message.add_reaction('⏳')
            async with ctx.typing():
                song = self.search_song(query)
            await ctx.message.remove_reaction('⏳', self.bot.user)
            if not song:
                await ctx.message.reply(f"Could not find a song with that query.", mention_author=False)
                await ctx.message.add_reaction('✅')
                return
            self.song_queue.append(song)
            await ctx.message.reply(f"Added {self.song_queue[-1]['title']}.", mention_author=False)
        # displaying the queue
        if len(self.song_queue) == 0:
            await ctx.reply("Empty queue.", mention_author=False)
            return
        max_int_length = len(str(len(self.song_queue)))
        for i in range(0, len(self.song_queue), 10):
            j = i
            queue_embeds = []
            while j < len(self.song_queue) and j < i+10:
                embed = discord.Embed(
                    description=f"{padded_int_string(j+1, max_int_length)}. {self.song_queue[j]['title']}", 
                    url=self.song_queue[j]['url'],
                    color=discord.Color.pink()
                )
                queue_embeds.append(embed)
                j += 1
            await ctx.send(embeds=queue_embeds)
        await ctx.message.add_reaction('✅')
    
    @commands.command(
        name="status",
        brief="Displays the status of the current song."
    )
    async def status(self, ctx: commands.Context):
        if self.bot.current_client and self.bot.current_client.is_playing() and len(self.song_queue) > 0:
            song = self.song_queue[0]
            embed = discord.Embed(
                title="Current song",
                description=f"**{song['title']}**\n{song['uploader']}\n\nDuration: {song['duration']//60} minutes {song['duration']%60} seconds", 
                url=song['url'],
                color=discord.Color.green()
            )
            embed.set_image(url=song["thumbnail"])
            await ctx.send(embed=embed)
        else:
            await ctx.reply("Nothing is being played right now.", mention_author=False)
        await ctx.message.add_reaction('✅')
