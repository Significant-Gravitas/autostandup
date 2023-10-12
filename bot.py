# Import required modules
import os
import json
from discord.ext import commands, tasks
from discord import Intents
from dotenv import load_dotenv
from scheduler import Scheduler
from team_member import TeamMember
from status_db import StatusDB

# Load environment variables from the .env file
load_dotenv()

# Retrieve bot, guild, and channel tokens from environment variables
BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN')
GUILD_TOKEN = int(os.getenv('DISCORD_GUILD_TOKEN'))
CHANNEL_TOKEN = int(os.getenv('DISCORD_CHANNEL_TOKEN'))

# Initialize bot with default intents
intents = Intents.default()
intents.members = True
bot = commands.Bot(command_prefix='!', intents=intents)
db = StatusDB()

# Define a loop that runs every 48 hours to ping for status updates
@tasks.loop(hours=48)
async def ping_for_status() -> None:
    # Get the guild (server) and channel using their IDs
    guild = bot.get_guild(GUILD_TOKEN)
    channel = guild.get_channel(CHANNEL_TOKEN)
    # Send a message to the channel to ping everyone for a status update
    await channel.send("Hey @everyone, time for a status update! Please share what you've been working on.")

async def send_status_request(member: TeamMember) -> None:
    user = bot.get_user(member.discord_id)
    if user:
        await user.send(f"Good morning {member.name}, time for your status update!")
        def check(m) -> bool:
            return m.author == user
        msg = await bot.wait_for('message', check=check)
        
        # Insert the status update into the database
        db.insert_status(member.discord_id, member.name, msg.content)


@bot.event
async def on_ready() -> None:
    print("Bot is online!")
    
    scheduler = Scheduler()
    
    # Read team member data from JSON file
    with open("team_members.json", "r") as f:
        team_members_data = json.load(f)
    
    for member_data in team_members_data:
        member = TeamMember(
            discord_id=member_data["discord_id"], 
            time_zone=member_data["time_zone"], 
            name=member_data["name"]
        )
        scheduler.add_job(send_status_request, member)

# Run the bot
bot.run(BOT_TOKEN)
