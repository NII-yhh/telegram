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
    btn3 = types.InlineKeyboardButton("USDT", callback_data="coin:USDT")

    btn4 = types.InlineKeyboardButton("BNB", callback_data="coin:BNB")
    btn5 = types.InlineKeyboardButton("USDC", callback_data="coin:USDC")
    btn6 = types.InlineKeyboardButton("Ripple", callback_data="coin:XRP")
    btn7 = types.InlineKeyboardButton("SOL", callback_data="coin:SOL")
    btn8 = types.InlineKeyboardButton("DOGE", callback_data="coin:DOGE")
    btn9 = types.InlineKeyboardButton("TRX", callback_data="coin:TRX")
    btn10 = types.InlineKeyboardButton("ADA", callback_data="coin:ADA")

    marcup.add(btn1, btn2, btn3, btn4, btn5, btn6, btn7, btn8, btn9, btn10)

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


def button(call):
    coin = call.data.split(":", 1)[1]

    markup = types.InlineKeyboardMarkup(row_width=2)

    btn0 = types.InlineKeyboardButton(
        "🟢 Купить",
        callback_data=f"trade:BUY:{coin}"
    )

    btn14 = types.InlineKeyboardButton(
        "🔴 Продать",
        callback_data=f"trade:SELL:{coin}"
    )

    markup.add(btn0, btn14)

    bot.send_message(
        call.message.chat.id,
        f"Выбрана валюта: {coin}\nВыбери направление сделки:",
        reply_markup=markup
    )


@bot.callback_query_handler(
    func=lambda call: call.data.startswith("coin:")
)
def coin_callback(call):
    bot.answer_callback_query(call.id)
    button(call)


@bot.callback_query_handler(
    func=lambda call: call.data.startswith("trade:")
)
def trade_callback(call):
    bot.answer_callback_query(call.id)

    _, trade_type, coin = call.data.split(":")

    payload = {
        "asset": coin,
        "fiat": "CNY",
        "tradeType": trade_type,
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
        ads = data.get("data", [])

        if ads:
            ads.sort(
                key=lambda item: float(item.get("adv", {}).get("price", 0)),
                reverse=(trade_type == "SELL")
            )

            action = "покупку" if trade_type == "BUY" else "продажу"
            text = f"Объявления на {action} {coin} найдены!\n\n"

            for index, item in enumerate(ads, start=1):
                ad = item.get("adv", {})
                advertiser = item.get("advertiser", {})

                try:
                    price = float(ad.get("price"))
                except (ValueError, TypeError):
                    continue

                if price <= 0:
                    continue

                nickname = advertiser.get("nickName", "Не указан")
                finish_rate = advertiser.get("monthFinishRate")
                try:
                    if 0 <= finish_rate <=1:
                     finish_rate = finish_rate * 100
                     finish_rate = (f"{finish_rate:.1f}%")

                except (ValueError, TypeError):
                    finish_rate = "Нет данных"
                if finish_rate < 95:
                    continue

                min_amount = ad.get("minSingleTransAmount", "?")
                max_amount = ad.get("maxSingleTransAmount", "?")
                available = ad.get("surplusAmount", "?")
                text += (
                    f"{index}. Цена: {price} CNY\n"
                    f"   Контрагент: {nickname}\n\n"
                    f"   Лимиты: {min_amount}–{max_amount} CNY\n"
                    f"   Доступно: {available} {coin}\n\n"
                    f"   Завершение сделок: {finish_rate}\n"
                )

            bot.send_message(
                call.message.chat.id,
                text
            )

        else:
            bot.send_message(
                call.message.chat.id,
                f"Объявления для {coin}/CNY не найдены."
            )

    except requests.exceptions.RequestException as error:
        print("Ошибка запроса:", error)

        bot.send_message(
            call.message.chat.id,
            "Не удалось получить объявления. Попробуй позже."
        )

    except (ValueError, TypeError) as error:
        print("Ошибка обработки ответа Binance:", error)

        bot.send_message(
            call.message.chat.id,
            "Не удалось обработать ответ Binance."
        )


bot.infinity_polling()
