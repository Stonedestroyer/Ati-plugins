from redbot.core import Config, commands
import datetime
import discord

try:
    import psutil
except:
    psutil = False


class Statistics(commands.Cog):
    """
    Statistics
    """

    def __init__(self, bot):
        self.bot = bot

    async def redapi_hook(self, data=None):
        if not data:
            x = self.retrieve_statistics()
            x["avatar"] = (
                self.bot.user.avatar_url
                if self.bot.user.avatar
                else self.bot.user.default_avatar_url
            )
            x["uptime"] = self.get_bot_uptime(brief=False)
            x["total_cogs"] = len(self.bot.cogs)
            x["total_commands"] = len(self.bot.commands)
            x["discord_version"] = str(discord.__version__)
            x["id"] = self.bot.user.id
            x["discriminator"] = self.bot.user.discriminator
            x["created_at"] = self.bot.user.created_at.strftime("%B %d, %Y at %H:%M:%S")
            x["loaded_cogs"] = [cog for cog in self.bot.cogs]
            x["prefixes"] = await self.bot.db.prefix()
            x["servers"] = [
                {"name": guild.name, "members": len(guild.members), "icon_url": guild.icon_url}
                for guild in self.bot.guilds
            ]
            x["cogs"] = len(self.bot.cogs)
            return x
        else:
            pass

    @commands.command()
    async def stats(self, ctx):
        """
        Retreive statistics
        """
        message = await self.embed_statistics()
        await ctx.send(embed=message)

    async def embed_statistics(self):
        stats = self.retrieve_statistics()
        em = discord.Embed(description=u"\u2063\n", color=discord.Color.red())
        avatar = (
            self.bot.user.avatar_url if self.bot.user.avatar else self.bot.user.default_avatar_url
        )
        em.set_author(name="Statistics of {}".format(stats["name"]), icon_url=avatar)

        em.add_field(name="**Uptime**", value="{}".format(self.get_bot_uptime(brief=True)))

        em.add_field(name="**Users**", value=stats["users"])
        em.add_field(name="**Servers**", value=stats["total_servers"])

        em.add_field(name="**Channels**", value=str(stats["channels"]))
        em.add_field(name="**Text channels**", value=str(stats["text_channels"]))
        em.add_field(name="**Voice channels**", value=str(stats["voice_channels"]))

        em.add_field(name="**Messages received**", value=str(stats["read_messages"]))
        em.add_field(name="**Commands run**", value=str(stats["commands_run"]))
        em.add_field(name=u"\u2063", value=u"\u2063")

        em.add_field(name="**Active cogs**", value=str(len(self.bot.cogs)))
        em.add_field(name="**Commands**", value=str(len(self.bot.commands)))
        em.add_field(name=u"\u2063", value=u"\u2063")

        em.add_field(name=u"\u2063", value=u"\u2063", inline=False)
        em.add_field(name="**CPU**", value="{0:.1f}%".format(stats["cpu_usage"]))
        em.add_field(
            name="**Memory**",
            value="{0:.0f} MB ({1:.2f}%)".format(stats["mem_v_mb"] / 1024 / 1024, stats["mem_v"]),
        )
        em.add_field(name="**Threads**", value="{}".format(stats["threads"]))
        em.set_footer(text="API version {}".format(discord.__version__))
        return em

    def retrieve_statistics(self):
        name = self.bot.user.name
        users = str(len(set(self.bot.get_all_members())))
        servers = str(len(self.bot.guilds))
        commands_run = self.bot.counter["processed_commands"]
        read_messages = self.bot.counter["messages_read"]
        text_channels = 0
        voice_channels = 0

        process = psutil.Process()

        cpu_usage = psutil.cpu_percent()

        mem_v = process.memory_percent()
        mem_v_mb = process.memory_full_info().uss
        threads = process.num_threads()

        io_reads = process.io_counters().read_count
        io_writes = process.io_counters().write_count

        text_channels = sum(len(s.text_channels) for s in self.bot.guilds)
        voice_channels = sum(len(s.text_channels) for s in self.bot.guilds)
        channels = text_channels + voice_channels

        stats = {
            "name": name,
            "users": users,
            "total_servers": servers,
            "commands_run": commands_run,
            "read_messages": read_messages,
            "text_channels": text_channels,
            "voice_channels": voice_channels,
            "channels": channels,
            "cpu_usage": cpu_usage,
            "mem_v": mem_v,
            "mem_v_mb": mem_v_mb,
            "threads": threads,
            "io_reads": io_reads,
            "io_writes": io_writes,
        }
        return stats

    def get_bot_uptime(self, *, brief=False):
        # Stolen from owner.py - Courtesy of Danny
        now = datetime.datetime.utcnow()
        delta = now - self.bot.uptime
        hours, remainder = divmod(int(delta.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        days, hours = divmod(hours, 24)

        if not brief:
            if days:
                fmt = "{d} days, {h} hours, {m} minutes, and {s} seconds"
            else:
                fmt = "{h} hours, {m} minutes, and {s} seconds"
        else:
            fmt = "{h} H - {m} M - {s} S"
            if days:
                fmt = "{d} D - " + fmt

        return fmt.format(d=days, h=hours, m=minutes, s=seconds)
