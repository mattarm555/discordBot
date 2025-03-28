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
from discord.ext import commands, tasks
from datetime import datetime
from discord import app_commands

# Load bot token from environment variable
TOKEN = os.getenv("TOKEN")  # Make sure TOKEN is set in your environment


intents = discord.Intents.default()
intents.members = True  # Enable member fetching
intents.message_content = True  # Keep this for message reading
intents.messages = True
intents.guilds = True
intents.voice_states = True

bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)
tree = bot.tree

xp_data = {}
voice_time = {}

@bot.event
async def on_ready():
    await bot.wait_until_ready()  # Ensure bot is fully ready
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name='/help'))
    try:
        synced = await tree.sync()
        print(f"Synced {len(synced)} commands.")
    except Exception as e:
        print(f"Failed to sync commands: {e}")
        
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


excluded_channels = [
    947702763146592307,
    947706529811943475
]


@bot.event
async def on_message(message):
    if message.author.bot:
        return  # Ignore bot messages

    if message.channel.id in excluded_channels:
        await bot.process_commands(message)  # Still allow commands
        return

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

@tree.command(name="level", description="Displays your current XP level.")
async def level(interaction: discord.Interaction):
    """Command to check user's level."""
    user_id = str(interaction.user.id)
    if user_id not in xp_data:
        embed = discord.Embed(
            title="🎮 Level Check",
            description=f"{interaction.user.mention}, you haven't gained any XP yet!",
            color=discord.Color.orange()
        )
    else:
        xp = xp_data[user_id]["xp"]
        level = xp_data[user_id]["level"]
        embed = discord.Embed(
            title="🏆 XP Level",
            description=f"{interaction.user.mention}, you are level **{level}** with **{xp} XP**!",
            color=discord.Color.green()
        )
    await interaction.response.send_message(embed=embed)


@tree.command(name="lol", description="Mentions the League of Legends role.")
@app_commands.describe(count="Number of times to mention the role (max 20)")
async def lol(interaction: discord.Interaction, count: int = 1):
    """Mentions the League of Legends role."""
    role_id = 882335005093810248  # Replace with actual role ID
    role = interaction.guild.get_role(role_id)

    if not role:
        embed = discord.Embed(title="❌ Error", description="Role not found!", color=discord.Color.red())
        await interaction.response.send_message(embed=embed)
        return

    if count > 20:
        embed = discord.Embed(title="⚠ Limit Exceeded", description="Please enter a number **20 or lower**.", color=discord.Color.orange())
        await interaction.response.send_message(embed=embed)
        return

    await interaction.response.defer()  # Defer response to prevent timeout

    for _ in range(count):
        await interaction.channel.send(f"{role.mention} Get on you pieces of shit", allowed_mentions=discord.AllowedMentions(roles=True))
        await asyncio.sleep(0.75)

    await interaction.followup.send(f"✅ Mentioned {role.mention} {count} times.")


@tree.command(name="spam", description="Mentions a user multiple times.")
@app_commands.describe(user="The user to mention", count="Number of times to mention the user (max 20)")
async def spam(interaction: discord.Interaction, user: discord.Member, count: int = 1):
    """Mentions a user multiple times."""
    
    if count > 20:
        embed = discord.Embed(title="⚠ Limit Exceeded", description="Please enter a number **20 or lower**.", color=discord.Color.red())
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    # Send the first ping immediately
    await interaction.response.send_message(f"{user.mention} wya")

    # If count is more than 1, loop through additional pings
    for _ in range(count - 1):
        await asyncio.sleep(0.75)
        await interaction.channel.send(f"{user.mention} wya")



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

@tree.command(name="champ", description="Randomly selects a League of Legends champion.")
async def champ(interaction: discord.Interaction):
    """Randomly selects a League of Legends champion."""
    champion = random.choice(league_champions)
    embed = discord.Embed(
        title="🎮 Random League Champion",
        description=f"Your champion is: **{champion}**!",
        color=discord.Color.purple()
    )
    await interaction.response.send_message(embed=embed)


@tree.command(name="leaderboard", description="Displays the top 10 users based on level first, then XP as a tiebreaker.")
async def leaderboard(interaction: discord.Interaction):
    """Displays the top 10 users based on level first, then XP as a tiebreaker."""
    if not xp_data:
        embed = discord.Embed(title="🏆 Leaderboard", description="No XP data available yet!", color=discord.Color.orange())
        await interaction.response.send_message(embed=embed)
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
    await interaction.response.send_message(embed=embed)

@tree.command(name="ward", description="Deletes your command message and replies with 'ward'.")
async def ward(interaction: discord.Interaction):
    """Deletes the user's command message and replies."""
    try:
        await interaction.response.defer(ephemeral=True)  # Defer response to prevent timeout
        await interaction.delete_original_response()  # Delete the interaction message
        await interaction.channel.send("nigward")  # Send the reply
    except discord.Forbidden:
        await interaction.followup.send("❌ I don't have permission to delete messages!", ephemeral=True)
    except discord.HTTPException:
        await interaction.followup.send("❌ Failed to delete the message.", ephemeral=True)


queues = {}
thumbnails = {}

# Function to play next song
def play_next(interaction: discord.Interaction):
    """Plays the next song in the queue, or disconnects if the queue is empty."""
    if not interaction.guild.voice_client:  # Check if bot is still connected
        return  # Exit function if bot is not connected

    if queues.get(interaction.guild.id):  # Check if queue is not empty
        next_song = queues[interaction.guild.id].pop(0)

        if interaction.guild.voice_client.is_connected():  # Ensure bot is still in VC
            interaction.guild.voice_client.play(
                discord.FFmpegPCMAudio(next_song['url'], executable='ffmpeg'),
                after=lambda e: play_next(interaction)
            )
            embed = discord.Embed(title='Now Playing', description=next_song['title'], color=discord.Color.green())
            embed.set_thumbnail(url=next_song['thumbnail'])
            asyncio.run_coroutine_threadsafe(interaction.channel.send(embed=embed), bot.loop)
    else:
        asyncio.run_coroutine_threadsafe(auto_disconnect(interaction), bot.loop)


# Function to auto-disconnect
async def auto_disconnect(interaction: discord.Interaction):
    """Automatically disconnects the bot if no song is playing after 1 minute."""
    await asyncio.sleep(60)  # Wait for 2 minutes

    if interaction.guild.voice_client and not interaction.guild.voice_client.is_playing():
        await interaction.guild.voice_client.disconnect()
        queues[interaction.guild.id] = []  # Clear the queue

        # Send embedded message
        embed = discord.Embed(
            title="Liam has ran away.",
            description="",
            color=discord.Color.purple()
        )
        await interaction.channel.send(embed=embed)


@tree.command(name="play", description="Plays a song from the given URL.")
@app_commands.describe(url="YouTube URL of the song to play")
async def play(interaction: discord.Interaction, url: str):
    """Plays a song or adds it to the queue if another song is playing."""
    await interaction.response.defer()  # Prevents "application did not respond" error

    if interaction.guild.id not in queues:
        queues[interaction.guild.id] = []
    
    ydl_opts = {'format': 'bestaudio', 'noplaylist': True}
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        song_info = {'url': info['url'], 'title': info['title'], 'thumbnail': info['thumbnail']}
    
    if not interaction.guild.voice_client:
        vc = await interaction.user.voice.channel.connect()
    else:
        vc = interaction.guild.voice_client
    
    if not vc.is_playing():
        vc.play(
            discord.FFmpegPCMAudio(song_info['url'], executable='ffmpeg'),
            after=lambda e: play_next(interaction)
        )
        embed = discord.Embed(title='Now Playing', description=song_info['title'], color=discord.Color.green())
        embed.set_thumbnail(url=song_info['thumbnail'])
        await interaction.followup.send(embed=embed)  # Use followup instead of response
    else:
        queues[interaction.guild.id].append(song_info)
        embed = discord.Embed(title='Added to Queue', description=song_info['title'], color=discord.Color.blue())
        embed.set_thumbnail(url=song_info['thumbnail'])
        await interaction.followup.send(embed=embed)  # Use followup instead of response



@tree.command(name="queue", description="Displays the current song queue.")
async def queue(interaction: discord.Interaction):
    """Displays the current song queue."""
    if interaction.guild.id in queues and queues[interaction.guild.id]:
        embed = discord.Embed(title='Current Queue', color=discord.Color.blue())

        for i, song in enumerate(queues[interaction.guild.id]):
            embed.add_field(name=f'{i+1}. {song["title"]}', value=' ', inline=False)
            embed.set_thumbnail(url=song['thumbnail'])

        await interaction.response.send_message(embed=embed)
    else:
        embed = discord.Embed(title='Queue Empty', description='The queue is empty.', color=discord.Color.red())
        await interaction.response.send_message(embed=embed)


@tree.command(name="skip", description="Skips the current song and plays the next one in the queue.")
async def skip(interaction: discord.Interaction):
    """Skips the current song and plays the next one in the queue."""
    if interaction.guild.voice_client and interaction.guild.voice_client.is_playing():
        interaction.guild.voice_client.stop()

        # Check if queue is empty
        if not queues.get(interaction.guild.id):  # If no songs left in queue
            embed = discord.Embed(title='End of Queue', description='No more songs left to play.', color=discord.Color.red())
            await interaction.response.send_message(embed=embed)
            return
        
        play_next(interaction)
        embed = discord.Embed(title='Skipped', description='Skipped to the next song.', color=discord.Color.orange())
        await interaction.response.send_message(embed=embed)
    else:
        embed = discord.Embed(title='No Song Playing', description='No song is currently playing.', color=discord.Color.red())
        await interaction.response.send_message(embed=embed)



@tree.command(name="stop", description="Pauses the current song.")
async def stop(interaction: discord.Interaction):
    """Pauses the current song."""
    if interaction.guild.voice_client and interaction.guild.voice_client.is_playing():
        interaction.guild.voice_client.pause()
        embed = discord.Embed(title="Paused", description="Music paused.", color=discord.Color.orange())
        await interaction.response.send_message(embed=embed)
    else:
        embed = discord.Embed(title="No Music Playing", description="No music is playing to pause.", color=discord.Color.red())
        await interaction.response.send_message(embed=embed)


@tree.command(name="start", description="Resumes the paused music.")
async def start(interaction: discord.Interaction):
    """Resumes the paused music."""
    if interaction.guild.voice_client and interaction.guild.voice_client.is_paused():
        interaction.guild.voice_client.resume()
        embed = discord.Embed(title="Started", description="Music resumed.", color=discord.Color.green())
        await interaction.response.send_message(embed=embed)
    else:
        embed = discord.Embed(title="Not Started", description="No music is currently paused.", color=discord.Color.red())
        await interaction.response.send_message(embed=embed)


@tree.command(name="leave", description="Makes the bot leave the voice channel and clears the queue.")
async def leave(interaction: discord.Interaction):
    """Makes the bot leave the voice channel and clears the queue."""
    if interaction.guild.voice_client:
        await interaction.guild.voice_client.disconnect()
        queues[interaction.guild.id] = []
        embed = discord.Embed(title="Liam has ran away.", description="Bot has left the voice channel and cleared the queue.", color=discord.Color.purple())
        await interaction.response.send_message(embed=embed)
    else:
        embed = discord.Embed(title="Not Connected", description="I am not connected to a voice channel.", color=discord.Color.red())
        await interaction.response.send_message(embed=embed)


@tree.command(name="help", description="Displays a list of available commands.")
async def help(interaction: discord.Interaction):
    """Displays a list of available commands."""
    embed = discord.Embed(title="Bot Commands", description="Here are the available commands:", color=discord.Color.blue())
    embed.add_field(name="/play <url>", value="Plays a song from the given URL.", inline=False)
    embed.add_field(name="/queue", value="Shows the current music queue.", inline=False)
    embed.add_field(name="/skip", value="Skips the current song.", inline=False)
    embed.add_field(name="/stop", value="Pauses the music.", inline=False)
    embed.add_field(name="/start", value="Resumes paused music.", inline=False)
    embed.add_field(name="/leave", value="Clears the queue and makes the bot leave the voice channel.", inline=False)
    embed.add_field(name="/champ", value="Selects a random champion from League of Legends.", inline=False)
    embed.add_field(name="/ward", value="Wards the river.", inline=False)
    embed.add_field(name="/level", value="Shows your XP level.", inline=False)
    embed.add_field(name="/leaderboard", value="Shows the leaders in XP in this server.", inline=False)
    embed.add_field(name="/spam <user> <num>", value="Spams a user a specified number of times.", inline=False)
    embed.add_field(name="/lol <num>", value="Pings the League of Legends role.", inline=False)
    embed.set_footer(text="Please let me know any more commands you would like to see!")

    await interaction.response.send_message(embed=embed)


        
print(f"Token: {TOKEN[:5]}********")
bot.run(TOKEN)
