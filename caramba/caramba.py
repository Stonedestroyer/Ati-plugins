import discord

class Caramba:
    def __init__(self, bot):
        self.bot = bot
        
    async def on_message(self, message):
        if message.content.lower().startswith('ayy') or message.content.lower().startswith('aayy'):
            await ctx.send("¡Caramba!")
