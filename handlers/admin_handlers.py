
import logging

from functools import wraps

from config import ADMIN_ID
from database import get_users_count


def is_admin(user_id):
    return user_id == ADMIN_ID


def admin_only(bot):

    def decorator(func):

        @wraps(func)
        def wrapper(message):

            user_id = message.from_user.id

            if not is_admin(user_id):
                bot.reply_to(
                    message,
                    "⛔ Доступ запрещён."
                )
                return

            return func(message)

        return wrapper

    return decorator


def register_admin_handlers(bot):

    @bot.message_handler(commands=["admin"])
    @admin_only(bot)
    def admin_command(message):
        bot.reply_to(
            message,
            "🛠 Панель администратора\n\n"
            "/users — количество пользователей"
        )

    @bot.message_handler(commands=["users"])
    @admin_only(bot)
    def users_command(message):
        try:
            users_count = get_users_count()

            bot.reply_to(
                message,
                f"Количество пользователей: {users_count}"
            )

        except Exception:
            logging.exception(
                "Ошибка получения количества пользователей"
            )

            bot.reply_to(
                message,
                "Не удалось получить статистику."
            )
