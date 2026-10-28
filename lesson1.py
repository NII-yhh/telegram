
import telebot
import requests
import os
from telebot import types

API_URL = "https://p2p.binance.com/bapi/c2c/v2/friendly/c2c/adv/search"



payload = {
    "asset": "ETH",
    "fiat": "CNY",
    "tradeType": "BUY",
    "page": 1,
    "rows": 10
}

TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    raise ValueError("Не задан BOT_TOKEN")

bot = telebot.TeleBot(TOKEN)

try:
    response = requests.post(
        API_URL,
        json=payload,
        timeout=15,

    )

    print("URL:", response.url)
    print("Отправленный payload:", payload)
    print("HTTP статус:", response.status_code)

    response.raise_for_status()
    data = response.json()

    print("Полный ответ:", data)
    print("Успех:", data.get("success"))
    print("Всего объявлений:", data.get("total"))
    print("Список объявлений:", data.get("data"))
    print("Код Binance:", data.get("code"))
    print("Сообщение:", data.get("message"))

except requests.exceptions.RequestException as error:
    print("Ошибка запроса:", error)

except ValueError as error:
    print("Ошибка обработки JSON:", error)

bot.infinity_polling()
