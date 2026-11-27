
import logging
import time

from database import (
    get_active_subscriptions,
    get_seen_ads,
    save_seen_ad,
    get_subscriptions_by_trade,
    add_notification,
    mark_notification_sent,
    increment_notification_attempts,
    save_notification_error,
    mark_notification_failed,
    claim_pending_notifications,
    release_notification,
    recover_stuck_notifications,
)

from services.ads import format_trade_message
from services.binance import get_binance_ads
from services.notifications import is_temporary_error


def send_pending_notifications(bot):
    notifications = claim_pending_notifications()

    for notification_id, user_id, message_text, attempts in notifications:

        # Проверяем лимит попыток до отправки
        if attempts >= 5:
            try:
                failed = mark_notification_failed(notification_id)

                if failed:
                    logging.warning(
                        f"Уведомление {notification_id} помечено как неудачное: "
                        "исчерпан лимит попыток"
                    )
                else:
                    logging.error(
                        f"Не удалось пометить уведомление {notification_id} "
                        "как неудачное"
                    )

            except Exception:
                logging.exception(
                    f"Ошибка при изменении статуса уведомления {notification_id}"
                )

            continue

        # Часть 1. Отправка сообщения Telegram
        try:
            bot.send_message(user_id, message_text)

        except Exception as error:
            # Увеличиваем количество неудачных попыток
            try:
                attempts = increment_notification_attempts(notification_id)
            except Exception:
                logging.exception(
                    f"Ошибка при увеличении счётчика попыток уведомления "
                    f"{notification_id}"
                )
                attempts = None

            if attempts is None:
                logging.error(
                    f"Не удалось обновить счётчик попыток уведомления "
                    f"{notification_id}"
                )

                try:
                    released = release_notification(notification_id)

                    if released:
                        logging.info(
                            f"Уведомление {notification_id} освобождено "
                            "после ошибки обновления счётчика попыток"
                        )
                    else:
                        logging.error(
                            f"Не удалось освободить уведомление {notification_id}"
                        )

                except Exception:
                    logging.exception(
                        f"Ошибка при освобождении уведомления {notification_id}"
                    )

                continue

            # Сохраняем текст ошибки
            try:
                saved = save_notification_error(
                    notification_id,
                    str(error)
                )

                if not saved:
                    logging.warning(
                        f"Не удалось сохранить ошибку уведомления {notification_id}"
                    )

            except Exception:
                logging.exception(
                    f"Ошибка сохранения текста ошибки уведомления {notification_id}"
                )

            # Определяем, можно ли повторить отправку
            if not is_temporary_error(error) or attempts >= 5:
                try:
                    failed = mark_notification_failed(notification_id)

                    if failed:
                        logging.warning(
                            f"Уведомление {notification_id} "
                            "помечено как окончательно неудачное"
                        )
                    else:
                        logging.error(
                            f"Не удалось изменить статус уведомления {notification_id}"
                        )

                except Exception:
                    logging.exception(
                        f"Не удалось пометить уведомление {notification_id} "
                        "как неудачное"
                    )

            else:
                try:
                    released = release_notification(notification_id)

                    if released:
                        logging.info(
                            f"Уведомление {notification_id} освобождено "
                            "и возвращено в очередь"
                        )
                    else:
                        logging.warning(
                            f"Не удалось освободить уведомление {notification_id}"
                        )

                except Exception:
                    logging.exception(
                        f"Ошибка при освобождении уведомления {notification_id}"
                    )

            continue

        # Часть 2. Обновление статуса в SQLite после успешной отправки
        try:
            marked = mark_notification_sent(notification_id)

            if marked:
                logging.info(
                    f"Уведомление {notification_id} отправлено "
                    f"пользователю {user_id}"
                )
            else:
                logging.error(
                    f"Не удалось обновить статус отправленного уведомления "
                    f"{notification_id}. Сообщение уже могло быть доставлено "
                    f"пользователю {user_id}"
                )

        except Exception:
            logging.exception(
                f"Ошибка SQLite при обновлении статуса уведомления "
                f"{notification_id}. Сообщение уже могло быть доставлено "
                f"пользователю {user_id}"
            )


def run_monitoring_cycle(bot):
    while True:
        try:
            subscriptions = get_active_subscriptions()
            pairs = set()

            # Получаем уникальные пары монет и типов торговли
            for pair in subscriptions:
                pairs.add((pair[2], pair[3]))

            for coin, trade_type in pairs:
                seen_ids = get_seen_ads(coin, trade_type)

                payload = {
                    "page": 1,
                    "rows": 10,
                    "payTypes": [],
                    "asset": coin,
                    "fiat": "CNY",
                    "tradeType": trade_type,
                }

                ads = get_binance_ads(payload)

                for item in ads:
                    ad_id = item["adv"]["advNo"]

                    if ad_id not in seen_ids:
                        subscribers = get_subscriptions_by_trade(
                            coin,
                            trade_type,
                        )

                        for subscriber in subscribers:
                            user_id = subscriber[1]

                            message_text = format_trade_message(
                                [item],
                                coin,
                                trade_type,
                            )

                            if message_text:
                                add_notification(
                                    user_id,
                                    ad_id,
                                    message_text,
                                )

                        saved = save_seen_ad(
                            ad_id,
                            coin,
                            trade_type,
                        )

                        if saved:
                            seen_ids.add(ad_id)
            recover_stuck_notifications()
            # Отправляем накопленные уведомления
            send_pending_notifications(bot)

        except Exception:
            logging.exception("Ошибка цикла мониторинга")

        time.sleep(60)
