import os

# Telegram
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

# Binance
API_URL = (
    "https://p2p.binance.com/"
    "bapi/c2c/v2/friendly/c2c/adv/search"
)

# Database
DB_PATH = "p2p_tracker.db"


# Проверка конфигурации
if not BOT_TOKEN:
    raise ValueError("Не задан BOT_TOKEN")

if ADMIN_ID == 0:
    raise ValueError("Не задан ADMIN_ID")