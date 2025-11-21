import os

from dotenv import load_dotenv
from utils.logger import setup_logger

logger = setup_logger(__name__)
load_dotenv()

# === Настройки бота ==
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ADMIN_IDS = list(map(int, os.getenv("ADMIN_IDS").split(",")))
ADMIN_CHAT_ID = int(os.getenv("ADMIN_CHAT_ID"))

# === Настройки API ===
VPN_API_URL = os.getenv("VPN_API_URL")
VPN_USERNAME = os.getenv("VPN_USERNAME")
VPN_PASSWORD = os.getenv("VPN_PASSWORD")
SERVER_DOMAIN = os.getenv("SERVER_DOMAIN")

logger.info("============ Конфигурация ============")

if VPN_API_URL:
    logger.info(f"VPN API URL: {VPN_API_URL}")
else:
    logger.error("❌ VPN API URL не задан!")
if VPN_USERNAME:
    logger.info(f"VPN Username: {VPN_USERNAME}")
else:
    logger.error("❌ VPN Username не задан!")
if VPN_PASSWORD:
    logger.info("VPN Password: ********")
else:
    logger.error("❌ VPN Password не задан!")
if SERVER_DOMAIN:
    logger.info(f"Server domain: {SERVER_DOMAIN}")
else:
    logger.error("❌ Server domain не задан!")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Список банковских карт
def load_bank_details():
    """Загружает банковские карты из переменных окружения и возвращает список словарей."""
    bank_details = []
    index = 1

    while True:
        bank_entry = os.getenv(f"BANK_{index}")
        if not bank_entry:
            break  # Выходим из цикла, если переменной больше нет

        try:
            bank_name, bank_card = bank_entry.split(",", 1)
            bank_details.append({"bank": bank_name.strip(), "card": bank_card.strip()})
        except ValueError:
            logger.error(f"❌ Ошибка в формате BANK_{index}: {bank_entry}")

        index += 1

    return bank_details


try:
    BANK_DETAILS = load_bank_details()
    logger.info("Загружены банковские карты для оплаты:")
    for bank in BANK_DETAILS:
        logger.info(f"{bank['bank']}: {bank['card']}")
except Exception as e:
    logger.error(f"Ошибка при загрузке банковских карт: {e}")

SUBSCRIPTION_PRICES = {
    30: int(os.getenv("SUBSCRIPTION_PRICE_30", 50)),
    60: int(os.getenv("SUBSCRIPTION_PRICE_60", 95)),
    90: int(os.getenv("SUBSCRIPTION_PRICE_90", 140)),
    120: int(os.getenv("SUBSCRIPTION_PRICE_120", 185)),
}

if SUBSCRIPTION_PRICES:
    logger.info("Загружены цены на подписки:")
    for months, price in SUBSCRIPTION_PRICES.items():
        logger.info(f"Цена подписки на {months} месяц(ев): {price} руб.")
else:
    logger.error("❌ Цены на подписки не заданы!")

# Словарь для отображаемых названий подписок
SUBSCRIPTION_DISPLAY = {
    "test": "Пробный период",
    "sub": "Подписка",
    "extend": "Подписка",
}

