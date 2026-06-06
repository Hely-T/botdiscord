# File: ui/ticket/emoji.py
# Purpose: Cung cấp emoji/icon cho hệ thống Ticket UI.
# Notes:
# - Không chứa business logic ngoài phạm vi ticket.
# - Không hardcode emoji UI trong code; emoji phải đi qua module này.
# - Custom emoji Discord được ưu tiên hơn fallback. Đây là file DUY NHẤT được chứa unicode.

from __future__ import annotations

import os
from typing import Mapping, Optional

_FALLBACK_EMOJI: Mapping[str, str] = {
    "ticket": "🎫",
    "support": "🛡️",
    "bug": "🐛",
    "report": "⚠️",
    "payment": "💳",
    "contact_admin": "👑",
    "claim": "👋",
    "close": "🔒",
    "confirm": "✅",
    "cancel": "❌",
    "add_user": "👤",
    "remove_user": "🗑️",
    "rename": "✏️",
    "log": "📁",
    "transcript": "📜",
    "warning": "⚠️",
    "success": "✅",
    "error": "❌",
    "lock": "🔒",
    "staff": "👨‍💼",
    "settings": "⚙️",
    "channel": "📺",
    "role": "🎭",
    "manage": "🛠️",
    "refresh": "🔄",
    "paste_id": "📋",
    "disable_log": "🔕",
    "disable_archive": "📂",
    "disable_transcript": "📝",
    "back": "⬅️",
    "id": "🆔",
    "open": "🔓",
    "opentime": "⏰"
}

_DEFAULT_EMOJI_NAMES: Mapping[str, str] = {k: k for k in _FALLBACK_EMOJI.keys()}

# Có thể map cấu hình ID tĩnh ở đây (Chỉ điền số ID, tuyệt đối không điền unicode hay format <:...>)
_CUSTOM_EMOJI_IDS: dict[str, str] = {}

def _env_key(key: str) -> str:
    return f"TICKET_EMOJI_{key.upper()}_ID"

def _get_custom_emoji_id(key: str) -> str:
    return os.getenv(_env_key(key), _CUSTOM_EMOJI_IDS.get(key, "")).strip()

def _build_custom_emoji(key: str, emoji_id: str) -> Optional[str]:
    if not emoji_id:
        return None
    if emoji_id.startswith("<:") or emoji_id.startswith("<a:"):
        return emoji_id
    if not emoji_id.isdigit():
        return None
    emoji_name = _DEFAULT_EMOJI_NAMES.get(key, key)
    return f"<:{emoji_name}:{emoji_id}>"

def get_ticket_emoji(key: str) -> str:
    custom = _build_custom_emoji(key, _get_custom_emoji_id(key))
    if custom: return custom
    return _FALLBACK_EMOJI.get(key, _FALLBACK_EMOJI["ticket"])

def ticket_text(key: str, text: str) -> str:
    return f"{get_ticket_emoji(key)} {text}"

class TicketEmoji:
    @classmethod
    def get(cls, key: str) -> str:
        return get_ticket_emoji(key)

    @classmethod
    def text(cls, key: str, text: str) -> str:
        return ticket_text(key, text)