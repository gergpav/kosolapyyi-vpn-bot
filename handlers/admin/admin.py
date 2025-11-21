from telegram import Update
from telegram.ext import CallbackContext
from config import ADMIN_IDS
from utils.logger import setup_logger
from datetime import datetime

logger = setup_logger(__name__)


def format_timestamp(ms):
    if not ms:
        return "-"
    try:
        return datetime.fromtimestamp(ms / 1000).strftime("%Y-%m-%d")
    except:
        return str(ms)


def clients_command(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        update.message.reply_text("❌ У вас нет прав для этой команды.")
        logger.warning(f"⚠️ Пользователь {user_id} попытался вызвать /clients без прав")
        return

    from database.database import conn
    with conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT telegram_id, username, subscription_type, expiry_time, payment_status,
                   duration, price, bank_name, bank_card_number
            FROM clients
            ORDER BY id DESC
        """
        )
        rows = cursor.fetchall()

    seen = set()
    summary = []
    for row in rows:
        telegram_id = row[0]
        if telegram_id in seen:
            continue
        seen.add(telegram_id)

        username = row[1] or "—"
        subscription_type = row[2]
        expiry = format_timestamp(row[3])
        payment_status = row[4]
        duration = row[5]
        price = row[6]
        bank = row[7] or "-"
        card = row[8] or "-"

        line = (
            f"👤 <b>{username}</b> (ID: <code>{telegram_id}</code>)\n"
            f"📜 Тип: <b>{subscription_type}</b>\n"
            f"💳 Статус: <b>{payment_status}</b>, до: <b>{expiry}</b>\n"
            f"💰 {price}₽ за {duration} мес | {bank}: {card}\n"
            f"─────────────"
        )
        summary.append(line)

    result = "\n".join(summary) or "Нет клиентов."

    update.message.reply_text(result, parse_mode="HTML")
    logger.info(f"📋 Админ {user_id} запросил список клиентов)")

