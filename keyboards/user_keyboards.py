
from telebot import types


COINS = [
    "BTC", "ETH",
    "USDT", "BNB",
    "USDC", "XRP",
    "SOL", "DOGE",
    "TRX", "ADA"
]


def get_coins_keyboard():
    keyboard = types.InlineKeyboardMarkup(row_width=2)

    buttons = []

    for coin in COINS:
        buttons.append(
            types.InlineKeyboardButton(
                text=coin,
                callback_data=f"coin:{coin}"
            )
        )

    keyboard.add(*buttons)

    return keyboard


def get_trade_keyboard(coin):
    keyboard = types.InlineKeyboardMarkup(row_width=2)

    buy_button = types.InlineKeyboardButton(
        text="🟢 BUY",
        callback_data=f"trade:BUY:{coin}"
    )

    sell_button = types.InlineKeyboardButton(
        text="🔴 SELL",
        callback_data=f"trade:SELL:{coin}"
    )

    keyboard.add(buy_button, sell_button)

    return keyboard
