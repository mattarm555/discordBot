import discord
import random
import json
import os
from discord.ext import commands

# Load bot token from environment variable
TOKEN = os.getenv("TOKEN")  # Make sure TOKEN is set in your environment

intents = discord.Intents.default()
intents.message_content = True  # Enable message reading

bot = commands.Bot(command_prefix="!", intents=intents)

# Load XP data from a file (persistent storage)
try:
    with open("xp_data.json", "r") as f:
        xp_data = json.load(f)
except FileNotFoundError:
    xp_data = {}

# XP system settings
XP_PER_MESSAGE = 10  # XP gained per message
LEVEL_UP_MULTIPLIER = 100  # XP required to level up (e.g., level 2 = 200 XP)

level_up_responses = [
    "Congrats {user}! You just reached level {level}! 🎉",
    "Well done {user}! You're now level {level}! 🚀",
    "Level up! {user}, you're now at level {level}! Keep going! 💪"
]

def get_level(xp):
    """Calculate the level based on XP."""
    return xp // LEVEL_UP_MULTIPLIER

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

@bot.event
async def on_message(message):
    if message.author.bot:
        return  # Ignore bot messages

    user_id = str(message.author.id)
    if user_id not in xp_data:
        xp_data[user_id] = {"xp": 0, "level": 0}

    # Add XP and check for level-up
    xp_data[user_id]["xp"] += XP_PER_MESSAGE
    new_level = get_level(xp_data[user_id]["xp"])

    if new_level > xp_data[user_id]["level"]:
        xp_data[user_id]["level"] = new_level
        response = random.choice(level_up_responses).format(user=message.author.mention, level=new_level)
        await message.channel.send(response)

    # Save XP data
    with open("xp_data.json", "w") as f:
        json.dump(xp_data, f, indent=4)

    await bot.process_commands(message)  # Process other bot commands

@bot.command()
async def level(ctx):
    """Command to check user's level."""
    user_id = str(ctx.author.id)
    if user_id not in xp_data:
        await ctx.send(f"{ctx.author.mention}, you haven't gained any XP yet!")
    else:
        xp = xp_data[user_id]["xp"]
        level = xp_data[user_id]["level"]
        await ctx.send(f"{ctx.author.mention}, you are level {level} with {xp} XP!")

bot.run(TOKEN)
