import os
from typing import List

# Auto-detects the permanent Railway Volume so data is never lost
DB_FILE = "/data/bot_database.db" if os.path.exists("/data") else "bot_database.db"

class Config:
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
    ADMIN_IDS: List[int] = [
        int(x.strip()) 
        for x in os.getenv("ADMIN_IDS", "").split(",") 
        if x.strip() and x.strip().isdigit()
    ]
    # Forces the bot to use the permanent storage
    DATABASE_PATH: str = os.getenv("DATABASE_PATH", DB_FILE)
    
    BROADCAST_BATCH_SIZE: int = 25
    BROADCAST_DELAY_SECONDS: float = 0.04  

    START_PHOTO_URL: str = "https://t.me/photouploadhere/21"
    WELCOME_PHOTO_URL: str = "https://t.me/photouploadhere/23"

config = Config()
