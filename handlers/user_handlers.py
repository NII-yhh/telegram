
from keyboards.user_keyboards import (

    get_coins_keyboard,
    get_trade_keyboard
)

def register_user_handlers(bot):
    @bot.message_handler(commands=["start"])
    def start_command(message):
        keyboard = get_coins_keyboard()
        with open("photo.png", "rb") as photo:
            bot.send_photo(
                message.chat.id,
                photo,
                caption=( """👋💱 P2P Tracker — мониторинг P2P-ордеров

Бот для поиска и анализа P2P-предложений по криптовалютам за китайские юани (CNY).

🇨🇳 Важно: пока бот работает только с китайским юанем (CNY). Поддержка других фиатных валют может появиться в будущих обновлениях.

🔎 Что умеет бот?

🪙 Отслеживать предложения по 10 криптовалютам.
📊 Показывать топ-10 ордеров по выбранному направлению.
💰 Помогать сравнивать цены покупки и продажи.
⚡ Упрощать поиск интересных предложений.

📌 Выбери криптовалюту, укажи направление сделки и изучи доступные ордера прямо в Telegram.

⚠️ Важно: цены и доступность предложений могут меняться. Перед сделкой проверяй условия, лимиты и репутацию контрагента на бирже. Бот не гарантирует безопасность или прибыльность сделки.

🚀 Меньше ручного поиска — больше удобства при анализе P2P-рынка!\n\n"""

                            
            "Выбери криптовалюту:"),
        reply_markup=keyboard
        )
    @bot.callback_query_handler(
        func=lambda call: call.data.startswith("coin:")
    )
    def coin_callback(call):
        parts = call.data.split(":")
        if len(parts) != 2:
            bot.answer_callback_query(
                call.id,
                "Некорректный запрос"
            )
            return
        coin = parts[1]
        from keyboards.user_keyboards import COINS
        if coin not in COINS:
            bot.answer_callback_query(
                call.id,
                "Неизвестная криптовалюта"
            )
            return
        keyboard = get_trade_keyboard(coin)
        bot.answer_callback_query(call.id)
        bot.edit_message_caption(
            f"Выбрана монета: {coin}\n\n"
            "Выбери направление торговли:",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=keyboard
        )
