from __future__ import annotations

import os


FALLBACK_EMOJIS = {
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
    "success": "✅",
    "error": "❌",
    "add_user": "👤",
    "remove_user": "🗑️",
    "rename": "✏️",
    "log": "📁",
    "settings": "⚙️",
    "manage": "🛠️",
    "refresh": "🔄",
    "channel": "📺",
    "back": "⬅️",
}

# Có thể điền trực tiếp Discord emoji ID tại đây.
DISCORD_EMOJI_IDS = {
    "ticket": "",
    "support": "",
    "bug": "",
    "report": "",
    "payment": "",
    "contact_admin": "",
    "claim": "",
    "close": "",
    "confirm": "",
    "cancel": "",
    "success": "",
    "error": "",
    "add_user": "",
    "remove_user": "",
    "rename": "",
    "log": "",
    "settings": "",
    "manage": "",
    "refresh": "",
    "channel": "",
    "back": "",
}


def ticket_emoji(key: str) -> str:
    emoji_id = os.getenv(
        f"TICKET_EMOJI_{key.upper()}_ID",
        DISCORD_EMOJI_IDS.get(key, ""),
    ).strip()
    if emoji_id.startswith("<:") or emoji_id.startswith("<a:"):
        return emoji_id
    if emoji_id.isdigit():
        return f"<:{key}:{emoji_id}>"
    return FALLBACK_EMOJIS.get(key, FALLBACK_EMOJIS["ticket"])


def ticket_text(key: str, text: str) -> str:
    return f"{ticket_emoji(key)} {text}"
