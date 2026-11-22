
import logging
import time

from database import (
    get_active_subscriptions,
    get_seen_ads,
    save_seen_ad,
    get_subscriptions_by_trade,
    add_notification,
get_pending_notifications,
mark_notification_sent
)
from services.ads import format_trade_message
from services.binance import get_binance_ads


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
                        saved = save_seen_ad(ad_id, coin, trade_type)

                        if saved:
                            seen_ids.add(ad_id)
                            subscribers = get_subscriptions_by_trade(
                                coin, trade_type
                            )

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

        except Exception:
            logging.exception("Ошибка цикла мониторинга")

        time.sleep(60)
def send_pending_notifications(bot):
    notifications = get_pending_notifications()
    for  notification_id, user_id, message_text in notifications:
        try:
            bot.send_message(user_id, message_text)
            mark_notification_sent(notification_id)
        except Exception as error:
            logging.error(f"Ошибка отправки уведомления: {error}")




