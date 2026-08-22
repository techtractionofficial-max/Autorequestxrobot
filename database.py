import aiosqlite
from typing import List, Optional, Tuple
from config import config

class Database:
    def __init__(self, db_path: str = config.DATABASE_PATH):
        self.db_path = db_path

    async def init_db(self):
        """Initializes tables and configures SQLite Write-Ahead Logging for high concurrency."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("PRAGMA journal_mode=WAL;")
            await db.execute("PRAGMA synchronous=NORMAL;")
            
            # Registered bot users
            await db.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    first_name TEXT,
                    username TEXT,
                    is_active INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)

            # Connected channels & groups
            await db.execute("""
                CREATE TABLE IF NOT EXISTS channels (
                    channel_id INTEGER PRIMARY KEY,
                    owner_id INTEGER,
                    title TEXT,
                    auto_approve INTEGER DEFAULT 1,
                    custom_dm_text TEXT DEFAULT '<b>Hello {name}!</b> 🎉\n\nYour request has been approved.\nJoin our exclusive channel below:',
                    promo_btn_text TEXT DEFAULT '🔥 Join VIP Channel',
                    promo_btn_url TEXT DEFAULT 'https://t.me/Telegram',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)

            # Queued join requests for manual batch mode
            await db.execute("""
                CREATE TABLE IF NOT EXISTS pending_requests (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    channel_id INTEGER,
                    user_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(channel_id, user_id)
                );
            """)
            await db.commit()

    async def register_user(self, user_id: int, first_name: str, username: Optional[str]):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO users (user_id, first_name, username, is_active)
                VALUES (?, ?, ?, 1)
                ON CONFLICT(user_id) DO UPDATE SET
                    first_name = excluded.first_name,
                    username = excluded.username,
                    is_active = 1;
            """, (user_id, first_name, username))
            await db.commit()

    async def set_user_active_status(self, user_id: int, is_active: bool):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "UPDATE users SET is_active = ? WHERE user_id = ?;",
                (1 if is_active else 0, user_id)
            )
            await db.commit()

    async def get_all_active_users(self) -> List[int]:
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT user_id FROM users WHERE is_active = 1;") as cursor:
                rows = await cursor.fetchall()
                return [row[0] for row in rows]

    async def get_global_stats(self) -> dict:
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT COUNT(*) FROM users;") as c:
                total_users = (await c.fetchone())[0]
            async with db.execute("SELECT COUNT(*) FROM users WHERE is_active = 1;") as c:
                active_users = (await c.fetchone())[0]
            async with db.execute("SELECT COUNT(*) FROM channels;") as c:
                total_channels = (await c.fetchone())[0]
            async with db.execute("SELECT COUNT(*) FROM pending_requests;") as c:
                pending_requests = (await c.fetchone())[0]

            return {
                "total_users": total_users,
                "active_users": active_users,
                "blocked_users": total_users - active_users,
                "total_channels": total_channels,
                "pending_requests": pending_requests
            }

    async def add_channel(self, channel_id: int, owner_id: int, title: str):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO channels (channel_id, owner_id, title)
                VALUES (?, ?, ?)
                ON CONFLICT(channel_id) DO UPDATE SET
                    title = excluded.title,
                    owner_id = excluded.owner_id;
            """, (channel_id, owner_id, title))
            await db.commit()

    async def get_channel(self, channel_id: int) -> Optional[Tuple]:
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT channel_id, owner_id, title, auto_approve, custom_dm_text, promo_btn_text, promo_btn_url FROM channels WHERE channel_id = ?;",
                (channel_id,)
            ) as cursor:
                return await cursor.fetchone()

    async def add_pending_request(self, channel_id: int, user_id: int):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT OR IGNORE INTO pending_requests (channel_id, user_id) VALUES (?, ?);",
                (channel_id, user_id)
            )
            await db.commit()

    async def get_pending_requests(self, channel_id: int, limit: int = 100) -> List[int]:
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT user_id FROM pending_requests WHERE channel_id = ? ORDER BY id ASC LIMIT ?;",
                (channel_id, limit)
            ) as cursor:
                rows = await cursor.fetchall()
                return [row[0] for row in rows]

    async def remove_pending_requests(self, channel_id: int, user_ids: List[int]):
        if not user_ids:
            return
        async with aiosqlite.connect(self.db_path) as db:
            placeholders = ",".join("?" for _ in user_ids)
            await db.execute(
                f"DELETE FROM pending_requests WHERE channel_id = ? AND user_id IN ({placeholders});",
                [channel_id, *user_ids]
            )
            await db.commit()

db = Database()
