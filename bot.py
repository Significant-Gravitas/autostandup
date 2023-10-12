# Import required modules
import os
from discord.ext import commands, tasks
from discord import Intents
from dotenv import load_dotenv

# Load environment variables from the .env file
load_dotenv()

# Retrieve bot, guild, and channel tokens from environment variables
BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN')
GUILD_TOKEN = int(os.getenv('DISCORD_GUILD_TOKEN'))
CHANNEL_TOKEN = int(os.getenv('DISCORD_CHANNEL_TOKEN'))

# Initialize bot with default intents
intents = Intents.default()
bot = commands.Bot(command_prefix='!', intents=intents)

# Define a loop that runs every 48 hours to ping for status updates
@tasks.loop(hours=48)
async def ping_for_status():
    # Get the guild (server) and channel using their IDs
    guild = bot.get_guild(GUILD_TOKEN)
    channel = guild.get_channel(CHANNEL_TOKEN)
    # Send a message to the channel to ping everyone for a status update
    await channel.send("Hey @everyone, time for a status update! Please share what you've been working on.")

# Event triggered when the bot is ready
@bot.event
async def on_ready():
    print("Bot is online!")  # Print a message to the console
    ping_for_status.start()  # Start the loop for pinging status updates

# Run the bot
bot.run(BOT_TOKEN)
