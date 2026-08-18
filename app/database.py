import aiosqlite
import datetime
import pytz
from typing import List, Dict, Any, Optional

from . import config

def now_utc():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()

def format_time(iso_str: str) -> str:
    if not iso_str:
        return "N/A"
    try:
        dt = datetime.datetime.fromisoformat(iso_str)
        tz = pytz.timezone(config.TIMEZONE)
        dt_local = dt.astimezone(tz)
        return dt_local.strftime('%Y-%m-%d %H:%M:%S %Z')
    except Exception:
        return iso_str

async def init_db():
    async with aiosqlite.connect(config.DATABASE_PATH) as db:
        await db.execute('''
            CREATE TABLE IF NOT EXISTS test_users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_user_id INTEGER UNIQUE,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                enabled BOOLEAN DEFAULT 1,
                created_at TEXT,
                updated_at TEXT
            )
        ''')
        await db.execute('''
            CREATE TABLE IF NOT EXISTS presence_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_user_id INTEGER,
                started_at TEXT,
                ended_at TEXT,
                duration_seconds INTEGER,
                created_at TEXT
            )
        ''')
        await db.execute('''
            CREATE TABLE IF NOT EXISTS presence_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_user_id INTEGER,
                event_type TEXT,
                status TEXT,
                timestamp TEXT
            )
        ''')
        await db.commit()

async def add_test_user(user_id: int, username: str = None, first_name: str = None, last_name: str = None):
    async with aiosqlite.connect(config.DATABASE_PATH) as db:
        now = now_utc()
        await db.execute('''
            INSERT INTO test_users (telegram_user_id, username, first_name, last_name, enabled, created_at, updated_at)
            VALUES (?, ?, ?, ?, 1, ?, ?)
            ON CONFLICT(telegram_user_id) DO UPDATE SET
                enabled=1,
                updated_at=?
        ''', (user_id, username, first_name, last_name, now, now, now))
        await db.commit()

async def remove_test_user(user_id: int):
    async with aiosqlite.connect(config.DATABASE_PATH) as db:
        now = now_utc()
        await db.execute('''
            UPDATE test_users SET enabled=0, updated_at=? WHERE telegram_user_id=?
        ''', (now, user_id))
        await db.commit()

async def get_test_users() -> List[Dict[str, Any]]:
    async with aiosqlite.connect(config.DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute('SELECT * FROM test_users WHERE enabled=1') as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

async def is_test_user(user_id: int) -> bool:
    async with aiosqlite.connect(config.DATABASE_PATH) as db:
        async with db.execute('SELECT enabled FROM test_users WHERE telegram_user_id=?', (user_id,)) as cursor:
            row = await cursor.fetchone()
            return row and row[0] == 1

async def log_event(user_id: int, event_type: str, status: str, timestamp: str):
    async with aiosqlite.connect(config.DATABASE_PATH) as db:
        await db.execute('''
            INSERT INTO presence_events (telegram_user_id, event_type, status, timestamp)
            VALUES (?, ?, ?, ?)
        ''', (user_id, event_type, status, timestamp))
        await db.commit()

async def save_session(user_id: int, started_at: str, ended_at: str, duration: int):
    async with aiosqlite.connect(config.DATABASE_PATH) as db:
        now = now_utc()
        await db.execute('''
            INSERT INTO presence_sessions (telegram_user_id, started_at, ended_at, duration_seconds, created_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, started_at, ended_at, duration, now))
        await db.commit()

async def get_user_history(user_id: int, limit: int = 5) -> List[Dict[str, Any]]:
    async with aiosqlite.connect(config.DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute('''
            SELECT * FROM presence_sessions 
            WHERE telegram_user_id=? 
            ORDER BY ended_at DESC LIMIT ?
        ''', (user_id, limit)) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

async def get_latest_event_for_users() -> Dict[int, Dict[str, Any]]:
    # Find the latest state for all enabled users
    async with aiosqlite.connect(config.DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute('''
            SELECT e.telegram_user_id, e.status, e.timestamp 
            FROM presence_events e
            JOIN test_users u ON e.telegram_user_id = u.telegram_user_id
            WHERE u.enabled = 1
            AND e.id = (
                SELECT MAX(id) FROM presence_events e2 
                WHERE e2.telegram_user_id = e.telegram_user_id
            )
        ''') as cursor:
            rows = await cursor.fetchall()
            return {row['telegram_user_id']: {"status": row["status"], "started_at": row["timestamp"]} for row in rows}
