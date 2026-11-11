
from telebot import types
from database import (
    get_user_settings,
    save_min_finish_rate,
    save_min_amount_cny
)
def register_settings_handlers(bot):
    @bot.message_handler(commands=["settings"])
    def settings_command(message):
        user_id = message.from_user.id
        settings = get_user_settings(user_id)
        current_rate = settings["min_finish_rate"]
        current_amount = settings["min_amount_cny"]
        rate_markup = types.InlineKeyboardMarkup(row_width=2)
        rate_buttons = [
            types.InlineKeyboardButton(
                f"{rate}%",
                callback_data=f"rate:{rate}"
            )
            for rate in [92, 94, 96, 98]
        ]
        rate_markup.add(*rate_buttons)
        bot.send_message(
            message.chat.id,
            f"⚙️ Минимальный процент завершения\n\n"
            f"Текущее значение: {current_rate}%\n"
            f"Выбери новое значение:",
            reply_markup=rate_markup
        )
        amount_markup = types.InlineKeyboardMarkup(row_width=2)
        amount_buttons = [
            types.InlineKeyboardButton(
                f"{amount} CNY",
                callback_data=f"amount:{amount}"
            )
            for amount in [100, 500, 1000, 5000]
        ]
        amount_markup.add(*amount_buttons)
        bot.send_message(
            message.chat.id,
            f"⚙️ Минимальная сумма сделки\n\n"
            f"Текущее значение: {current_amount} CNY\n"
            f"Выбери новое значение:",
            reply_markup=amount_markup
        )
    @bot.callback_query_handler(
        func=lambda call: call.data.startswith(("rate:", "amount:"))
    )
    def settings_callback(call):
        user_id = call.from_user.id
        bot.answer_callback_query(call.id)
        try:
            parts = call.data.split(":")
            if len(parts) != 2:
                raise ValueError("Некорректный формат callback")
            setting_type, value = parts
            value = int(value)
        except ValueError:
            return
        if setting_type not in ("rate", "amount"):
            return
        if setting_type == "rate":
            if value not in [92, 94, 96, 98]:
                return
            save_min_finish_rate(user_id, value)
            message = f"Минимальный процент завершения: {value}%"
        else:
            if value not in [100, 500, 1000, 5000]:
               return
            save_min_amount_cny(user_id, value)
            message = f"Минимальная сумма сделки: {value} CNY"
        bot.send_message(
            call.message.chat.id,
            f"✅ {message}"
        )
