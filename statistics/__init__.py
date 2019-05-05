from .statistics import Statistics
import psutil

def setup(bot):
    if psutil is False:
        raise RuntimeError(
            "psutil is not installed. Run `pip3 install psutil --upgrade` to use this cog."
        )
    bot.add_cog(Statistics(bot))