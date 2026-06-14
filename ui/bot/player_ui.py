from __future__ import annotations

import asyncio
import io
import re
from dataclasses import dataclass
from pathlib import Path

import aiohttp
import discord
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps


CARD_WIDTH = 1000
CARD_HEIGHT = 360
CARD_FILENAME = "music-player.png"
ASSET_DIR = Path(__file__).resolve().parent / "assets"
THUMBNAIL_CACHE: dict[str, bytes] = {}


@dataclass(slots=True)
class PlayerCardData:
    title: str
    requester: str
    duration: int | None
    elapsed: int
    thumbnail: str | None
    volume: int
    paused: bool
    loop: bool
    autoplay: bool
    queue_count: int = 0
    accent_color: str = "#7f314d"
    background_url: str | None = None
    header_text: str = "BLACK LOUS MUSIC"


def _font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        Path("C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf"),
        Path("/System/Library/Fonts/SFNS.ttf"),
        Path("/System/Library/Fonts/HelveticaNeue.ttc"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
    ]
    for path in candidates:
        if not path.exists():
            continue
        try:
            return ImageFont.truetype(str(path), size=size)
        except OSError:
            continue
    return ImageFont.load_default()


def _fit_text(draw: ImageDraw.ImageDraw, text: str, font, max_width: int) -> str:
    value = " ".join((text or "Không rõ").split())
    if draw.textlength(value, font=font) <= max_width:
        return value
    suffix = "..."
    while value and draw.textlength(value + suffix, font=font) > max_width:
        value = value[:-1]
    return value.rstrip() + suffix


def _time_text(seconds: int | None) -> str:
    value = max(0, int(seconds or 0))
    hours, remainder = divmod(value, 3600)
    minutes, secs = divmod(remainder, 60)
    if hours:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes}:{secs:02d}"


async def _download_thumbnail(url: str | None) -> bytes | None:
    if not url:
        return None
    if url in THUMBNAIL_CACHE:
        return THUMBNAIL_CACHE[url]
    timeout = aiohttp.ClientTimeout(total=8)
    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url) as response:
                if response.status != 200:
                    return None
                raw = await response.read()
                if len(THUMBNAIL_CACHE) >= 30:
                    THUMBNAIL_CACHE.pop(next(iter(THUMBNAIL_CACHE)))
                THUMBNAIL_CACHE[url] = raw
                return raw
    except (aiohttp.ClientError, asyncio.TimeoutError):
        return None


def _cover_image(raw: bytes | None) -> Image.Image:
    if raw:
        try:
            image = Image.open(io.BytesIO(raw)).convert("RGB")
            return ImageOps.fit(image, (270, 270), method=Image.Resampling.LANCZOS)
        except (OSError, ValueError):
            pass

    image = Image.new("RGB", (270, 270), "#2b1820")
    draw = ImageDraw.Draw(image)
    draw.ellipse((58, 58, 212, 212), fill="#f8c6d8")
    draw.ellipse((94, 94, 176, 176), fill="#542636")
    draw.ellipse((127, 127, 143, 143), fill="#f8c6d8")
    return image


def _open_background(raw: bytes | None, cover: Image.Image) -> Image.Image:
    if raw:
        try:
            image = Image.open(io.BytesIO(raw)).convert("RGB")
            return ImageOps.fit(image, (CARD_WIDTH, CARD_HEIGHT), method=Image.Resampling.LANCZOS)
        except (OSError, ValueError):
            pass
    local_background = ASSET_DIR / "player_background.png"
    if local_background.exists():
        try:
            image = Image.open(local_background).convert("RGB")
            return ImageOps.fit(image, (CARD_WIDTH, CARD_HEIGHT), method=Image.Resampling.LANCZOS)
        except OSError:
            pass
    return cover.resize((CARD_WIDTH, CARD_HEIGHT)).filter(ImageFilter.GaussianBlur(30))


def normalize_accent_color(value: str | None) -> str:
    color = str(value or "").strip()
    if re.fullmatch(r"#[0-9a-fA-F]{6}", color):
        return color.lower()
    return "#7f314d"


def _render_card(
    data: PlayerCardData,
    raw_thumbnail: bytes | None,
    raw_background: bytes | None,
) -> io.BytesIO:
    cover = _cover_image(raw_thumbnail)
    background = _open_background(raw_background, cover)
    dark_layer = Image.new("RGBA", background.size, (29, 10, 18, 210))
    canvas = Image.alpha_composite(background.convert("RGBA"), dark_layer)

    draw = ImageDraw.Draw(canvas)
    draw.rounded_rectangle(
        (18, 18, CARD_WIDTH - 18, CARD_HEIGHT - 18),
        radius=34,
        fill=(255, 245, 239, 238),
        outline=(255, 197, 216, 255),
        width=5,
    )

    cover_mask = Image.new("L", (270, 270), 0)
    ImageDraw.Draw(cover_mask).rounded_rectangle((0, 0, 270, 270), radius=28, fill=255)
    canvas.paste(cover, (48, 45), cover_mask)

    title_font = _font(42, bold=True)
    meta_font = _font(25)
    small_font = _font(20)
    status_font = _font(22, bold=True)
    accent = normalize_accent_color(data.accent_color)
    text = "#27171e"
    muted = "#725d65"

    header_font = _font(18, bold=True)
    title = _fit_text(draw, data.title, title_font, 590)
    header = _fit_text(draw, data.header_text.upper(), header_font, 580)
    draw.text((355, 35), header, font=header_font, fill=accent)
    draw.text((355, 62), title, font=title_font, fill=text)
    draw.text((355, 125), f"Yêu cầu bởi: {data.requester}", font=meta_font, fill=muted)

    status = "TẠM DỪNG" if data.paused else "ĐANG PHÁT"
    status_color = "#c44c72" if data.paused else "#4f9b72"
    draw.rounded_rectangle((355, 170, 500, 208), radius=16, fill=status_color)
    draw.text((372, 177), status, font=status_font, fill="white")

    duration = max(0, int(data.duration or 0))
    duration_text = _time_text(duration) if duration else "Không rõ"
    draw.text((355, 235), "THỜI LƯỢNG", font=small_font, fill=muted)
    draw.text((355, 263), duration_text, font=status_font, fill=accent)

    modes = [
        f"Âm lượng {data.volume}%",
        f"Loop {'Bật' if data.loop else 'Tắt'}",
        f"Đề xuất YouTube {'Bật' if data.autoplay else 'Tắt'}",
        f"Queue {data.queue_count}",
    ]
    x = 355
    for mode in modes:
        width = int(draw.textlength(mode, font=small_font)) + 30
        draw.rounded_rectangle((x, 298, x + width, 330), radius=14, fill="#f2dce4")
        draw.text((x + 15, 303), mode, font=small_font, fill=accent)
        x += width + 12

    frame_path = ASSET_DIR / "player_frame.png"
    if frame_path.exists():
        try:
            frame = Image.open(frame_path).convert("RGBA")
            frame = ImageOps.fit(frame, (CARD_WIDTH, CARD_HEIGHT), method=Image.Resampling.LANCZOS)
            canvas = Image.alpha_composite(canvas, frame)
        except OSError:
            pass

    output = io.BytesIO()
    canvas.convert("RGB").save(output, format="PNG", optimize=True)
    output.seek(0)
    return output


async def build_player_file(data: PlayerCardData) -> discord.File:
    raw_thumbnail, raw_background = await asyncio.gather(
        _download_thumbnail(data.thumbnail),
        _download_thumbnail(data.background_url),
    )
    buffer = await asyncio.to_thread(_render_card, data, raw_thumbnail, raw_background)
    return discord.File(buffer, filename=CARD_FILENAME)


class PlayerVolumeModal(discord.ui.Modal, title="Chỉnh âm lượng"):
    volume = discord.ui.TextInput(
        label="Âm lượng từ 0 đến 200",
        placeholder="100",
        min_length=1,
        max_length=3,
    )

    def __init__(self, controller, guild_id: int):
        super().__init__()
        self.controller = controller
        self.guild_id = guild_id

    async def on_submit(self, interaction: discord.Interaction):
        await self.controller.handle_player_volume(interaction, self.guild_id, self.volume.value)


class PlayerThemeModal(discord.ui.Modal, title="Chỉnh giao diện Player"):
    accent = discord.ui.TextInput(
        label="Màu chính",
        placeholder="#7f314d",
        required=False,
        max_length=7,
    )
    title_text = discord.ui.TextInput(
        label="Tiêu đề nhỏ",
        placeholder="BLACK LOUS MUSIC",
        required=False,
        max_length=40,
    )
    background_url = discord.ui.TextInput(
        label="URL ảnh nền",
        placeholder="https://... hoặc để trống để dùng ảnh trong UI",
        required=False,
        max_length=500,
    )

    def __init__(self, controller, guild_id: int, theme: dict):
        super().__init__()
        self.controller = controller
        self.guild_id = guild_id
        self.accent.default = str(theme.get("accent_color") or "#7f314d")
        self.title_text.default = str(theme.get("title_text") or "BLACK LOUS MUSIC")
        self.background_url.default = str(theme.get("background_url") or "")

    async def on_submit(self, interaction: discord.Interaction):
        await self.controller.handle_player_theme_submit(
            interaction,
            self.guild_id,
            accent=str(self.accent.value),
            title_text=str(self.title_text.value),
            background_url=str(self.background_url.value),
        )


class PlayerSettingsView(discord.ui.View):
    def __init__(self, controller, guild_id: int):
        super().__init__(timeout=300)
        self.controller = controller
        self.guild_id = guild_id

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return await self.controller.check_player_settings_interaction(interaction, self.guild_id)

    @discord.ui.button(label="Chỉnh giao diện", emoji="🎨", style=discord.ButtonStyle.primary)
    async def edit(self, interaction: discord.Interaction, button: discord.ui.Button):
        theme = self.controller.player_service.get_theme(self.guild_id)
        await interaction.response.send_modal(PlayerThemeModal(self.controller, self.guild_id, theme))

    @discord.ui.button(label="Xem trước", emoji="🖼️", style=discord.ButtonStyle.secondary)
    async def preview(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.controller.send_player_preview(interaction, self.guild_id)

    @discord.ui.button(label="Mặc định", emoji="↩️", style=discord.ButtonStyle.danger)
    async def reset(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.controller.reset_player_theme(interaction, self.guild_id)


class MusicPlayerView(discord.ui.View):
    def __init__(self, controller, guild_id: int):
        super().__init__(timeout=900)
        self.controller = controller
        self.guild_id = guild_id

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return await self.controller.check_player_interaction(interaction, self.guild_id)

    @discord.ui.button(label="Pause / Resume", emoji="⏯️", style=discord.ButtonStyle.primary, row=0)
    async def pause_resume(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.controller.handle_player_button(interaction, self.guild_id, "pause_resume")

    @discord.ui.button(label="Stop", emoji="⏹️", style=discord.ButtonStyle.danger, row=0)
    async def stop(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.controller.handle_player_button(interaction, self.guild_id, "stop")

    @discord.ui.button(label="Skip", emoji="⏭️", style=discord.ButtonStyle.secondary, row=0)
    async def skip(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.controller.handle_player_button(interaction, self.guild_id, "skip")

    @discord.ui.button(label="Loop", emoji="🔁", style=discord.ButtonStyle.secondary, row=0)
    async def loop(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.controller.handle_player_button(interaction, self.guild_id, "loop")

    @discord.ui.button(label="Đề xuất YouTube", emoji="♾️", style=discord.ButtonStyle.secondary, row=0)
    async def autoplay(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.controller.handle_player_button(interaction, self.guild_id, "autoplay")

    @discord.ui.button(label="Shuffle", emoji="🔀", style=discord.ButtonStyle.secondary, row=1)
    async def shuffle(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.controller.handle_player_button(interaction, self.guild_id, "shuffle")

    @discord.ui.button(label="Queue", emoji="📋", style=discord.ButtonStyle.secondary, row=1)
    async def queue(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.controller.handle_player_button(interaction, self.guild_id, "queue")

    @discord.ui.button(label="Âm lượng", emoji="🔊", style=discord.ButtonStyle.secondary, row=1)
    async def volume(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(PlayerVolumeModal(self.controller, self.guild_id))

    @discord.ui.button(label="Settings", emoji="⚙️", style=discord.ButtonStyle.secondary, row=1)
    async def settings(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.controller.handle_player_settings_button(interaction, self.guild_id)

    @discord.ui.button(label="Rời voice", emoji="🚪", style=discord.ButtonStyle.secondary, row=1)
    async def leave(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.controller.handle_player_button(interaction, self.guild_id, "leave")
