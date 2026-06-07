from __future__ import annotations

from datetime import datetime, timezone

import discord


LOG_CATEGORY_LABELS = {
    "chat": "Chat",
    "voice": "Voice",
    "server": "Server",
    "member": "Member Leave/Out",
}

LOG_CATEGORY_EMOJIS = {
    "chat": "💬",
    "voice": "🎙️",
    "server": "🧩",
    "member": "👥",
}

LOG_COLORS = {
    "chat": discord.Color.from_rgb(96, 165, 250),
    "voice": discord.Color.from_rgb(34, 197, 94),
    "server": discord.Color.from_rgb(168, 85, 247),
    "member": discord.Color.from_rgb(251, 191, 36),
    "danger": discord.Color.from_rgb(239, 68, 68),
}


def local_time_text(dt: datetime | None = None) -> str:
    value = dt or datetime.now().astimezone()
    return f"Hôm nay lúc {value.strftime('%H:%M')}"


def discord_time(dt: datetime | None = None) -> str:
    value = dt or datetime.now(timezone.utc)
    timestamp = int(value.timestamp())
    return f"<t:{timestamp}:F>"


def avatar_url(user: discord.abc.User | discord.Member | None) -> str | None:
    if not user:
        return None
    return user.display_avatar.url


def truncate_text(value: str | None, limit: int = 950) -> str:
    text = str(value or "").strip()
    if not text:
        return "`Không có nội dung`"
    if len(text) <= limit:
        return text
    return text[: limit - 3] + "..."


def build_log_settings_embed(guild: discord.Guild, config: dict | None) -> discord.Embed:
    embed = discord.Embed(
        title="🧾 Log System",
        description="Quản lý log chat, voice, server và member leave/out.",
        color=discord.Color.from_rgb(59, 130, 246),
    )
    embed.set_author(name=guild.name, icon_url=guild.icon.url if guild.icon else None)
    config = config or {}
    for category, label in LOG_CATEGORY_LABELS.items():
        field_name = {
            "chat": "chat_channel_id",
            "voice": "voice_channel_id",
            "server": "server_channel_id",
            "member": "member_channel_id",
        }[category]
        channel_id = config.get(field_name)
        value = f"<#{int(channel_id)}>" if channel_id else "`Chưa set`"
        embed.add_field(name=f"{LOG_CATEGORY_EMOJIS[category]} {label}", value=value, inline=True)

    announce_id = config.get("voice_announce_channel_id")
    announce_text = f"<#{int(announce_id)}>" if announce_id else "`Tắt`"
    embed.add_field(name="📣 Voice greeting", value=announce_text, inline=True)
    embed.add_field(
        name="📝 Voice join template",
        value=truncate_text(config.get("voice_join_template") or "Dạ em chào đại ca {user} ạ", 250),
        inline=False,
    )
    embed.add_field(
        name="📦 Embed greeting",
        value="`Bật`" if int(config.get("voice_announce_embed") or 0) else "`Tắt`",
        inline=True,
    )
    embed.set_footer(text=f"Log • {local_time_text()}")
    return embed


def build_basic_log_embed(
    title: str,
    description: str,
    category: str,
    user: discord.abc.User | discord.Member | None = None,
) -> discord.Embed:
    embed = discord.Embed(
        title=title,
        description=description,
        color=LOG_COLORS.get(category, discord.Color.blurple()),
    )
    if user:
        embed.set_author(name=getattr(user, "display_name", str(user)), icon_url=avatar_url(user))
    embed.set_footer(text=local_time_text())
    return embed
