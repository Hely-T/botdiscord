from __future__ import annotations

from utils import CogDatabase, get_timestamp


DEFAULT_PLAYER_THEME = {
    "accent_color": "#7f314d",
    "background_url": "",
    "title_text": "BLACK LOUS MUSIC",
}

DEFAULT_USER_PREFERENCES = {
    "volume": 65,
}


class MusicPlayerService:
    def __init__(self):
        self.db = CogDatabase("music_player")
        self.db.create_table(
            "player_theme",
            """
            guild_id INTEGER PRIMARY KEY,
            accent_color TEXT NOT NULL DEFAULT '#7f314d',
            background_url TEXT DEFAULT '',
            title_text TEXT NOT NULL DEFAULT 'BLACK LOUS MUSIC',
            updated_at TEXT
            """,
        )
        self.db.create_table(
            "user_preferences",
            """
            user_id INTEGER PRIMARY KEY,
            volume INTEGER NOT NULL DEFAULT 65,
            updated_at TEXT
            """,
        )

    def get_theme(self, guild_id: int) -> dict:
        saved = self.db.select_one("player_theme", "guild_id = ?", (int(guild_id),)) or {}
        return {**DEFAULT_PLAYER_THEME, **saved}

    def set_theme(self, guild_id: int, **values) -> dict:
        guild_id = int(guild_id)
        allowed = {key: str(value) for key, value in values.items() if key in DEFAULT_PLAYER_THEME}
        if not allowed:
            return self.get_theme(guild_id)
        allowed["updated_at"] = get_timestamp()
        if self.db.select_one("player_theme", "guild_id = ?", (guild_id,)):
            self.db.update("player_theme", allowed, "guild_id = ?", (guild_id,))
        else:
            self.db.insert("player_theme", {"guild_id": guild_id, **DEFAULT_PLAYER_THEME, **allowed})
        return self.get_theme(guild_id)

    def reset_theme(self, guild_id: int) -> dict:
        self.db.delete("player_theme", "guild_id = ?", (int(guild_id),))
        return self.get_theme(guild_id)

    def get_user_preferences(self, user_id: int) -> dict:
        saved = self.db.select_one(
            "user_preferences",
            "user_id = ?",
            (int(user_id),),
        ) or {}
        preferences = {**DEFAULT_USER_PREFERENCES, **saved}
        preferences["volume"] = max(0, min(200, int(preferences["volume"])))
        return preferences

    def set_user_preferences(self, user_id: int, **values) -> dict:
        user_id = int(user_id)
        allowed = {}
        if "volume" in values:
            allowed["volume"] = max(0, min(200, int(values["volume"])))
        if not allowed:
            return self.get_user_preferences(user_id)

        allowed["updated_at"] = get_timestamp()
        if self.db.select_one("user_preferences", "user_id = ?", (user_id,)):
            self.db.update("user_preferences", allowed, "user_id = ?", (user_id,))
        else:
            self.db.insert(
                "user_preferences",
                {
                    "user_id": user_id,
                    **DEFAULT_USER_PREFERENCES,
                    **allowed,
                },
            )
        return self.get_user_preferences(user_id)
