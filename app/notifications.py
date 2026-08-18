import aiohttp
from .config import BOT_TOKEN, ADMIN_CHAT_ID

async def send_telegram_notification(text: str):
    if not BOT_TOKEN or not ADMIN_CHAT_ID:
        return
    
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": ADMIN_CHAT_ID,
        "text": text,
        "parse_mode": "HTML"
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as response:
                await response.json()
    except Exception as e:
        print(f"Failed to send notification: {e}")

async def notify_online(user_id: int, name: str, started_at_local: str):
    text = (
        f"🟢 <b>TEST ACCOUNT ONLINE</b>\n\n"
        f"User: {name}\n"
        f"ID: <code>{user_id}</code>\n"
        f"Started: {started_at_local}"
    )
    await send_telegram_notification(text)

async def notify_offline(user_id: int, name: str, started_at_local: str, ended_at_local: str, duration: int):
    text = (
        f"🔴 <b>TEST ACCOUNT OFFLINE</b>\n\n"
        f"User: {name}\n"
        f"ID: <code>{user_id}</code>\n"
        f"Started: {started_at_local}\n"
        f"Ended: {ended_at_local}\n"
        f"Duration: {duration} seconds"
    )
    await send_telegram_notification(text)
