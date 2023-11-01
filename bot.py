# Import required modules
import os
import pytz
from typing import List
from dotenv import load_dotenv
from datetime import datetime, timedelta
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
import requests

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

ORG_NAME = os.getenv('GITHUB_ORG_NAME')
ORG_TOKEN = os.getenv('GITHUB_ORG_TOKEN')

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# Initialize bot with default intents
intents = Intents.default()
intents.members = True
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)
openai.api_key = OPENAI_API_KEY

# TODO: Remove these globals
streaks_manager = None
weekly_post_manager = None
team_member_manager = None
updates_manager = None
scheduler = None
ongoing_status_requests = {}

THUMBS_UP_EMOJI = "👍"
PENCIL_EMOJI = "✏️"

async def weekly_state_reset(weekly_post_manager: WeeklyPostManager, streaks_manager: StreaksManager, team_members: List[TeamMember]):
    # Reset streaks for the previous week
    for member in team_members:
        if member.weekly_checkins < 5:
            streaks_manager.reset_streak(member.discord_id)
            member.reset_streak()
        member.reset_weekly_checkins()
    
    # Initialize new weekly post
    await weekly_post_manager.initialize_post(team_members)

def get_all_commit_messages_for_user(org_name: str, token: str, member: TeamMember) -> list:
    """Retrieve all commit messages for a user across all repos in an organization from the last 24 hours."""
    
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    last_update_timestamp, user_time_zone = updates_manager.get_last_update_timestamp(member.discord_id)
    if last_update_timestamp:
        # Convert the timestamp to UTC
        local_tz = pytz.timezone(user_time_zone)
        localized_timestamp = local_tz.localize(last_update_timestamp)
        utc_timestamp = localized_timestamp.astimezone(pytz.utc)
        since_date = utc_timestamp.isoformat() + 'Z'
    else:
        # If no updates found, default to last 24 hours (or you can adjust this default behavior as needed)
        since_date = (datetime.utcnow() - timedelta(days=1)).isoformat() + 'Z'

    # Get a list of all repositories in the organization
    repos_url = f"https://api.github.com/orgs/{org_name}/repos"
    response = requests.get(repos_url, headers=headers)
    
    if response.status_code != 200:
        # Handle errors
        return []
    
    repos = response.json()
    
    all_commit_messages = []

    # Iterate over each repository
    for repo in repos:
        repo_name = repo["name"]
        commits_url = f"https://api.github.com/repos/{org_name}/{repo_name}/commits?author={member.github_username}&since={since_date}"
        response = requests.get(commits_url, headers=headers)
        
        if response.status_code != 200:
            continue
        
        commits = response.json()
        
        # Extract commit messages for this repository
        # TODO: Potentially return commit URLs as well.
        repo_commit_messages = [commit["commit"]["message"] for commit in commits]
        
        all_commit_messages.extend(repo_commit_messages)
    
    return all_commit_messages

async def send_status_request(member: TeamMember, 
                              weekly_post_manager: WeeklyPostManager, 
                              streaks_manager: StreaksManager, 
                              updates_manager: UpdatesManager):
    if member.weekly_checkins == 5:
        return  # If already completed 5 check-ins, do nothing

    user = bot.get_user(member.discord_id)
    if user:
        # Notify the admin
        admin_user = bot.get_user(ADMIN_DISCORD_ID)
        if admin_user:
            await admin_user.send(f"Status request sent to {member.name}.")

        # Cancel the previous wait_for task if it exists
        ongoing_task: Task = ongoing_status_requests.get(member.discord_id)
        if ongoing_task:
            ongoing_task.cancel()

        await user.send(
            f"# Good morning {member.name}, time for your daily status update!\n"
            f"## Please include in a single message:\n"
            f"### What work-related tasks you accomplished on your last working day.\n"
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
        updates_manager.insert_status(member.discord_id, msg.content, member.time_zone)

        # Generate the daily summary using the UpdatesManager's method
        summarized_message = await updates_manager.generate_daily_summary(msg.content)

        updates_manager.update_summarized_status(member.discord_id, summarized_message)

        # Update the streak for this member
        streak = streaks_manager.get_streak(member.discord_id)
        streaks_manager.update_streak(member.discord_id, streak + 1)
        member.update_streak(streaks_manager.get_streak(member.discord_id))
        member.increment_weekly_checkins()

        # Update the Discord post using WeeklyPostManager
        await weekly_post_manager.rebuild_post(team_member_manager.team_members)
        
        # Send the generated summary to a designated Discord channel
        guild = bot.get_guild(GUILD_TOKEN)
        channel_to_post_in = guild.get_channel(CHANNEL_TOKEN)
        await channel_to_post_in.send(f"**{member.name}'s summary:**\n{summarized_message}")

async def send_status_request_revised(member: TeamMember):
    if member.weekly_checkins == 5:
        return  # If already completed 5 check-ins, do nothing

    user = bot.get_user(member.discord_id)
    if user:
        # Cancel the previous task if it exists
        ongoing_task: Task = ongoing_status_requests.get(member.discord_id)
        if ongoing_task:
            ongoing_task.cancel()

        # Retrieve all commit messages for the member
        commit_messages = get_all_commit_messages_for_user(ORG_NAME, ORG_TOKEN, member)
            
        if not commit_messages:
            msg = "You have no commits for the previous working day."
        else:
            summarized_report = await updates_manager.summarize_technical_updates(commit_messages)
            msg = f"Here's your summarized report based on your commits:\n{summarized_report}\nReact with {THUMBS_UP_EMOJI} to confirm or {PENCIL_EMOJI} to suggest changes."

        # Send initial message and wait for reaction
        sent_message = await user.send(msg)
        await sent_message.add_reaction(THUMBS_UP_EMOJI)
        await sent_message.add_reaction(PENCIL_EMOJI)
        
        def check(m) -> bool:
            return m.author == user and isinstance(m.channel, DMChannel)

        # Store the new wait_for reaction task in the global dictionary
        ongoing_task = ensure_future(bot.wait_for('reaction_add', check=lambda r, u: u == user and r.message.id == sent_message.id and isinstance(r.message.channel, DMChannel) and str(r.emoji) in [THUMBS_UP_EMOJI, PENCIL_EMOJI]))
        ongoing_status_requests[member.discord_id] = ongoing_task
        reaction, reactor = await ongoing_task
        ongoing_status_requests.pop(member.discord_id, None)  # Remove the task once we get the reaction
        
        for emoji in [THUMBS_UP_EMOJI, PENCIL_EMOJI]:
            await sent_message.remove_reaction(emoji, bot.user)
        
        while str(reaction.emoji) == PENCIL_EMOJI:
            await user.send("Please provide your feedback or edit the status.")
            
            # Store the new wait_for message (feedback) task in the global dictionary
            ongoing_task = ensure_future(bot.wait_for('message', check=check))
            ongoing_status_requests[member.discord_id] = ongoing_task
            feedback = await ongoing_task
            ongoing_status_requests.pop(member.discord_id, None)  # Remove the task once we get the feedback
                
            # Send original + feedback to LLM for reformatting
            summarized_report = await updates_manager.summarize_feedback_and_revisions(summarized_report, feedback.content)
            msg = f"Here's the revised report:\n{summarized_report}\nReact with {THUMBS_UP_EMOJI} to confirm or {PENCIL_EMOJI} to provide further feedback."
            
            sent_message = await user.send(msg)
            await sent_message.add_reaction(THUMBS_UP_EMOJI)
            await sent_message.add_reaction(PENCIL_EMOJI)
            
            # Store the new wait_for reaction task in the global dictionary
            ongoing_task = ensure_future(bot.wait_for('reaction_add', check=lambda r, u: u == user and r.message.id == sent_message.id and isinstance(r.message.channel, DMChannel) and str(r.emoji) in [THUMBS_UP_EMOJI, PENCIL_EMOJI]))
            ongoing_status_requests[member.discord_id] = ongoing_task
            reaction, user = await ongoing_task
            ongoing_status_requests.pop(member.discord_id, None)  # Remove the task once we get the reaction

            for emoji in [THUMBS_UP_EMOJI, PENCIL_EMOJI]:
                await sent_message.remove_reaction(emoji, bot.user)
                
        # Prompt user for non-technical updates from the previous day
        non_technical_msg_prompt = "Please provide any non-technical updates from your previous working day, e.g., important meetings, interviews, etc."
        await user.send(non_technical_msg_prompt)

        # Store the new wait_for message (non-technical update) task in the global dictionary
        ongoing_task = ensure_future(bot.wait_for('message', check=check))
        ongoing_status_requests[member.discord_id] = ongoing_task
        non_technical_update_raw = await ongoing_task
        ongoing_status_requests.pop(member.discord_id, None)  # Remove the task once we get the non-technical update
        
        # Summarize non-technical update with LLM
        non_technical_update = await updates_manager.summarize_non_technical_updates(non_technical_update_raw.content)
        
        # Prompt user for their goals for the day
        goals_msg_prompt = "What do you plan to work on or accomplish today?"
        await user.send(goals_msg_prompt)

        # Store the new wait_for message (goals for the day) task in the global dictionary
        ongoing_task = ensure_future(bot.wait_for('message', check=check))
        ongoing_status_requests[member.discord_id] = ongoing_task
        goals_for_today_raw = await ongoing_task
        ongoing_status_requests.pop(member.discord_id, None)  # Remove the task once we get the goals
        
        # Summarize goals for the day with LLM
        goals_for_today = await updates_manager.summarize_goals_for_the_day(goals_for_today_raw.content)

        # Member name update as a header
        member_update_header = f"## {member.name}'s Update:"

        # Compile the final report with Markdown formatting
        final_report = (
            f"\n### Technical Update:\n"
            f"{summarized_report}\n"
            f"\n### Non-Technical Update:\n"
            f"{non_technical_update}\n"
            f"\n### Goals for Today:\n"
            f"{goals_for_today}"
        )

        # Concatenate the member name update with the final report and send to the designated Discord channel
        complete_message = f"{member_update_header}{final_report}"
        guild = bot.get_guild(GUILD_TOKEN)
        channel_to_post_in = guild.get_channel(CHANNEL_TOKEN)
        await channel_to_post_in.send(complete_message)

@bot.command(name='viewscheduledjobs')
async def view_scheduled_jobs(ctx):
    if ctx.message.author.id != ADMIN_DISCORD_ID or not isinstance(ctx.channel, DMChannel):
        await ctx.send("You're not authorized to view scheduled jobs.")
        return

    # Get all scheduled jobs using the Scheduler's method
    scheduled_jobs = scheduler.get_all_scheduled_jobs(team_member_manager)

    # Send the scheduled jobs to the admin user
    for job in scheduled_jobs:
        await ctx.send(job)

@bot.command(name='statusrequestv2')
async def status_request_v2(ctx, discord_id: int):
    if ctx.message.author.id != ADMIN_DISCORD_ID or not isinstance(ctx.channel, DMChannel):
        await ctx.send("You're not authorized to test revised status.")
        return

    # Find the member object using the Discord ID
    member_to_test = team_member_manager.find_member(discord_id)

    if member_to_test:
        # Send the revised status request to the member
        await ctx.send(f"Revised status request sent to user with Discord ID {discord_id}.")
        await send_status_request_revised(member_to_test)
        await ctx.send(f"Revised status request process completed for user with Discord ID {discord_id}.")
    else:
        await ctx.send(f"No user with Discord ID {discord_id} found.")

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
async def add_user(ctx, discord_id: int, time_zone: str, name: str, github_username: str):
    if ctx.message.author.id != ADMIN_DISCORD_ID or not isinstance(ctx.channel, DMChannel):
        await ctx.send("You're not authorized to add users.")
        return
    
    # Add the new member using team_member_manager
    team_member_manager.add_member(discord_id, name, time_zone, github_username)
    
    # Update the weekly post to include the new member
    new_member = team_member_manager.find_member(discord_id)
    if new_member:
        await weekly_post_manager.rebuild_post(team_member_manager.team_members)
        scheduler.add_job(send_status_request, new_member, weekly_post_manager, streaks_manager, updates_manager) 
        scheduler.unschedule_weekly_post()
        scheduler.schedule_weekly_post(weekly_state_reset, weekly_post_manager, streaks_manager, team_member_manager.team_members)
    
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
        await weekly_post_manager.rebuild_post(team_member_manager.team_members)
        scheduler.remove_job(discord_id)
        scheduler.unschedule_weekly_post()
        scheduler.schedule_weekly_post(weekly_state_reset, weekly_post_manager, streaks_manager, team_member_manager.team_members)

        await ctx.send(f"User with Discord ID {discord_id} removed successfully.")
    else:
        await ctx.send(f"No user with Discord ID {discord_id} found.")

@bot.command(name='listusers')
async def list_users(ctx):
    if ctx.message.author.id != ADMIN_DISCORD_ID or not isinstance(ctx.channel, DMChannel):
        await ctx.send("You're not authorized to list users.")
        return

    # List users using team_member_manager
    users = [(member.discord_id, member.name, member.time_zone, member.github_username, member.current_streak) for member in team_member_manager.team_members]
    user_list = '\n'.join([f"Name: {user[1]}, Discord ID: {user[0]}, Time Zone: {user[2]}, GitHub Username: {user[3]}, Current Streak: {user[4]}" for user in users])

    await ctx.send(f"List of users:\n{user_list}")

@bot.command(name='updatestreak')
async def update_streak(ctx, discord_id: int, new_streak: int):
    if ctx.message.author.id != ADMIN_DISCORD_ID or not isinstance(ctx.channel, DMChannel):
        await ctx.send("You're not authorized to update streaks.")
        return

    # Find the member object using the Discord ID
    member_to_update = team_member_manager.find_member(discord_id)

    if member_to_update:
        # Update the streak in the database
        streaks_manager.update_streak(discord_id, new_streak)
        member_to_update.update_streak(new_streak)

        # Update the Discord post using WeeklyPostManager
        await weekly_post_manager.rebuild_post(team_member_manager.team_members)
        
        await ctx.send(f"Streak for user with Discord ID {discord_id} updated to {new_streak}.")
    else:
        await ctx.send(f"No user with Discord ID {discord_id} found.")

@bot.command(name='forcepostrebuild')
async def force_post_rebuild(ctx):
    if ctx.message.author.id != ADMIN_DISCORD_ID or not isinstance(ctx.channel, DMChannel):
        await ctx.send("You're not authorized to force a post rebuild.")
        return

    # Rebuild the post
    await weekly_post_manager.rebuild_post(team_member_manager.team_members)

    await ctx.send("Post rebuilt successfully.")

@bot.command(name='deletelateststatus')
async def delete_latest_status(ctx, discord_id: int):
    if ctx.message.author.id != ADMIN_DISCORD_ID or not isinstance(ctx.channel, DMChannel):
        await ctx.send("You're not authorized to delete status updates.")
        return

    # Find the member object using the Discord ID
    member = team_member_manager.find_member(discord_id)

    if not member:
        await ctx.send(f"No user with Discord ID {discord_id} found.")
        return

    # Delete the newest status using the UpdatesManager's method
    updates_manager.delete_newest_status(discord_id)
    await ctx.send(f"Latest status update for user with Discord ID {discord_id} deleted successfully.")

@bot.command(name='viewuser')
async def view_user(ctx, discord_id: int):
    if ctx.message.author.id != ADMIN_DISCORD_ID or not isinstance(ctx.channel, DMChannel):
        await ctx.send("You're not authorized to view user data.")
        return

    # Get the member's statuses using the UpdatesManager's method
    statuses = updates_manager.get_all_statuses_for_user(discord_id)

    if not statuses:
        await ctx.send(f"No status updates found for user with Discord ID {discord_id}.")
        return

    # Loop through the statuses and send individual messages
    for status in statuses:
        await ctx.send(f"### **Timestamp:** {status['timestamp']}")
        await ctx.send(f"### **Raw Status:** {status['status']}")
        await ctx.send(f"### **Summarized Status:** \n{status['summarized_status']}")

@bot.command(name='weeklysummary')
async def weekly_summary(ctx, discord_id: int, start_date: str, end_date: str):
    if ctx.message.author.id != ADMIN_DISCORD_ID or not isinstance(ctx.channel, DMChannel):
        await ctx.send("You're not authorized to generate weekly summaries.")
        return

    # Find the member object using the Discord ID
    member = team_member_manager.find_member(discord_id)

    if not member:
        await ctx.send(f"No user with Discord ID {discord_id} found.")
        return

    # Convert the start_date and end_date strings to datetime objects
    # Adjusting the date format to MM-DD-YYYY and setting the time
    try:
        start_date = datetime.strptime(start_date, '%m-%d-%Y')
        end_date = datetime.strptime(end_date, '%m-%d-%Y')

        # Setting the time to ensure the whole week is captured
        start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = end_date.replace(hour=23, minute=59, second=59, microsecond=999999)
    except ValueError:
        await ctx.send("Invalid date format. Please use MM-DD-YYYY.")
        return

    # Generate the weekly summary
    weekly_summary = await updates_manager.generate_weekly_summary(discord_id, start_date, end_date)

    # Send the weekly summary to the admin user
    admin_user = bot.get_user(ADMIN_DISCORD_ID)
    if admin_user:
        await admin_user.send(f"**{member.name}'s Weekly Summary for {start_date.strftime('%m-%d-%Y')} to {end_date.strftime('%m-%d-%Y')}:**\n{weekly_summary}")
    else:
        await ctx.send("Unable to find the admin user.")

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

    # Update each team member's streak from the database
    for member in team_member_manager.team_members:
        member.update_streak(streaks_manager.get_streak(member.discord_id))
        member.update_weekly_checkins(updates_manager.get_weekly_checkins_count(member.discord_id, member.time_zone))

    global weekly_post_manager
    
    weekly_post_manager = WeeklyPostManager(channel, weekly_posts_db)
    # Initialize new weekly post
    await weekly_post_manager.initialize_post(team_member_manager.team_members)
    await weekly_post_manager.rebuild_post(team_member_manager.team_members)

    global scheduler
    scheduler = Scheduler()

    scheduler.schedule_weekly_post(weekly_state_reset, weekly_post_manager, streaks_manager, team_member_manager.team_members)
    
    for member in team_member_manager.team_members:
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