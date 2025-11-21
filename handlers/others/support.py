import os

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackContext

from config import BASE_DIR
from utils.logger import setup_logger

logger = setup_logger(__name__)

SUPPORT_TEXT = (
    "🆘 <b>По всем вопросам:</b> @kosolapyyi"
)


def support_command(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = query.from_user.id
    logger.info(f"📘 Пользователь {user_id} открыл поддержку")
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
    with open(os.path.join(BASE_DIR, "images", "teh-podderjka.jpg"), "rb") as img:
        context.bot.send_photo(
            chat_id=chat_id,
            photo=img,
            caption="<b>По всем вопросам:</b> @kosolapyyi",
            reply_markup=reply_markup,
            parse_mode="HTML"
        )
