import telebot
import requests
import os
from telebot import types
import sqlite3
import time
import random
import logging
from logging.handlers import RotatingFileHandler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        RotatingFileHandler(
            "bot.log",
            maxBytes=5 * 1024 * 1024,
            backupCount=3,
            encoding="utf-8"
        ),
        logging.StreamHandler()
    ],
    force=True
)

API_URL = "https://p2p.binance.com/bapi/c2c/v2/friendly/c2c/adv/search"
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
if ADMIN_ID == 0:
    raise ValueError("Не задан ADMIN_ID")
if not TOKEN:
    raise ValueError("Не задан BOT_TOKEN")

bot = telebot.TeleBot(TOKEN)

class TelegramErrorHandler(logging.Handler):
    def emit(self, record):
        try:
            message = self.format(record),
            bot.send_message(ADMIN_ID,f'Критическая ошибка P2P: \n\n {message}')

        except Exception:
            pass
telegram_handler = TelegramErrorHandler()
telegram_handler.setLevel(logging.CRITICAL)
telegram_handler.setFormatter(
    logging.Formatter(
        "%(asctime)s - %(levelname)s - %(message)s"
    )
)
logging.getLogger().addHandler(telegram_handler)

DB_PATH = "p2p_tracker.db"

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_settings (
        user_id INTEGER PRIMARY KEY,
        min_finish_rate REAL DEFAULT 95,
        min_amount_cny REAL DEFAULT 100
    )
""")

try:
    cursor.execute("""
        ALTER TABLE user_settings
        ADD COLUMN min_amount_cny REAL DEFAULT 100
    """)
except sqlite3.OperationalError as error:
    if "duplicate column name" not in str(error):
        raise

conn.commit()
conn.close()
def save_min_amount_cny(user_id, min_amount_cny):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
           INSERT INTO user_settings (user_id, min_amount_cny)
           VALUES (?, ?)
           ON CONFLICT(user_id)
           DO UPDATE SET min_amount_cny = excluded.min_amount_cny
       """, (user_id, min_amount_cny))
    conn.commit()
    conn.close()
def get_min_amount_cny(user_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        "SELECT min_amount_cny FROM user_settings WHERE user_id = ?",
        (user_id,)
    )

    result = cursor.fetchone()
    conn.close()

    if result is None or result[0] is None:
        return 100

    return result[0]


def save_user_settings(user_id, min_finish_rate):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO user_settings (user_id, min_finish_rate)
        VALUES (?, ?)
        ON CONFLICT(user_id)
        DO UPDATE SET min_finish_rate = excluded.min_finish_rate
    """, (user_id, min_finish_rate))

    conn.commit()
    conn.close()

def get_min_finish_rate(user_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT min_finish_rate FROM user_settings WHERE user_id = ?",(user_id,))

    result = cursor.fetchone()

    conn.close()

    if result is None:
        return 95

    return result[0]
@bot.message_handler(commands=["settings"])
def settings(message):
    user_id = message.from_user.id

    current_rate = get_min_finish_rate(user_id)
    current_amount = get_min_amount_cny(user_id)

    # Настройка минимального процента завершения
    rate_markup = types.InlineKeyboardMarkup(row_width=2)

    rate_buttons = [
        types.InlineKeyboardButton("92%", callback_data="rate:92"),
        types.InlineKeyboardButton("94%", callback_data="rate:94"),
        types.InlineKeyboardButton("96%", callback_data="rate:96"),
        types.InlineKeyboardButton("98%", callback_data="rate:98"),
    ]

    rate_markup.add(*rate_buttons)

    bot.send_message(
        message.chat.id,
        "⚙️ Настройка процента завершения\n\n"
        f"Текущее значение: {current_rate:.1f}%\n"
        "Выбери минимальный процент:",
        reply_markup=rate_markup
    )

    # Настройка минимальной суммы сделки
    amount_markup = types.InlineKeyboardMarkup(row_width=2)

    amount_buttons = [
        types.InlineKeyboardButton("100 CNY", callback_data="amount:100"),
        types.InlineKeyboardButton("500 CNY", callback_data="amount:500"),
        types.InlineKeyboardButton("1000 CNY", callback_data="amount:1000"),
        types.InlineKeyboardButton("5000 CNY", callback_data="amount:5000"),
    ]

    amount_markup.add(*amount_buttons)

    bot.send_message(
        message.chat.id,
        "⚙️ Настройка минимальной суммы сделки\n\n"
        f"Текущее значение: {current_amount:,.0f} CNY\n"
        "Выбери минимальную сумму:",
        reply_markup=amount_markup
    )


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
@bot.callback_query_handler(func=lambda call: call.data.startswith(("rate:", "amount:")))
def post_with_retry(url, payload, attempts=3):
    if attempts < 1:
        raise ValueError("Количество попыток должно быть не меньше 1")

    if attempts < 1:
        raise ValueError(
            "Количество попыток должно быть не меньше 1"
        )

    for attempt in range(1, attempts + 1):

        try:
            response = requests.post(
                url,
                json=payload,
                timeout=20
            )

            logging.info(
                f"Запрос выполнен. HTTP {response.status_code}"
            )

            # Проверяем HTTP 429
            if response.status_code == 429:

                logging.warning(
                    f"Binance ограничил запросы. Попытка №{attempt}"
                )

                if attempt == attempts:
                    response.raise_for_status()

                retry_after = response.headers.get("Retry-After")

                try:
                    delay = float(retry_after)
                except (TypeError, ValueError):
                    delay = 2 ** (attempt - 1)

                delay += random.uniform(0, 1)

                logging.warning(
                    f"HTTP 429. Повтор через {delay:.2f} секунд"
                )

                time.sleep(delay)
                continue

            # Проверяем временные серверные ошибки
            if response.status_code in (500, 502, 503, 504):

                if attempt == attempts:
                    response.raise_for_status()

                delay = 2 ** (attempt - 1)
                delay += random.uniform(0, 1)

                logging.warning(
                    f"HTTP {response.status_code}. "
                    f"Повтор через {delay:.2f} секунд"
                )

                time.sleep(delay)
                continue
            if response.status_code in (500, 502, 503, 504):

                if attempt == attempts:
                    response.raise_for_status()

                delay = 2 ** (attempt - 1)
                delay += random.uniform(0, 1)

                print(f"HTTP {response.status_code}. Повтор через {delay:.2f} секунд")

                time.sleep(delay)
                continue

            response.raise_for_status()

            return response

        except requests.exceptions.HTTPError:
            raise

        except requests.exceptions.RequestException as e:

            logging.error(
                f"Ошибка при запросе к Binance: {e}"
            )

            if attempt == attempts:
                raise RuntimeError(
                    f"Не удалось выполнить запрос после {attempts} попыток"
                ) from e

            delay = 2 ** (attempt - 1)
            delay += random.uniform(0, 1)

            logging.warning(
                f"Повтор через {delay:.2f} секунд"
            )

            time.sleep(delay)

    raise RuntimeError(
        f"Не удалось выполнить POST-запрос после {attempts} попыток"
    )

@bot.callback_query_handler(
    func=lambda call: call.data.startswith("trade:")
)
def trade_callback(call):
    bot.answer_callback_query(call.id)

    _, trade_type, coin = call.data.split(":")

    user_id = call.from_user.id

    min_finish_rate = get_min_finish_rate(user_id)
    min_amount_cny = get_min_amount_cny(user_id)



    try:
        # Загружаем страницы, пока не найдём 10 подходящих объявлений
        all_ads = []
        seen_ids = set()
        page = 1
        max_pages = 10
        # или пока Binance не перестанет возвращать объявления.
        while len(all_ads) < 10 and page <= max_pages:
            payload = {
                "asset": coin,
                "fiat": "CNY",
                "tradeType": trade_type,
                "page": page,
                "rows": 10,
                "payTypes": [],
                "publisherType": None,
                "transAmount": ""
            }

            try:
                response = post_with_retry(API_URL, payload)
                data = response.json()

            except requests.exceptions.JSONDecodeError:
                print("Binance вернула некорректный JSON")
                bot.send_message(
                    call.message.chat.id,
                    "Binance вернула некорректный ответ. Попробуй позже."
                )
                return

            if not isinstance(data, dict):
                raise ValueError("Неожиданный формат ответа Binance")

            ads = data.get("data", [])

            if not isinstance(ads, list):
                raise ValueError("Не удалось прочитать список объявлений")

            if not ads:
                break

            for item in ads:
                if not isinstance(item, dict):
                    continue

                ad = item.get("adv", {})
                advertiser = item.get("advertiser", {})

                if not isinstance(ad, dict):
                    continue

                if not isinstance(advertiser, dict):
                    advertiser = {}

                try:
                    price = float(ad.get("price", 0))
                    finish_rate = float(advertiser.get("monthFinishRate"))
                    min_amount = ad.get("minSingleTransAmount", "?")
                    min_single_amount = float(min_amount)
                    available = float(ad.get("surplusAmount", 0))
                except (ValueError, TypeError):
                    continue

                if 0 <= finish_rate <= 1:
                    finish_rate *= 100

                if price <= 0:
                    continue

                if finish_rate < min_finish_rate:
                    continue

                if min_single_amount < min_amount_cny:
                    continue

                if available < 100:
                    continue

                ad_id = ad.get("advNo")

                if not ad_id or ad_id in seen_ids:
                    continue

                seen_ids.add(ad_id)
                all_ads.append(item)

                if len(all_ads) >= 10:
                    break

            page += 1

        if all_ads:
            # Сортируем все найденные объявления по цене.
            all_ads.sort(
                key=lambda item: float(item["adv"]["price"]),
                reverse=(trade_type == "SELL")
            )

            action = "покупку" if trade_type == "BUY" else "продажу"
            text = f"Объявления на {action} {coin} найдены!\n\n"

            for shown_count, item in enumerate(all_ads[:10], start=1):
                ad = item.get("adv", {})
                advertiser = item.get("advertiser", {})

                price = float(ad["price"])
                nickname = advertiser.get("nickName", "Не указан")
                finish_rate = float(advertiser["monthFinishRate"])

                if 0 <= finish_rate <= 1:
                    finish_rate *= 100

                min_amount = ad.get("minSingleTransAmount", "?")
                max_amount = ad.get("maxSingleTransAmount", "?")
                available = float(ad.get("surplusAmount", 0))
                finish_rate_text = f"{finish_rate:.1f}%"

                text += (
                    f"{shown_count}. Цена: {price} CNY\n"
                    f"   Контрагент: {nickname}\n\n"
                    f"   Лимиты: {min_amount}–{max_amount} CNY\n"
                    f"   Доступно: {available} {coin}\n\n"
                    f"   Завершение сделок: {finish_rate_text}\n"
                )

            bot.send_message(call.message.chat.id, text)

        else:
            bot.send_message(
                call.message.chat.id,
                f"Для {coin}/CNY не найдено объявлений, "
                "подходящих под заданные фильтры."
            )
    except requests.exceptions.Timeout:
        print("Время ожидания ответа Binance истекло")
        bot.send_message(
            call.message.chat.id,
            "Binance долго не отвечает. Попробуй позже."
        )
        return
    except requests.exceptions.ConnectionError:
        print("Ошибка подключения к Binance")
        bot.send_message(
            call.message.chat.id,
            "Не удалось подключиться к Binance. Проверь интернет."
        )
        return

    except requests.exceptions.HTTPError as error:
        print("HTTP-ошибка Binance:", error)
        bot.send_message(
            call.message.chat.id,
            "Binance вернула ошибку сервера. Попробуй позже."
        )
        return


    except requests.exceptions.RequestException as error:
        print("Другая ошибка запроса:", error)
        bot.send_message(
            call.message.chat.id,
            "Не удалось получить объявления. Попробуй позже."
        )



    except ValueError as error:
        print("Некорректный ответ Binance:", error)
        bot.send_message(
            call.message.chat.id,
            "Binance вернула данные неожиданного формата. Попробуй позже."
        )
        return
    except RuntimeError as e:
        print(f"Ошибка выполнения запроса: {e}")
        bot.send_message(
        call.message.chat.id,
        "Не удалось получить объявления. Попробуй позже."
    )
    return


bot.infinity_polling()


