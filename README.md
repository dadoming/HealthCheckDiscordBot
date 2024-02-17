# API Endpoint Health Check Discord Bot

This bot is designed to manage the health state of api's. It will check the health based on the numeric response got from the endpoint and send a message to a warning-channel if the api is down, and if it's up again.

The warning-channel has a visual reference to know the state, meaning:
a green ball if all the endpoints give OK responses, and a red ball if at least one is KO.

Created using [discord.py](https://github.com/Rapptz/discord.py).

## Creating a Discord Developer Account

First you need to create a Discord Developer Account and set up a bot:

1. Go to the [Discord Developer Portal](https://discord.com/developers/applications).
2. Click on "New Application" and give it a name.
3. Navigate to the "Bot" tab and click on "Add Bot".
4. Under the "Token" section, click on "Copy" to copy the bot token. Put this token on a .env file in the root of the project. The .env file should look like this
```
DISCORD_TOKEN=your_token
```

## Inviting the Bot to your Server

To invite the bot to your server, follow these steps:

1. Go to the "OAuth2" tab in the Discord Developer Portal.
2. In the "Scopes" section, select "bot".
3. In the "Bot Permissions" section, choose the necessary permissions for your bot.
4. Copy the generated OAuth2 URL and open it in a new browser tab.
5. Select the server where you want to add the bot and click "Authorize".

# Running the Bot

To run the bot, you must first run the virtual environment and then run the bot. To do this, follow these steps:

1. Create a virtual environment by running the following command in the root of the project:
```
python -m venv venv
```
2. Activate the virtual environment by running the following command:
```
source venv/bin/activate
```
3. Install the required packages by running the following command:
```
pip install -r requirements.txt
```
4. Run the bot by running the following command:
```
python main.py
```

# Commands

The bot has the following commands:

- `!help`: Shows this list of commands.
- `!ping <channel_name> <url> <interval>`: Adds a new health check to the bot. The bot will check the health of the given URL every `interval` seconds and send a message to the warning-channel if the health is down.
- `!remove <channel_name>`: Removes the health check from the bot.
- `!export <channel_name>`: Exports the whole channel health check to a file.
- `!clean <channel_name>`: Removes all the health checks from the bot.
- `!remove`: Removes the health check from the bot.
