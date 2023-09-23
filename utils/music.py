import discord
from discord.ext import commands

async def get_voice_client(ctx: commands.Context, vc: discord.VoiceClient | None) -> discord.VoiceClient | None:
    if not ctx.author.voice:
        await ctx.reply("You are not in any voice channel.", mention_author=False)
        return
    elif ctx.voice_client and not vc:
        await ctx.voice_client.disconnect()
    elif ctx.voice_client and vc:
        await vc.move_to(ctx.author.voice.channel)
        return vc
    return await ctx.author.voice.channel.connect()
    