
from services.binance import get_binance_ads
from services.ads import filter_ads, get_ad_price


def load_trade_ads(
    coin,
    trade_type,
    min_finish_rate,
    min_amount_cny,
    limit=10,
    max_pages=10
):
    all_ads = []
    seen_ids = set()

    for page in range(1, max_pages + 1):

        if len(all_ads) >= limit:
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

        filtered_ads = filter_ads(
            ads,
            min_finish_rate,
            min_amount_cny,
            seen_ids
        )

        remaining = limit - len(all_ads)
        all_ads.extend(filtered_ads[:remaining])

    all_ads.sort(
        key=get_ad_price,
        reverse=(trade_type == "SELL")
    )

    return all_ads
