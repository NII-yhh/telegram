import logging
import time

from database import (
    get_active_subscriptions,
    get_seen_ads,
    save_seen_ad,
    get_subscriptions_by_trade,
    add_notification,
    get_pending_notifications,
    mark_notification_sent,
    increment_notification_attempts,
    save_notification_error,
    mark_notification_failed
)
from services.ads import format_trade_message
from services.binance import get_binance_ads
from services.notifications import is_temporary_error

def send_pending_notifications(bot):
    notifications = get_pending_notifications()

    for notification_id, user_id, message_text, attempts in notifications:
        if attempts >= 5:
          failed =   mark_notification_failed(notification_id)

          if failed:
              logging.warning(
                  f"Уведомление {notification_id} помечено как неудачное: "
                  f"исчерпан лимит попыток"
              )
          else:
              logging.error(
                  f"Не удалось пометить уведомление {notification_id} как неудачное"
              )

          continue

        try:

            bot.send_message(user_id, message_text)

            marked = mark_notification_sent(notification_id)

            if marked:
                logging.info(
                    f"Уведомление {notification_id} отправлено "
                    f"пользователю {user_id}"
                )
            else:
                logging.warning(
                    f"Не удалось обновить статус уведомления "
                    f"{notification_id}"
                )



        except Exception as error:
            attempts= increment_notification_attempts(notification_id)
            if attempts is None:
                logging.error(
                    f"Не удалось обновить счётчик попыток уведомления {notification_id}"
                )
                continue


            try:
                save_notification_error(notification_id, str(error))
            except Exception:
                logging.exception(
                    f"Не удалось сохранить ошибку уведомления {notification_id}"
                )

            if not is_temporary_error(error) or attempts >= 5:
                try:
                    failed = mark_notification_failed(notification_id)

                    if failed:
                        logging.warning(
                            f"Уведомление {notification_id} "
                            f"помечено как окончательно неудачное"
                        )
                    else:
                        logging.warning(
                            f"Не удалось изменить статус уведомления {notification_id}"
                        )

                except Exception:
                    logging.exception(
                        f"Не удалось пометить уведомление {notification_id} как неудачное"
                    )

def run_monitoring_cycle(bot):
    while True:
        try:
            subscriptions = get_active_subscriptions()
            pairs = set()

            for pair in subscriptions:
                pairs.add((pair[2], pair[3]))

            for pair in pairs:
                coin = pair[0]
                trade_type = pair[1]
                seen_ids = get_seen_ads(coin, trade_type)


                payload = {
                    "page": 1,
                    "rows": 10,
                    "payTypes": [],
                    "asset": coin,
                    "fiat": "CNY",
                    "tradeType": trade_type
                }

                ads = get_binance_ads(payload)

                for item in ads:
                    ad_id = item["adv"]["advNo"]

                    if ad_id not in seen_ids:
                        subscribers = get_subscriptions_by_trade(
                            coin, trade_type
                        )

                        # Сначала добавляем уведомления в очередь
                        for subscriber in subscribers:
                            user_id = subscriber[1]

                            message_text = format_trade_message(
                                [item],
                                coin,
                                trade_type
                            )

                            if message_text:
                                add_notification(
                                    user_id,
                                    ad_id,
                                    message_text
                                )

                        # Затем сохраняем объявление
                        saved = save_seen_ad(
                            ad_id, coin, trade_type
                        )

                        if saved:
                            seen_ids.add(ad_id)

            # Отправляем накопленные уведомления
            send_pending_notifications(bot)

        except Exception:
            logging.exception("Ошибка цикла мониторинга")




        time.sleep(60)
