
import requests
import logging
import time
import random

from config import API_URL


def post_with_retry(payload, attempts=3, timeout=20):
    if attempts < 1:
        raise ValueError("Количество попыток должно быть не меньше 1")

    retry_status_codes = (429, 500, 502, 503, 504)

    for attempt in range(1, attempts + 1):
        try:
            response = requests.post(
                API_URL,
                json=payload,
                timeout=timeout
            )

            logging.info(
                "Запрос к Binance. Попытка %s из %s. HTTP %s",
                attempt,
                attempts,
                response.status_code
            )

            if response.status_code in retry_status_codes:
                if attempt == attempts:
                    response.raise_for_status()

                retry_after = response.headers.get("Retry-After")

                try:
                    delay = float(retry_after)
                except (TypeError, ValueError):
                    delay = 2 ** (attempt - 1)

                delay += random.uniform(0, 1)

                logging.warning(
                    "Binance вернул HTTP %s. Повтор через %.2f сек.",
                    response.status_code,
                    delay
                )

                time.sleep(delay)
                continue

            response.raise_for_status()
            return response

        except (requests.Timeout, requests.ConnectionError):
            logging.exception(
                "Ошибка соединения. Попытка %s из %s",
                attempt,
                attempts
            )

            if attempt == attempts:
                raise

            delay = 2 ** (attempt - 1) + random.uniform(0, 1)
            time.sleep(delay)


def get_binance_ads(payload):
    response = post_with_retry(payload)
    data = response.json()

    if not isinstance(data, dict):
        raise ValueError("Неожиданный формат ответа Binance")

    ads = data.get("data", [])

    if not isinstance(ads, list):
        raise ValueError("Некорректный список объявлений")

    return ads


