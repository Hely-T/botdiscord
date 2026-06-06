"""
Note Service Layer
- Luu ghi chu ca nhan theo tung server vao database/notes.db
"""

from __future__ import annotations

from utils import CogDatabase, get_timestamp


class NoteService:
    def __init__(self):
        self.db = CogDatabase("notes")
        self._init_database()

    def _init_database(self):
        self.db.create_table(
            "notes",
            """
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guild_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            content TEXT NOT NULL,
            amount INTEGER,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
            """,
        )

    @staticmethod
    def _scope_guild_id(guild_id: int | None) -> int:
        return int(guild_id or 0)

    def add_note(self, guild_id: int | None, user_id: int, content: str, amount: int | None = None) -> dict | None:
        now = get_timestamp()
        self.db.insert(
            "notes",
            {
                "guild_id": self._scope_guild_id(guild_id),
                "user_id": int(user_id),
                "content": content.strip(),
                "amount": int(amount) if amount is not None else None,
                "created_at": now,
                "updated_at": now,
            },
        )
        return self.db.fetch_one("SELECT * FROM notes WHERE rowid = last_insert_rowid()")

    def list_notes(self, guild_id: int | None, user_id: int) -> list[dict]:
        return self.db.fetch(
            """
            SELECT * FROM notes
            WHERE guild_id = ? AND user_id = ?
            ORDER BY id ASC
            """,
            (self._scope_guild_id(guild_id), int(user_id)),
        )

    def get_note_at(self, guild_id: int | None, user_id: int, position: int) -> dict | None:
        notes = self.list_notes(guild_id, user_id)
        if position < 1 or position > len(notes):
            return None
        note = notes[position - 1].copy()
        note["position"] = position
        return note

    def delete_positions(self, guild_id: int | None, user_id: int, positions: list[int]) -> list[dict]:
        notes = self.list_notes(guild_id, user_id)
        deleted: list[dict] = []
        for position in sorted(set(positions), reverse=True):
            if position < 1 or position > len(notes):
                continue
            note = notes[position - 1]
            deleted.append({**note, "position": position})
            self.db.delete("notes", "id = ? AND guild_id = ? AND user_id = ?", (note["id"], self._scope_guild_id(guild_id), int(user_id)))
        return sorted(deleted, key=lambda row: row["position"])

    def adjust_amount(self, guild_id: int | None, user_id: int, position: int, delta: int) -> dict | None:
        note = self.get_note_at(guild_id, user_id, position)
        if not note:
            return None
        current_amount = int(note["amount"] or 0)
        new_amount = current_amount + int(delta)
        self.db.update(
            "notes",
            {"amount": new_amount, "updated_at": get_timestamp()},
            "id = ? AND guild_id = ? AND user_id = ?",
            (note["id"], self._scope_guild_id(guild_id), int(user_id)),
        )
        updated = self.get_note_at(guild_id, user_id, position)
        return updated
