from telebot.apihelper import (
    Timeout,
    ConnectionError,
    ApiTelegramException,
    ApiHTTPException
)


def is_temporary_error(error):
    if isinstance(error, (Timeout, ConnectionError)):
        return True
    if isinstance(error, ApiTelegramException):
        error_code = error.error_code
        return error_code == 429 or 500 <= error_code <= 599

    if isinstance(error, ApiHTTPException):
        status_code = error.result.status_code
        return status_code == 429 or 500 <= status_code <= 599
    return False

