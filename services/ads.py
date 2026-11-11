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