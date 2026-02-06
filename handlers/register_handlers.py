from telegram.ext import CommandHandler, CallbackQueryHandler, Filters, MessageHandler

from handlers.admin.admin import clients_command
from handlers.admin.admin_approval import approve_payment_router, reject_payment_router
from handlers.helpers import handle_text, unknown_callback, callback_router, save_receipt_message
from handlers.others.instructions import show_instructions_menu, show_instruction_platform_router
from handlers.others.news import show_news
from handlers.others.reviews import handle_rating, leave_review, view_reviews_page_router, view_reviews, \
    show_reviews_menu
from handlers.others.support import support_command
from handlers.start import start_command, show_menu
from handlers.subscriptions.buy_subscription import subscribe_command, subscribe_with_duration_router
from handlers.subscriptions.confirm_payment import cancel_payment_command, confirm_payment_command
from handlers.subscriptions.extend_subscription import extend_command, extend_with_duration_router
from handlers.subscriptions.my_subscription import subscription_command
from handlers.subscriptions.subscription_menu import show_subscription_menu
from handlers.subscriptions.test_subscription import test_command


def register_start(dp):
    dp.add_handler(CommandHandler("start", start_command))
    dp.add_handler(
        CallbackQueryHandler(show_menu, pattern="^show_menu$")
    )


def register_reviews(dp):
    dp.add_handler(CallbackQueryHandler(show_reviews_menu, pattern="^reviews_menu$"))
    dp.add_handler(CallbackQueryHandler(view_reviews, pattern="^view_reviews$"))
    dp.add_handler(
        CallbackQueryHandler(view_reviews_page_router, pattern="^view_reviews_page_")
    )
    dp.add_handler(CallbackQueryHandler(leave_review, pattern="^leave_review$"))
    dp.add_handler(CallbackQueryHandler(handle_rating, pattern="^rate_"))


def register_support(dp):
    dp.add_handler(CallbackQueryHandler(support_command, pattern="^support$"))


def register_news(dp):
    dp.add_handler(CallbackQueryHandler(show_news, pattern="^news$"))


def register_instructions(dp):
    dp.add_handler(
        CallbackQueryHandler(show_instructions_menu, pattern="^instructions$")
    )
    dp.add_handler(
        CallbackQueryHandler(show_instruction_platform_router, pattern="^inst_")
    )


def register_subscriptions(dp):
    dp.add_handler(
        CallbackQueryHandler(show_subscription_menu, pattern="^subscription_menu$")
    )
    dp.add_handler(CallbackQueryHandler(test_command, pattern="^test$"))
    dp.add_handler(CallbackQueryHandler(subscribe_command, pattern="^subscribe$"))
    dp.add_handler(CallbackQueryHandler(subscription_command, pattern="^subscription$"))
    dp.add_handler(CallbackQueryHandler(extend_command, pattern="^extend$"))
    dp.add_handler(
        CallbackQueryHandler(confirm_payment_command, pattern="^confirm_payment$")
    )
    dp.add_handler(
        CallbackQueryHandler(cancel_payment_command, pattern="^cancel_payment$")
    )

    # Обработчики для подписки/продления по сроку
    dp.add_handler(
        CallbackQueryHandler(subscribe_with_duration_router, pattern="^subscribe_")
    )
    dp.add_handler(
        CallbackQueryHandler(extend_with_duration_router, pattern="^extend_")
    )


def register_admin(dp):
    dp.add_handler(CommandHandler("clients", clients_command))

    # Обработчики подтверждения/отклонения оплат админом
    dp.add_handler(
        CallbackQueryHandler(approve_payment_router, pattern="^approve_[0-9]+$")
    )

    dp.add_handler(
        CallbackQueryHandler(reject_payment_router, pattern="^^reject_[0-9]+$")
    )


def register_helpers(dp):
    dp.add_handler(
        MessageHandler(Filters.photo | Filters.document, save_receipt_message)
    )
    dp.add_handler(CallbackQueryHandler(callback_router, pattern="^back_to_main$"))
    dp.add_handler(
        CallbackQueryHandler(unknown_callback)
    )  
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_text))
