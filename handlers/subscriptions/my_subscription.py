from datetime import datetime

from telegram import InlineKeyboardMarkup, InlineKeyboardButton, Update
from telegram.ext import CallbackContext

from api.vpn_api import vless_key_generate
from database.database import get_client_by_tg_id
from utils.validators import is_subscription_active, get_subscription_display


# Текущая подписка
def subscription_command(update: Update, context: CallbackContext):
    """
    Показывает информацию о текущей (или последней) подписке пользователя:
    - Тип (test / monthly)
    - UUID
    - Дата окончания
    - Ссылка для подключения
    Если подписка истекла, укажем, что она просрочена.
    """
    query = update.callback_query
    query.answer()
    user_id_str = str(update.effective_user.id)
    client_data = get_client_by_tg_id(user_id_str)

    if not client_data:
        keyboard = [
            [
                InlineKeyboardButton("🔙 Главное меню", callback_data="back_to_main")
            ]
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)
        query.message.edit_text("🚫 У вас пока нет оформленных подписок.", reply_markup=reply_markup)
        return

    (
        _,
        client_uuid,
        sub_id,
        subscription_type,
        expiry_time_ms,
        payment_status,
        _,
        _,
        _,
    ) = client_data

    dt_end = datetime.fromtimestamp(expiry_time_ms / 1000.0)
    dt_human = dt_end.strftime("%Y-%m-%d %H:%M")

    username = update.effective_user.username or "Без имени"

    vless_key = vless_key_generate(client_uuid, username)

    subscription_type = get_subscription_display(subscription_type)

    if is_subscription_active(expiry_time_ms) and payment_status == "approved":
        # Действующая подписка
        keyboard = [
            [
                InlineKeyboardButton(
                    "📖 Инструкции для подключения", callback_data="instructions"
                )
            ],
            [InlineKeyboardButton("🔙 Главное меню", callback_data="back_to_main")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        query.message.edit_text(
            f"🆔 <b>Ваш ID:</b> {user_id_str}\n\n"
            f"📜 <b>Тип доступа:</b> {subscription_type}\n\n"
            f"📅 <b>Действует до:</b> {dt_human}\n\n"
            f"🔗 <b>Ключ для подключения:</b>\n<pre>{vless_key}</pre>",
            parse_mode="HTML",
            reply_markup=reply_markup,
        )

    elif subscription_type == "extend":
        keyboard = [[InlineKeyboardButton("🔄 Продление", callback_data="extend")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        query.message.edit_text(
            "⏳ Ожидается оплата для продления подписки.\n\n"
            "Нажмите кнопку ниже для получения дополнительной информации.",
            reply_markup=reply_markup,
        )
    elif subscription_type == "sub":
        keyboard = [[InlineKeyboardButton("💳 Подписка", callback_data="subscribe")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        query.message.edit_text(
            "⏳ Ожидается оплата подписки.\n\n"
            "Нажмите кнопку ниже для получения дополнительной информации.",
            reply_markup=reply_markup,
        )

    elif payment_status == "pending":
        keyboard = [
            [
                InlineKeyboardButton("🔙 Главное меню", callback_data="back_to_main")
            ]
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)
        query.message.edit_text(
            "⏳ Ваша оплата ожидает подтверждения администратором.\n\n"
            "Пожалуйста, дождитесь уведомления о подтверждении.",
            reply_markup=reply_markup,
        )
    else:
        # Подписка есть, но уже истекла
        keyboard = [
            [
                InlineKeyboardButton("🔙 Главное меню", callback_data="back_to_main")
            ]
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)
        query.message.reply_text(
            f"⚠️ <b>Ваш доступ закончился.</b>\n\n"
            f"📜 <b>Тип доступа:</b> {subscription_type}\n"
            f"📅 <b>Срок действия до:</b> {dt_human}\n\n",
            parse_mode="HTML",
            reply_markup=reply_markup,
        )