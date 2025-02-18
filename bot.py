import discord
from discord.ext import commands

TOKEN = "NzYxNjUyNjM3NzAzNDcxMTA1.G5RbJE.FzeGuzJvy22vknxhLxdDhQfd2fZPSM3YxdRFWg"

intents = discord.Intents.default()
intents.message_content = True  # Enable message reading

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

@bot.command()
async def hello(ctx):
    await ctx.send("Hello! I'm your bot 🤖")

bot.run(TOKEN)
