
import os
import time
import random
import sqlite3
import logging
import requests
import telebot

from functools import wraps
from logging.handlers import RotatingFileHandler
from telebot import types


# ==================================================
# 1. НАСТРОЙКИ
# ==================================================

API_URL = "https://p2p.binance.com/bapi/c2c/v2/friendly/c2c/adv/search"

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

DB_PATH = "p2p_tracker.db"

if ADMIN_ID == 0:
    raise ValueError("Не задан ADMIN_ID")

if not TOKEN:
    raise ValueError("Не задан BOT_TOKEN")


bot = telebot.TeleBot(TOKEN)


# ==================================================
# 2. ЛОГИРОВАНИЕ
# ==================================================

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


class TelegramErrorHandler(logging.Handler):

    def emit(self, record):
        try:
            message = self.format(record)

            bot.send_message(
                ADMIN_ID,
                f"Критическая ошибка P2P:\n\n{message}"
            )

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


# ==================================================
# 3. АДМИНИСТРАТОР И ДЕКОРАТОР
# ==================================================

def is_admin(user_id):
    return user_id == ADMIN_ID


def admin_only(func):

    @wraps(func)
    def wrapper(message):

        user_id = message.from_user.id

        if not is_admin(user_id):
            bot.reply_to(
                message,
                "⛔ У тебя нет доступа к этой команде."
            )
            return

        return func(message)

    return wrapper


# ==================================================
# 4. БАЗА ДАННЫХ
# ==================================================

def init_database():

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_settings (
            user_id INTEGER PRIMARY KEY,
            min_finish_rate REAL DEFAULT 95,
            min_amount_cny REAL DEFAULT 100
        )
    """)

    # Миграция для старых баз данных
    try:
        cursor.execute("""
            ALTER TABLE user_settings
            ADD COLUMN min_amount_cny REAL DEFAULT 100
        """)

    except sqlite3.OperationalError as error:

        if "duplicate column name" not in str(error):
            conn.close()
            raise

    conn.commit()
    conn.close()

    logging.info("База данных успешно инициализирована")


def register_user(user_id):

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        "INSERT OR IGNORE INTO users (user_id) VALUES (?)",
        (user_id,)
    )

    conn.commit()
    conn.close()


def get_users_count():

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM users")

    result = cursor.fetchone()

    conn.close()

    return result[0]


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

    cursor.execute(
        "SELECT min_finish_rate FROM user_settings WHERE user_id = ?",
        (user_id,)
    )

    result = cursor.fetchone()
    conn.close()

    if result is None or result[0] is None:
        return 95

    return result[0]


# ==================================================
# 5. АДМИНИСТРАТИВНЫЕ КОМАНДЫ
# ==================================================

@bot.message_handler(commands=["admin"])
@admin_only
def admin_command(message):

    bot.reply_to(
        message,
        "Добро пожаловать в панель администратора!"
    )


@bot.message_handler(commands=["users"])
@admin_only
def users_command(message):

    users_count = get_users_count()

    bot.reply_to(
        message,
        f"Количество пользователей: {users_count}"
    )


# ==================================================
# 6. НАСТРОЙКИ ПОЛЬЗОВАТЕЛЯ
# ==================================================

@bot.message_handler(commands=["settings"])
def settings(message):

    user_id = message.from_user.id

    current_rate = get_min_finish_rate(user_id)
    current_amount = get_min_amount_cny(user_id)

    rate_markup = types.InlineKeyboardMarkup(row_width=2)

    rate_buttons = [
        types.InlineKeyboardButton(
            "92%", callback_data="rate:92"
        ),
        types.InlineKeyboardButton(
            "94%", callback_data="rate:94"
        ),
        types.InlineKeyboardButton(
            "96%", callback_data="rate:96"
        ),
        types.InlineKeyboardButton(
            "98%", callback_data="rate:98"
        ),
    ]

    rate_markup.add(*rate_buttons)

    bot.send_message(
        message.chat.id,
        "⚙️ Настройка процента завершения\n\n"
        f"Текущее значение: {current_rate:.1f}%\n"
        "Выбери минимальный процент:",
        reply_markup=rate_markup
    )

    amount_markup = types.InlineKeyboardMarkup(row_width=2)

    amount_buttons = [
        types.InlineKeyboardButton(
            "100 CNY", callback_data="amount:100"
        ),
        types.InlineKeyboardButton(
            "500 CNY", callback_data="amount:500"
        ),
        types.InlineKeyboardButton(
            "1000 CNY", callback_data="amount:1000"
        ),
        types.InlineKeyboardButton(
            "5000 CNY", callback_data="amount:5000"
        ),
    ]

    amount_markup.add(*amount_buttons)

    bot.send_message(
        message.chat.id,
        "⚙️ Настройка минимальной суммы сделки\n\n"
        f"Текущее значение: {current_amount:,.0f} CNY\n"
        "Выбери минимальную сумму:",
        reply_markup=amount_markup
    )


@bot.callback_query_handler(
    func=lambda call: call.data.startswith(("rate:", "amount:"))
)
def settings_callback(call):

    user_id = call.from_user.id

    try:
        setting, value = call.data.split(":", 1)

        if setting == "rate":

            rate = float(value)

            if rate not in (92, 94, 96, 98):
                raise ValueError("Недопустимый процент")

            save_user_settings(user_id, rate)

            bot.answer_callback_query(
                call.id,
                "Процент завершения сохранён!"
            )

            bot.send_message(
                call.message.chat.id,
                f"Минимальный процент завершения: {rate}%"
            )

        elif setting == "amount":

            amount = float(value)

            if amount not in (100, 500, 1000, 5000):
                raise ValueError("Недопустимая сумма")

            save_min_amount_cny(user_id, amount)

            bot.answer_callback_query(
                call.id,
                "Минимальная сумма сохранена!"
            )

            bot.send_message(
                call.message.chat.id,
                f"Минимальная сумма сделки: {amount:.0f} CNY"
            )

    except ValueError:

        bot.answer_callback_query(
            call.id,
            "Некорректное значение!",
            show_alert=True
        )


# ==================================================
# 7. КОМАНДА START
# ==================================================

@bot.message_handler(commands=["start"])
def start(message):

    register_user(message.from_user.id)

    markup = types.InlineKeyboardMarkup(row_width=2)

    buttons = [
        types.InlineKeyboardButton(
            "BTC", callback_data="coin:BTC"
        ),
        types.InlineKeyboardButton(
            "ETH", callback_data="coin:ETH"
        ),
        types.InlineKeyboardButton(
            "USDT", callback_data="coin:USDT"
        ),
        types.InlineKeyboardButton(
            "BNB", callback_data="coin:BNB"
        ),
        types.InlineKeyboardButton(
            "USDC", callback_data="coin:USDC"
        ),
        types.InlineKeyboardButton(
            "Ripple", callback_data="coin:XRP"
        ),
        types.InlineKeyboardButton(
            "SOL", callback_data="coin:SOL"
        ),
        types.InlineKeyboardButton(
            "DOGE", callback_data="coin:DOGE"
        ),
        types.InlineKeyboardButton(
            "TRX", callback_data="coin:TRX"
        ),
        types.InlineKeyboardButton(
            "ADA", callback_data="coin:ADA"
        ),
    ]

    markup.add(*buttons)

    try:
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

🚀 Меньше ручного поиска — больше удобства при анализе P2P-рынка!""",
                reply_markup=markup
            )

    except FileNotFoundError:

        logging.exception("Не найден файл images/dddd.png")

        bot.send_message(
            message.chat.id,
            "Добро пожаловать в P2P Tracker!",
            reply_markup=markup
        )


# ==================================================
# 8. ВЫБОР КРИПТОВАЛЮТЫ
# ==================================================

@bot.callback_query_handler(
    func=lambda call: call.data.startswith("coin:")
)
def button(call):

    bot.answer_callback_query(call.id)

    coin = call.data.split(":", 1)[1]

    markup = types.InlineKeyboardMarkup(row_width=2)

    btn_buy = types.InlineKeyboardButton(
        "🟢 Купить",
        callback_data=f"trade:BUY:{coin}"
    )

    btn_sell = types.InlineKeyboardButton(
        "🔴 Продать",
        callback_data=f"trade:SELL:{coin}"
    )

    markup.add(btn_buy, btn_sell)

    bot.send_message(
        call.message.chat.id,
        f"Выбрана валюта: {coin}\n"
        "Выбери направление сделки:",
        reply_markup=markup
    )


# ==================================================
# 9. ПОВТОРНЫЕ HTTP-ЗАПРОСЫ
# ==================================================

def post_with_retry(url, payload, attempts=3):

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
                "Запрос выполнен. HTTP %s",
                response.status_code
            )

            # HTTP 429
            if response.status_code == 429:

                logging.warning(
                    "Binance ограничил запросы. Попытка №%s",
                    attempt
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
                    "Повтор через %.2f секунд",
                    delay
                )

                time.sleep(delay)
                continue

            # HTTP 500, 502, 503, 504
            if response.status_code in (500, 502, 503, 504):

                if attempt == attempts:
                    response.raise_for_status()

                delay = 2 ** (attempt - 1)
                delay += random.uniform(0, 1)

                logging.warning(
                    "HTTP %s. Повтор через %.2f секунд",
                    response.status_code,
                    delay
                )

                time.sleep(delay)
                continue

            response.raise_for_status()

            return response

        except requests.exceptions.HTTPError:
            raise

        except requests.exceptions.RequestException as error:

            logging.error(
                "Ошибка запроса к Binance: %s",
                error
            )

            if attempt == attempts:

                raise RuntimeError(
                    f"Не удалось выполнить запрос после {attempts} попыток"
                ) from error

            delay = 2 ** (attempt - 1)
            delay += random.uniform(0, 1)

            logging.warning(
                "Повтор через %.2f секунд",
                delay
            )

            time.sleep(delay)

    raise RuntimeError(
        f"Не удалось выполнить POST-запрос после {attempts} попыток"
    )


# ==================================================
# 10. ПОИСК P2P-ОБЪЯВЛЕНИЙ
# ==================================================

@bot.callback_query_handler(
    func=lambda call: call.data.startswith("trade:")
)
def trade_callback(call):

    bot.answer_callback_query(call.id)

    try:
        _, trade_type, coin = call.data.split(":")

        if trade_type not in ("BUY", "SELL"):
            raise ValueError("Недопустимое направление сделки")

        user_id = call.from_user.id

        min_finish_rate = get_min_finish_rate(user_id)
        min_amount_cny = get_min_amount_cny(user_id)

        all_ads = []
        seen_ids = set()

        page = 1
        max_pages = 10

        # Загружаем страницы, пока не найдём 10 объявлений
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

            response = post_with_retry(API_URL, payload)

            try:
                data = response.json()

            except requests.exceptions.JSONDecodeError:

                logging.error(
                    "Binance вернула некорректный JSON"
                )

                bot.send_message(
                    call.message.chat.id,
                    "Binance вернула некорректный ответ. Попробуй позже."
                )
                return

            if not isinstance(data, dict):
                raise ValueError(
                    "Неожиданный формат ответа Binance"
                )

            ads = data.get("data", [])

            if not isinstance(ads, list):
                raise ValueError(
                    "Не удалось прочитать список объявлений"
                )

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

                    finish_rate = float(
                        advertiser.get("monthFinishRate")
                    )

                    min_amount = ad.get(
                        "minSingleTransAmount", "?"
                    )

                    min_single_amount = float(min_amount)

                    available = float(
                        ad.get("surplusAmount", 0)
                    )

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

        # ==================================================
        # 11. ФОРМИРОВАНИЕ РЕЗУЛЬТАТА
        # ==================================================

        if all_ads:

            all_ads.sort(
                key=lambda item: float(item["adv"]["price"]),
                reverse=(trade_type == "SELL")
            )

            action = (
                "покупку"
                if trade_type == "BUY"
                else "продажу"
            )

            text = (
                f"Объявления на {action} {coin} найдены!\n\n"
            )

            for shown_count, item in enumerate(
                all_ads[:10],
                start=1
            ):

                ad = item.get("adv", {})
                advertiser = item.get("advertiser", {})

                price = float(ad["price"])

                nickname = advertiser.get(
                    "nickName", "Не указан"
                )

                finish_rate = float(
                    advertiser["monthFinishRate"]
                )

                if 0 <= finish_rate <= 1:
                    finish_rate *= 100

                min_amount = ad.get(
                    "minSingleTransAmount", "?"
                )

                max_amount = ad.get(
                    "maxSingleTransAmount", "?"
                )

                available = float(
                    ad.get("surplusAmount", 0)
                )

                finish_rate_text = f"{finish_rate:.1f}%"

                text += (
                    f"{shown_count}. Цена: {price} CNY\n"
                    f"   Контрагент: {nickname}\n\n"
                    f"   Лимиты: {min_amount}–{max_amount} CNY\n"
                    f"   Доступно: {available} {coin}\n\n"
                    f"   Завершение сделок: {finish_rate_text}\n\n"
                )

            bot.send_message(
                call.message.chat.id,
                text
            )

        else:

            bot.send_message(
                call.message.chat.id,
                f"Для {coin}/CNY не найдено объявлений, "
                "подходящих под заданные фильтры."
            )

    # ==================================================
    # 12. ОБРАБОТКА ОШИБОК
    # ==================================================

    except requests.exceptions.Timeout:

        logging.exception(
            "Время ожидания ответа Binance истекло"
        )

        bot.send_message(
            call.message.chat.id,
            "Binance долго не отвечает. Попробуй позже."
        )

    except requests.exceptions.ConnectionError:

        logging.exception(
            "Ошибка подключения к Binance"
        )

        bot.send_message(
            call.message.chat.id,
            "Не удалось подключиться к Binance. Проверь интернет."
        )

    except requests.exceptions.HTTPError:

        logging.exception(
            "HTTP-ошибка Binance"
        )

        bot.send_message(
            call.message.chat.id,
            "Binance вернула ошибку сервера. Попробуй позже."
        )

    except requests.exceptions.RequestException:

        logging.exception(
            "Ошибка HTTP-запроса"
        )

        bot.send_message(
            call.message.chat.id,
            "Не удалось получить объявления. Попробуй позже."
        )

    except ValueError:

        logging.exception(
            "Некорректные данные Binance или параметры запроса"
        )

        bot.send_message(
            call.message.chat.id,
            "Получены некорректные данные. Попробуй позже."
        )

    except RuntimeError:

        logging.exception(
            "Не удалось выполнить запрос к Binance"
        )

        bot.send_message(
            call.message.chat.id,
            "Не удалось получить объявления. Попробуй позже."
        )

    except Exception:

        logging.exception(
            "Непредвиденная ошибка при поиске объявлений"
        )

        bot.send_message(
            call.message.chat.id,
            "Произошла внутренняя ошибка. Попробуй позже."
        )


# ==================================================
# 13. ЗАПУСК БОТА
# ==================================================

if __name__ == "__main__":

    init_database()

    logging.info("P2P Tracker запущен")

    bot.infinity_polling()
