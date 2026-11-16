from database import get_active_subscriptions
from services.binance import get_binance_ads

def run_monitoring_cycle():
    subscriptions = get_active_subscriptions()
    for subscription in subscriptions:
        print(subscription)
        user_id = subscription[1]
        coin = subscription[2]
        trade_type = subscription[3]
        payload = {
            "page": 1,
            "rows": 10,
            "payTypes": [],
            "asset": coin,
            "fiat": "CNY",
            "tradeType": trade_type
        }
        ads = get_binance_ads(payload)


