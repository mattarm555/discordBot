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

riot = os.getenv("RIOT_API_KEY")  # Changed variable name to `riot`
RIOT_BASE_URL = "https://na1.api.riotgames.com/lol"

@bot.command()
async def rank(ctx, summoner_name: str):
    """Fetches a player's rank, last 5 matches, and most played champion."""
    if not riot:
        await ctx.send("❌ Riot API key is missing! Set it in your environment variables.")
        return

    try:
        # Get Summoner ID
        summoner_url = f"{RIOT_BASE_URL}/summoner/v4/summoners/by-name/{summoner_name}?api_key={riot}"
        summoner_data = requests.get(summoner_url).json()

        if "id" not in summoner_data:
            await ctx.send("❌ Summoner not found.")
            return

        summoner_id = summoner_data["id"]
        account_id = summoner_data["accountId"]

        # Get Ranked Data
        rank_url = f"{RIOT_BASE_URL}/league/v4/entries/by-summoner/{summoner_id}?api_key={riot}"
        rank_data = requests.get(rank_url).json()

        if rank_data:
            solo_rank = next((entry for entry in rank_data if entry["queueType"] == "RANKED_SOLO_5x5"), None)
            if solo_rank:
                rank_tier = f"{solo_rank['tier']} {solo_rank['rank']} ({solo_rank['leaguePoints']} LP)"
            else:
                rank_tier = "Unranked"
        else:
            rank_tier = "Unranked"

        # Get Match History (Last 5 Games)
        matches_url = f"{RIOT_BASE_URL}/match/v4/matchlists/by-account/{account_id}?endIndex=5&api_key={riot}"
        matches_data = requests.get(matches_url).json()

        match_history = ""
        champion_usage = {}

        for match in matches_data["matches"]:
            champion_id = match["champion"]
            match_id = match["gameId"]

            # Count champion usage
            champion_usage[champion_id] = champion_usage.get(champion_id, 0) + 1

            # Get match result
            match_detail_url = f"{RIOT_BASE_URL}/match/v4/matches/{match_id}?api_key={riot}"
            match_detail = requests.get(match_detail_url).json()

            # Find the player in match data
            player = next(p for p in match_detail["participantIdentities"] if p["player"]["accountId"] == account_id)
            participant_id = player["participantId"]

            # Get player's team ID & match outcome
            participant_data = next(p for p in match_detail["participants"] if p["participantId"] == participant_id)
            team_id = participant_data["teamId"]
            game_result = "Win" if any(t["win"] == "Win" for t in match_detail["teams"] if t["teamId"] == team_id) else "Loss"

            match_history += f"Game {match_id}: Champion {champion_id} - **{game_result}**\n"

        # Find most played champion
        most_played_champion = max(champion_usage, key=champion_usage.get)

        # Send Embed Response
        embed = discord.Embed(title=f"📊 {summoner_name}'s Stats", color=discord.Color.blue())
        embed.add_field(name="🏆 Rank", value=rank_tier, inline=False)
        embed.add_field(name="📜 Last 5 Matches", value=match_history, inline=False)
        embed.add_field(name="🔥 Most Played Champion", value=f"Champion ID: {most_played_champion}", inline=False)

        await ctx.send(embed=embed)

    except Exception as e:
        await ctx.send(f"❌ Error retrieving data: {e}")
        print(f"Error: {e}")


print(f"Token: {TOKEN[:5]}********")
bot.run(TOKEN)
