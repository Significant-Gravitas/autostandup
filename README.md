# AutoStandup Bot

## Overview
This Discord bot automates various team management tasks, enhancing visibility, accountability, and productivity within remote teams. Built with Python, it uses Flask for web functionalities and MySQL for database operations. The bot also incorporates gamification aspects like streaks and utilizes Language Model (LLM)-based summarization to make status updates more efficient.

## Features
- **Automatic Pinging**: Customizable pings for status updates based on team members' time zones.
- **Weekly Summaries**: Automated weekly summary posts in a Discord channel.
- **Team Member Management**: Add, update, and remove team members with ease.
- **Database-Backed**: Persistence for status updates and team member details.
- **Streaks**: Gamification to encourage regular status updates.
- **LLM-Based Summarization**: Uses language models to summarize updates, reducing the burden on engineers.

## Prerequisites
- Python 3.x
- `discord.py` library
- `python-dotenv` library
- `mysql-connector-python` library
- `apscheduler` library
- `Flask` library
- A Discord account and server (guild)
- MySQL Database
- (Optional) Docker

## Setup

### Discord Developer Portal
1. **Create a New Application**: Go to the [Discord Developer Portal](https://discord.com/developers/applications) and create a new application.
2. **Add a Bot**: Navigate to the "Bot" tab and click "Add a Bot".
3. **Get Bot Token**: Under the "Bot" tab, you'll find your bot token. Keep this handy for the `.env` file.
4. **Invite Bot to Server**: In the "OAuth2" tab, under "OAuth2 URL Generator", check the "bot" scope and choose necessary permissions to generate an invite URL. Use this URL to invite your bot to your server.

### Environment Variables
Create a `.env` file in the root of your project and add the following variables:
```
DISCORD_BOT_TOKEN=<Your Bot Token Here>
DISCORD_GUILD_TOKEN=<Your Guild (Server) Token Here>
DISCORD_CHANNEL_TOKEN=<Your Channel Token Here>
ADMIN_DISCORD_ID=<Your Admin Discord ID Here>
MYSQL_HOST=<MySQL Host>
MYSQL_USER=<MySQL User>
MYSQL_PASSWORD=<MySQL Password>
MYSQL_DB=<MySQL Database>
MYSQL_PORT=<MySQL Port>
OPENAI_API_KEY=<OpenAI API Key>
```

### Database Setup
1. **Install MySQL**: If not already installed, download and install MySQL Server.
2. **Create Database**: Create a new MySQL database named as per the `MYSQL_DB` variable in the `.env` file.
3. **User Privileges**: Ensure that the MySQL user specified in `MYSQL_USER` has necessary privileges on the database.

### Docker Setup (Optional)
To run the bot in a Docker container, build the Docker image and run it:
```
docker build -t autostandup-bot .
docker run -d autostandup-bot
```

## Installation
1. Clone this repository.
2. Navigate to the project directory.
3. Install the required packages:
```
pip install -r requirements.txt
```
4. Run the bot:
```
python bot.py
```

## Usage
Once the bot is running and has joined your server, it will automatically perform configured tasks. The bot also keeps track of streaks for regular updates and can summarize updates using language models.

## Contributions
Feel free to contribute to this project by submitting issues or pull requests.

## License
This project is licensed under the MIT License.