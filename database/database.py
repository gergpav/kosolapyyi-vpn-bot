import os

from utils.logger import setup_logger

logger = setup_logger(__name__)

import sqlite3

# === Подключаемся к базе данных SQLite ===
# При первом подключении, если файл не существует, он создастся автоматически.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "..", "database.db")
conn = sqlite3.connect(DB_PATH, check_same_thread=False)


# Создание таблиц
def init_db():
    with conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS clients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id TEXT,
                client_uuid TEXT,
                sub_id TEXT,
                subscription_type TEXT,
                expiry_time INTEGER,
                payment_status TEXT DEFAULT 'waiting_for_pay',
                confirmation_requested INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                duration INTEGER,
                price INTEGER,
                bank_name TEXT,
                bank_card_number TEXT,
                username TEXT
            )
        """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                username TEXT,
                review TEXT,
                rating INTEGER,
                status TEXT DEFAULT 'pending'
            )
        """
        )
        logger.info(
            "✅ Таблицы инициализированы (clients, reviews)."
        )


# Функция для добавления клиента в БД
def add_client_to_db(
    telegram_id,
    client_uuid,
    sub_id,
    subscription_type,
    expiry_time,
    duration,
    price,
    bank_name,
    bank_card_number,
    username=None,
    payment_status="waiting_for_pay",
    confirmation_requested=0,
):
    """
    Сохраняем запись. created_at по умолчанию = NOW.
    """
    with conn:
        conn.execute(
            """
            INSERT INTO clients (telegram_id, client_uuid, sub_id, subscription_type, expiry_time, duration, price, payment_status, confirmation_requested, 
                bank_name, bank_card_number, username)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                telegram_id,
                client_uuid,
                sub_id,
                subscription_type,
                expiry_time,
                duration,
                price,
                payment_status,
                confirmation_requested,
                bank_name,
                bank_card_number,
                username,
            ),
        )
        logger.info(
            f"🆕 Добавлен клиент {telegram_id} с UUID {client_uuid} и типом {subscription_type}"
        )


def update_client_expiry(telegram_id, new_expiry_time):
    """
    Апдейтим expiry_time (продлеваем подписку).
    """
    with conn:
        conn.execute(
            """
            UPDATE clients
            SET expiry_time = ?
            WHERE telegram_id = ?
        """,
            (new_expiry_time, telegram_id),
        )
        logger.info(
            f"🔄 Продлена подписка для пользователя {telegram_id} до {new_expiry_time}"
        )


# Получение данных о клиенте из БД (по telegram_id)
def get_client_by_tg_id(telegram_id):
    """
    Возвращает последнюю (ORDER BY id DESC) запись о подписке данного телеграм-пользователя.
    """
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT telegram_id, client_uuid, sub_id, subscription_type, expiry_time, payment_status, created_at, duration, price
        FROM clients
        WHERE telegram_id = ?
        ORDER BY id DESC
        LIMIT 1
    """,
        (telegram_id,),
    )
    return cursor.fetchone()


# Получить все подписки данного пользователя (вдруг нужно более гибко)
def get_all_user_subscriptions(telegram_id):
    """
    Получить все подписки пользователя.
    """
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT telegram_id, client_uuid, sub_id, subscription_type, expiry_time, payment_status, created_at, duration, price, bank_name, bank_card_number
        FROM clients
        WHERE telegram_id = ?
        ORDER BY id ASC
    """,
        (telegram_id,),
    )
    return cursor.fetchall()
