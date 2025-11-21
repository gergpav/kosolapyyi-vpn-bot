import random
import string
import time

from config import SUBSCRIPTION_DISPLAY
from database.database import get_client_by_tg_id
from utils.logger import setup_logger

logger = setup_logger(__name__)


def is_subscription_active(expiry_time_ms: int) -> bool:
    now_ms = int(time.time() * 1000)
    return now_ms < expiry_time_ms


# Генерация случайной строки (для subId) в формате: "jajmd2sepcdylq1l"
def generate_sub_id(length=18):
    # Возьмём только строчные буквы и цифры
    chars = string.ascii_lowercase + string.digits
    result = "".join(random.choice(chars) for _ in range(length))
    logger.info(f"🆔 Сгенерирован sub_id: {result}")
    return result


def get_subscription_display(subscription_type):
    """
    Возвращает отображаемое название подписки на основе её типа.
    Если тип неизвестен, возвращает исходный тип.
    """
    return SUBSCRIPTION_DISPLAY.get(subscription_type, subscription_type)


def user_has_active_subscription(user_id_str: str) -> bool:
    """Универсальная проверка: есть ли у пользователя активная подписка."""
    # Достанем последнюю запись
    client_data = get_client_by_tg_id(user_id_str)

    if not client_data:
        logger.info(f"👤 Пользователь {user_id_str} не найден в базе (нет подписки).")
        return False

    expiry_time_ms = client_data[4]
    payment_status = client_data[5]

    active = is_subscription_active(expiry_time_ms) and payment_status == "approved"
    logger.info(
        f"👤 Подписка пользователя {user_id_str}: active={active}, status={payment_status}"
    )
    return active
