import os
from typing import List

class Config:
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
    ADMIN_IDS: List[int] = [
        int(x.strip()) 
        for x in os.getenv("ADMIN_IDS", "").split(",") 
        if x.strip() and x.strip().isdigit()
    ]
    DATABASE_PATH: str = os.getenv("DATABASE_PATH", "bot_database.db")
    
    # Broadcast rate-limit settings
    BROADCAST_BATCH_SIZE: int = 25
    BROADCAST_DELAY_SECONDS: float = 0.04  # ~25 messages/second

    # Images
    START_PHOTO_URL: str = "https://t.me/photouploadhere/21"
    WELCOME_PHOTO_URL: str = "https://t.me/photouploadhere/22"

config = Config()
