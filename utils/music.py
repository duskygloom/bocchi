import discord
from discord.ext import commands

voice_client: discord.VoiceClient = None

async def get_voice_client(ctx: commands.Context) -> discord.VoiceClient | None:
    '''
        returns None if author is not connected to voice
        else returns client
    '''
    global voice_client
    if not ctx.author.voice:
        # does not return client if author is not connected to voice
        await ctx.reply("You are not in any voice channel.", mention_author=False)
        return
    elif ctx.voice_client and voice_client:
        # if client exists, moves to author's channel
        await voice_client.move_to(ctx.author.voice.channel)
        return voice_client
    elif ctx.voice_client and not voice_client:
        # disconnects if has an unsaved client
        await ctx.voice_client.disconnect()
    voice_client = await ctx.author.voice.channel.connect()
    return voice_client

async def disconnect_client(ctx: commands.Context):
    global voice_client
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
    voice_client = None
    