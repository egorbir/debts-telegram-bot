from src.credentials import DB_USER, DB_PASSWORD, DB_NAME, DB_HOST, DB_PORT, REDIS_HOST, REDIS_PORT, REDIS_PASS
from src.interfaces.db_interface import DBInterface
from src.interfaces.redis_interface import RedisInterface

# Map of emojis used in buttons
EMOJIS = {
    "back": "\u21A9",
    "all": "\u2714",
    "cancel": "\u274C",
    "done": "\u2705",
    "checkbox": "\u2611",
    "forward": "\u25B6",
    "backward": "\u25C0"
}

# Database interface instance
DB = DBInterface(
    user=DB_USER,
    password=DB_PASSWORD,
    database_name=DB_NAME,
    host=DB_HOST,
    port=DB_PORT
)

# Redis interface instance
RDS = RedisInterface(host=REDIS_HOST, port=REDIS_PORT, password=REDIS_PASS)
