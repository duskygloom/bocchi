from discord.ext import commands

context_type = commands.Context

class Music(commands.Cog):
    def __init__(self, bot: commands.Bot):
        super().__init__()
        self.bot = bot

    @commands.command(
        name="come",
        description="Can I come into your vc?",
        usage="!come",
        brief="Invites Bocchi into your voice channel.",
        help="Invites Bocchi into your voice channel."
    )
    async def come(self, ctx: context_type):
        voice_channel = ctx.author.voice.channel
        if voice_channel is None:
            await ctx.reply("You are not in any voice channel.", mention_author=False)
            return
        await voice_channel.connect()
        await ctx.message.add_reaction('✅')
