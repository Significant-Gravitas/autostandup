# AutoGPT's TeamStatusTrackerDiscordBot

## Overview
This repository contains the code for a Discord bot designed to automate status updates within remote teams. It's part of the AutoGPT team's initiative to enhance visibility and accountability. The bot pings team members in a specific channel at regular intervals, asking for a quick status update.

## Features
- Automatic pinging for status updates every 48 hours
- (Future) Integration with Notion for task management

## Prerequisites
- Python 3.x
- `discord.py` library
- `python-dotenv` library
- A Discord account and server (guild)

## Setup

### Discord Developer Portal
1. **Create a New Application**: Go to the [Discord Developer Portal](https://discord.com/developers/applications) and create a new application.
2. **Add a Bot**: Navigate to the "Bot" tab and click "Add a Bot".
3. **Get Bot Token**: Under the "Bot" tab, you'll see your bot token. Keep this handy.
4. **Invite Bot to Server**: In the "OAuth2" tab, under "OAuth2 URL Generator", check the "bot" scope and choose necessary permissions to generate an invite URL. Use this URL to invite your bot to your server.

### Environment Variables
Create a `.env` file in the root of your project and add the following variables:
DISCORD_BOT_TOKEN=<Your Bot Token Here>
DISCORD_GUILD_ID=<Your Guild (Server) ID Here>
DISCORD_CHANNEL_ID=<Your Channel ID Here>

### Installation
1. Clone this repository.
2. Navigate to the project directory.
3. Install the required packages:
    ```bash
    pip install -U discord.py python-dotenv
    ```
4. Run the bot:
    ```bash
    python bot.py
    ```

## Usage
Once the bot is running and has joined your server, it will automatically ping members in the specified channel for their status updates every 48 hours.

## Contributions
Feel free to contribute to this project by submitting issues or pull requests.

## License
This project is licensed under the MIT License.
