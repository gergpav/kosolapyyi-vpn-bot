import random
import time
from uuid import uuid4

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackContext

from config import SUBSCRIPTION_PRICES, BANK_DETAILS
from database.database import get_all_user_subscriptions, add_client_to_db
from utils.logger import setup_logger
from utils.validators import is_subscription_active, generate_sub_id


logger = setup_logger(__name__)


# Оформление подписки
def subscribe_command(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()

    user_id_str = str(update.effective_user.id)

    # Проверяем, нет ли уже активной подписки
    all_subs = get_all_user_subscriptions(user_id_str)

    has_active_subscription = False
    has_active_test = False
    has_pending_payment = False
    pending_bank_name = None
    pending_bank_card = None

    had_trial = False
    trial_expired = False

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

        now_ms = int(time.time() * 1000)

        if sub_type == "test":
            had_trial = True
            if expiry_time_ms < now_ms and payment_status == "approved":
                trial_expired = True
            if expiry_time_ms > now_ms and payment_status == "approved":
                has_active_test = True

        if sub_type in ("sub", "extend") and is_subscription_active(expiry_time_ms) and payment_status == "approved":
            has_active_subscription = True


        if payment_status == "waiting_for_pay":
            has_pending_payment = True
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

    # --- Логика запретов ---
    if has_active_subscription:
        keyboard = [
            [
                InlineKeyboardButton("🔙 Главное меню", callback_data="back_to_main")
            ]
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)

        query.message.edit_text(
            "🚫 У вас уже есть активная подписка.\n\nДля продления подписки воспользуйтесь кнопкой для продления в главном меню.",
            reply_markup=reply_markup
        )

        return

    if has_active_test:
        keyboard = [
            [
                InlineKeyboardButton("🔙 Главное меню", callback_data="back_to_main")
            ]
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)

        query.message.edit_text(
            "🚫 У вас уже есть активный пробный период.",
            reply_markup=reply_markup
        )

        return

    # Проверяем, была ли пробная, но продление уже оформлено
    if had_trial and trial_expired and not has_active_subscription:
        keyboard = [
            [
                InlineKeyboardButton("🔙 Главное меню", callback_data="back_to_main")
            ]
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)

        query.message.edit_text(
            "⚠️ Ваш пробный период завершился.\n\n🔄Для продления подписки воспользуйтесь кнопкой для продления в главном меню.",
            reply_markup=reply_markup
        )

        return

    if has_pending_payment:
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
            payment_details,
            reply_markup=reply_markup
        )

        return

    keyboard = [
        [
            InlineKeyboardButton(
                f"30 дней - {SUBSCRIPTION_PRICES[30]} ₽", callback_data="subscribe_30"
            ),
            InlineKeyboardButton(
                f"60 дней - {SUBSCRIPTION_PRICES[60]} ₽",
                callback_data="subscribe_60",
            ),
        ],
        [
            InlineKeyboardButton(
                f"90 дней - {SUBSCRIPTION_PRICES[90]} ₽",
                callback_data="subscribe_90",
            ),
            InlineKeyboardButton(
                f"120 дней - {SUBSCRIPTION_PRICES[120]} ₽",
                callback_data="subscribe_120",
            ),
        ],
        [InlineKeyboardButton("🔙 Главное меню", callback_data="back_to_main")],
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    query.message.edit_text(
        "Выберите срок подписки:",
        reply_markup=reply_markup
    )


def subscribe_with_duration(
    update: Update, context: CallbackContext, duration_days: int
):
    """
    Создаёт подписку с выбранным сроком
    """
    query = update.callback_query
    query.answer()
    user_id_str = str(update.effective_user.id)
    price = SUBSCRIPTION_PRICES.get(duration_days)
    if not price:
        query.message.reply_text("Неверный срок подписки.")
        return
    # Формируем срок действия
    expiry_time_ms = int(time.time() * 1000) + duration_days * 24 * 3600 * 1000
    # Генерируем UUID и subId
    client_uuid = str(uuid4())
    sub_id = generate_sub_id()
    # Выбор случайной банковской карты
    selected_bank = random.choice(BANK_DETAILS)
    bank_name = selected_bank["bank"]
    bank_card_number = selected_bank["card"]
    user_username = update.effective_user.username or "Без имени"

    # Сохраняем в БД
    add_client_to_db(
        telegram_id=user_id_str,
        client_uuid=client_uuid,
        sub_id=sub_id,
        subscription_type="sub",
        expiry_time=expiry_time_ms,
        duration=duration_days,
        price=price,
        bank_name=bank_name,
        bank_card_number=bank_card_number,
        payment_status="waiting_for_pay",
        username=user_username,
    )
    # Формируем реквизиты для оплаты
    payment_details = (
        f"💳 <b>Стоимость подписки на {duration_days} дней составит {price} руб.</b>\n\n"
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


# === Маршрутизатор для подписки по сроку ===test
def subscribe_with_duration_router(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    try:
        duration_days = int(query.data.split("_")[1])
        subscribe_with_duration(update, context, duration_days)
    except Exception as e:
        logger.error(f"Ошибка при оформлении подписки: {e}", exc_info=True)
        query.message.reply_text(f"❌ Ошибка при оформлении подписки: {e}")