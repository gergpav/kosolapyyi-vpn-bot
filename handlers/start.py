import os

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext

from config import BASE_DIR
from handlers.helpers import MAIN_MENU_KEYBOARD


def start_command(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id

    keyboard = [
        [InlineKeyboardButton("Газ! Подключаемся", callback_data="show_menu")],
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    with open(os.path.join(BASE_DIR, "images", "icon.jpg"), "rb") as img:
        context.bot.send_photo(
            chat_id=chat_id,
            photo=img,
            caption="<b>kosolapyyi</b> - пора пользоваться нормальным VPN)",
            reply_markup=reply_markup,
            parse_mode="HTML"
        )

def show_menu(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()

    chat_id = query.message.chat.id

    # Удаляем старое сообщение
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

