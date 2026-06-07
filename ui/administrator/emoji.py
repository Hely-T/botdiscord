from __future__ import annotations

import re


GIVEAWAY_DEFAULT_ENTRY_EMOJI = "🎉"
GIVEAWAY_CUSTOM_EMOJI_RE = re.compile(r"<(?P<animated>a?):(?P<name>[A-Za-z0-9_~]+):(?P<id>\d+)>")

GIVEAWAY_ICONS = {
    "start": "🌸",
    "ended": "🏁",
    "winner": "🏆",
    "time": "⏳",
    "host": "👑",
    "selected": "🎯",
    "package": "🎁",
    "template": "📝",
    "dm": "🎉",
    "result": "🎉",
    "reroll": "🔄",
    "random": "🎲",
    "config": "🎉",
    "created": "🎉",
    "set": "🎯",
}


def giveaway_icon(key: str) -> str:
    return GIVEAWAY_ICONS.get(key, GIVEAWAY_DEFAULT_ENTRY_EMOJI)
