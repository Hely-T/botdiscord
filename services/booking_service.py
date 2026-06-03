"""
Booking Service Layer
- Lưu booking stats cho user
- Lưu inventory quà cho các hệ thống tương lai như marry
"""

from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP

from utils import CogDatabase, get_timestamp


DEFAULT_GIFTS = [
    ("blind_box", "Blind Box"),
    ("ring", "Nhẫn"),
    ("marry_ring", "Nhẫn Marry"),
]

DEFAULT_BOOKING_SETTINGS = {
    "hour_price_vnd": "0",
    "payout_percent": "100",
}


class BookingService:
    def __init__(self):
        self.db = CogDatabase("booking")
        self._init_database()

    def _init_database(self):
        self.db.create_table(
            "booking_stats",
            """
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE NOT NULL,
            username TEXT NOT NULL,
            booking_hours REAL DEFAULT 0,
            booking_spent_money INTEGER DEFAULT 0,
            booking_deducted_money INTEGER DEFAULT 0,
            booking_received_money INTEGER DEFAULT 0,
            booking_current_money INTEGER DEFAULT 0,
            booking_messages INTEGER DEFAULT 0,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
            """,
        )
        self.db.create_table(
            "gift_inventory",
            """
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            gift_key TEXT UNIQUE NOT NULL,
            gift_name TEXT NOT NULL,
            amount INTEGER DEFAULT 0,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
            """,
        )
        self.db.create_table(
            "booking_settings",
            """
            setting_key TEXT PRIMARY KEY,
            setting_value TEXT NOT NULL,
            updated_at TEXT NOT NULL
            """,
        )
        self.db.create_table(
            "booking_hour_details",
            """
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            hour_value REAL NOT NULL,
            count INTEGER DEFAULT 0,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            UNIQUE(user_id, hour_value)
            """,
        )
        self._ensure_schema_columns()
        self._seed_default_settings()
        self._seed_default_gifts()

    def _ensure_schema_columns(self):
        columns = {row["name"] for row in self.db.fetch("PRAGMA table_info(booking_stats)")}
        required_columns = {
            "booking_hours": "REAL DEFAULT 0",
            "booking_spent_money": "INTEGER DEFAULT 0",
            "booking_deducted_money": "INTEGER DEFAULT 0",
            "booking_received_money": "INTEGER DEFAULT 0",
            "booking_current_money": "INTEGER DEFAULT 0",
            "booking_messages": "INTEGER DEFAULT 0",
        }

        for column_name, column_sql in required_columns.items():
            if column_name not in columns:
                self.db.execute(f"ALTER TABLE booking_stats ADD COLUMN {column_name} {column_sql}")

    def _seed_default_gifts(self):
        existing = {row["gift_key"] for row in self.db.fetch("SELECT gift_key FROM gift_inventory")}
        for gift_key, gift_name in DEFAULT_GIFTS:
            if gift_key not in existing:
                self.db.insert(
                    "gift_inventory",
                    {
                        "gift_key": gift_key,
                        "gift_name": gift_name,
                        "amount": 0,
                        "created_at": get_timestamp(),
                        "updated_at": get_timestamp(),
                    },
                )

    def _seed_default_settings(self):
        for setting_key, setting_value in DEFAULT_BOOKING_SETTINGS.items():
            if self.db.select_one("booking_settings", "setting_key = ?", (setting_key,)) is None:
                self.db.insert(
                    "booking_settings",
                    {
                        "setting_key": setting_key,
                        "setting_value": setting_value,
                        "updated_at": get_timestamp(),
                    },
                )

    def get_setting(self, key: str, default: str | None = None) -> str | None:
        result = self.db.select_one("booking_settings", "setting_key = ?", (key,))
        return result["setting_value"] if result else default

    def set_setting(self, key: str, value: str) -> bool:
        payload = {
            "setting_value": str(value),
            "updated_at": get_timestamp(),
        }
        if self.db.select_one("booking_settings", "setting_key = ?", (key,)):
            return self.db.update("booking_settings", payload, "setting_key = ?", (key,))
        return self.db.insert(
            "booking_settings",
            {
                "setting_key": key,
                **payload,
            },
        )

    def get_hour_price_vnd(self) -> int:
        return int(self.get_setting("hour_price_vnd", DEFAULT_BOOKING_SETTINGS["hour_price_vnd"]))

    def set_hour_price_vnd(self, amount: int) -> bool:
        if amount < 0:
            raise ValueError("Giá booking không thể âm")
        return self.set_setting("hour_price_vnd", str(int(amount)))

    def get_payout_percent(self) -> Decimal:
        return Decimal(str(self.get_setting("payout_percent", DEFAULT_BOOKING_SETTINGS["payout_percent"])))

    def set_payout_percent(self, percent: Decimal) -> bool:
        if percent < 0 or percent > 100:
            raise ValueError("Phần trăm trả tiền phải nằm trong khoảng 0-100")
        return self.set_setting("payout_percent", str(percent))

    def set_fee_percent(self, percent: Decimal) -> bool:
        if percent < 0 or percent > 100:
            raise ValueError("Phần trăm ăn phải nằm trong khoảng 0-100")
        return self.set_payout_percent(Decimal("100") - percent)

    def get_booking_config(self) -> dict:
        payout_percent = self.get_payout_percent()
        return {
            "hour_price_vnd": self.get_hour_price_vnd(),
            "payout_percent": payout_percent,
            "fee_percent": Decimal("100") - payout_percent,
        }

    def calculate_session_money(self, hours: float) -> dict:
        if hours <= 0:
            raise ValueError("Hours phải > 0")
        hour_price = Decimal(self.get_hour_price_vnd())
        total_price = hour_price * Decimal(str(hours))
        payout = total_price * self.get_payout_percent() / Decimal("100")
        return {
            "spent_money": int(total_price.to_integral_value(rounding=ROUND_HALF_UP)),
            "received_money": int(payout.to_integral_value(rounding=ROUND_HALF_UP)),
        }

    def get_booking(self, user_id: int) -> dict | None:
        return self.db.select_one("booking_stats", "user_id = ?", (user_id,))

    def get_or_create_booking(self, user_id: int, username: str) -> dict:
        booking = self.get_booking(user_id)
        if booking:
            if booking["username"] != username:
                self.db.update(
                    "booking_stats",
                    {"username": username, "updated_at": get_timestamp()},
                    "user_id = ?",
                    (user_id,),
                )
            return self.get_booking(user_id)

        self.db.insert(
            "booking_stats",
            {
                "user_id": user_id,
                "username": username,
                "booking_hours": 0,
                "booking_spent_money": 0,
                "booking_deducted_money": 0,
                "booking_received_money": 0,
                "booking_current_money": 0,
                "booking_messages": 0,
                "created_at": get_timestamp(),
                "updated_at": get_timestamp(),
            },
        )
        return self.get_booking(user_id)

    def _recalc_current_money(self, user_id: int):
        booking = self.get_booking(user_id)
        if not booking:
            return
        current_money = int(booking["booking_received_money"]) - int(booking["booking_deducted_money"])
        self.db.update(
            "booking_stats",
            {
                "booking_current_money": current_money,
                "updated_at": get_timestamp(),
            },
            "user_id = ?",
            (user_id,),
        )

    def add_booking_hours(self, user_id: int, username: str, hours: float):
        if hours <= 0:
            raise ValueError("Hours phải > 0")
        booking = self.get_or_create_booking(user_id, username)
        new_hours = float(booking["booking_hours"]) + float(hours)
        self.db.update(
            "booking_stats",
            {"booking_hours": new_hours, "updated_at": get_timestamp()},
            "user_id = ?",
            (user_id,),
        )

    def add_booking_hour_detail(self, user_id: int, hours: float):
        if hours <= 0:
            raise ValueError("Hours phải > 0")
        hour_value = round(float(hours), 2)
        existing = self.db.select_one(
            "booking_hour_details",
            "user_id = ? AND hour_value = ?",
            (user_id, hour_value),
        )
        timestamp = get_timestamp()
        if existing:
            self.db.update(
                "booking_hour_details",
                {
                    "count": int(existing["count"]) + 1,
                    "updated_at": timestamp,
                },
                "user_id = ? AND hour_value = ?",
                (user_id, hour_value),
            )
            return

        self.db.insert(
            "booking_hour_details",
            {
                "user_id": user_id,
                "hour_value": hour_value,
                "count": 1,
                "created_at": timestamp,
                "updated_at": timestamp,
            },
        )

    def get_booking_hour_details(self, user_id: int) -> list:
        return self.db.fetch(
            """
            SELECT hour_value, count
            FROM booking_hour_details
            WHERE user_id = ?
            ORDER BY hour_value ASC
            """,
            (user_id,),
        )

    def add_booking_session(self, user_id: int, username: str, hours: float) -> dict:
        money = self.calculate_session_money(hours)
        self.add_booking_hours(user_id, username, hours)
        self.add_booking_hour_detail(user_id, hours)
        if money["spent_money"] > 0:
            self.add_booking_spent_money(user_id, username, money["spent_money"])
        if money["received_money"] > 0:
            self.add_booking_received_money(user_id, username, money["received_money"])
        return money

    def add_booking_spent_money(self, user_id: int, username: str, amount: int):
        if amount <= 0:
            raise ValueError("Amount phải > 0")
        booking = self.get_or_create_booking(user_id, username)
        new_value = int(booking["booking_spent_money"]) + int(amount)
        self.db.update(
            "booking_stats",
            {"booking_spent_money": new_value, "updated_at": get_timestamp()},
            "user_id = ?",
            (user_id,),
        )
        self._recalc_current_money(user_id)

    def add_booking_deducted_money(self, user_id: int, username: str, amount: int):
        if amount <= 0:
            raise ValueError("Amount phải > 0")
        booking = self.get_or_create_booking(user_id, username)
        new_value = int(booking["booking_deducted_money"]) + int(amount)
        self.db.update(
            "booking_stats",
            {"booking_deducted_money": new_value, "updated_at": get_timestamp()},
            "user_id = ?",
            (user_id,),
        )
        self._recalc_current_money(user_id)

    def add_booking_received_money(self, user_id: int, username: str, amount: int):
        if amount <= 0:
            raise ValueError("Amount phải > 0")
        booking = self.get_or_create_booking(user_id, username)
        new_value = int(booking["booking_received_money"]) + int(amount)
        self.db.update(
            "booking_stats",
            {"booking_received_money": new_value, "updated_at": get_timestamp()},
            "user_id = ?",
            (user_id,),
        )
        self._recalc_current_money(user_id)

    def add_booking_message(self, user_id: int, username: str):
        booking = self.get_or_create_booking(user_id, username)
        new_value = int(booking["booking_messages"]) + 1
        self.db.update(
            "booking_stats",
            {"booking_messages": new_value, "updated_at": get_timestamp()},
            "user_id = ?",
            (user_id,),
        )

    def get_top_bookers(self, limit: int = 10) -> list:
        return self.db.fetch(
            """
            SELECT *
            FROM booking_stats
            ORDER BY booking_hours DESC, booking_received_money DESC, booking_messages DESC
            LIMIT ?
            """,
            (limit,),
        )

    def get_top_booking_hours(self, limit: int = 10) -> list:
        return self.db.fetch(
            """
            SELECT *
            FROM booking_stats
            ORDER BY booking_hours DESC, booking_received_money DESC, booking_messages DESC
            LIMIT ?
            """,
            (limit,),
        )

    def get_top_recharges(self, limit: int = 10) -> list:
        return self.db.fetch(
            """
            SELECT *
            FROM booking_stats
            ORDER BY booking_received_money DESC, booking_hours DESC, booking_messages DESC
            LIMIT ?
            """,
            (limit,),
        )

    def get_all_bookings(self) -> list:
        return self.db.fetch(
            """
            SELECT *
            FROM booking_stats
            ORDER BY booking_received_money DESC, booking_hours DESC, username ASC
            """
        )

    def get_gifts(self) -> list:
        return self.db.fetch(
            "SELECT * FROM gift_inventory ORDER BY amount DESC, gift_name ASC"
        )

    def get_total_gifts(self) -> int:
        result = self.db.fetch_one("SELECT COALESCE(SUM(amount), 0) AS total_gifts FROM gift_inventory")
        return int(result["total_gifts"]) if result else 0
