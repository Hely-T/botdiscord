from __future__ import annotations


EVENT_FALLBACK_EMOJIS = {
    "event": "🎉",
    "create": "➕",
    "manage": "⚙️",
    "leaderboard": "🏆",
    "channel": "📺",
    "emoji": "✨",
    "filter": "🔍",
    "start": "▶️",
    "stop": "⏹️",
    "delete": "🗑️",
    "back": "⬅️",
    "theme": "🎨",
}

EVENT_THEME_DEFAULTS = {
    "title_manager": "Event Manager",
    "desc_manager": "Quản lý các sự kiện thi ảnh/video/meme trong server.",
    "title_leaderboard": "Bảng Xếp Hạng",
    "label_no_event": "Chưa có sự kiện nào. Bấm **Tạo Sự kiện mới** để bắt đầu.",
    "label_select_event": "Chọn một sự kiện từ menu để quản lý hoặc tạo sự kiện mới.",
    "label_active": "Đang chạy",
    "label_draft": "Bản nháp",
    "label_closed": "Đã kết thúc",
    "button_create": "Tạo Sự kiện mới",
    "button_start": "Bắt đầu sự kiện",
    "button_stop": "Kết thúc sự kiện",
    "button_delete": "Xóa sự kiện",
    "button_edit_name": "Sửa tên",
    "button_emoji": "Emoji Vote",
    "button_theme": "Giao diện (Theme)",
}

def event_theme_value(theme: dict | None, key: str) -> str:
    theme = theme or {}
    value = theme.get(key)
    if value is not None and str(value).strip():
        return str(value)
    return EVENT_THEME_DEFAULTS.get(key, "")
    
def event_text(key: str, text: str) -> str:
    return f"{EVENT_FALLBACK_EMOJIS.get(key, '🎉')} {text}"