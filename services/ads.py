def convert_rate(rate):
    try:
        finish_rate = float(rate)

        if 0 <= finish_rate <= 1:
            finish_rate *= 100

        return finish_rate

    except (ValueError, TypeError):
        return 0


def get_ad_price(item):
    if not isinstance(item, dict):
        return 0

    ad = item.get("adv", {})

    if not isinstance(ad, dict):
        return 0

    try:
        price = float(ad.get("price", 0))

        if price <= 0:
            return 0

        return price

    except (ValueError, TypeError):
        return 0


def get_finish_rate(advertiser):
    if not isinstance(advertiser, dict):
        return 0

    return convert_rate(
        advertiser.get("monthFinishRate", 0)
    )


def filter_ads(ads, min_finish_rate, min_amount_cny, seen_ids):
    filtered_ads = []

    for item in ads:
        if not isinstance(item, dict):
            continue

        ad = item.get("adv", {})
        advertiser = item.get("advertiser", {})

        if not isinstance(ad, dict):
            continue

        if not isinstance(advertiser, dict):
            continue

        price = get_ad_price(item)
        finish_rate = get_finish_rate(advertiser)

        try:
            min_single_amount = float(
                ad.get("minSingleTransAmount", 0)
            )
            available = float(
                ad.get("surplusAmount", 0)
            )
        except (TypeError, ValueError):
            continue

        if price <= 0:
            continue

        if finish_rate < min_finish_rate:
            continue

        if min_single_amount < min_amount_cny:
            continue

        if available < 1:
            continue

        ad_id = ad.get("advNo")

        if not ad_id or ad_id in seen_ids:
            continue

        seen_ids.add(ad_id)
        filtered_ads.append(item)

    return filtered_ads


def format_ads(ads, coin):
    ad_lines = []

    for item in ads:
        ad = item.get("adv", {})
        advertiser = item.get("advertiser", {})

        if not isinstance(ad, dict):
            continue

        if not isinstance(advertiser, dict):
            advertiser = {}

        price = get_ad_price(item)

        if price <= 0:
            continue

        try:
            available = float(ad.get("surplusAmount", 0))
        except (TypeError, ValueError):
            continue

        nickname = advertiser.get("nickName", "Не указан")
        finish_rate = get_finish_rate(advertiser)

        min_amount = ad.get("minSingleTransAmount", "?")
        max_amount = ad.get("maxSingleTransAmount", "?")

        number = len(ad_lines) + 1

        ad_lines.append(
            f"{number}. Цена: {price} CNY\n"
            f"Контрагент: {nickname}\n"
            f"Лимиты: {min_amount}–{max_amount} CNY\n"
            f"Доступно: {available} {coin}\n"
            f"Завершение сделок: {finish_rate:.1f}%"
        )

    return ad_lines

def format_trade_message(ads, coin, trade_type):
    ad_lines = format_ads(ads, coin)

    if not ad_lines:
        return None

    action = "покупку" if trade_type == "BUY" else "продажу"

    result = (
        f"🔎 Объявления на {action} {coin}\n"
        f"Найдено: {len(ad_lines)}\n\n"
        + "\n\n".join(ad_lines)
    )

    return result