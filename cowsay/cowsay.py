import discord
from discord.ext import commands
import textwrap
import asyncio, aiohttp, io, time, imghdr, os, json

    class CowSay:
    """
    Commands that are used for fun.
    """

    def __init__(self, bot):
        self.bot = bot

    def _box_text(self, text : str):
        """ Convert text into a box of fixedwidth text. """

        # Prevent escaping from the preformatted text block by adding a
        # zero-width space after each backtick in the input.
        text_sanitised = text.replace("`", "`\u200B")
        text_boxed = '```txt\n{0}```'.format(text_sanitised)
        return text_boxed

    @commands.command()
    async def cowthink(self, *, message : str):
        cow = self.build_box(message, 40) + self.build_thinkcow()

        return await ctx.send(self._box_text(cow))

    @commands.command()
    async def cowsay(self, *, message : str):
        cow = self.build_box(message, 40) + self.build_saycow()

        return await ctx.send(self._box_text(cow))


    # Cowsay code used from https://github.com/jcn/cowsay-py

    def build_saycow(self):
        return """
         \   ^__^
          \  (oo)\_______
             (__)\       )\/\\
                 ||----w |
                 ||     ||
        """

    def build_thinkcow(self):
        return """
         o   ^__^
          o  (oo)\_______
             (__)\       )\/\\
                 ||----w |
                 ||     ||
        """

    def build_box(self, str, length=40):
        bubble = []

        lines = self.normalize_text(str, length)

        bordersize = len(lines[0])

        bubble.append("  "  + "_" * bordersize)

        for index, line in enumerate(lines):
            border = self.get_border(lines, index)

            bubble.append("%s %s %s" % (border[0], line, border[1]))

        bubble.append("  " + "-" * bordersize)

        return "\n".join(bubble)

    def normalize_text(self, str, length):
        lines  = textwrap.wrap(str, length)
        maxlen = len(max(lines, key=len))
        return [ line.ljust(maxlen) for line in lines ]

    def get_border(self, lines, index):
        if len(lines) < 2:
            return [ "<", ">" ]

        elif index == 0:
            return [ "/", "\\" ]

        elif index == len(lines) - 1:
            return [ "\\", "/" ]

        else:
            return [ "|", "|" ]
