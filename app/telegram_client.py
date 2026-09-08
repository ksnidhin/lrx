from telethon import TelegramClient, events, functions
from .config import API_ID, API_HASH, SESSION_NAME, LOG_GROUP_ID
import os
import re
from datetime import datetime
import pytz
import asyncio

try:
    from groq import AsyncGroq
except ImportError:
    AsyncGroq = None

# Initialize Client
client = TelegramClient(SESSION_NAME, API_ID, API_HASH)

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
if AsyncGroq and GROQ_API_KEY:
    groq_client = AsyncGroq(api_key=GROQ_API_KEY)
else:
    groq_client = None

async def solve_scrambled_word(scrambled: str) -> str:
    if not groq_client:
        print("⚠️ Groq client not initialized. Install 'groq' package and set GROQ_API_KEY.")
        return ""
        
    try:
        completion = await groq_client.chat.completions.create(
            model="groq/compound-mini",
            messages=[
                {
                    "role": "system", 
                    "content": "You are a highly advanced anagram solver. The user will give you a scrambled sequence of letters. Respond with EXACTLY ONE unscrambled dictionary word in lowercase. Do not include any punctuation, spaces, quotes, or conversational text. Just the single word."
                },
                {"role": "user", "content": scrambled}
            ],
            temperature=0.0,
            max_tokens=15
        )
        return completion.choices[0].message.content.strip().lower()
    except Exception as e:
        print(f"⚠️ Groq API Error: {e}")
        return ""

@client.on(events.NewMessage(func=lambda e: e.is_group and not e.out))
async def scramble_game_handler(event):
    text = event.message.message or ""
    
    if "Scrambled Word Challenge!" in text and "Word:" in text:
        match = re.search(r"Word:\s*([A-Za-z]+)", text)
        if match:
            scrambled_word = match.group(1)
            print(f"🧩 Detected scramble game! Word: {scrambled_word}")
            
            answer = await solve_scrambled_word(scrambled_word)
            if answer:
                clean_answer = re.sub(r"[^a-z]", "", answer)
                print(f"💡 Groq Solved it: {clean_answer}. Sending to group!")
                
                await event.client.send_message(event.chat_id, clean_answer)
                
                # Send log to log group
                if LOG_GROUP_ID:
                    try:
                        chat = await event.get_chat()
                        chat_title = getattr(chat, 'title', str(event.chat_id))
                        log_text = f"✅ **Solved Scrambled Word!**\n\n**Group:** `{chat_title}`\n**Word:** `{scrambled_word}`\n**Answer:** `{clean_answer}`"
                        await event.client.send_message(LOG_GROUP_ID, log_text)
                    except Exception as e:
                        print(f"⚠️ Failed to send log: {e}")

async def keep_online_task(client):
    """
    Keeps the userbot explicitly 'Online' during the first 20 minutes
    of every hour in Indian Standard Time (IST).
    """
    ist_tz = pytz.timezone('Asia/Kolkata')
    while True:
        try:
            now_ist = datetime.now(ist_tz)
            if 0 <= now_ist.minute < 20:
                print(f"[{now_ist.strftime('%H:%M')}] IST: Within first 20 mins. Setting status to Online.")
                await client(functions.account.UpdateStatusRequest(offline=False))
                # Ping every 3 minutes to keep the "Online" status alive
                await asyncio.sleep(3 * 60)
            else:
                # Go offline explicitly when the 20 minutes are over
                if now_ist.minute == 20:
                    print(f"[{now_ist.strftime('%H:%M')}] IST: 20 mins passed. Setting status to Offline.")
                    await client(functions.account.UpdateStatusRequest(offline=True))
                
                # Sleep until the next hour starts
                minutes_to_next_hour = 60 - now_ist.minute
                print(f"[{now_ist.strftime('%H:%M')}] IST: Sleeping for {minutes_to_next_hour} minutes until next hour.")
                await asyncio.sleep(minutes_to_next_hour * 60)
        except Exception as e:
            print(f"Error in keep_online_task: {e}")
            await asyncio.sleep(60)
