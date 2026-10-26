import telebot
import requests

import os
from telebot import types

API_URL = (
    "https://www.binance.com/bapi/c2c/v1/public/c2c/agent/ad-lis")

TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)


amount = 0
@bot.message_handler(commands=['start'])
def start(message):

    marcup = types.InlineKeyboardMarkup(row_width=2)
    btn1 = types.InlineKeyboardButton("BTC", callback_data="BTC")
    btn2 = types.InlineKeyboardButton("ETH", callback_data="ETH")
    btn3 = types.InlineKeyboardButton("USDT",callback_data="USDT")
    btn4 = types.InlineKeyboardButton("BNB", callback_data="BNB")
    btn5 = types.InlineKeyboardButton("USDC", callback_data="USDC")
    btn6 = types.InlineKeyboardButton("Ripple", callback_data="Ripple")
    btn7 = types.InlineKeyboardButton("SOL", callback_data="SOL")
    btn8 = types.InlineKeyboardButton("DOGE", callback_data="DOGE")
    btn9 = types.InlineKeyboardButton("TRX", callback_data="TRX")
    btn10 = types.InlineKeyboardButton("ADA", callback_data="ADA")

    marcup.add(btn1,btn2,btn3,btn4,btn5,btn6,btn7,btn8,btn9,btn10)

    with open("images/dddd.png", "rb") as photo:
        bot.send_photo(
            message.chat.id,
            photo,
            caption="""💱 P2P Tracker — мониторинг P2P-ордеров

    Бот для быстрого поиска выгодных P2P-предложений по криптовалютам за российские рубли (RUB).

    🔎 Что умеет бот?

    🪙 Отслеживать предложения по 10 криптовалютам.
    📊 Показывать топ-10 ордеров по выбранному направлению.
    💰 Сравнивать цены покупки и продажи.
    ⚡ Помогать быстрее находить интересные предложения.

    📌 Выбери криптовалюту, укажи направление сделки и изучи доступные ордера прямо в Telegram.

    ⚠️ Важно: цены и доступность предложений могут меняться. Перед сделкой проверяй условия, лимиты и репутацию контрагента на бирже. Бот не гарантирует безопасность или прибыльность сделки.

    🚀 Меньше ручного поиска — больше удобства при анализе P2P-рынка!""",
            reply_markup=marcup
        )


@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    coin = call.data
    bot.answer_callback_query(call.id)

def btc(message):
    global amount



bot.infinity_polling()
