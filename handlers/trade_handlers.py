

import logging
import requests

from database import get_user_settings
from services.binance import get_binance_ads
from services.ads import (
    get_ad_price,
    filter_ads,
    format_ads
)
from keyboards.user_keyboards import COINS


def register_trade_handlers(bot):

    @bot.callback_query_handler(
        func=lambda call: call.data.startswith("trade:")
    )
    def trade_callback(call):

        bot.answer_callback_query(call.id)

        try:
            parts = call.data.split(":")

            if len(parts) != 3:
                raise ValueError("Некорректный формат callback")

            _, trade_type, coin = parts

            if coin not in COINS:
                raise ValueError("Неизвестная криптовалюта")

            if trade_type not in ("BUY", "SELL"):
                raise ValueError("Неизвестное направление торговли")

            user_id = call.from_user.id

            # Получаем настройки пользователя
            settings = get_user_settings(user_id)

            min_finish_rate = settings["min_finish_rate"]
            min_amount_cny = settings["min_amount_cny"]

            all_ads = []
            seen_ids = set()

            max_pages = 10

            # Загружаем объявления Binance
            for page in range(1, max_pages + 1):

                if len(all_ads) >= 10:
                    break

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

                ads = get_binance_ads(payload)

                if not ads:
                    break

                # Фильтруем объявления
                filtered_ads = filter_ads(
                    ads,
                    min_finish_rate,
                    min_amount_cny,
                    seen_ids
                )

                for item in filtered_ads:
                    all_ads.append(item)

                    if len(all_ads) >= 10:
                        break

            if not all_ads:
                bot.send_message(
                    call.message.chat.id,
                    f"Для {coin}/CNY не найдено подходящих объявлений."
                )
                return

            # Сортируем объявления по цене
            all_ads.sort(
                key=get_ad_price,
                reverse=(trade_type == "SELL")
            )

            action = "покупку" if trade_type == "BUY" else "продажу"

            # Формируем список объявлений
            ad_lines = format_ads(all_ads, coin)

            if not ad_lines:
                bot.send_message(
                    call.message.chat.id,
                    f"Для {coin}/CNY не найдено подходящих объявлений."
                )
                return

            result = (
                f"🔎 Объявления на {action} {coin}\n"
                f"Найдено: {len(ad_lines)}\n\n"
                + "\n\n".join(ad_lines)
            )

            bot.send_message(call.message.chat.id, result)

        except requests.RequestException:
            logging.exception("Ошибка запроса к Binance")

            bot.send_message(
                call.message.chat.id,
                "Не удалось получить объявления. Попробуй позже."
            )

        except (ValueError, TypeError, KeyError):
            logging.exception("Ошибка обработки объявлений Binance")

            bot.send_message(
                call.message.chat.id,
                "Binance вернула некорректные данные."
            )

        except Exception:
            logging.exception("Неожиданная ошибка trade_callback")

            bot.send_message(
                call.message.chat.id,
                "Произошла внутренняя ошибка."
            )
