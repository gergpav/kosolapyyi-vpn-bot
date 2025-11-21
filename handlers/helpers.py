import os

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext

from config import BASE_DIR
from handlers.others.reviews import handle_text_review
from utils.logger import setup_logger


logger = setup_logger(__name__)


MAIN_MENU_KEYBOARD = InlineKeyboardMarkup(
    [
        [
            InlineKeyboardButton("🎁 Пробный период 24ч", callback_data="test"),
            InlineKeyboardButton("💳 Подписка", callback_data="subscription_menu"),
        ],
        [
            InlineKeyboardButton("🆘 Поддержка", callback_data="support"),
            InlineKeyboardButton("⭐ Отзывы", callback_data="reviews_menu"),
        ],
        [InlineKeyboardButton("📢 Новости", callback_data="news")],
    ]
)


def save_receipt_message(update: Update, context: CallbackContext):
    """
    Сохраняем последнее сообщение пользователя (фото или файл)
    чтобы потом переслать админу через copy_message
    """

    keyboard = [
        [
            InlineKeyboardButton("✅ Подтвердить", callback_data=f"confirm_payment"),
        ]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    # Сохраняем id сообщения + id чата
    context.user_data["last_receipt_message_id"] = update.message.message_id
    context.user_data["last_receipt_chat_id"] = update.message.chat_id

    update.message.reply_text(
        "📸 Чек получен!\nТеперь нажмите кнопку «Подтвердить оплату».",
        reply_markup=reply_markup,
    )


def handle_text(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    text = update.message.text
    logger.info(f"✉️ Пользователь {user_id} прислал текст: {text}")

    if context.user_data.get("awaiting_review"):
        logger.info(f"⭐ Пользователь {user_id} отправляет отзыв")
        handle_text_review(update, context)
        return


def unknown_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = query.from_user.id
    chat_id = query.message.chat_id
    data = query.data
    logger.warning(f"❓ Неизвестный callback от пользователя {user_id}: {data}")
    query.answer()
    context.bot.send_message(
        chat_id=chat_id,
        text="❓ Неизвестная команда. Пожалуйста, вернитесь в главное меню."
    )


def back_to_main(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = query.from_user.id
    logger.info(f"🔙 Пользователь {user_id} вернулся в главное меню")
    query.answer()

    chat_id = query.message.chat.id

    try:
        query.message.delete()
    except:
        pass

    # Отправляем новое фото с меню
    with open(os.path.join(BASE_DIR, "images", "menu.jpg"), "rb") as img:
        context.bot.send_photo(
            chat_id=chat_id,
            photo=img,
            reply_markup=MAIN_MENU_KEYBOARD
        )


def callback_router(update: Update, context: CallbackContext):
    query = update.callback_query
    data = query.data

    if data == "back_to_main":
        back_to_main(update, context)