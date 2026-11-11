from database import (
    init_db,
    get_user_settings,
    save_min_finish_rate,
    save_min_amount_cny
)

init_db()

test_user_id = 999999999

print("Исходные настройки:")
print(get_user_settings(test_user_id))

save_min_finish_rate(test_user_id, 98)
save_min_amount_cny(test_user_id, 500)

print("Обновлённые настройки:")
print(get_user_settings(test_user_id))
import sqlite3
from config import DB_PATH

with sqlite3.connect(DB_PATH) as connection:
    connection.execute(
        "DELETE FROM user_settings WHERE user_id = ?",
        (test_user_id,)
    )

print("Тестовый пользователь удалён.")