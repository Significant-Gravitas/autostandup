import os
from discord.ext import commands
from discord import Intents
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN')

intents = Intents.default()
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print("Bot is online!")

bot.run(BOT_TOKEN)
