import json
from datetime import datetime

import requests
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackContext

from api import vpn_api
from api.vpn_api import vless_key_generate
from config import VPN_API_URL
from utils.logger import setup_logger

logger = setup_logger(__name__)

# ================================
# ===  ВАЛИДАЦИЯ/ОТКАЗ ОПЛАТЫ  ===
# ================================
def approve_payment(telegram_id, context, query):
    from database.database import conn
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT id, client_uuid, sub_id, expiry_time, duration, price
        FROM clients
        WHERE telegram_id = ? AND payment_status = 'pending'
        ORDER BY id DESC
        LIMIT 1
    """,
        (telegram_id,),
    )
    payment_record = cursor.fetchone()

    if not payment_record:
        query.answer("⚠️ Платеж не найден или уже обработан.", show_alert=True)
        return

    record_id, client_uuid, sub_id, expiry_time_ms, duration, price = payment_record

    cursor.execute(
        "SELECT username FROM clients WHERE id = ?",
        (record_id,)
    )
    username_row = cursor.fetchone()
    username = username_row[0] if username_row and username_row[0] else f"ID: {telegram_id}"

    cursor.execute(
        """
    SELECT subscription_type
    FROM clients
    WHERE id = ?
    """,
        (record_id,),
    )
    row = cursor.fetchone()

    subscription_type = row[0]

    if subscription_type == "extend":
        payment_type = "Подписка продлена"
        api_endpoint = f"{VPN_API_URL}/panel/api/inbounds/updateClient/{client_uuid}"
    else:
        payment_type = "Новая подписка"
        api_endpoint = f"{VPN_API_URL}/panel/api/inbounds/addClient"

    body = {
        "id": 1,
        "settings": json.dumps(
            {
                "clients": [
                    {
                        "id": client_uuid,
                        "flow": "xtls-rprx-vision",
                        "email": username,
                        "limitIp": 0,
                        "totalGB": 0,
                        "expiryTime": expiry_time_ms,
                        "enable": True,
                        "tgId": telegram_id,
                        "subId": sub_id,
                        "comment": f"{payment_type} на {duration} дней",
                        "reset": 0,
                    }
                ]
            }
        ),
    }

    try:
        logger.info(f"POST URL: {api_endpoint}")
        logger.info(f"POST BODY: {json.dumps(body, indent=2)}")

        resp = requests.post(api_endpoint, cookies=vpn_api.SESSION_COOKIES, json=body)
        resp.raise_for_status()
    except Exception as e:
        logger.error(f"Ошибка при обновлении подписки пользователя {telegram_id}: {e}")
        query.answer("❌ Ошибка при подтверждении оплаты.", show_alert=True)
        return

    # Обновляем статус оплаты в БД на 'approved'
    from database.database import conn
    with conn:
        conn.execute(
            """
            UPDATE clients
            SET payment_status = 'approved'
            WHERE id = ?
        """,
            (payment_record[0],),
        )
        conn.commit()

    # Получаем информацию о подписке
    dt_end = datetime.fromtimestamp(expiry_time_ms / 1000.0)
    dt_human = dt_end.strftime("%Y-%m-%d %H:%M")

    vless_key = vless_key_generate(client_uuid, username)

    # Отправляем пользователю уведомление о подтверждении
    keyboard = [
        [
            InlineKeyboardButton(
                "📖 Инструкции для подключения", callback_data="instructions"
            )
        ],
        [InlineKeyboardButton("🔙 Главное меню", callback_data="back_to_main")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Получаем информацию о пользователе
    user = context.bot.get_chat(telegram_id)
    username = user.username if user.username else f"ID: {telegram_id}"

    logger.info(f"✅ Админ подтвердил оплату подписки пользователя {telegram_id}")
    context.bot.send_message(
        chat_id=telegram_id,
        text=(
            f"🎉 <b>Ваша оплата успешно подтверждена!</b>\n\n"
            f"🆔 <b>Ваш ID:</b> {telegram_id}\n\n"
            f"📅 <b>Подписка действует до:</b> {dt_human}\n\n"
            f"🔗 <b>Ключ для подключения:</b>\n<pre>{vless_key}</pre>"
        ),
        parse_mode="HTML",
        reply_markup=reply_markup,
    )

    # Информируем администратора об успешном подтверждении
    query.message.edit_reply_markup(reply_markup=None)
    query.message.reply_text(
        f"✅ Оплата от @{username} подтверждена и подписка активирована."
    )


def reject_payment(telegram_id, context, query):
    # Обновляем статус платежа в базе данных
    from database.database import conn
    with conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE clients
            SET payment_status = 'rejected'
            WHERE telegram_id = ? AND payment_status = 'pending'
        """,
            (telegram_id,),
        )
        conn.commit()

        if cursor.rowcount == 0:
            query.answer("⚠️ Не найдено ожидающих подтверждения платежей для данного пользователя.", show_alert=True)
            return

    # Получаем информацию о пользователе
    user = context.bot.get_chat(telegram_id)
    username = user.username if user.username else f"ID: {telegram_id}"

    # Отправляем пользователю уведомление об отклонении оплаты
    keyboard = [[InlineKeyboardButton("🔙 Главное меню", callback_data="back_to_main")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    logger.info(f"❌ Админ отклонил оплату пользователя {telegram_id}")
    context.bot.send_message(
        chat_id=telegram_id,
        text="❌ К сожалению, ваша оплата не была подтверждена. Пожалуйста, попробуйте снова или обратитесь в техподдержку.",
        reply_markup=reply_markup,
    )

    query.message.edit_reply_markup(reply_markup=None)
    query.message.reply_text(f"⛔ Платёж от @{username} отклонён.")


# === Маршрутизаторы для админских кнопок оплаты ===


def approve_payment_router(update: Update, context: CallbackContext):
    query = update.callback_query
    telegram_id = int(query.data.split("_")[1])
    approve_payment(telegram_id, context, query)


def reject_payment_router(update: Update, context: CallbackContext):
    query = update.callback_query
    telegram_id = int(query.data.split("_")[1])
    reject_payment(telegram_id, context, query)