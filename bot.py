# Import required modules
import os
import pytz
from typing import List
from dotenv import load_dotenv
from datetime import datetime
from multiprocessing import Process

from streaks.streaks_db import StreaksDB
from team_members.team_member_db import TeamMemberDB
from updates.updates_db import UpdatesDB
from weekly_posts.weekly_posts_db import WeeklyPostsDB

from streaks.streaks_manager import StreaksManager
from team_members.team_member_manager import TeamMemberManager
from updates.updates_manager import UpdatesManager
from weekly_posts.weekly_post_manager import WeeklyPostManager

from scheduler import Scheduler
from team_members.team_member import TeamMember

from discord.ext import commands, tasks
from discord import Intents, DMChannel

from flask import Flask
import openai
from asyncio import Task, ensure_future, CancelledError

app = Flask(__name__)

# Load environment variables from the .env file
load_dotenv()

# Retrieve bot, guild, and channel tokens from environment variables
BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN')
GUILD_TOKEN = int(os.getenv('DISCORD_GUILD_TOKEN'))
CHANNEL_TOKEN = int(os.getenv('DISCORD_CHANNEL_TOKEN'))
ADMIN_DISCORD_ID = int(os.getenv('ADMIN_DISCORD_ID'))

# Retrieve database credentials from environment variables
MYSQL_HOST = os.getenv('MYSQL_HOST')
MYSQL_USER = os.getenv('MYSQL_USER')
MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD')
MYSQL_DB = os.getenv('MYSQL_DB')
MYSQL_PORT = os.getenv('MYSQL_PORT')

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# Initialize bot with default intents
intents = Intents.default()
intents.members = True
bot = commands.Bot(command_prefix='!', intents=intents)
openai.api_key = OPENAI_API_KEY

# TODO: Remove these globals
streaks_manager = None
weekly_post_manager = None
team_member_manager = None
updates_manager = None
scheduler = None
ongoing_status_requests = {}

# Define a loop that runs every 30 minutes to check if a new weekly post should be created
@tasks.loop(minutes=30)
async def check_weekly_post(weekly_post_manager: WeeklyPostManager, streaks_manager: StreaksManager, team_members: List[TeamMember]):
    earliest_time_zone = None
    earliest_time = None
    
    for member in team_members:
        tz = pytz.timezone(member.time_zone)
        local_time = datetime.now(tz)
        
        if local_time.weekday() == 0 and local_time.hour >= 9:
            if earliest_time is None or local_time < earliest_time:
                earliest_time = local_time
                earliest_time_zone = member.time_zone
                
    if earliest_time is not None:
        print(f"Initializing weekly post based on the earliest time zone: {earliest_time_zone}")

        # Reset streaks for the previous week
        for member in team_members:
            if not weekly_post_manager.has_minimum_checkmarks(member, 5):
                streaks_manager.reset_streak(member.discord_id)
        
        # Initialize new weekly post
        await weekly_post_manager.initialize_post()

async def send_status_request(member: TeamMember, weekly_post_manager: WeeklyPostManager, streaks_manager: StreaksManager, updates_manager: UpdatesManager):
    if weekly_post_manager.has_all_checkmarks(member):
        return  # If all checkmarks are present, do nothing

    user = bot.get_user(member.discord_id)
    if user:
        # Cancel the previous wait_for task if it exists
        ongoing_task: Task = ongoing_status_requests.get(member.discord_id)
        if ongoing_task:
            ongoing_task.cancel()

        await user.send(
            f"# Good morning {member.name}, time for your daily status update!\n"
            f"## Please include in a single message:\n"
            f"### What work-related tasks you accomplished yesterday.\n"
            f"### What work-related tasks you plan to work on today.\n"
            f"### **(Note: We're currently only processing the first message you send back. Multi-message updates are coming soon!)**"
        )

        def check(m) -> bool:
            return m.author == user and isinstance(m.channel, DMChannel)
        
        # Store the new wait_for task in the global dictionary
        ongoing_task = ensure_future(bot.wait_for('message', check=check))
        ongoing_status_requests[member.discord_id] = ongoing_task
        
        try:
            msg = await ongoing_task
            ongoing_status_requests.pop(member.discord_id, None)
        except CancelledError:
            return  # If the task is cancelled, do nothing

        # Insert the status update into the database
        updates_manager.insert_status(member.discord_id, msg.content)

        # Update the streak for this member
        streak = streaks_manager.get_streak(member.discord_id)
        streaks_manager.update_streak(member.discord_id, streak + 1)

        # Update the Discord post using WeeklyPostManager
        await weekly_post_manager.update_post(member)

        # Prepare a system message to guide OpenAI's model
        system_message = "Please summarize the user's update into two sections: 'Did' for tasks completed yesterday and 'Do' for tasks planned for today."
        
        # User's message that you want to summarize
        user_message = msg.content
        
        # Prepare the messages input for ChatCompletion
        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_message}
        ]
        
        # OpenAI API call using ChatCompletion
        model_engine = "gpt-3.5-turbo-0613"
        response = openai.ChatCompletion.create(
            model=model_engine,
            messages=messages
        )
        
        # Extract the generated text
        generated_text = response['choices'][0]['message']['content'].strip()

        updates_manager.update_summarized_status(member.discord_id, generated_text)
        
        # Send the generated summary to a designated Discord channel
        guild = bot.get_guild(GUILD_TOKEN)
        channel_to_post_in = guild.get_channel(CHANNEL_TOKEN)
        await channel_to_post_in.send(f"**{member.name}'s summary:**\n{generated_text}")

@bot.command(name='statusrequest')
async def status_request(ctx, discord_id: int):
    if ctx.message.author.id != ADMIN_DISCORD_ID or not isinstance(ctx.channel, DMChannel):
        await ctx.send("You're not authorized to request status.")
        return

    # Find the member object using the Discord ID
    member_to_request = team_member_manager.find_member(discord_id)

    if member_to_request:
        # Send the status request to the member
        await ctx.send(f"Status request sent to user with Discord ID {discord_id}.")
        await send_status_request(member_to_request, weekly_post_manager, streaks_manager, updates_manager)
        await ctx.send(f"Status request received from user with Discord ID {discord_id}.")
    else:
        await ctx.send(f"No user with Discord ID {discord_id} found.")

@bot.command(name='adduser')
async def add_user(ctx, discord_id: int, time_zone: str, name: str):
    if ctx.message.author.id != ADMIN_DISCORD_ID or not isinstance(ctx.channel, DMChannel):
        await ctx.send("You're not authorized to add users.")
        return
    
    # Add the new member using team_member_manager
    team_member_manager.add_member(discord_id, name, time_zone)
    
    # Update the weekly post to include the new member
    new_member = team_member_manager.find_member(discord_id)
    if new_member:
        await weekly_post_manager.add_member_to_post(new_member)
        scheduler.add_job(send_status_request, new_member, weekly_post_manager, streaks_manager, updates_manager) 
    
    await ctx.send(f"User {name} added successfully.")

@bot.command(name='removeuser')
async def remove_user(ctx, discord_id: int):
    if ctx.message.author.id != ADMIN_DISCORD_ID or not isinstance(ctx.channel, DMChannel):
        await ctx.send("You're not authorized to remove users.")
        return

    # Find the member object
    member_to_remove = team_member_manager.find_member(discord_id)

    if member_to_remove:
        # Remove the member from the database
        team_member_manager.remove_member(discord_id)
        
        # Update the weekly post to remove the member
        await weekly_post_manager.remove_member_from_post(member_to_remove)
        scheduler.remove_job(discord_id)

        await ctx.send(f"User with Discord ID {discord_id} removed successfully.")
    else:
        await ctx.send(f"No user with Discord ID {discord_id} found.")

@bot.command(name='listusers')
async def list_users(ctx):
    if ctx.message.author.id != ADMIN_DISCORD_ID or not isinstance(ctx.channel, DMChannel):
        await ctx.send("You're not authorized to list users.")
        return

    # List users using team_member_manager
    users = [(member.discord_id, member.name, member.time_zone) for member in team_member_manager.team_members]
    user_list = '\n'.join([f"Name: {user[1]}, Discord ID: {user[0]}, Time Zone: {user[2]}" for user in users])

    await ctx.send(f"List of users:\n{user_list}")

@bot.event
async def on_ready():
    print("Bot is online!")  # Log that the bot is online

    streaks_db = StreaksDB(MYSQL_HOST, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DB, MYSQL_PORT)
    team_member_db = TeamMemberDB(MYSQL_HOST, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DB, MYSQL_PORT)
    weekly_posts_db = WeeklyPostsDB(MYSQL_HOST, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DB, MYSQL_PORT)
    updates_db = UpdatesDB(MYSQL_HOST, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DB, MYSQL_PORT)

    guild = bot.get_guild(GUILD_TOKEN)
    channel = guild.get_channel(CHANNEL_TOKEN)

    global updates_manager

    updates_manager = UpdatesManager(updates_db)

    global streaks_manager

    streaks_manager = StreaksManager(streaks_db)

    global team_member_manager

    team_member_manager = TeamMemberManager(team_member_db)
    team_members = team_member_manager.load_team_members()

    # Update each team member's streak from the database
    for member in team_members:
        member.update_streak(streaks_manager.get_streak(member.discord_id))
        member.update_weekly_checkins(updates_manager.get_weekly_checkins_count(member.discord_id, member.time_zone))

    global weekly_post_manager
    
    weekly_post_manager = WeeklyPostManager(channel, team_members, streaks_manager, weekly_posts_db)
    # Initialize new weekly post
    await weekly_post_manager.initialize_post()

    check_weekly_post.start(weekly_post_manager, streaks_manager, team_members)

    global scheduler
    scheduler = Scheduler()
    
    for member in team_members:
        scheduler.add_job(send_status_request, member, weekly_post_manager, streaks_manager, updates_manager)

@app.route('/')
def index(): 
    return 'Discord bot is running.'

def run_bot():
    bot.run(BOT_TOKEN)

def run_app():
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 80)))

if __name__ == '__main__':
    p1 = Process(target=run_bot)
    p2 = Process(target=run_app)

    p1.start()
    p2.start()

    p1.join()
    p2.join()