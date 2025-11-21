import os

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackContext

from config import BASE_DIR
from utils.logger import setup_logger

logger = setup_logger(__name__)

NEWS_TEXT = (
    "📢 <b>Новости о нашем VPN тут:</b> https://t.me/kosolapyyiVPN"
)


def show_news(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = query.from_user.id
    logger.info(f"📘 Пользователь {user_id} открыл новости")
    query.answer()
    keyboard = [
        [InlineKeyboardButton("🔙 Главное меню", callback_data="back_to_main")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    chat_id = query.message.chat.id

    # Удаляем старое сообщение
    try:
        query.message.delete()
    except:
        pass

    # Отправляем новое фото с меню
    with open(os.path.join(BASE_DIR, "images", "novosti.jpg"), "rb") as img:
        context.bot.send_photo(
            chat_id=chat_id,
            photo=img,
            caption=NEWS_TEXT,
            reply_markup=reply_markup,
            parse_mode="HTML"
        )

