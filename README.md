# Telegram Presence Test

A Python application to test Telegram's MTProto presence updates between your own test accounts.

## Overview

This tool connects to Telegram using Telethon to track the online/offline transitions of specific Telegram accounts you control. It persists sessions in a local SQLite database and can send notifications to a designated admin chat via a Telegram Bot.

**This is strictly a development/testing tool for accounts you control.**

## Prerequisites

- Python 3.11+
- Two or more Telegram test accounts that you own.
- API ID and API Hash from [my.telegram.org](https://my.telegram.org/).
- A Telegram Bot Token from [@BotFather](https://t.me/botfather).

## Setup Instructions

1. Clone or copy this repository.
2. Install the requirements:
   ```bash
   pip install -r requirements.txt
   ```
3. Create a `.env` file by copying `.env.example`:
   ```bash
   cp .env.example .env
   ```
4. Fill in the `.env` file:
   - `API_ID` and `API_HASH`: Your API credentials.
   - `BOT_TOKEN`: The token of your notification bot.
   - `ADMIN_CHAT_ID`: Your personal Telegram User ID (where you want to receive bot notifications and commands).
   - `SESSION_NAME`: Any string (e.g., `presence_test`).

## Real MTProto Integration Test

To perform a real test between two accounts you control:

1. **Account A (The Tracker)**: This is the account whose API credentials you provided in the `.env` file. It will run the client.
2. **Account B (The Target)**: This is the second test account whose presence you want to track.

### Steps:
1. Start the application:
   ```bash
   python -m app.main
   ```
2. The first time you run it, you'll be prompted in the terminal to log into **Account A** (The Tracker). Enter your phone number and login code.
3. Open a chat with your Notification Bot (using Account A or your main account, matching `ADMIN_CHAT_ID`).
4. Add **Account B** to the test users list by sending:
   ```
   /add <Account B User ID>
   ```
   *(You can find Account B's User ID using various bots on Telegram, e.g., @userinfobot).*
5. On your phone or another client, open Telegram with **Account B**.
6. The bot should notify you: `🟢 TEST ACCOUNT ONLINE`.
7. Close the Telegram app for **Account B** (force close or wait for timeout).
8. The bot should notify you: `🔴 TEST ACCOUNT OFFLINE` along with the session duration.

### Interacting with the Bot
Send commands to your Bot:
- `/add <user_id>` - Register a test account to track.
- `/remove <user_id>` - Stop tracking a test account.
- `/list` - List all configured test accounts.
- `/status <user_id>` - View current status.
- `/history <user_id>` - View session history.

## Development and Testing

You can run automated tests using `pytest` without needing real Telegram accounts. The simulation layer covers logic and calculations.

```bash
pytest
```

## Docker

You can run the application with Docker:

```bash
docker-compose up -d --build
```
*(Make sure your `.env` is configured and `presence_test.session` is either mapped or you run the container interactively for the first login).*

## Limitations & Privacy

- This tool only tracks accounts explicitly added via the admin interface.
- It only registers explicit `ONLINE` and `OFFLINE` status updates. Vague statuses (like `Recently`, `LastWeek`) are ignored.
- It does not bypass any of Telegram's privacy settings. If the target account hides their "Last Seen & Online" status from the tracker account, this tool will not be able to track them.
