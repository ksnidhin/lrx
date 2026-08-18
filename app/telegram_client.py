from telethon import TelegramClient, events
from telethon.tl.types import UserStatusOnline, UserStatusOffline, User
from .config import API_ID, API_HASH, SESSION_NAME
from .presence import tracker

# We initialize it but do not start it here, we will start it in main.py
client = TelegramClient(SESSION_NAME, API_ID, API_HASH)

@client.on(events.UserUpdate)
async def handler(event):
    if not event.status:
        return
    
    user_id = event.user_id
    
    # Optional: fetch user to get name
    try:
        user = await client.get_entity(user_id)
        name = f"{user.first_name or ''} {user.last_name or ''}".strip() or user.username or "Unknown"
    except Exception:
        name = "Unknown"

    if isinstance(event.status, UserStatusOnline):
        await tracker.handle_status_change(user_id, "ONLINE", name)
    elif isinstance(event.status, UserStatusOffline):
        await tracker.handle_status_change(user_id, "OFFLINE", name)
    # Vague states are ignored per requirements
