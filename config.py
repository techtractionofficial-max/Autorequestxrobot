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

config = Config()

    # Add these below your existing variables in config.py
    START_PHOTO_URL: str = "https://images.unsplash.com/photo-1618401471353-b98afee0b2eb?q=80&w=800&auto=format&fit=crop"
    WELCOME_PHOTO_URL: str = "https://images.unsplash.com/photo-1556155092-490a1ba16284?q=80&w=800&auto=format&fit=crop"

