import time

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackContext

from config import ADMIN_CHAT_ID
from utils.logger import setup_logger


logger = setup_logger(__name__)


def confirm_payment_command(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()

    user_id_str = str(query.from_user.id)

    # Получаем последнюю запись о подписке 'pending'
    from database.database import conn
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT telegram_id, client_uuid, sub_id, subscription_type, expiry_time, duration, price, payment_status, confirmation_requested, created_at, bank_name, bank_card_number
        FROM clients
        WHERE telegram_id = ? AND payment_status = 'waiting_for_pay'
        ORDER BY id DESC
        LIMIT 1
    """,
        (user_id_str,),
    )
    payment_record = cursor.fetchone()

    (
        telegram_id,
        client_uuid,
        sub_id,
        subscription_type,
        expiry_time_ms,
        duration,
        price,
        payment_status,
        confirmation_requested,
        created_at,
        bank_name,
        bank_card_number,
    ) = payment_record

    if confirmation_requested:
        # Если запрос уже отправлен
        query.message.reply_text(
            "Вы уже отправили запрос на подтверждение оплаты. Пожалуйста, дождитесь одобрения администратором."
        )
        return

    # Проверяем наличие активной подписки до текущей записи
    cursor.execute(
        """
        SELECT COUNT(*)
        FROM clients
        WHERE telegram_id = ? 
          AND subscription_type = 'sub' 
          AND payment_status = 'approved'
          AND expiry_time > ?
    """,
        (telegram_id, time.time() * 1000),
    )
    active_count = cursor.fetchone()[0]

    if active_count > 0:
        payment_type = "Продление подписки"
    else:
        payment_type = "Новая подписка"

    with conn:
        conn.execute(
            """
            UPDATE clients
            SET payment_status = 'pending'
            WHERE id = ?
              AND payment_status = 'waiting_for_pay'
        """,
            (payment_record[0],),
        )
        conn.commit()

    # Отправка чека админу
    last_msg_id = context.user_data.get("last_receipt_message_id")
    last_chat_id = context.user_data.get("last_receipt_chat_id")

    if last_msg_id:
        context.bot.copy_message(
            chat_id=ADMIN_CHAT_ID,
            from_chat_id=last_chat_id,
            message_id=last_msg_id
        )
    else:
        context.bot.send_message(
            chat_id=ADMIN_CHAT_ID,
            text="⚠️ Пользователь отправил запрос на подтверждение, но чек НЕ найден.",
        )

    # Отправляем уведомление администратору
    user_username = update.effective_user.username or "Без имени"
    user_display = f"@{user_username}" if user_username else f"ID: {user_id_str}"

    keyboard = [
        [
            InlineKeyboardButton("✅ Подтвердить", callback_data=f"approve_{telegram_id}"),
        ],
        [
            InlineKeyboardButton("❌ Отклонить", callback_data=f"reject_{telegram_id}"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    logger.info(
        f"✅ Пользователь {user_id_str} отправил запрос на подтверждение оплаты ({price}₽, {bank_name})"
    )

    notification_text = (
        f"📥 <b>Новая оплата подписки от пользователя:</b> {user_display}\n\n"
        f"<b>Тип оплаты:</b> {payment_type}\n"
        f"<b>Telegram ID:</b> {telegram_id}\n"
        f"<b>UUID:</b> {client_uuid}\n"
        f"<b>Срок подписки:</b> {duration} дней\n"
        f"<b>Дата оформления:</b> {created_at}\n"
        f"<b>Сумма:</b> {price} руб.\n"
        f"<b>Банк:</b> {bank_name}\n"
        f"<b>Номер карты:</b> {bank_card_number}\n\n"
    )

    context.bot.send_message(
        chat_id=ADMIN_CHAT_ID,
        text=notification_text,
        parse_mode="HTML",
        reply_markup=reply_markup,
    )

    # Обновляем поле confirmation_requested на 1 (True)
    from database.database import conn
    with conn:
        conn.execute(
            """
            UPDATE clients
            SET confirmation_requested = 1,
                payment_status = 'pending'
            WHERE telegram_id = ? AND payment_status = 'waiting_for_pay'
        """,
            (telegram_id,),
        )
        conn.commit()

    keyboard = [[InlineKeyboardButton("🔙 Главное меню", callback_data="back_to_main")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    query.message.edit_text(
        "✅ Ваш чек отправлен администратору.\nОжидайте подтверждения.",
        reply_markup=reply_markup,
    )


def cancel_payment_command(update: Update, context: CallbackContext):
    """
    Отменяет ожидающую оплату подписки пользователя.
    Удаляет запись из базы данных с payment_status = 'waiting_for_pay'.
    """
    query = update.callback_query
    query.answer()
    user_id_str = str(query.from_user.id)

    from database.database import conn
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT id, bank_name, bank_card_number, price
        FROM clients
        WHERE telegram_id = ? AND payment_status = 'waiting_for_pay'
        ORDER BY id DESC
        LIMIT 1
    """,
        (user_id_str,),
    )
    payment_record = cursor.fetchone()

    if not payment_record:
        query.message.reply_text("⚠️ Нет активных подписок, ожидающих оплаты.")
        return

    record_id, bank_name, bank_card_number, price = payment_record

    # Удаляем запись о платеже из базы данных
    from database.database import conn
    with conn:
        conn.execute(
            """
            DELETE FROM clients
            WHERE id = ?
        """,
            (record_id,),
        )
        conn.commit()

    # Информируем пользователя об успешной отмене оплаты
    keyboard = [[InlineKeyboardButton("🔙 Главное меню", callback_data="back_to_main")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    query.message.edit_text(
        "✅ Ваша оплата была успешно отменена. Вы можете оформить подписку снова, если захотите.",
        reply_markup=reply_markup,
    )

    logger.info(f"🚫 Пользователь {user_id_str} отменил оплату ({price}₽, {bank_name})")