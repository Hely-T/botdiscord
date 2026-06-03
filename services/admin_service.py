"""
Bot Admin Service
- Quản lý admin cứng từ env
- Quản lý admin mềm từ database
"""

from __future__ import annotations

from typing import List, Dict

from config import DISCORD_OWNER_IDS
from utils import CogDatabase, get_timestamp


class AdminService:
    def __init__(self):
        self.db = CogDatabase('bot_admins')
        self._init_database()

    def _init_database(self):
        self.db.create_table('admins', '''
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE NOT NULL,
            added_by INTEGER NOT NULL,
            created_at TEXT NOT NULL
        ''')

    def is_hard_admin(self, user_id: int) -> bool:
        return user_id in DISCORD_OWNER_IDS

    def is_admin(self, user_id: int) -> bool:
        if self.is_hard_admin(user_id):
            return True
        return self.db.select_one('admins', 'user_id = ?', (user_id,)) is not None

    def add_admin(self, user_id: int, added_by: int) -> bool:
        if self.is_hard_admin(user_id):
            raise ValueError("User này là hard admin từ .env, không cần thêm vào DB")

        existing = self.db.select_one('admins', 'user_id = ?', (user_id,))
        if existing:
            raise ValueError("User này đã là admin trong DB")

        return self.db.insert('admins', {
            'user_id': user_id,
            'added_by': added_by,
            'created_at': get_timestamp(),
        })

    def remove_admin(self, user_id: int) -> bool:
        if self.is_hard_admin(user_id):
            raise ValueError("Không thể xoá hard admin từ .env")

        return self.db.delete('admins', 'user_id = ?', (user_id,))

    def get_admins(self) -> List[Dict]:
        return self.db.fetch('SELECT * FROM admins ORDER BY created_at DESC')
