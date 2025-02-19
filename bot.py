import discord
import random
import json
import os
import asyncio
from discord.ext import commands

# Load bot token from environment variable
TOKEN = os.getenv("TOKEN")  # Make sure TOKEN is set in your environment

intents = discord.Intents.default()
intents.members = True  # Enable member fetching
intents.message_content = True  # Keep this for message reading

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

# Load XP data from a file (persistent storage)
try:
    with open("xp_data.json", "r") as f:
        xp_data = json.load(f)
except FileNotFoundError:
    xp_data = {}

# XP system settings
XP_PER_MESSAGE = 10  # XP gained per message
BASE_XP = 100  # Starting XP requirement for level 1

level_up_responses = [
    "Fuck you {user}! You just reached level {level}! 🎉",
    "Keep yourself safe {user}! You're now level {level}! 🚀",
    "Die {user}, you're now at level {level}! Keep going! 💪"
]

def get_xp_needed(level):
    """Returns the XP required to reach the next level."""
    return BASE_XP * (level + 1)  # XP increases with level

@bot.event
async def on_message(message):
    if message.author.bot:
        return  # Ignore bot messages

    user_id = str(message.author.id)
    if user_id not in xp_data:
        xp_data[user_id] = {"xp": 0, "level": 0}

    # Add XP
    xp_data[user_id]["xp"] += XP_PER_MESSAGE
    current_level = xp_data[user_id]["level"]
    next_level_xp = get_xp_needed(current_level)

    # Check for level-up
    if xp_data[user_id]["xp"] >= next_level_xp:
        xp_data[user_id]["level"] += 1  # Increase level
        new_level = xp_data[user_id]["level"]
        xp_data[user_id]["xp"] = 0  # Reset XP on level-up

        embed = discord.Embed(
            title="🎮 Level Up!",
            description=random.choice(level_up_responses).format(user=message.author.mention, level=new_level),
            color=discord.Color.gold()
        )
        await message.channel.send(embed=embed)

    # Save XP data
    with open("xp_data.json", "w") as f:
        json.dump(xp_data, f, indent=4)

    await bot.process_commands(message)  # Process other commands

@bot.command()
async def level(ctx):
    """Command to check user's level."""
    user_id = str(ctx.author.id)
    if user_id not in xp_data:
        embed = discord.Embed(
            title="🎮 Level Check",
            description=f"{ctx.author.mention}, you haven't gained any XP yet!",
            color=discord.Color.orange()
        )
    else:
        xp = xp_data[user_id]["xp"]
        level = xp_data[user_id]["level"]
        embed = discord.Embed(
            title="🏆 XP Level",
            description=f"{ctx.author.mention}, you are level **{level}** with **{xp} XP**!",
            color=discord.Color.green()
        )
    await ctx.send(embed=embed)

@bot.command()
async def lol(ctx, count: int = 1):
    """Mentions the League of Legends role."""
    role_id = 882335005093810248  # Replace with actual role ID
    role = ctx.guild.get_role(role_id)

    if not role:
        embed = discord.Embed(title="❌ Error", description="Role not found!", color=discord.Color.red())
        await ctx.send(embed=embed)
        return

    if count > 10:
        await ctx.send("⚠ Please enter a number **10 or lower**.")
        return

    for _ in range(count):
        await ctx.send(f"{role.mention} Get on you pieces of shit", allowed_mentions=discord.AllowedMentions(roles=True))
        await asyncio.sleep(0.75)

@bot.command()
async def spam(ctx, count: int):
    """Mentions a specific user multiple times."""
    user_id = 310933291928649730  # Replace with actual user ID
    user = await bot.fetch_user(user_id)

    if count > 10:
        await ctx.send("⚠ Please enter a number **10 or lower**.")
        return

    for _ in range(count):
        await ctx.send(f"{user.mention} I NEED MASTER RIGHT NOW")
        await asyncio.sleep(0.5)

@bot.event
async def on_member_join(member):
    """Assigns a role and welcomes a new member."""
    role_id = 870551516837199902  # Replace with actual role ID
    welcome_channel_id = 870519197279608834  # Replace with actual welcome channel ID

    role = member.guild.get_role(role_id)
    welcome_channel = bot.get_channel(welcome_channel_id)

    if role:
        await member.add_roles(role)

    if welcome_channel:
        embed = discord.Embed(
            title="🎉 Welcome!",
            description=f"Welcome {member.mention} to **{member.guild.name}**! Enjoy your stay!",
            color=discord.Color.green()
        )
        await welcome_channel.send(embed=embed)

# List of League of Legends champions
league_champions = [
    "Ahri", "Akali", "Aatrox", "Alistar", "Amumu", "Anivia", "Annie", "Aphelios", "Ashe",
    "Aurelion Sol", "Azir", "Bard", "Blitzcrank", "Brand", "Braum", "Caitlyn", "Camille",
    "Cassiopeia", "Cho'Gath", "Corki", "Darius", "Diana", "Dr. Mundo", "Draven", "Ekko",
    "Elise", "Evelynn", "Ezreal", "Fiddlesticks", "Fiora", "Fizz", "Galio", "Gangplank",
    "Garen", "Gnar", "Gragas", "Graves", "Gwen", "Hecarim", "Heimerdinger", "Illaoi",
    "Irelia", "Ivern", "Janna", "Jarvan IV", "Jax", "Jayce", "Jhin", "Jinx", "Kai'Sa",
    "Kalista", "Karma", "Karthus", "Kassadin", "Katarina", "Kayle", "Kayn", "Kennen",
    "Kha'Zix", "Kindred", "Kled", "Kog'Maw", "LeBlanc", "Lee Sin", "Leona", "Lillia",
    "Lissandra", "Lucian", "Lulu", "Lux", "Malphite", "Malzahar", "Maokai", "Master Yi",
    "Miss Fortune", "Mordekaiser", "Morgana", "Nami", "Nasus", "Nautilus", "Neeko",
    "Nidalee", "Nocturne", "Nunu & Willump", "Olaf", "Orianna", "Ornn", "Pantheon",
]

@bot.command()
async def champ(ctx):
    """Randomly selects a League of Legends champion."""
    champion = random.choice(league_champions)
    embed = discord.Embed(title="🎮 Random League Champion", description=f"Your champion is: **{champion}**!", color=discord.Color.purple())
    await ctx.send(embed=embed)

print(f"Token: {TOKEN[:5]}********")
bot.run(TOKEN)
