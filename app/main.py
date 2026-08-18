import asyncio
from .database import init_db
from .telegram_client import client
from .bot import bot
from .config import BOT_TOKEN
from .presence import tracker

async def main():
    await init_db()
    await tracker.recover()
    print("Database initialized and previous state recovered.")
    
    # Start bot
    if BOT_TOKEN:
        await bot.start(bot_token=BOT_TOKEN)
        print("Admin bot started.")
    
    # Start user client
    await client.start()
    print("User client started. Listening for presence updates...")
    
    # Run both indefinitely
    await asyncio.gather(
        client.run_until_disconnected(),
        bot.run_until_disconnected() if BOT_TOKEN else asyncio.sleep(0)
    )

if __name__ == '__main__':
    asyncio.run(main())
