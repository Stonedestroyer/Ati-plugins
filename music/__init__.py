from .Music import Music
from discord.ext import commands


def setup(bot: commands.Bot):
    bot.add_cog(Music(bot))