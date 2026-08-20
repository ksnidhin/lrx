from telethon import TelegramClient, events
from telethon.tl.types import UserStatusOnline, UserStatusOffline, User
from .config import API_ID, API_HASH, SESSION_NAME
from .presence import tracker

# We initialize it but do not start it here, we will start it in main.py
client = TelegramClient(SESSION_NAME, API_ID, API_HASH)

@client.on(events.UserUpdate)
async def handler(event):
    # Log raw MTProto update info
    print("=============================")
    print("RAW STATUS UPDATE")
    print(f"user_id={event.user_id}")
    print(f"status={type(event.status).__name__ if event.status else 'None'}")
    
    if isinstance(event.status, UserStatusOnline):
        print(f"expires={getattr(event.status, 'expires', 'Unknown')}")
    elif isinstance(event.status, UserStatusOffline):
        print(f"was_online={getattr(event.status, 'was_online', 'Unknown')}")
        
    print(f"RAW EVENT: {event.original_update}")
    print("=============================")
    
    if not event.status:
        return
        
    user_id = event.user_id
    
    from .database import get_test_user_name
    name = await get_test_user_name(user_id)

    if isinstance(event.status, UserStatusOnline):
        await tracker.handle_status_change(user_id, "ONLINE", name)
    elif isinstance(event.status, UserStatusOffline):
        await tracker.handle_status_change(user_id, "OFFLINE", name)
    # Vague states are ignored per requirements
