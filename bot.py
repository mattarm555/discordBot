import discord
import random
import json
import os
import asyncio
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
from dotenv import load_dotenv
from discord import ui, Interaction, Embed
import math
import pytz
load_dotenv()
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
TOKEN = os.getenv("TOKEN")
test_guild_id = 870519196419760188

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
sniped_messages = {}
quote_data = []




@bot.event
async def on_ready():
    await bot.wait_until_ready()

    guild = discord.Object(id=test_guild_id)

    # Fast sync to your test server for instant access
    await tree.sync(guild=guild)
    print(f"✅ Synced commands to test guild {test_guild_id}")

    # Also sync globally (takes up to 1 hour)
    await tree.sync()
    print("🌐 Synced commands globally (may take up to 60 minutes)")

    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name='/help'))
    print(f"✅ Logged in as {bot.user}")


try:
    with open("quotes.json", "r") as f:
        quote_data = json.load(f)
except:
    quote_data = []

def save_quotes():
    with open("quotes.json", "w") as f:
        json.dump(quote_data, f, indent=4)

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

print(f"\033[1;36m[DEBUG] OpenAI API Key: {client.api_key}\033[0m")


def debug_command(command_name, user, **kwargs):
    print(f"\033[1;32m[COMMAND] /{command_name}\033[0m triggered by \033[1;33m{user.display_name}\033[0m")
    if kwargs:
        print("\033[1;36mInput:\033[0m")
        for key, value in kwargs.items():
            print(f"\033[1;31m  {key.capitalize()}: {value}\033[0m")

@bot.event
async def on_message_delete(message):
    if message.author.bot:
        return
    sniped_messages[message.channel.id] = {
        "content": message.content,
        "author": message.author,
        "time": message.created_at
    }

@tree.command(name="snipe", description="Snipes the last deleted message in this channel.", guild=discord.Object(id=test_guild_id))
async def snipe(interaction: discord.Interaction):
    debug_command("snipe", interaction.user)
    snipe_data = sniped_messages.get(interaction.channel.id)

    if not snipe_data:
        await interaction.response.send_message("❌ Nothing to snipe here.", ephemeral=True)
        return

    embed = discord.Embed(
        title="Get Sniped Gang",
        description=snipe_data["content"],
        color=discord.Color.dark_red(),
        timestamp=snipe_data["time"]
    )
    embed.set_author(name=snipe_data["author"].display_name, icon_url=snipe_data["author"].avatar.url if snipe_data["author"].avatar else None)
    await interaction.response.send_message(embed=embed)

@tree.command(name="quote_add", description="Add a new quote.", guild=discord.Object(id=test_guild_id))
@app_commands.describe(text="The quote and who said it.")
async def quote_add(interaction: discord.Interaction, text: str):
    debug_command("quote_add", interaction.user, text=text)
    quote_data.append(text)
    save_quotes()
    embed = discord.Embed(title="✅ Quote Saved", description="Your quote was added!", color=discord.Color.green())
    await interaction.response.send_message(embed=embed)


@tree.command(name="quote_get", description="Get a random quote.", guild=discord.Object(id=test_guild_id))
async def quote_get(interaction: discord.Interaction):
    debug_command("quote_get", interaction.user)
    if not quote_data:
        await interaction.response.send_message("No quotes yet!")
        return
    quote = random.choice(quote_data)
    embed = discord.Embed(title="📜 Random Quote", description=f"\"{quote}\"", color=discord.Color.blurple())
    await interaction.response.send_message(embed=embed)


@tree.command(name="quote_list", description="Lists saved quotes with pagination.", guild=discord.Object(id=test_guild_id))
async def quote_list(interaction: discord.Interaction):
    debug_command("quote_list", interaction.user)

    if not quote_data:
        await interaction.response.send_message("❌ No quotes saved.")
        return

    class QuotePagination(ui.View):
        def __init__(self, quotes, per_page=5):
            super().__init__(timeout=60)
            self.quotes = quotes
            self.per_page = per_page
            self.page = 0
            self.max_pages = (len(quotes) - 1) // per_page + 1

        def get_embed(self):
            start = self.page * self.per_page
            end = start + self.per_page
            embed = discord.Embed(
                title=f"📜 Saved Quotes (Page {self.page + 1}/{self.max_pages})",
                description="\n".join([f"**{i+1}.** {q}" for i, q in enumerate(self.quotes[start:end], start=start)]),
                color=discord.Color.blurple()
            )
            return embed

        @ui.button(label="⬅️ Prev", style=discord.ButtonStyle.blurple)
        async def prev(self, interaction: Interaction, button: ui.Button):
            if self.page > 0:
                self.page -= 1
                await interaction.response.edit_message(embed=self.get_embed(), view=self)
            else:
                await interaction.response.defer()

        @ui.button(label="➡️ Next", style=discord.ButtonStyle.blurple)
        async def next(self, interaction: Interaction, button: ui.Button):
            if self.page < self.max_pages - 1:
                self.page += 1
                await interaction.response.edit_message(embed=self.get_embed(), view=self)
            else:
                await interaction.response.defer()

    view = QuotePagination(quote_data)
    await interaction.response.send_message(embed=view.get_embed(), view=view)


@tree.command(name="quote_edit", description="Edit an existing quote.", guild=discord.Object(id=test_guild_id))
@app_commands.describe(index="The quote number to edit", new_text="The new quote text")
async def quote_edit(interaction: discord.Interaction, index: int, new_text: str):
    debug_command("quote_edit", interaction.user, index=index, new_text=new_text)
    if index < 1 or index > len(quote_data):
        await interaction.response.send_message("❌ Invalid quote number.")
        return
    quote_data[index - 1] = new_text
    save_quotes()
    embed = discord.Embed(title="✏️ Quote Updated", description=f"Quote #{index} was successfully updated.", color=discord.Color.green())
    await interaction.response.send_message(embed=embed)


@tree.command(name="quote_delete", description="Delete a quote by its number.", guild=discord.Object(id=test_guild_id))
@app_commands.describe(index="The quote number to delete")
async def quote_delete(interaction: discord.Interaction, index: int):
    debug_command("quote_delete", interaction.user, index=index)
    if index < 1 or index > len(quote_data):
        await interaction.response.send_message("❌ Invalid quote number.")
        return
    removed = quote_data.pop(index - 1)
    save_quotes()
    embed = discord.Embed(
    title="🗑️ Quote Deleted",
    description=f"Removed quote #{index}:\n\n\"{removed}\"",
    color=discord.Color.red()
)
    await interaction.response.send_message(embed=embed)




@tree.command(name="askai", description="Ask AI anything (GPT-style response).")
@app_commands.describe(prompt="What would you like to ask?")
async def askai(interaction: discord.Interaction, prompt: str):
    debug_command("askai", interaction.user, prompt=prompt)
    await interaction.response.defer()

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300,
            temperature=0.7
        )
        answer = response.choices[0].message.content

        embed = discord.Embed(
            title="🧠 AI says:",
            description=answer,
            color=discord.Color.blue()
        )
        await interaction.followup.send(embed=embed)

    except Exception as e:
        embed = discord.Embed(
            title="❌ Error",
            description=str(e),
            color=discord.Color.red()
        )
        await interaction.followup.send(embed=embed)



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
    debug_command("level", interaction.user)
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
    debug_command("lol", interaction.user, count=count)
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
    debug_command("spam", interaction.user, target=user.display_name, count=count)
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
    print(f"yo gang this new mf just joined btw: {member}")  # For debugging in console

    role_id = 870551516837199902
    welcome_channel_id = 870519197279608834

    role = member.guild.get_role(role_id)
    welcome_channel = bot.get_channel(welcome_channel_id)

    if role:
        await member.add_roles(role)

    if welcome_channel:
        embed = discord.Embed(
            title="🎉 Welcome!",
            description=f"Welcome {member.mention} to **{member.guild.name}**!",
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
    debug_command("champ", interaction.user)
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
    debug_command("leaderboard", interaction.user)
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
    debug_command("ward", interaction.user)
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
    await interaction.response.defer()
    debug_command("play", interaction.user, url=url)
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



@tree.command(name="queue", description="Displays the current song queue with pagination.")
async def queue(interaction: discord.Interaction):
    debug_command("queue", interaction.user)  # Replace "queue" with the command name
    """Displays the current song queue with pagination."""
    guild_id = interaction.guild.id
    song_queue = queues.get(guild_id, [])

    if not song_queue:
        embed = discord.Embed(title="Queue Empty", description="The queue is empty.", color=discord.Color.red())
        await interaction.response.send_message(embed=embed)
        return

    # Pagination class
    class QueueView(ui.View):
        def __init__(self, queue, per_page=5):
            super().__init__(timeout=60)
            self.queue = queue
            self.per_page = per_page
            self.page = 0
            self.max_pages = math.ceil(len(queue) / per_page)

        def format_embed(self):
            start = self.page * self.per_page
            end = start + self.per_page

            embed = discord.Embed(
                title=f"🎶 Current Queue (Page {self.page + 1}/{self.max_pages})",
                color=discord.Color.blue()
            )

            songs_on_page = self.queue[start:end]

            for i, song in enumerate(songs_on_page, start=start + 1):
                embed.add_field(name=f"{i}. {song['title']}", value=" ", inline=False)

            if songs_on_page:
                # 🧊 Use the first song on *this* page at this moment for the thumbnail
                embed.set_thumbnail(url=songs_on_page[0]['thumbnail'])

            return embed


        @ui.button(label="⬅️", style=discord.ButtonStyle.blurple)
        async def previous(self, interaction: Interaction, button: ui.Button):
            if self.page > 0:
                self.page -= 1
                await interaction.response.edit_message(embed=self.format_embed(), view=self)
            else:
                await interaction.response.defer()

        @ui.button(label="➡️", style=discord.ButtonStyle.blurple)
        async def next(self, interaction: Interaction, button: ui.Button):
            if self.page < self.max_pages - 1:
                self.page += 1
                await interaction.response.edit_message(embed=self.format_embed(), view=self)
            else:
                await interaction.response.defer()

    # Show first page
    view = QueueView(song_queue)
    embed = view.format_embed()
    await interaction.response.send_message(embed=embed, view=view)






@tree.command(name="skip", description="Skips the current song and plays the next one in the queue.")
async def skip(interaction: discord.Interaction):
    debug_command("skip", interaction.user)
    """Skips the current song and lets the after= callback trigger play_next."""
    if interaction.guild.voice_client and interaction.guild.voice_client.is_playing():
        interaction.guild.voice_client.stop()  # This triggers after=play_next

        embed = discord.Embed(title='Skipped', description='Skipped to the next song.', color=discord.Color.orange())
        await interaction.response.send_message(embed=embed)
    else:
        embed = discord.Embed(title='No Song Playing', description='No song is currently playing.', color=discord.Color.red())
        await interaction.response.send_message(embed=embed)



@tree.command(name="stop", description="Pauses the current song.")
async def stop(interaction: discord.Interaction):
    debug_command("stop", interaction.user)
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
    debug_command("start", interaction.user)
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
    debug_command("leave", interaction.user)
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
    debug_command("help", interaction.user)
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
    embed.add_field(name="/poll", value="Allows user to create poll. Configurable.", inline=False)
    embed.add_field(name="/event", value="Allows user to create event. Other members can RSVP.", inline=False)
    embed.add_field(name="/quote_add, /quote_get, /quote_list, /quote_edit, /quote_delete", value="Allows users to upload a quote! Edit, type a number from the list to edit a quote. Delete, same thing to delete. List provides a list of quotes uploaded by users. Get randomly picks a quote!", inline=False)
    embed.add_field(name="/askai", value="Ask ChatGPT for some help!", inline=False)
    embed.set_footer(text="Please let me know any more commands you would like to see!")

    await interaction.response.send_message(embed=embed)


@tree.command(name="poll", description="Create a custom emoji poll with 2–6 options and a closing timer.", guild=discord.Object(id=test_guild_id))
@app_commands.describe(
    question="Your poll question",
    duration_minutes="How many minutes until the poll closes?",
    anonymous="Hide voter usernames in the final results?",
    option1_text="Option 1 text", option1_emoji="Option 1 emoji",
    option2_text="Option 2 text", option2_emoji="Option 2 emoji",
    option3_text="Option 3 text", option3_emoji="Option 3 emoji",
    option4_text="Option 4 text", option4_emoji="Option 4 emoji",
    option5_text="Option 5 text", option5_emoji="Option 5 emoji",
    option6_text="Option 6 text", option6_emoji="Option 6 emoji"
)
async def poll(
    interaction: Interaction,
    question: str,
    duration_minutes: int,
    anonymous: bool,
    option1_text: str, option1_emoji: str,
    option2_text: str, option2_emoji: str,
    option3_text: str = None, option3_emoji: str = None,
    option4_text: str = None, option4_emoji: str = None,
    option5_text: str = None, option5_emoji: str = None,
    option6_text: str = None, option6_emoji: str = None
):
    await interaction.response.defer()

    debug_command(
    "poll", interaction.user,
    question=question,
    duration=f"{duration_minutes} minutes",
    anonymous=anonymous,
    **{f"option{i+1}": f"{text} {emoji}" for i, (text, emoji) in enumerate([
        (option1_text, option1_emoji),
        (option2_text, option2_emoji),
        (option3_text, option3_emoji),
        (option4_text, option4_emoji),
        (option5_text, option5_emoji),
        (option6_text, option6_emoji),
    ]) if text and emoji}
)

    # Build list of valid options
    options = []
    raw_options = [
        (option1_text, option1_emoji),
        (option2_text, option2_emoji),
        (option3_text, option3_emoji),
        (option4_text, option4_emoji),
        (option5_text, option5_emoji),
        (option6_text, option6_emoji),
    ]
    for text, emoji in raw_options:
        if text and emoji:
            options.append((text, emoji))

    if len(options) < 2:
        await interaction.followup.send("You must provide at least two options with emojis.", ephemeral=True)
        return

    # Send poll embed
    embed = Embed(title="📊 Poll", description=question, color=0x5865F2)
    for text, emoji in options:
        embed.add_field(name=f"{emoji} {text}", value=" ", inline=False)
    embed.set_footer(text=f"Poll closes in {duration_minutes} minutes • Created by {interaction.user.display_name}")
    embed.timestamp = datetime.now(pytz.timezone("US/Eastern"))

    msg = await interaction.followup.send(embed=embed, wait=True)

    # Add all emoji reactions
    for _, emoji in options:
        try:
            await msg.add_reaction(emoji)
        except:
            pass  # Invalid emoji? Skip.

    await asyncio.sleep(duration_minutes * 60)

    # Fetch updated message with reactions
    msg = await interaction.channel.fetch_message(msg.id)

    # Tally votes
    votes = {}  # emoji: [usernames]
    user_voted = set()

    for reaction in msg.reactions:
        if str(reaction.emoji) not in [e for _, e in options]:
            continue  # Ignore unrelated reactions

        async for user in reaction.users():
            if user.bot:
                continue

            if user.id not in user_voted:
                votes.setdefault(str(reaction.emoji), []).append(user)
                user_voted.add(user.id)  # Prevent duplicate voting

    # Build result message
    result_embed = Embed(
        title="📊 Poll Closed",
        description=question,
        color=discord.Color.gray()
    )

    for text, emoji in options:
        voters = votes.get(emoji, [])
        count = len(voters)

        if anonymous:
            result_embed.add_field(name=f"{emoji} {text}", value=f"**{count} vote(s)**", inline=False)
        else:
            names = ', '.join(user.display_name for user in voters) or "No votes"
            result_embed.add_field(name=f"{emoji} {text}", value=f"**{count} vote(s)**\n{names}", inline=False)

    result_embed.set_footer(text=f"Poll created by {interaction.user.display_name}")
    await msg.edit(embed=result_embed)

class RSVPView(ui.View):
    def __init__(self, creator: discord.User, event_title: str):
        super().__init__(timeout=None)
        self.going = set()
        self.not_going = set()
        self.creator = creator
        self.event_title = event_title
        self.message = None

    def format_embed(self):
        embed = Embed(
            title=f"📅 {self.event_title}",
            description="Click a button to RSVP!",
            color=discord.Color.gold()
        )
        embed.add_field(
            name="✅ Going",
            value="\n".join(user.mention for user in self.going) or "No one yet",
            inline=True
        )
        embed.add_field(
            name="❌ Not Going",
            value="\n".join(user.mention for user in self.not_going) or "No one yet",
            inline=True
        )
        embed.set_footer(text=f"Event created by {self.creator.display_name}")
        embed.timestamp = datetime.now(pytz.timezone("US/Eastern"))
        return embed

    @ui.button(label="✅ Going", style=discord.ButtonStyle.success)
    async def rsvp_yes(self, interaction: Interaction, button: ui.Button):
        self.not_going.discard(interaction.user)
        self.going.add(interaction.user)
        await self.update(interaction)

    @ui.button(label="❌ Not Going", style=discord.ButtonStyle.danger)
    async def rsvp_no(self, interaction: Interaction, button: ui.Button):
        self.going.discard(interaction.user)
        self.not_going.add(interaction.user)
        await self.update(interaction)

    async def update(self, interaction: Interaction):
        await interaction.response.edit_message(embed=self.format_embed(), view=self)

@tree.command(name="event", description="Create an interactive RSVP event.", guild=discord.Object(id=test_guild_id))
@app_commands.describe(
    title="Event title",
    time="When is the event?",
    location="Where is it?",
    details="More information about the event"
)
async def event(
    interaction: Interaction,
    title: str,
    time: str,
    location: str,
    details: str
):
    await interaction.response.defer()

    debug_command(
    "event", interaction.user,
    title=title,
    time=time,
    location=location,
    details=details
)

    view = RSVPView(creator=interaction.user, event_title=title)
    embed = view.format_embed()
    embed.add_field(name="🕒 Time", value=time, inline=False)
    embed.add_field(name="📍 Location", value=location, inline=False)
    embed.add_field(name="📝 Details", value=details, inline=False)

    message = await interaction.followup.send(embed=embed, view=view, wait=True)
    view.message = message



        
print(f"Token: {TOKEN[:5]}********")
bot.run(TOKEN)
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
