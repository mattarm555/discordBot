import discord
import random
import json
import os
import asyncio
import openai
import speech_recognition as sr
import wave
import pyaudio
import aiohttp
import yt_dlp
import yt_dlp as youtube_dl
from gtts import gTTS
from discord.ext import commands

# Load bot token from environment variable
TOKEN = os.getenv("TOKEN")  # Make sure TOKEN is set in your environment


intents = discord.Intents.default()
intents.members = True  # Enable member fetching
intents.message_content = True  # Keep this for message reading
intents.messages = True
intents.guilds = True
intents.voice_states = True

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

    if count > 20:
        await ctx.send("⚠ Please enter a number **20 or lower**.")
        return

    for _ in range(count):
        await ctx.send(f"{role.mention} Get on you pieces of shit", allowed_mentions=discord.AllowedMentions(roles=True))
        await asyncio.sleep(0.75)

@bot.command()
async def spam(ctx, count: int):
    """Mentions a specific user multiple times."""
    user_id = 310933291928649730  # Replace with actual user ID
    user = await bot.fetch_user(user_id)

    if count > 20:
        await ctx.send("⚠ Please enter a number **20 or lower**.")
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
    "Aurelion Sol", "Azir", "Bard", "Bel'Veth", "Blitzcrank", "Brand", "Braum", "Caitlyn", "Camille",
    "Cassiopeia", "Cho'Gath", "Corki", "Darius", "Diana", "Dr. Mundo", "Draven", "Ekko",
    "Elise", "Evelynn", "Ezreal", "Fiddlesticks", "Fiora", "Fizz", "Galio", "Gangplank",
    "Garen", "Gnar", "Gragas", "Graves", "Gwen", "Hecarim", "Heimerdinger", "Hwei", "Illaoi",
    "Irelia", "Ivern", "Janna", "Jarvan IV", "Jax", "Jayce", "Jhin", "Jinx", "Kai'Sa",
    "Kalista", "Karma", "Karthus", "Kassadin", "Katarina", "Kayle", "Kayn", "Kennen",
    "Kha'Zix", "Kindred", "Kled", "Kog'Maw", "LeBlanc", "Lee Sin", "Leona", "Lillia",
    "Lissandra", "Lucian", "Lulu", "Lux", "Malphite", "Malzahar", "Maokai", "Mel", "Milio", "Master Yi",
    "Miss Fortune", "Mordekaiser", "Morgana", "Naafiri", "Nami", "Nasus", "Nautilus", "Neeko",
    "Nidalee", "Nilah", "Nocturne", "Nunu & Willump", "Olaf", "Orianna", "Ornn", "Pantheon",
    "Poppy", "Pyke", "Qiyana", "Quinn", "Rakan", "Rammus", "Rek'Sai", "Rell", "Renata Glasc",
    "Renekton", "Rengar", "Riven", "Rumble", "Ryze", "Samira", "Sejuani", "Senna", "Seraphine",
    "Sett", "Shaco", "Shen", "Shyvana", "Singed", "Sion", "Sivir", "Skarner", "Smolder", "Sona",
    "Soraka", "Swain", "Sylas", "Syndra", "Tahm Kench", "Taliyah", "Talon", "Taric",
    "Teemo", "Thresh", "Tristana", "Trundle", "Tryndamere", "Twisted Fate", "Twitch",
    "Udyr", "Urgot", "Varus", "Vayne", "Veigar", "Kel'Koz", "Vex", "Vi", "Viego",
    "Viktor", "Vladimir", "Volibear", "Warwick", "Wukong", "Xayah", "Xerath", "Xin Zhao",
    "Yasuo", "Yone", "Yorick", "Yuumi", "Zac", "Zed", "Zeri", "Ziggs", "Zilean", "Zoe",
    "Zyra"
]

@bot.command()
async def champ(ctx):
    """Randomly selects a League of Legends champion."""
    champion = random.choice(league_champions)
    embed = discord.Embed(title="🎮 Random League Champion", description=f"Your champion is: **{champion}**!", color=discord.Color.purple())
    await ctx.send(embed=embed)

@bot.command()
async def leaderboard(ctx):
    """Displays the top 10 users based on level first, then XP as a tiebreaker."""
    if not xp_data:
        embed = discord.Embed(title="🏆 Leaderboard", description="No XP data available yet!", color=discord.Color.orange())
        await ctx.send(embed=embed)
        return

    # Sort by level first, then by XP (highest to lowest)
    sorted_xp = sorted(xp_data.items(), key=lambda x: (x[1]["level"], x[1]["xp"]), reverse=True)
    
    # Take the top 10 users
    top_users = sorted_xp[:10]

    leaderboard_text = ""
    for rank, (user_id, data) in enumerate(top_users, start=1):
        user = await bot.fetch_user(int(user_id))
        leaderboard_text += f"**{rank}. {user.name}** - Level {data['level']} ({data['xp']} XP)\n"

    embed = discord.Embed(title="🏆 Dumbass Leaderboard", description=leaderboard_text, color=discord.Color.gold())
    await ctx.send(embed=embed)

@bot.command()
async def ward(ctx):
    """Deletes the user's command message and replies."""
    try:
        await ctx.message.delete()  # Delete the command message
        await ctx.send(f"nigward")
    except discord.Forbidden:
        await ctx.send("❌ I don't have permission to delete messages!")
    except discord.HTTPException:
        await ctx.send("❌ Failed to delete the message.")

queues = {}
thumbnails = {}

# Function to play next song
def play_next(ctx):
    if queues[ctx.guild.id]:
        next_song = queues[ctx.guild.id].pop(0)
        ctx.voice_client.play(discord.FFmpegPCMAudio(next_song['url'], executable='ffmpeg'), after=lambda e: play_next(ctx))
        embed = discord.Embed(title='Now Playing', description=next_song['title'], color=discord.Color.green())
        embed.set_thumbnail(url=next_song['thumbnail'])
        asyncio.run_coroutine_threadsafe(ctx.send(embed=embed), bot.loop)
    else:
        asyncio.run_coroutine_threadsafe(auto_disconnect(ctx), bot.loop)

# Function to auto-disconnect
timer_tasks = {}
async def auto_disconnect(ctx):
    await asyncio.sleep(120)
    if not ctx.voice_client.is_playing():
        await ctx.voice_client.disconnect()
        queues[ctx.guild.id] = []

@bot.command()
async def play(ctx, url: str):
    if ctx.guild.id not in queues:
        queues[ctx.guild.id] = []
    
    ydl_opts = {'format': 'bestaudio', 'noplaylist': True}
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        song_info = {'url': info['url'], 'title': info['title'], 'thumbnail': info['thumbnail']}
    
    if not ctx.voice_client:
        vc = await ctx.author.voice.channel.connect()
    else:
        vc = ctx.voice_client
    
    if not vc.is_playing():
        vc.play(discord.FFmpegPCMAudio(song_info['url'], executable='ffmpeg'), after=lambda e: play_next(ctx))
        embed = discord.Embed(title='Now Playing', description=song_info['title'], color=discord.Color.green())
        embed.set_thumbnail(url=song_info['thumbnail'])
        await ctx.send(embed=embed)
    else:
        queues[ctx.guild.id].append(song_info)
        embed = discord.Embed(title='Added to Queue', description=song_info['title'], color=discord.Color.blue())
        embed.set_thumbnail(url=song_info['thumbnail'])
        await ctx.send(embed=embed)

@bot.command()
async def queue(ctx):
    if ctx.guild.id in queues and queues[ctx.guild.id]:
        embed = discord.Embed(title='Current Queue', color=discord.Color.blue())
        for i, song in enumerate(queues[ctx.guild.id]):
            embed.add_field(name=f'{i+1}. {song["title"]}', value=' ', inline=False)
            embed.set_thumbnail(url=song['thumbnail'])
        await ctx.send(embed=embed)
    else:
        embed = discord.Embed(title='Queue Empty', description='The queue is empty.', color=discord.Color.red())
        await ctx.send(embed=embed)

@bot.command()
async def skip(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.stop()
        play_next(ctx)
        embed = discord.Embed(title='Skipped', description='Skipped to the next song.', color=discord.Color.orange())
        await ctx.send(embed=embed)
    else:
        embed = discord.Embed(title='No Song Playing', description='No song is currently playing.', color=discord.Color.red())
        await ctx.send(embed=embed)

@bot.command()
async def stop(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.pause()
        embed = discord.Embed(title='Paused', description='Music paused.', color=discord.Color.orange())
        await ctx.send(embed=embed)
    else:
        embed = discord.Embed(title='No Music Playing', description='No music is playing to pause.', color=discord.Color.red())
        await ctx.send(embed=embed)

@bot.command()
async def start(ctx):
    if ctx.voice_client and ctx.voice_client.is_paused():
        ctx.voice_client.resume()
        embed = discord.Embed(title='Started', description='Music resumed.', color=discord.Color.green())
        await ctx.send(embed=embed)
    else:
        embed = discord.Embed(title='Not Started', description='No music is currently paused.', color=discord.Color.red())
        await ctx.send(embed=embed)

@bot.command()
async def leave(ctx):
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        queues[ctx.guild.id] = []
        embed = discord.Embed(title='Liam has ran away.', description='Bot has left the voice channel and cleared the queue.', color=discord.Color.purple())
        await ctx.send(embed=embed)
    else:
        embed = discord.Embed(title='Not Connected', description='I am not connected to a voice channel.', color=discord.Color.red())
        await ctx.send(embed=embed)
        
print(f"Token: {TOKEN[:5]}********")
bot.run(TOKEN)
