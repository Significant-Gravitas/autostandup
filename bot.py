# Import required modules
import os
import json
from typing import List
import pytz
from discord.ext import commands, tasks
from discord import Intents
from dotenv import load_dotenv
from scheduler import Scheduler
from team_member import TeamMember
from status_db import StatusDB
from datetime import datetime, timedelta
from weekly_post_manager import WeeklyPostManager
from team_member_manager import TeamMemberManager

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

team_member_manager = None
weekly_post_manager = None

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

        # Determine which weekday it is in the member's local time zone
        utc_now = pytz.utc.localize(datetime.utcnow())
        local_now = utc_now.astimezone(pytz.timezone(member.time_zone))
        weekday = local_now.weekday()

        # Update the Discord post using WeeklyPostManager
        await weekly_post_manager.update_post(member, weekday)

@bot.event
async def on_ready() -> None:
    print("Bot is online!")  # Log that the bot is online
    
    # Initialize a job scheduler for sending status requests to team members
    scheduler = Scheduler()
    
    team_member_manager = TeamMemberManager("team_members.json")
    # Use TeamMemberManager to load team members from the JSON file
    team_members = team_member_manager.load_team_members()
    
    # Get the Discord guild (server) and channel objects
    guild = bot.get_guild(GUILD_TOKEN)
    channel = guild.get_channel(CHANNEL_TOKEN)
    
    # Schedule status request jobs for each team member
    for member in team_members:
        scheduler.add_job(send_status_request, member)

    # Declare the global variable for the WeeklyPostManager
    global weekly_post_manager
    
    # Initialize the WeeklyPostManager with the channel and team members
    weekly_post_manager = WeeklyPostManager(channel, team_members)
    
    # Call the method to create the initial weekly post
    await weekly_post_manager.initialize_post()


# Run the bot
bot.run(BOT_TOKEN)