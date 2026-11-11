from contextlib import contextmanager
import sqlite3

from config import DB_PATH


@contextmanager
def get_connection():
    connection = sqlite3.connect(DB_PATH)

    try:
        yield connection
        connection.commit()

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()
def init_db():
    with get_connection() as connection:
        cursor = connection.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_settings (
                user_id INTEGER PRIMARY KEY,
                min_finish_rate INTEGER DEFAULT 95,
                min_amount_cny INTEGER DEFAULT 100
            )
        """)


def get_users_count():
    with get_connection() as connection:
        cursor = connection.cursor()

        cursor.execute("SELECT COUNT(*) FROM user_settings")

        return cursor.fetchone()[0]

def get_user_settings(user_id):
    with get_connection() as connection:
        cursor = connection.cursor()

        # Создаём пользователя, если его ещё нет
        cursor.execute(
            """
            INSERT OR IGNORE INTO user_settings (user_id)
            VALUES (?)
            """,
            (user_id,)
        )

        # Получаем настройки пользователя
        cursor.execute(
            """
            SELECT min_finish_rate, min_amount_cny
            FROM user_settings
            WHERE user_id = ?
            """,
            (user_id,)
        )

        settings = cursor.fetchone()
        if settings is None:
            raise ValueError("Не удалось получить настройки пользователя")

        return {
            "min_finish_rate": settings[0],
            "min_amount_cny": settings[1]
        }

def save_min_finish_rate(user_id, min_finish_rate):
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO user_settings (user_id, min_finish_rate)
            VALUES (?, ?)
            ON CONFLICT(user_id)
            DO UPDATE SET min_finish_rate = excluded.min_finish_rate
            """,
            (user_id, min_finish_rate)
        )


def save_min_amount_cny(user_id, min_amount_cny):
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO user_settings (user_id, min_amount_cny)
            VALUES (?, ?)
            ON CONFLICT(user_id)
            DO UPDATE SET min_amount_cny = excluded.min_amount_cny
            """,
            (user_id, min_amount_cny)
        )
