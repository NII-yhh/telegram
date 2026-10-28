import telebot
import requests
import os
from telebot import types

API_URL = "https://p2p.binance.com/bapi/c2c/v2/friendly/c2c/adv/search"
TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise ValueError("Не задан BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)



amount = 0
@bot.message_handler(commands=['start'])
def start(message):

    marcup = types.InlineKeyboardMarkup(row_width=2)
    btn1 = types.InlineKeyboardButton("BTC", callback_data="coin:BTC")
    btn2 = types.InlineKeyboardButton("ETH", callback_data="coin:ETH")
    btn3 = types.InlineKeyboardButton("USDT",callback_data="coin:USDT")

    btn4 = types.InlineKeyboardButton("BNB", callback_data="coin:BNB")
    btn5 = types.InlineKeyboardButton("USDC", callback_data="coin:USDC")
    btn6 = types.InlineKeyboardButton("Ripple", callback_data="coin:Ripple")
    btn7 = types.InlineKeyboardButton("SOL", callback_data="coin:SOL")
    btn8 = types.InlineKeyboardButton("DOGE", callback_data="coin:DOGE")
    btn9 = types.InlineKeyboardButton("TRX", callback_data="coin:TRX")
    btn10 = types.InlineKeyboardButton("ADA", callback_data="coin:ADA")

    marcup.add(btn1,btn2,btn3,btn4,btn5,btn6,btn7,btn8,btn9,btn10)

    with open("images/dddd.png", "rb") as photo:
        bot.send_photo(
            message.chat.id,
            photo,
            caption="""💱 P2P Tracker — мониторинг P2P-ордеров

Бот для поиска и анализа P2P-предложений по криптовалютам за китайские юани (CNY).

🇨🇳 Важно: пока бот работает только с китайским юанем (CNY). Поддержка других фиатных валют может появиться в будущих обновлениях.

🔎 Что умеет бот?

🪙 Отслеживать предложения по 10 криптовалютам.
📊 Показывать топ-10 ордеров по выбранному направлению.
💰 Помогать сравнивать цены покупки и продажи.
⚡ Упрощать поиск интересных предложений.

📌 Выбери криптовалюту, укажи направление сделки и изучи доступные ордера прямо в Telegram.

⚠️ Важно: цены и доступность предложений могут меняться. Перед сделкой проверяй условия, лимиты и репутацию контрагента на бирже. Бот не гарантирует безопасность или прибыльность сделки.

🚀 Меньше ручного поиска — больше удобства при анализе P2P-рынка!
""",
            reply_markup=marcup
        )


@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):

    bot.answer_callback_query(call.id)
    coin = call.data.split(":", 1)[1]

    payload = {
        "asset": coin,
        "fiat": "CNY",
        "tradeType": "BUY",
        "page": 1,
        "rows": 10,
        "payTypes": [],
        "publisherType": None,
        "transAmount": ""
    }

    try:
        response = requests.post(
            API_URL,
            json=payload,
            timeout=20
        )

        response.raise_for_status()
        data = response.json()
        if data.get("data"):
            bot.send_message(call.message.chat.id,f"Обьявления для {coin} найдены.")
        else:
            bot.send_message(call.message.chat.id, f"Обьявления для {coin} не найдены.")


    except requests.exceptions.RequestException as error:
        print("Ошибка запроса:", error)


    bot.send_message(call.message.chat.id,"Не удалось получить объявления. Попробуй позже."


        )



bot.infinity_polling()
