import aiosqlite
import time

DB_NAME = "tacac.db"

async def init_db():
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, hwid TEXT, subscription_end INTEGER DEFAULT 0)")
        await db.execute("CREATE TABLE IF NOT EXISTS keys (key TEXT PRIMARY KEY, days INTEGER, used INTEGER DEFAULT 0, used_by INTEGER)")
        await db.commit()

async def get_user(user_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)) as cur:
            return await cur.fetchone()

async def create_user(user_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
        await db.commit()

async def reset_hwid(user_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("UPDATE users SET hwid = NULL WHERE user_id = ?", (user_id,))
        await db.commit()

async def add_subscription(user_id: int, days: int):
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT subscription_end FROM users WHERE user_id = ?", (user_id,)) as cur:
            row = await cur.fetchone()
            current = row[0] if row and row[0] else 0
        now = int(time.time())
        new_end = max(current, now) + days * 86400
        await db.execute("UPDATE users SET subscription_end = ? WHERE user_id = ?", (new_end, user_id))
        await db.commit()

async def create_key(key: str, days: int):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("INSERT INTO keys (key, days) VALUES (?, ?)", (key, days))
        await db.commit()

async def activate_key(user_id: int, key: str):
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT days, used FROM keys WHERE key = ?", (key,)) as cur:
            row = await cur.fetchone()
        if not row or row[1]:
            return False
        days = row[0]
        await db.execute("UPDATE keys SET used = 1, used_by = ? WHERE key = ?", (user_id, key))
        await db.commit()
    await add_subscription(user_id, days)
    return True
