from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackContext


def show_subscription_menu(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()

    try:
        query.message.delete()
    except:
        pass

    keyboard = [
        [
            InlineKeyboardButton("💳 Оформление подписки", callback_data="subscribe"),
            InlineKeyboardButton("🔄 Продление подписки", callback_data="extend"),
        ],
        [
            InlineKeyboardButton("📜 Текущая подписка", callback_data="subscription"),
            InlineKeyboardButton("🔙 Назад", callback_data="back_to_main")
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    query.message.reply_text(
        "💼 <b>Меню подписок</b>\n\nВыберите действие:",
        parse_mode="HTML",
        reply_markup=reply_markup,
    )
