from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackContext

from database.database import get_client_by_tg_id
from utils.validators import is_subscription_active

from utils.logger import setup_logger

logger = setup_logger(__name__)

REVIEWS_PER_PAGE = 5  # Количество отзывов на одной странице


def show_reviews_menu(update: Update, context: CallbackContext):
    query = update.callback_query
    logger.info(f"📋 Пользователь {query.from_user.id} открыл меню отзывов")
    query.answer()

    try:
        query.message.delete()
    except:
        pass

    keyboard = [
        [
            InlineKeyboardButton("📖 Посмотреть отзывы", callback_data="view_reviews"),
            InlineKeyboardButton("✍ Оставить отзыв", callback_data="leave_review"),
        ],
        [InlineKeyboardButton("🔙 Назад", callback_data="back_to_main")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    query.message.reply_text(
        "⭐ <b>Меню отзывов</b>\n\nВыберите действие:",
        parse_mode="HTML",
        reply_markup=reply_markup,
    )


def view_reviews(update: Update, context: CallbackContext):
    """Показываем отзывы с пагинацией."""
    query = update.callback_query
    query.answer()
    page = int(context.user_data.get("review_page", 1))
    logger.info(f"📖 Пользователь {query.from_user.id} смотрит отзывы, страница {page}")

    from database.database import conn
    with conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT user_id, username, review, rating FROM reviews WHERE status = 'approved'"
        )
        reviews = cursor.fetchall()

    total_reviews = len(reviews)
    total_pages = (total_reviews + REVIEWS_PER_PAGE - 1) // REVIEWS_PER_PAGE

    if total_reviews > 0:
        start_index = (page - 1) * REVIEWS_PER_PAGE
        end_index = start_index + REVIEWS_PER_PAGE
        reviews_on_page = reviews[start_index:end_index]

        # Форматируем отзывы с динамическими звёздами
        stars = "★★★★★"

        reviews_text = f"🌟 <b>Отзывы наших пользователей ({total_reviews})</b>\n\n"
        for r in reviews_on_page:
            username = r[1] if r[1] else "Пользователь"
            rating = r[3] if r[3] is not None else 5  # Если rating NULL, по умолчанию 5
            star_display = stars[:rating] + "☆" * (5 - rating)  # ★★★★☆ для rating=4
            reviews_text += (
                f'👤 <b><a href="https://t.me/{username}">{username}</a></b> {star_display}\n'
                f"💬 <i>{r[2]}</i>\n\n"
            )

        # Кнопки пагинации
        keyboard = []
        if total_pages > 1:
            buttons = []
            if page > 1:
                buttons.append(
                    InlineKeyboardButton(
                        "⬅️ Назад", callback_data=f"view_reviews_page_{page - 1}"
                    )
                )
            if page < total_pages:
                buttons.append(
                    InlineKeyboardButton(
                        "Вперед ➡️", callback_data=f"view_reviews_page_{page + 1}"
                    )
                )
            keyboard.append(buttons)

        keyboard.append(
            [InlineKeyboardButton("🔙 Главное меню", callback_data="back_to_main")]
        )
        reply_markup = InlineKeyboardMarkup(keyboard)

        query.message.edit_text(
            reviews_text,
            parse_mode="HTML",
            disable_web_page_preview=True,
            reply_markup=reply_markup,
        )

    else:
        keyboard = [
            [InlineKeyboardButton("🔙 Главное меню", callback_data="back_to_main")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        query.message.edit_text(
            "✨ <i>Пока нет отзывов. Будьте первым и поделитесь своим впечатлением!</i> ✨",
            parse_mode="HTML",
            reply_markup=reply_markup,
        )


def leave_review(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()

    keyboard = [
        [InlineKeyboardButton("🔙 Главное меню", callback_data="back_to_main")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    user_id_str = str(query.from_user.id)
    client_data = get_client_by_tg_id(user_id_str)
    if not client_data:
        logger.warning(
            f"🚫 Пользователь {user_id_str} без подписки попытался оставить отзыв"
        )
        query.message.edit_text(
            "🚫 У вас пока нет оформленных подписок.",
            reply_markup=reply_markup,
        )
        return

    # Проверяем, оставлял ли пользователь уже отзыв
    from database.database import conn
    with conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM reviews WHERE user_id = ?", (user_id_str,))
        review_count = cursor.fetchone()[0]

    if review_count > 0:
        logger.info(f"🚫 Пользователь {user_id_str} уже оставлял отзыв")
        query.message.edit_text(
            "🚫 Вы уже оставляли отзыв.",
            reply_markup=reply_markup,
        )
        return

    with conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT expiry_time, payment_status FROM clients WHERE telegram_id = ? ORDER BY expiry_time DESC",
            (str(user_id_str),),
        )
        result = cursor.fetchone()

    expiry_time_ms, payment_status = result
    if not is_subscription_active(expiry_time_ms) or payment_status != "approved":
        logger.info(
            f"🚫 Пользователь {user_id_str} не имеет активной подписки для отзыва"
        )
        query.message.edit_text(
            "🚫 У вас нет активной подписки.",
            reply_markup=reply_markup,
        )
        return

    # Кнопки для выбора рейтинга
    keyboard = [
        [
            InlineKeyboardButton("★☆☆☆☆ (1)", callback_data="rate_1"),
            InlineKeyboardButton("★★☆☆☆ (2)", callback_data="rate_2"),
            InlineKeyboardButton("★★★☆☆ (3)", callback_data="rate_3"),
        ],
        [
            InlineKeyboardButton("★★★★☆ (4)", callback_data="rate_4"),
            InlineKeyboardButton("★★★★★ (5)", callback_data="rate_5"),
        ],
    ]
    reply_markup_stars = InlineKeyboardMarkup(keyboard)

    keyboard.append(
        [InlineKeyboardButton("🔙 Главное меню", callback_data="back_to_main")]
    )
    reply_markup_stars = InlineKeyboardMarkup(keyboard)

    query.message.edit_text(
        "🌟 Оцените наш сервис (выберите количество звёзд):",
        reply_markup=reply_markup_stars,
    )

    context.user_data["awaiting_rating"] = True


def handle_text_review(update: Update, context: CallbackContext):
    if not context.user_data.get("awaiting_review"):
        return

    user_id = update.message.from_user.id
    username = update.message.from_user.username or f"User-{user_id}"
    review_text = update.message.text
    rating = context.user_data.get("review_rating", 5)

    logger.info(
        f"✅ Пользователь {user_id} отправил отзыв (rating={rating}): {review_text}"
    )

    keyboard = [
        [InlineKeyboardButton("🔙 Главное меню", callback_data="back_to_main")],
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    update.message.reply_text("✅ Ваш отзыв опубликован.", reply_markup=reply_markup)

    from database.database import conn
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO reviews (user_id, username, review, rating, status) VALUES (?, ?, ?, ?, 'approved')",
        (user_id, username, review_text, rating),
    )

    context.user_data.pop("awaiting_review", None)
    context.user_data.pop("review_rating", None)


def handle_rating(update: Update, context: CallbackContext):
    query = update.callback_query
    if not context.user_data.get("awaiting_rating"):
        return

    rating = int(query.data.split("_")[1])  # Извлекаем число из "rate_1" -> 1
    logger.info(f"⭐ Пользователь {query.from_user.id} выбрал рейтинг: {rating}")
    context.user_data["review_rating"] = rating
    context.user_data["awaiting_rating"] = False
    context.user_data["awaiting_review"] = True

    query.message.edit_text(
        f"✅ Вы выбрали рейтинг: {'★' * rating}{'☆' * (5 - rating)}\n\nПожалуйста, отправьте ваш отзыв одним сообщением."
    )


def view_reviews_page_router(update: Update, context: CallbackContext):
    query = update.callback_query
    try:
        page = int(query.data.split("_")[-1])
        context.user_data["review_page"] = page
        view_reviews(update, context)
    except ValueError:
        query.message.reply_text("❌ Ошибка при переходе между страницами.")
