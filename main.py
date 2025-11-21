from telegram.ext import Updater

from config import TELEGRAM_BOT_TOKEN
from database.database import init_db
from handlers.register_handlers import register_start, register_subscriptions, register_admin, register_helpers, \
    register_reviews, register_support, register_news, register_instructions
from utils.logger import setup_logger
from api.vpn_api import periodic_session_refresh


logger = setup_logger(__name__)


# ===========================
# ===  ЗАПУСК  ===
# ===========================
def main():
    logger.info("============ Запуск ============")
    # Сначала инициализируем БД
    init_db()

    # Обновление сессии
    periodic_session_refresh()

    # Запускаем бота
    updater = Updater(token=TELEGRAM_BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    register_start(dp)
    register_reviews(dp)
    register_support(dp)
    register_news(dp)
    register_instructions(dp)
    register_subscriptions(dp)
    register_admin(dp)
    register_helpers(dp)

    updater.start_polling()
    logger.info("✅ Бот запущен и слушает команды...")

    updater.idle()


if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Программа завершена.")
