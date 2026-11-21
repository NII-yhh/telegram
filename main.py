

import telebot

from config import BOT_TOKEN, ADMIN_ID
from database import init_db

from handlers.user_handlers import register_user_handlers
from handlers.admin_handlers import register_admin_handlers
from handlers.trade_handlers import register_trade_handlers
from handlers.settings_handlers import register_settings_handlers

if not BOT_TOKEN:
    raise ValueError("Не задан BOT_TOKEN")

if ADMIN_ID == 0:
    raise ValueError("Не задан ADMIN_ID")


# Создаём экземпляр бота
bot = telebot.TeleBot(BOT_TOKEN)


def main():
    # Инициализируем базу данных
    init_db()

    # Регистрируем обработчики
    register_user_handlers(bot)
    register_admin_handlers(bot)
    register_trade_handlers(bot)
    register_settings_handlers(bot)

    print("P2P Tracker запускается...")

    # Запускаем бота
    bot.infinity_polling(skip_pending=True)


if __name__ == "__main__":
    main()
