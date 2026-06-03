"""
Bot Settings Service
- Lưu các cài đặt global của bot
"""

from __future__ import annotations

from config import BOT_PREFIX
from utils import CogDatabase, get_timestamp


class SettingsService:
    def __init__(self):
        self.db = CogDatabase("bot_settings")
        self._init_database()

    def _init_database(self):
        self.db.create_table(
            "settings",
            """
            setting_key TEXT PRIMARY KEY,
            setting_value TEXT NOT NULL,
            updated_at TEXT NOT NULL
            """,
        )
        if self.db.select_one("settings", "setting_key = ?", ("prefix",)) is None:
            self.set_prefix(BOT_PREFIX)

    def get_setting(self, key: str, default: str | None = None) -> str | None:
        result = self.db.select_one("settings", "setting_key = ?", (key,))
        if not result:
            return default
        return result["setting_value"]

    def set_setting(self, key: str, value: str) -> bool:
        existing = self.db.select_one("settings", "setting_key = ?", (key,))
        payload = {
            "setting_value": value,
            "updated_at": get_timestamp(),
        }
        if existing:
            return self.db.update("settings", payload, "setting_key = ?", (key,))
        return self.db.insert(
            "settings",
            {
                "setting_key": key,
                "setting_value": value,
                "updated_at": get_timestamp(),
            },
        )

    def get_prefix(self) -> str:
        return str(self.get_setting("prefix", BOT_PREFIX))

    def set_prefix(self, prefix: str) -> bool:
        prefix = prefix.strip()
        if not prefix:
            raise ValueError("Prefix không được để trống")
        return self.set_setting("prefix", prefix)
