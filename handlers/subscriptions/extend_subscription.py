import random
import time

from telegram import InlineKeyboardMarkup, InlineKeyboardButton, Update
from telegram.ext import CallbackContext

from config import SUBSCRIPTION_PRICES, BANK_DETAILS
from database.database import get_all_user_subscriptions, add_client_to_db
from utils.logger import setup_logger
from utils.validators import is_subscription_active


logger = setup_logger(__name__)


# Продление подписки
def extend_command(update: Update, context: CallbackContext):
    """
    Продление существующей подписки:
    - Если это "test" — запрещаем продление.
    - Если это "monthly" — продлеваем на +31 день.
    - Логику расчёта: если старая подписка ещё не истекла, продлеваем от старого срока,
      иначе — от текущего времени.
    """
    query = update.callback_query
    query.answer()

    user_id_str = str(update.effective_user.id)

    all_subs = get_all_user_subscriptions(user_id_str)

    allow_extend = False
    has_pending = False
    pending_bank_name = None
    pending_bank_card = None

    now_ms = int(time.time() * 1000)

    for sub in all_subs:
        (
            _,
            _,
            _,
            sub_type,
            expiry_time_ms,
            payment_status,
            _,
            _,
            price,
            bank_name,
            bank_card_number,
        ) = sub

        if sub_type == "sub" and is_subscription_active(expiry_time_ms) and payment_status == "approved":
            allow_extend = True
            break

        if sub_type == "test" and expiry_time_ms < now_ms and payment_status == "approved":
            allow_extend = True
            break

        if payment_status == "waiting_for_pay":
            has_pending = True
            pending_bank_name = bank_name
            pending_bank_card = bank_card_number
            pending_price = price
            break

        if payment_status == "pending":
            keyboard = [
                [
                    InlineKeyboardButton("🔙 Главное меню", callback_data="back_to_main")
                ]
            ]

            reply_markup = InlineKeyboardMarkup(keyboard)

            query.message.edit_text(
                "🚫 У вас уже есть оплаченная подписка, которая ожидает подтверждения администратором.",
                reply_markup=reply_markup
            )

            return

    if not allow_extend:
        keyboard = [
            [
                InlineKeyboardButton("🔙 Главное меню", callback_data="back_to_main")
            ]
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)

        query.message.edit_text(
            "🚫 У вас нет подписки, доступной для продления.", reply_markup=reply_markup
        )

        return

    # Проверяем наличие ожидающей оплаты на продление
    if has_pending:
        # Если уже есть ожидающая оплата на продление
        payment_details = (
            "⏳ <b>Ваша подписка ожидает оплаты</b>\n\n"
            f"<b>Сумма:</b> {pending_price} руб.\n\n"
            "<b>Способы оплаты:</b>\n\n"
            "⚠️ Внимательно ознакомьтесь с информацией ниже ⚠️\n"
            f"1. (Перевод на карту) {pending_bank_name} {pending_bank_card}\n"
            "В КОММЕНТАРИИ К ОПЛАТЕ НИЧЕГО НЕ ПИСАТЬ!\n"
            f"2. ПО СБП({pending_bank_name}) +79126469603 (Татьяна Л)\n"
            "В КОММЕНТАРИИ К ОПЛАТЕ НИЧЕГО НЕ ПИСАТЬ!\n"
            "⚠️ После оплаты отправьте чек платежа, содержащий в себе дату оплаты ⚠️"
        )

        keyboard = [
            [InlineKeyboardButton("🚫 Отменить", callback_data="cancel_payment")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        query.message.edit_text(
            payment_details, reply_markup=reply_markup
        )

        return

    # Если нет ожидающей оплаты, предлагаем выбрать срок продления
    extend_keyboard = [
        [
            InlineKeyboardButton(
                f"30 дней - {SUBSCRIPTION_PRICES[30]} ₽",
                callback_data="extend_30"
            ),
            InlineKeyboardButton(
                f"60 дней - {SUBSCRIPTION_PRICES[60]} ₽",
                callback_data="extend_60",
            ),
        ],
        [
            InlineKeyboardButton(
                f"90 дней - {SUBSCRIPTION_PRICES[90]} ₽",
                callback_data="extend_90",
            ),
            InlineKeyboardButton(
                f"120 дней - {SUBSCRIPTION_PRICES[120]} ₽",
                callback_data="extend_120",
            ),
        ],
        [InlineKeyboardButton("🔙 Главное меню", callback_data="back_to_main")],
    ]

    reply_markup = InlineKeyboardMarkup(extend_keyboard)

    query.message.edit_text(
        "🔄 Выберите срок для продления подписки:",
        reply_markup=reply_markup
    )


def extend_with_duration(
        update: Update, context: CallbackContext, duration_days: int
):
    query = update.callback_query
    query.answer()
    user_id_str = str(update.effective_user.id)
    price = SUBSCRIPTION_PRICES.get(duration_days)
    if not price:
        query.message.reply_text("Неверный срок подписки.")
        return

    all_subs = get_all_user_subscriptions(user_id_str)
    # Находим последнюю оплаченною подписку
    active_sub = None

    for sub in reversed(all_subs):
        (
            _,
            client_uuid,
            sub_id,
            sub_type,
            expiry_time_ms,
            payment_status,
            _,
            _,
            _,
            _,
            _,
        ) = sub

        if payment_status == "approved":
            active_sub = sub
            break

    if not active_sub:
        query.message.reply_text("❌ Нет подписки для продления.")
        return

    (
        _,
        client_uuid,
        existing_sub_id,
        sub_type,
        current_expiry_time_ms,
        _,
        _,
        _,
        _,
        _,
        _,
    ) = active_sub

    # Продляем от текущего времени или от даты окончания подписки (если ещё не истекла)
    sub_type = active_sub[3]
    current_expiry_time_ms = active_sub[4]

    if sub_type == "test" or not is_subscription_active(current_expiry_time_ms):
        base_time = int(time.time() * 1000)
    else:
        base_time = current_expiry_time_ms

    new_expiry_time_ms = base_time + duration_days * 24 * 3600 * 1000

    selected_bank = random.choice(BANK_DETAILS)
    bank_name = selected_bank["bank"]
    bank_card_number = selected_bank["card"]
    user_username = update.effective_user.username or "Без имени"

    add_client_to_db(
        telegram_id=user_id_str,
        client_uuid=client_uuid,
        sub_id=existing_sub_id,
        subscription_type="extend",
        expiry_time=new_expiry_time_ms,
        duration=duration_days,
        price=price,
        bank_name=bank_name,
        bank_card_number=bank_card_number,
        payment_status="waiting_for_pay",
        username=user_username,
    )
    payment_details = (
        f"💳 <b>Стоимость продления подписки на {duration_days} дней составит {price} руб.</b>\n\n"
        "<b>Способы оплаты:</b>\n\n"
        "⚠️ Внимательно ознакомьтесь с информацией ниже ⚠️\n"
        f"1. (Перевод на карту) {bank_name} {bank_card_number}\n"
        "В КОММЕНТАРИИ К ОПЛАТЕ НИЧЕГО НЕ ПИСАТЬ!\n"
        f"2. ПО СБП({bank_name}) +79126469603 (Татьяна Л)\n"
        "В КОММЕНТАРИИ К ОПЛАТЕ НИЧЕГО НЕ ПИСАТЬ!\n"
        "⚠️ После оплаты отправьте чек платежа, содержащий в себе дату оплаты ⚠️"
    )
    keyboard = [
        [
            InlineKeyboardButton("🚫 Отменить", callback_data="cancel_payment"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    query.message.edit_text(
        payment_details, reply_markup=reply_markup, parse_mode="HTML"
    )


# === Маршрутизаторы для продления по сроку ===test
def extend_with_duration_router(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    try:
        duration_days = int(query.data.split("_")[1])
        extend_with_duration(update, context, duration_days)
    except Exception as e:
        logger.error(f"Ошибка при продлении подписки: {e}", exc_info=True)
        query.message.reply_text(f"❌ Ошибка при продлении подписки: {e}")