import asyncio

# Setup event loop before importing Telethon to satisfy Python 3.14+ requirements
try:
    loop = asyncio.get_running_loop()
except RuntimeError:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

from .telegram_client import client, keep_online_task

async def main():
    print("Starting Userbot Client...")
    await client.start()
    print("Userbot started successfully.")
    
    print("Starting IST Online Scheduler...")
    
    # Run indefinitely
    await asyncio.gather(
        client.run_until_disconnected(),
        keep_online_task(client)
    )

if __name__ == '__main__':
    # Use the pre-created loop
    loop.run_until_complete(main())
