# Lavalink.py for Red v3 beta 7+
# Cog base thanks to Kromatic's example cog.
import asyncio
import discord
import lavalink
import math
from discord.ext import commands
from redbot.core import Config, checks

__version__ = "2.0.2.4.c"


class Music:
    def __init__(self, bot, loop: asyncio.BaseEventLoop):
        self.bot = bot
        self.config = Config.get_conf(self, 2711759128, force_registration=True)

        default_global = {
            "host": 'localhost',
            "port": '80',
            "passw": 'youshallnotpass',
            "status": False
        }

        default_guild = {
            "notify": False
        }

        self.config.register_guild(**default_guild)
        self.config.register_global(**default_global)
        loop.create_task(self.init_config(bot, loop))

    async def init_config(self, bot, loop):
        host = await self.config.host()
        passw = await self.config.passw()
        port = await self.config.port()

        try:
            self._lavalink = lavalink.Client(bot=bot, password=passw, host=host, port=port, loop=loop)
        except RuntimeError:
            pass

        self.bot.lavalink.client.register_hook(self.track_hook)

    @property
    def lavalink(self):
        return self._lavalink

    async def track_hook(self, player, event):
        notify = await self.config.guild(self.bot.get_guild(player.fetch('guild'))).notify()
        status = await self.config.status()
        playing_servers = self.bot.lavalink.players.get_playing()
        get_players = [p for p in self.bot.lavalink.players._players.values() if p.is_playing]
        try:
            get_single_title = get_players[0].current.title
        except IndexError:
            pass

        if event == 'TrackStartEvent' and notify:
            c = player.fetch('channel')
            if c:
                c = self.bot.get_channel(c)
                if c:
                    embed = discord.Embed(colour=c.guild.me.top_role.colour, title='Now Playing', description='**[{}]({})**'.format(player.current.title, player.current.uri))
                    await c.send(embed=embed)

        if event == 'TrackStartEvent' and status:
            if playing_servers > 1:
                await self.bot.change_presence(game=discord.Game(name='music in {} servers'.format(playing_servers)))
            else:
                await self.bot.change_presence(game=discord.Game(name=get_single_title, type=2))

        if event == 'QueueEndEvent' and notify:
            c = player.fetch('channel')
            if c:
                c = self.bot.get_channel(c)
                if c:
                    embed = discord.Embed(colour=c.guild.me.top_role.colour, title='Queue ended.')
                    await c.send(embed=embed)

        if event == 'QueueEndEvent' and status:
            await asyncio.sleep(1)
            if playing_servers == 0:
                await self.bot.change_presence(game=None)
            if playing_servers == 1:
                await self.bot.change_presence(game=discord.Game(name=get_single_title, type=2))
            if playing_servers > 1:
                await self.bot.change_presence(game=discord.Game(name='music in {} servers'.format(playing_servers)))

    @commands.group()
    @checks.is_owner()
    async def audioset(self, ctx):
        """Music configuration options."""
        if ctx.invoked_subcommand is None:
            await ctx.send_help()

    @audioset.command()
    async def notify(self, ctx):
        """Toggle song announcement and other bot messages."""
        notify = await self.config.guild(ctx.guild).notify()
        await self.config.guild(ctx.guild).notify.set(not notify)
        get_notify = await self.config.guild(ctx.guild).notify()
        await self._embed_msg(ctx, "Verbose mode on: {}.".format(get_notify))

    @audioset.command()
    async def settings(self, ctx):
        """Show the current settings."""
        player = self.bot.lavalink.players.get(ctx.guild.id)
        notify = await self.config.guild(ctx.guild).notify()
        status = await self.config.status()
        shuffle = player.shuffle
        repeat = player.repeat

        msg = "```ini\n"
        msg += "----Guild Settings----\n"
        msg += "audioset notify: [{}]\n".format(notify)
        msg += "audioset status: [{}]\n".format(status)
        msg += "Repeat:          [{}]\n".format(repeat)
        msg += "Shuffle:         [{}]\n".format(shuffle)
        msg += "---Lavalink Settings---\n"
        msg += "Cog version: {}\n".format(__version__)
        msg += "Pip version: {}\n```".format(lavalink.__version__)

        embed = discord.Embed(colour=ctx.guild.me.top_role.colour, description=msg)
        return await ctx.send(embed=embed)

    @audioset.command()
    @checks.is_owner()
    async def status(self, ctx):
        """Enables/disables songs' titles as status."""
        status = await self.config.status()
        await self.config.status.set(not status)
        get_status = await self.config.status()
        await self._embed_msg(ctx, "Song titles as status: {}.".format(get_status))

    @commands.command()
    async def audiostats(self, ctx):
        """Audio stats."""
        server_num = self.bot.lavalink.players.get_playing()
        server_ids = self.bot.lavalink.players._players
        server_list = []
        for k, v in server_ids.items():
            guild_id = k
            player = v
            try:
                server_list.append(self.bot.get_guild(guild_id).name + ": **[{}]({})**".format(v.current.title, v.current.uri))
            except AttributeError:
                server_list.append(self.bot.get_guild(guild_id).name + ": Connected, but no current song.")
            servers = '\n'.join(server_list)
        if server_list == []:
            servers = "Not connected anywhere."
        embed = discord.Embed(colour=ctx.guild.me.top_role.colour, title='Playing in {} servers:'.format(server_num), description=servers)
        await ctx.send(embed=embed)

    @commands.command()
    async def bump(self, ctx, index: int):
        """Bump a song number to the top of the queue."""
        player = self.bot.lavalink.players.get(ctx.guild.id)

        if not player.queue:
            return await self._embed_msg(ctx, 'Nothing queued.')

        if index > len(player.queue) or index < 1:
            return await self._embed_msg(ctx, 'Song number must be greater than 1 and within the queue limit.')

        bump_index = index - 1
        bump_song = self.bot.lavalink.players.get(ctx.guild.id).queue[bump_index]
        player.queue.insert(0, bump_song)
        removed = player.queue.pop(index)
        await self._embed_msg(ctx, 'Moved **' + removed.title + '** to the top of the queue.')

    @commands.command(aliases=['dc'])
    async def disconnect(self, ctx):
        """Disconnect from the voice channel."""
        player = self.bot.lavalink.players.get(ctx.guild.id)
        await player.disconnect()

    @commands.command(aliases=['np', 'n', 'song'])
    async def now(self, ctx):
        """Now playing."""
        expected = ['⏹', '⏸', '⏭']
        emoji = {
            'stop': '⏹',
            'pause': '⏸',
            'next': '⏭'
        }
        player = self.bot.lavalink.players.get(ctx.guild.id)
        song = 'Nothing'
        if player.current:
            arrow = await self._draw_time(ctx)
            pos = lavalink.Utils.format_time(player.position)
            if player.current.stream:
                dur = 'LIVE'
            else:
                dur = lavalink.Utils.format_time(player.current.duration)
        if not player.current:
            song = 'Nothing.'
        else:
            req_user = self.bot.get_user(player.current.requester)
            song = '**[{}]({})**\nRequested by: **{}**\n{}\n({}/{})'.format(player.current.title, player.current.uri, req_user, arrow, pos, dur)

        embed = discord.Embed(colour=ctx.guild.me.top_role.colour, title='Now Playing', description=song)
        message = await ctx.send(embed=embed)

        def check(r, u):
            return r.message.id == message.id and u == ctx.message.author

        if player.current:
            for i in range(3):
                await message.add_reaction(expected[i])
        try:
            (r, u) = await self.bot.wait_for('reaction_add', check=check, timeout=10.0)
        except asyncio.TimeoutError:
            await self._clear_react(message)
            return

        reacts = {v: k for k, v in emoji.items()}
        react = reacts[r.emoji]

        if react == 'stop':
            await self._clear_react(message)
            await ctx.invoke(self.stop)
        elif react == 'pause':
            await self._clear_react(message)
            await ctx.invoke(self.pause)
        elif react == 'next':
            await self._clear_react(message)
            await ctx.invoke(self.skip)

    @commands.command(aliases=['resume'])
    async def pause(self, ctx):
        """Pause and resume."""
        player = self.bot.lavalink.players.get(ctx.guild.id)
        if not ctx.author.voice or (player.is_connected and ctx.author.voice.channel.id != int(player.channel_id)):
            return await self._embed_msg(ctx, 'You must be in the voice channel to pause the music.')

        if not player.is_playing:
            return

        if player.paused:
            await player.set_pause(False)
            await self._embed_msg(ctx, 'Music resumed.')
        else:
            await player.set_pause(True)
            await self._embed_msg(ctx, 'Music paused.')

    @commands.command(aliases=['p'])
    async def play(self, ctx, *, query):
        """Play a URL or search for a song."""
        player = self.bot.lavalink.players.get(ctx.guild.id)
        if not ctx.author.voice or (player.is_connected and ctx.author.voice.channel.id != int(player.channel_id)):
            return await self._embed_msg(ctx, 'You must be in the voice channel to use the play command.')

        player.store('channel', ctx.channel.id)
        player.store('guild', ctx.guild.id)

        if not player.is_connected:
            await player.connect(ctx.author.voice.channel.id)

        query = query.strip('<>')
        if not query.startswith('http'):
            query = 'ytsearch:{}'.format(query)

        tracks = await self.bot.lavalink.client.get_tracks(query)
        if not tracks:
            return await self._embed_msg(ctx, 'Nothing found 👀')

        if 'list' in query and 'ytsearch:' not in query:
            for track in tracks:
                await player.add_and_play(requester=ctx.author.id, track=track)
            embed = discord.Embed(colour=ctx.guild.me.top_role.colour, title='Playlist Enqueued', description='Added {} tracks to the queue.'.format(len(tracks)))
        else:
            await player.add_and_play(requester=ctx.author.id, track=tracks[0])
            track_title = tracks[0]["info"]["title"]
            track_url = tracks[0]["info"]["uri"]
            embed = discord.Embed(colour=ctx.guild.me.top_role.colour, title='Track Enqueued', description='[**{}**]({})'.format(track_title, track_url))

        await ctx.send(embed=embed)

    @commands.command(aliases=['q'])
    async def queue(self, ctx, page: int=1):
        """Lists the queue."""
        player = self.bot.lavalink.players.get(ctx.guild.id)
        if not player.queue:
            return await self._embed_msg(ctx, 'There\'s nothing in the queue.')

        if player.current is None:
            return await self._embed_msg(ctx, 'The player is stopped.')

        items_per_page = 10
        pages = math.ceil(len(player.queue) / items_per_page)

        start = (page - 1) * items_per_page
        end = start + items_per_page

        queue_list = ''

        for i, track in enumerate(player.queue[start:end], start=start):
            req_user = self.bot.get_user(track.requester)
            next = i + 1
            queue_list += '`{}.` [**{}**]({}), requested by **{}**\n'.format(next, track.title, track.uri, req_user)

        pos = player.position
        dur = player.current.duration
        remain = dur - pos
        time_remain = lavalink.Utils.format_time(remain)
        embed = discord.Embed(colour=ctx.guild.me.top_role.colour, title='Queue for ' + ctx.guild.name, description=queue_list)

        if player.current.stream:
            embed.set_footer(text='Page {}/{} | {} tracks | Currently livestreaming {}'.format(page, pages, len(player.queue), player.current.title))
            await ctx.send(embed=embed)
        else:
            embed.set_footer(text='Page {}/{} | {} tracks | {} left on {}'.format(page, pages, len(player.queue), time_remain, player.current.title))
            await ctx.send(embed=embed)

    @commands.command()
    async def repeat(self, ctx):
        """Toggles repeat."""
        player = self.bot.lavalink.players.get(ctx.guild.id)
        if not ctx.author.voice or (player.is_connected and ctx.author.voice.channel.id != int(player.channel_id)):
            return await self._embed_msg(ctx, 'You must be in the voice channel to toggle shuffle.')

        if not player.is_playing:
            return await self._embed_msg(ctx, 'Nothing playing.')

        player.repeat = not player.repeat

        title = ('Repeat ' + ('enabled.' if player.repeat else 'disabled.'))
        return await self._embed_msg(ctx, title)

    @commands.command()
    async def remove(self, ctx, index: int):
        """Remove a specific song number from the queue."""
        player = self.bot.lavalink.players.get(ctx.guild.id)

        if not player.queue:
            return await self._embed_msg(ctx, 'Nothing queued.')

        if index > len(player.queue) or index < 1:
            return await self._embed_msg(ctx, 'Song number must be greater than 1 and within the queue limit.')

        index = index - 1
        removed = player.queue.pop(index)

        await self._embed_msg(ctx, 'Removed **' + removed.title + '** from the queue.')

    @commands.command()
    async def search(self, ctx, *, query):
        """Pick a song with a search.
        Use [p]search list <search term> to queue all songs.
        """
        expected = ["1⃣", "2⃣", "3⃣", "4⃣", "5⃣", "⏪", "⏩"]
        emoji = {
            "one": "1⃣",
            "two": "2⃣",
            "three": "3⃣",
            "four": "4⃣",
            "five": "5⃣",
            "back": "⏪",
            "next": "⏩"
        }
        player = self.bot.lavalink.players.get(ctx.guild.id)
        player.store('channel', ctx.channel.id)
        player.store('guild', ctx.guild.id)

        if not ctx.author.voice or (player.is_connected and ctx.author.voice.channel.id != int(player.channel_id)):
            return await self._embed_msg(ctx, 'You must be in the voice channel to enqueue songs.')
        if not player.is_connected:
            await player.connect(ctx.author.voice.channel.id)
        query = query.strip('<>')
        if not query.startswith('http'):
            query = 'ytsearch:{}'.format(query)
        tracks = await self.bot.lavalink.client.get_tracks(query)
        if not tracks:
            return await self._embed_msg(ctx, 'Nothing found 👀')
        if 'list' not in query and 'ytsearch:' or 'scsearch:' in query:
            page = 1
            items_per_page = 5
            pages = math.ceil(len(tracks) / items_per_page)
            start = (page - 1) * items_per_page
            end = start + items_per_page

            search_list = ''

            for i, track in enumerate(tracks[start:end], start=start):
                next = i + 1
                search_list += '`{0}.` [**{1}**]({2})\n'.format(next, tracks[i]["info"]["title"], tracks[i]["info"]["uri"])

            embed = discord.Embed(colour=ctx.guild.me.top_role.colour, title='Tracks Found:', description=search_list)
            embed.set_footer(text='Page {}/{} | {} search results'.format(page, pages, len(tracks)))
            message = await ctx.send(embed=embed)

            def check(r, u):
                return r.message.id == message.id and u == ctx.message.author
            for i in range(7):
                await message.add_reaction(expected[i])
            try:
                (r, u) = await self.bot.wait_for('reaction_add', check=check, timeout=30.0)
            except asyncio.TimeoutError:
                await self._clear_react(message)
                return
            reacts = {v: k for k, v in emoji.items()}
            react = reacts[r.emoji]
            if react == 'one':
                await self._search_button(ctx, message, tracks, entry=0)
            elif react == 'two':
                await self._search_button(ctx, message, tracks, entry=1)
            elif react == 'three':
                await self._search_button(ctx, message, tracks, entry=2)
            elif react == 'four':
                await self._search_button(ctx, message, tracks, entry=3)
            elif react == 'five':
                await self._search_button(ctx, message, tracks, entry=4)

            elif react == 'back':
                page = page - 1

                await self._clear_react(message)
                return
            elif react == 'next':
                await self._clear_react(message)
                return
        else:
            for track in tracks:
                await player.add_and_play(requester=ctx.author.id, track=track)
            songembed = discord.Embed(colour=ctx.guild.me.top_role.colour, title='Queued {} track(s).'.format(len(tracks)))
            message = await ctx.send(embed=songembed)

    async def _search_button(self, ctx, message, tracks, entry: int):
        player = self.bot.lavalink.players.get(ctx.guild.id)
        await self._clear_react(message)
        await player.add_and_play(requester=ctx.author.id, track=tracks[entry])
        track_title = tracks[entry]["info"]["title"]
        track_url = tracks[entry]["info"]["uri"]
        embed = discord.Embed(colour=ctx.guild.me.top_role.colour, title='Track Enqueued', description='[**{}**]({})'.format(track_title, track_url))
        return await ctx.send(embed=embed)

    @commands.command()
    async def seek(self, ctx, seconds: int=5):
        """Seeks ahead or behind on a track by seconds."""
        player = self.bot.lavalink.players.get(ctx.guild.id)
        if not ctx.author.voice or (player.is_connected and ctx.author.voice.channel.id != int(player.channel_id)):
            return await self._embed_msg(ctx, 'You must be in the voice channel to use seek.')
        if player.is_playing:
            if player.current.stream:
                return await self._embed_msg(ctx, 'Can\'t seek on a stream.')
            else:
                time_sec = seconds * 1000
                seek = player.position + time_sec
                await self._embed_msg(ctx, 'Moved {}s to {}'.format(seconds, lavalink.Utils.format_time(seek)))
                return await player.seek(seek)

    @commands.command()
    async def shuffle(self, ctx):
        """Toggles shuffle."""
        player = self.bot.lavalink.players.get(ctx.guild.id)
        if not ctx.author.voice or (player.is_connected and ctx.author.voice.channel.id != int(player.channel_id)):
            return await self._embed_msg(ctx, 'You must be in the voice channel to toggle shuffle.')

        if not player.is_playing:
            return await self._embed_msg(ctx, 'Nothing playing.')

        player.shuffle = not player.shuffle

        title = ('Shuffle ' + ('enabled.' if player.shuffle else 'disabled.'))
        return await self._embed_msg(ctx, title)

    @commands.command(aliases=['forceskip', 'fs'])
    async def skip(self, ctx):
        """Skips to the next track."""
        player = self.bot.lavalink.players.get(ctx.guild.id)

        if player.current is None:
            return await self._embed_msg(ctx, 'The player is stopped.')

        if not player.queue:
            pos = player.position
            dur = player.current.duration
            remain = dur - pos
            time_remain = lavalink.Utils.format_time(remain)
            if player.current.stream:
                embed = discord.Embed(colour=ctx.guild.me.top_role.colour, title='There\'s nothing in the queue.')
                embed.set_footer(text='Currently livestreaming {}'.format(player.current.title))
                return await ctx.send(embed=embed)
            elif player.current.track:
                embed = discord.Embed(colour=ctx.guild.me.top_role.colour, title='There\'s nothing in the queue.')
                embed.set_footer(text='{} left on {}'.format(time_remain, player.current.title))
                return await ctx.send(embed=embed)
            else:
                return await self._embed_msg(ctx, 'There\'s nothing in the queue.')

        if not ctx.author.voice or (player.is_connected and ctx.author.voice.channel.id != int(player.channel_id)):
            return await self._embed_msg(ctx, 'You must be in the voice channel to skip the music.')

        await player.skip()

    @commands.command(aliases=['s'])
    async def stop(self, ctx):
        """Stops playback and clears the queue."""
        player = self.bot.lavalink.players.get(ctx.guild.id)
        if not ctx.author.voice or (player.is_connected and ctx.author.voice.channel.id != int(player.channel_id)):
            return await self._embed_msg(ctx, 'You must be in the voice channel to stop the music.')
        if player.is_playing:
            await self._embed_msg(ctx, 'Stopping...')
            player.queue.clear()
            await player.stop()
            await self.bot.lavalink.client._trigger_event("QueueEndEvent", ctx.guild.id)

    @commands.command(aliases=['vol'])
    async def volume(self, ctx, volume: int=None):
        """Sets the volume, 1% - 150%."""
        player = self.bot.lavalink.players.get(ctx.guild.id)
        if not ctx.author.voice or (player.is_connected and ctx.author.voice.channel.id != int(player.channel_id)):
            return await self._embed_msg(ctx, 'You must be in the voice channel to change the volume.')
        if not volume:
            vol = player.volume
            embed = discord.Embed(colour=ctx.guild.me.top_role.colour, title='Volume:', description=str(vol) + '%')
            return await ctx.send(embed=embed)
        if not player.is_playing:
            return await self._embed_msg(ctx, 'Nothing playing.')
        if int(volume) > 150:
            volume = 150
            await player.set_volume(volume)
        else:
            await player.set_volume(volume)
        embed = discord.Embed(colour=ctx.guild.me.top_role.colour, title='Volume:', description=str(volume) + '%')
        await ctx.send(embed=embed)

    @commands.group(aliases=['llset'])
    @checks.is_owner()
    async def llsetup(self, ctx):
        """Lavalink server configuration options."""
        if ctx.invoked_subcommand is None:
            await ctx.send_help()

    @llsetup.command()
    async def host(self, ctx, host):
        """Set the lavalink server host."""
        await self.config.host.set(host)
        get_host = await self.config.host()
        await self._embed_msg(ctx, "Host set to {}.".format(get_host))

    @llsetup.command()
    async def password(self, ctx, passw):
        """Set the lavalink server password."""
        await self.config.passw.set(str(passw))
        get_passw = await self.config.passw()
        await self._embed_msg(ctx, "Server password set to {}.".format(get_passw))

    @llsetup.command()
    async def port(self, ctx, port):
        """Set the lavalink server port."""
        await self.config.port.set(str(port))
        get_port = await self.config.port()
        await self._embed_msg(ctx, "Port set to {}.".format(get_port))

    async def _clear_react(self, message):
        try:
            await message.clear_reactions()
        except:
            return

    async def _draw_time(self, ctx):
        player = self.bot.lavalink.players.get(ctx.guild.id)
        pos = player.position
        dur = player.current.duration
        sections = 12
        loc_time = round((pos / dur) * sections)
        bar = ':white_small_square:'
        seek = ':small_blue_diamond:'
        msg = '|'
        for i in range(sections):
            if i == loc_time:
                msg += seek
            else:
                msg += bar
        msg += '|'
        return msg

    async def _embed_msg(self, ctx, title):
        embed = discord.Embed(colour=ctx.guild.me.top_role.colour, title=title)
        await ctx.send(embed=embed)

    def __unload(self):
        self.bot.lavalink.client.destroy()