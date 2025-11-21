import json
import time
from datetime import datetime
from uuid import uuid4

import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext

from api import vpn_api
from api.vpn_api import vless_key_generate
from config import VPN_API_URL
from database.database import get_all_user_subscriptions, add_client_to_db
from utils.logger import setup_logger
from utils.validators import is_subscription_active, generate_sub_id


logger = setup_logger(__name__)


# Тестовая подписка
def test_command(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()

    try:
        query.message.delete()
    except:
        pass

    user_id_str = str(update.effective_user.id)
    username = update.effective_user.username or "Без имени"

    # Получаем все подписки пользователя
    all_subs = get_all_user_subscriptions(user_id_str)

    has_active_subscription = False
    has_active_test = False
    has_pending_payment = False

    for sub in all_subs:
        _, _, _, sub_type, expiry_time_ms, payment_status, _, _, _, _, _ = sub

        if sub_type == "test" and is_subscription_active(expiry_time_ms):
            has_active_test = True

        if (
            sub_type != "test"
            and is_subscription_active(expiry_time_ms)
            and payment_status == "approved"
        ):
            has_active_subscription = True

        if payment_status in ["waiting_for_pay", "pending"]:
            has_pending_payment = True

    if has_active_subscription:

        keyboard = [
            [
            InlineKeyboardButton("🔙 Главное меню", callback_data="back_to_main")
            ]
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)

        query.message.reply_text(
            "🚫 У вас уже есть активная подписка.",
            reply_markup=reply_markup,
        )

        return

    if has_active_test:
        keyboard = [
            [
                InlineKeyboardButton("🔙 Главное меню", callback_data="back_to_main")
            ]
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)

        query.message.reply_text(
            "🚫 У вас уже активен пробный период.",
            reply_markup=reply_markup,
        )

        return

    if has_pending_payment:
        keyboard = [
            [
                InlineKeyboardButton("🔙 Главное меню", callback_data="back_to_main")
            ]
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)

        query.message.reply_text(
            "🚫 У вас уже есть подписка, ожидающая оплаты. Пожалуйста, подтвердите оплату или отмените её.",
            reply_markup=reply_markup,
        )

        return

    for sub in all_subs:
        if sub[3] == "test":
            keyboard = [
                [
                    InlineKeyboardButton("🔙 Главное меню", callback_data="back_to_main")
                ]
            ]

            reply_markup = InlineKeyboardMarkup(keyboard)

            query.message.reply_text(
                "Вы уже оформляли пробный период.",
                reply_markup=reply_markup,
            )

            return

    # Генерируем UUID и subId
    client_uuid = str(uuid4())
    sub_id = generate_sub_id()

    # Считаем окончание через 24 часа
    expiry_time_ms = int(time.time() * 1000) + 24 * 3600 * 1000

    # Формируем тело для запроса addClient
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
                        "tgId": user_id_str,
                        "subId": sub_id,
                        "comment": "Пробная подписка",
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

        add_client_to_db(
            telegram_id=user_id_str,
            client_uuid=client_uuid,
            sub_id=sub_id,
            subscription_type="test",
            duration=1,
            price=0,
            payment_status="approved",
            expiry_time=expiry_time_ms,
            bank_name=None,
            bank_card_number=None,
            username=username,
        )

        vless_key = vless_key_generate(client_uuid, username)

        dt_end = datetime.fromtimestamp(expiry_time_ms / 1000.0)
        dt_human = dt_end.strftime("%Y-%m-%d %H:%M")
        logger.info(
            f"🎁 Пользователь {user_id_str} активировал пробный период до {dt_human}"
        )

        keyboard = [
            [
                InlineKeyboardButton(
                    "📖 Инструкции для подключения", callback_data="instructions"
                )
            ],
            [InlineKeyboardButton("🔙 Главное меню", callback_data="back_to_main")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        query.message.reply_text(
            f"🎉 <b>Пробный период успешно активирован до {dt_human}</b>\n\n"
            f"🆔 <b>Ваш ID:</b> {user_id_str}\n\n"
            f"🔗 <b>Ключ для подключения:</b>\n"
            f"<pre>{vless_key}</pre>",
            parse_mode="HTML",
            reply_markup=reply_markup,
        )

    except Exception as e:
        logger.error(f"Ошибка при обработке пробного периода: {e}", exc_info=True)
        query.message.reply_text(f"Ошибка при обработке пробного периода: {e}")