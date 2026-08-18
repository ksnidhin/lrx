from telethon import TelegramClient, events
from .config import API_ID, API_HASH, BOT_TOKEN, ADMIN_CHAT_ID
from .database import add_test_user, remove_test_user, get_test_users, get_user_history, format_time
from .presence import tracker

bot = TelegramClient('bot_session', API_ID, API_HASH)

def is_admin(event):
    return event.chat_id == ADMIN_CHAT_ID

@bot.on(events.NewMessage(pattern='/start|/help'))
async def help_handler(event):
    if not is_admin(event):
        return
    text = (
        "🤖 **Presence Test Bot Admin**\n\n"
        "/add <user_id> - Add a test account\n"
        "/remove <user_id> - Remove a test account\n"
        "/list - List all test accounts\n"
        "/status <user_id> - Get current status\n"
        "/history <user_id> - Get session history\n"
        "/help - Show this message\n"
    )
    await event.reply(text)

@bot.on(events.NewMessage(pattern=r'/add\s+(\d+)'))
async def add_handler(event):
    if not is_admin(event):
        return
    user_id = int(event.pattern_match.group(1))
    await add_test_user(user_id, first_name="Manual Added")
    await event.reply(f"✅ Added {user_id} to test accounts.")

@bot.on(events.NewMessage(pattern=r'/remove\s+(\d+)'))
async def remove_handler(event):
    if not is_admin(event):
        return
    user_id = int(event.pattern_match.group(1))
    await remove_test_user(user_id)
    await event.reply(f"❌ Removed {user_id} from test accounts.")

@bot.on(events.NewMessage(pattern='/list'))
async def list_handler(event):
    if not is_admin(event):
        return
    users = await get_test_users()
    if not users:
        await event.reply("No test accounts configured.")
        return
    
    text = "**Test Accounts:**\n"
    for u in users:
        text += f"- `{u['telegram_user_id']}` ({u['first_name'] or 'Unknown'})\n"
    await event.reply(text)

@bot.on(events.NewMessage(pattern=r'/status\s+(\d+)'))
async def status_handler(event):
    if not is_admin(event):
        return
    user_id = int(event.pattern_match.group(1))
    state = tracker.user_states.get(user_id)
    if state:
        status = state['status']
        started = format_time(state['started_at']) if state['started_at'] else "N/A"
        await event.reply(f"Status for `{user_id}`: **{status}**\nStarted at: {started}")
    else:
        await event.reply(f"Status for `{user_id}`: **OFFLINE** (No active tracking data)")

@bot.on(events.NewMessage(pattern=r'/history\s+(\d+)'))
async def history_handler(event):
    if not is_admin(event):
        return
    user_id = int(event.pattern_match.group(1))
    history = await get_user_history(user_id)
    if not history:
        await event.reply(f"No history found for `{user_id}`.")
        return
    
    text = f"**History for {user_id}:**\n\n"
    for h in history:
        start = format_time(h['started_at'])
        end = format_time(h['ended_at'])
        duration = h['duration_seconds']
        text += f"🟢 {start} -> 🔴 {end}\n⏳ Duration: {duration}s\n\n"
    
    await event.reply(text)
