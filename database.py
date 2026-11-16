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
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS monitoring_subscriptions (
    subscription_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    coin TEXT NOT NULL,
    trade_type TEXT NOT NULL CHECK (trade_type IN ('BUY', 'SELL')),
    is_active INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0, 1)),
    UNIQUE (user_id, coin, trade_type)
);"""
        )
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS seen_ads (
    ad_id TEXT PRIMARY KEY,
    coin TEXT NOT NULL,
    trade_type TEXT NOT NULL
);""")

def save_seen_ad(ad_id, coin, trade_type):
    with get_connection() as connection:
        cursor = connection.cursor()
        cursor.execute("""INSERT INTO seen_ads (ad_id, coin, trade_type)
VALUES (?, ?, ?)
ON CONFLICT(ad_id) DO NOTHING;""", (ad_id, coin, trade_type))
        saved = cursor.rowcount == 1
    return saved


def create_subscription(user_id, coin, trade_type):
    with get_connection() as connection:
        cursor = connection.cursor()

        cursor.execute(
            """
            INSERT INTO monitoring_subscriptions
                (user_id, coin, trade_type)
            VALUES (?, ?, ?)
            ON CONFLICT (user_id, coin, trade_type) DO NOTHING
            """,
            (user_id, coin, trade_type)
        )

        created = cursor.rowcount == 1

    return created
def get_user_subscriptions(user_id):
    with get_connection() as connection:
        cursor = connection.cursor()
        cursor.execute( """
    SELECT *
    FROM monitoring_subscriptions
    WHERE user_id = ?
    """,
    (user_id,))


        subscriptions = cursor.fetchall()

    if subscriptions:
        print("Подписки найдены")

    else:
        print("Подписок пока нет")

    return subscriptions

def deactivate_subscription(user_id, coin, trade_type):
    with get_connection() as connection:
        cursor = connection.cursor()
        cursor.execute("""UPDATE monitoring_subscriptions
SET is_active = 0
WHERE user_id = ?
AND coin = ?
AND trade_type = ?
AND is_active = 1""",
        (user_id, coin, trade_type))
        deactivated = cursor.rowcount == 1
        return deactivated


def get_active_subscriptions():
    with get_connection() as connection:
        cursor = connection.cursor()
        cursor.execute( """
        SELECT *
        FROM monitoring_subscriptions
        WHERE is_active = 1;
        """)

        subscriptions = cursor.fetchall()
        return subscriptions
def get_subscriptions_by_trade(coin, trade_type):
    with get_connection() as connection:
        cursor = connection.cursor()
        cursor.execute( """SELECT *
    FROM monitoring_subscriptions
    WHERE coin = ?
    AND trade_type = ?
    AND is_active = 1
    """,
    (coin, trade_type))
        subscriptions = cursor.fetchall()
        return subscriptions

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
