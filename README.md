# ONTU Schedule BOT

A Telegram bot for getting schedule for your group from ONTU website.

## Installation

For local deployment you can use Devcontainers in VSCode. Just open the project in VSCode and choose option "Reopen in Devcontainer".

For "production" deployment (bare metal), you need to use PDM to install dependencies.

1. Install PDM (follow official instructions);
2. Run `pdm install` to install dependencies;
3. Run `pdm run bot` to start the bot.

## Usage

When you first start a bot it'll check environment (either a `.env` file or your env variables) for:
- API_TOKEN - A token from BotFather;
- API_URL - URL to an instance of [ONTU Schedule Bot Admin](https://github.com/Wandering-Cursor/ontu-schedule-bot-admin);
- DEBUG_CHAT_ID - A chat ID for debugging purposes (can be personal chat with a bot, or a group ID).

After that the bot will start polling updates.
