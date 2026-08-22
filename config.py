import os
from dataclasses import dataclass
from typing import List

@dataclass
class Config:
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
    ADMIN_IDS: List[int] = (
        [int(x.strip()) for x in os.getenv("ADMIN_IDS", "123456789").split(",") if x.strip()]
    )
    DATABASE_PATH: str = os.getenv("DATABASE_PATH", "bot_database.db")
    
    # Broadcast safety limits
    BROADCAST_BATCH_SIZE: int = 25
    BROADCAST_DELAY_SECONDS: float = 0.04  # ~25 messages/second

config = Config()
