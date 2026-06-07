from __future__ import annotations

import asyncio
import ctypes.util
import importlib.util
import os
import random
import re
import shutil
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import discord
from discord.ext import commands

from cogs.admin_command_utils import (
    create_error_splash,
    create_info_splash,
    create_success_splash,
    format_duration_seconds,
)


IDLE_TIMEOUT_SECONDS = 300
MAX_QUEUE_ITEMS = 80
QUEUE_PAGE_SIZE = 12
DEFAULT_VOLUME = 0.65
FFMPEG_BEFORE_OPTIONS = "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5"
FFMPEG_OPTIONS = "-vn"
WINDOWS_OPUS_NAMES = ("libopus-0.dll", "opus.dll", "libopus.dll")
POSIX_OPUS_NAMES = ("libopus", "opus")


@dataclass
class AudioItem:
    title: str
    query: str
    requester_id: int
    requester_name: str
    item_type: str = "music"
    webpage_url: str | None = None
    stream_url: str | None = None
    duration: int | None = None
    thumbnail: str | None = None
    local_file: str | None = None


@dataclass
class GuildAudioState:
    queue: list[AudioItem] = field(default_factory=list)
    current: AudioItem | None = None
    voice_client: discord.VoiceClient | None = None
    voice_owner_id: int | None = None
    voice_owner_name: str | None = None
    text_channel_id: int | None = None
    volume: float = DEFAULT_VOLUME
    loop_current: bool = False
    autoplay: bool = False
    idle_task: asyncio.Task | None = None
    skip_requested: bool = False
    stop_requested: bool = False


class BotVoiceCog(commands.Cog):
    PLAY_ACTIONS = {
        "queue": "queue",
        "q": "queue",
        "list": "queue",
        "shuffle": "shuffle",
        "shufle": "shuffle",
        "sh": "shuffle",
        "sf": "shuffle",
        "autoplay": "autoplay",
        "auto": "autoplay",
        "ap": "autoplay",
        "a": "autoplay",
        "skip": "skip",
        "s": "skip",
        "next": "skip",
        "pause": "pause",
        "p": "pause",
        "pa": "pause",
        "resume": "resume",
        "continue": "resume",
        "r": "resume",
        "stop": "stop",
        "st": "stop",
        "clear": "clear",
        "c": "clear",
        "leave": "leave",
        "disconnect": "leave",
        "dc": "leave",
        "l": "leave",
        "out": "leave",
        "now": "now",
        "n": "now",
        "np": "now",
        "current": "now",
        "volume": "volume",
        "vol": "volume",
        "v": "volume",
        "loop": "loop",
        "lo": "loop",
        "repeat": "loop",
        "remove": "remove",
        "rm": "remove",
        "delete": "remove",
        "del": "remove",
    }

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.states: dict[int, GuildAudioState] = {}
        self.tts_dir = Path(tempfile.gettempdir()) / "black_lous_tts"
        self.tts_dir.mkdir(parents=True, exist_ok=True)
        self._last_opus_error: str | None = None
        self._dll_directory_handles: list[Any] = []
        self._ffmpeg_path: str | None = None

    def cog_unload(self):
        for state in self.states.values():
            if state.idle_task and not state.idle_task.done():
                state.idle_task.cancel()

    def _get_state(self, guild_id: int) -> GuildAudioState:
        if guild_id not in self.states:
            self.states[guild_id] = GuildAudioState()
        return self.states[guild_id]

    @staticmethod
    def _set_voice_owner(state: GuildAudioState, member: discord.Member):
        state.voice_owner_id = member.id
        state.voice_owner_name = member.display_name

    @staticmethod
    def _clear_voice_owner(state: GuildAudioState):
        state.voice_owner_id = None
        state.voice_owner_name = None

    @staticmethod
    def _voice_owner_text(state: GuildAudioState) -> str:
        if state.voice_owner_id:
            return f"<@{state.voice_owner_id}>"
        if state.voice_owner_name:
            return f"`{state.voice_owner_name}`"
        return "người đã mời bot vào voice"

    @staticmethod
    def _has_package(package_name: str) -> bool:
        return importlib.util.find_spec(package_name) is not None

    def _refresh_voice_dependency_flags(self) -> tuple[bool, str | None]:
        try:
            import nacl.secret  # noqa: F401
            import nacl.utils  # noqa: F401
        except ImportError:
            return False, "PyNaCl"

        try:
            import davey  # noqa: F401
        except ImportError:
            return False, "davey"

        try:
            import discord.voice_client as voice_client

            voice_client.has_nacl = True
            voice_client.has_dave = True
            voice_client.VoiceClient.warn_nacl = False
        except Exception:
            pass

        if not self._load_opus_library():
            return False, "libopus"
        return True, None

    @staticmethod
    def _project_root() -> Path:
        return Path(__file__).resolve().parents[2]

    def _add_dll_directory(self, directory: Path):
        if os.name != "nt" or not hasattr(os, "add_dll_directory"):
            return
        try:
            handle = os.add_dll_directory(str(directory))
            self._dll_directory_handles.append(handle)
        except (FileNotFoundError, OSError):
            pass

    def _iter_opus_candidates(self) -> list[str]:
        candidates: list[str] = []
        env_path = os.getenv("DISCORD_OPUS_LIBRARY") or os.getenv("OPUS_LIBRARY")
        if env_path:
            candidates.append(env_path)

        project_root = self._project_root()
        python_dir = Path(sys.executable).resolve().parent
        if os.name == "nt":
            search_dirs = [
                project_root,
                project_root / "bin",
                project_root / "libs",
                python_dir,
                python_dir / "DLLs",
                Path("C:/ffmpeg/bin"),
                Path("C:/Program Files/ffmpeg/bin"),
                Path("C:/Program Files/Opus/bin"),
            ]
            for directory in search_dirs:
                for name in WINDOWS_OPUS_NAMES:
                    candidates.append(str(directory / name))
            for name in WINDOWS_OPUS_NAMES:
                found = shutil.which(name)
                if found:
                    candidates.append(found)
                candidates.append(name)
        else:
            candidates.extend(
                [
                    "/opt/homebrew/lib/libopus.dylib",
                    "/opt/homebrew/opt/opus/lib/libopus.dylib",
                    "/usr/local/lib/libopus.dylib",
                    "/usr/local/opt/opus/lib/libopus.dylib",
                    "/usr/lib/x86_64-linux-gnu/libopus.so.0",
                    "/usr/lib/aarch64-linux-gnu/libopus.so.0",
                    "/usr/local/lib/libopus.so",
                ]
            )
            candidates.extend(POSIX_OPUS_NAMES)

        found_library = ctypes.util.find_library("opus")
        if found_library:
            candidates.append(found_library)

        deduped: list[str] = []
        seen: set[str] = set()
        for candidate in candidates:
            normalized = str(candidate).strip()
            if normalized and normalized.lower() not in seen:
                deduped.append(normalized)
                seen.add(normalized.lower())
        return deduped

    def _load_opus_library(self) -> bool:
        if discord.opus.is_loaded():
            return True

        errors: list[str] = []
        for candidate in self._iter_opus_candidates():
            try:
                candidate_path = Path(candidate)
                if os.name == "nt" and candidate_path.is_absolute() and candidate_path.parent.exists():
                    self._add_dll_directory(candidate_path.parent)
                discord.opus.load_opus(candidate)
                if discord.opus.is_loaded():
                    self._last_opus_error = None
                    return True
            except OSError as exc:
                if len(errors) < 6:
                    errors.append(f"{candidate}: {exc}")
                continue
        self._last_opus_error = "\n".join(errors)
        return False

    def _opus_install_hint(self) -> str:
        if os.name == "nt":
            detail = (
                "Không load được `libopus-0.dll` trên Windows.\n"
                "Cách sửa nhanh: kiểm tra file `C:\\ffmpeg\\bin\\libopus-0.dll` có tồn tại, "
                "hoặc đặt biến môi trường `DISCORD_OPUS_LIBRARY=C:\\ffmpeg\\bin\\libopus-0.dll` rồi restart bot.\n"
                "Nếu chưa có file này, cài bản FFmpeg full/shared từ Gyan rồi giải nén vào `C:\\ffmpeg`."
            )
            if self._last_opus_error:
                detail += f"\n\nLần thử gần nhất:\n```text\n{self._short_text(self._last_opus_error, 650)}\n```"
            return detail
        if sys.platform == "darwin":
            return "Không load được `libopus`. Trên macOS dùng `brew install opus`, hoặc set `DISCORD_OPUS_LIBRARY=/opt/homebrew/lib/libopus.dylib`."
        return "Không load được `libopus`. Trên Linux cài `libopus0`/`opus-tools`, hoặc set `DISCORD_OPUS_LIBRARY=/usr/lib/x86_64-linux-gnu/libopus.so.0`."

    @staticmethod
    def _pip_install_hint(install_name: str) -> str:
        executable = Path(sys.executable).name or "python"
        return f"Cần cài `{install_name}` cho đúng Python đang chạy bot: `{executable} -m pip install {install_name}`."

    async def _require_voice_ready(self, ctx) -> bool:
        is_ready, missing_package = self._refresh_voice_dependency_flags()
        if not is_ready:
            if missing_package == "libopus":
                detail = self._opus_install_hint()
            else:
                detail = self._pip_install_hint(str(missing_package))
            await ctx.send(
                embed=create_error_splash(
                    "❌ Thiếu Voice Library",
                    detail,
                )
            )
            return False
        return True

    def _find_ffmpeg(self) -> str | None:
        if self._ffmpeg_path and Path(self._ffmpeg_path).exists():
            return self._ffmpeg_path
        candidates = [
            shutil.which("ffmpeg"),
            str(self._project_root() / "bin" / ("ffmpeg.exe" if os.name == "nt" else "ffmpeg")),
            str(Path("C:/ffmpeg/bin/ffmpeg.exe")),
            str(Path("C:/Program Files/ffmpeg/bin/ffmpeg.exe")),
            str(Path(sys.executable).resolve().parent / "ffmpeg.exe"),
        ]
        for candidate in [item for item in candidates if item]:
            if Path(candidate).exists() or candidate == shutil.which("ffmpeg"):
                self._ffmpeg_path = str(candidate)
                return self._ffmpeg_path
        return None

    async def _require_ffmpeg(self, ctx) -> bool:
        if self._find_ffmpeg() is None:
            if os.name == "nt":
                detail = "Cần `ffmpeg.exe`. Bot sẽ tự nhận nếu có ở `C:\\ffmpeg\\bin\\ffmpeg.exe`; nếu mới cài xong hãy restart CMD/bot."
            else:
                detail = "Cần cài `ffmpeg` để phát nhạc/đọc giọng. Trên macOS dùng: `brew install ffmpeg`."
            await ctx.send(
                embed=create_error_splash(
                    "❌ Thiếu FFmpeg",
                    detail,
                )
            )
            return False
        return True

    async def _require_package(self, ctx, package_name: str, install_name: str) -> bool:
        if not self._has_package(package_name):
            await ctx.send(
                embed=create_error_splash(
                    "❌ Thiếu Package",
                    self._pip_install_hint(install_name),
                )
            )
            return False
        return True

    async def _ensure_voice(self, ctx) -> discord.VoiceClient | None:
        if ctx.guild is None:
            await ctx.send(embed=create_error_splash("❌ Chỉ Dùng Trong Server", "Lệnh voice chỉ hoạt động trong server."))
            return None
        if not await self._require_voice_ready(ctx):
            return None
        if not getattr(ctx.author, "voice", None) or not ctx.author.voice.channel:
            await ctx.send(embed=create_error_splash("❌ Chưa Vào Voice", "Bạn cần vào voice channel trước."))
            return None

        state = self._get_state(ctx.guild.id)
        target_channel = ctx.author.voice.channel
        voice_client = ctx.voice_client or state.voice_client

        try:
            if voice_client and voice_client.is_connected():
                if voice_client.channel != target_channel:
                    if state.voice_owner_id and state.voice_owner_id != ctx.author.id:
                        await ctx.send(
                            embed=create_error_splash(
                                "❌ Voice Đang Được Giữ",
                                f"Bot đang ở `{voice_client.channel.name}` do {self._voice_owner_text(state)} mời vào. Chỉ người đó mới được chuyển phòng hoặc leave.",
                            )
                        )
                        return None
                    await voice_client.move_to(target_channel)
                if state.voice_owner_id is None:
                    self._set_voice_owner(state, ctx.author)
            else:
                voice_client = await target_channel.connect(self_deaf=True)
                self._set_voice_owner(state, ctx.author)
            state.voice_client = voice_client
            state.text_channel_id = ctx.channel.id
            self._cancel_idle(state)
            return voice_client
        except discord.ClientException as exc:
            await ctx.send(embed=create_error_splash("❌ Không Join Được Voice", str(exc)))
        except discord.Forbidden:
            await ctx.send(embed=create_error_splash("❌ Thiếu Quyền Discord", "Bot thiếu quyền vào/nói trong voice channel này."))
        except discord.HTTPException as exc:
            await ctx.send(embed=create_error_splash("❌ Voice Lỗi", str(exc)))
        except RuntimeError as exc:
            if "PyNaCl" in str(exc) or "davey" in str(exc).lower():
                await ctx.send(
                    embed=create_error_splash(
                        "❌ Voice Library Chưa Sẵn Sàng",
                        "Voice library đã được cài nhưng process bot cũ vẫn chưa nhận. Hãy `breload bot` hoặc restart `python3 main.py` rồi thử lại.",
                    )
                )
            else:
                await ctx.send(embed=create_error_splash("❌ Voice Lỗi", str(exc)))
        return None

    def _cancel_idle(self, state: GuildAudioState):
        if state.idle_task and not state.idle_task.done():
            state.idle_task.cancel()
        state.idle_task = None

    def _schedule_idle_disconnect(self, guild_id: int):
        state = self._get_state(guild_id)
        self._cancel_idle(state)
        state.idle_task = self.bot.loop.create_task(self._idle_disconnect(guild_id))

    async def _idle_disconnect(self, guild_id: int):
        try:
            await asyncio.sleep(IDLE_TIMEOUT_SECONDS)
            state = self._get_state(guild_id)
            voice_client = state.voice_client
            if not voice_client or not voice_client.is_connected():
                return
            if state.queue or voice_client.is_playing() or voice_client.is_paused():
                return
            await voice_client.disconnect(force=False)
            state.voice_client = None
            state.current = None
            self._clear_voice_owner(state)
        except asyncio.CancelledError:
            return

    @staticmethod
    def _is_url(value: str) -> bool:
        return bool(re.match(r"https?://", value.strip(), flags=re.IGNORECASE))

    @staticmethod
    def _short_text(value: str, limit: int = 90) -> str:
        value = " ".join(value.split())
        if len(value) <= limit:
            return value
        return value[: limit - 3].rstrip() + "..."

    @staticmethod
    def _duration_text(seconds: int | None) -> str:
        if not seconds:
            return "không rõ"
        return format_duration_seconds(int(seconds))

    async def _send_to_state_channel(self, guild_id: int, embed: discord.Embed):
        state = self._get_state(guild_id)
        if not state.text_channel_id:
            return
        channel = self.bot.get_channel(state.text_channel_id)
        if channel:
            await channel.send(embed=embed)

    def _build_music_item(self, entry: dict[str, Any], requester: discord.Member, fallback_query: str) -> AudioItem | None:
        if not entry:
            return None

        title = entry.get("title") or fallback_query
        webpage_url = entry.get("webpage_url") or entry.get("original_url")
        raw_url = entry.get("url")
        if not webpage_url and raw_url:
            if entry.get("ie_key") == "Youtube" and entry.get("id") and not self._is_url(str(raw_url)):
                webpage_url = f"https://www.youtube.com/watch?v={entry['id']}"
            else:
                webpage_url = str(raw_url)

        query = webpage_url or raw_url or fallback_query
        if not query:
            return None

        return AudioItem(
            title=str(title),
            query=str(query),
            webpage_url=str(webpage_url) if webpage_url else None,
            duration=entry.get("duration"),
            thumbnail=entry.get("thumbnail"),
            requester_id=requester.id,
            requester_name=requester.display_name,
        )

    async def _extract_music_items(self, query: str, requester: discord.Member) -> list[AudioItem]:
        from yt_dlp import YoutubeDL

        search_query = query.strip()
        if not self._is_url(search_query):
            search_query = f"ytsearch1:{search_query}"

        ytdl_options = {
            "format": "bestaudio/best",
            "quiet": True,
            "no_warnings": True,
            "ignoreerrors": True,
            "default_search": "ytsearch",
            "extract_flat": "in_playlist",
            "noplaylist": False,
        }

        def run_extract():
            with YoutubeDL(ytdl_options) as ydl:
                return ydl.extract_info(search_query, download=False)

        info = await self.bot.loop.run_in_executor(None, run_extract)
        if not info:
            return []

        entries = info.get("entries") if isinstance(info, dict) else None
        if entries:
            items = [
                self._build_music_item(entry, requester, query)
                for entry in list(entries)[:MAX_QUEUE_ITEMS]
                if entry
            ]
            return [item for item in items if item]

        item = self._build_music_item(info, requester, query)
        return [item] if item else []

    async def _resolve_stream_url(self, item: AudioItem) -> AudioItem:
        from yt_dlp import YoutubeDL

        ytdl_options = {
            "format": "bestaudio/best",
            "quiet": True,
            "no_warnings": True,
            "ignoreerrors": False,
            "default_search": "ytsearch",
            "noplaylist": True,
        }

        def run_extract():
            with YoutubeDL(ytdl_options) as ydl:
                return ydl.extract_info(item.webpage_url or item.query, download=False)

        info = await self.bot.loop.run_in_executor(None, run_extract)
        if isinstance(info, dict) and info.get("entries"):
            info = next((entry for entry in info["entries"] if entry), None)
        if not info:
            raise ValueError("Không lấy được nguồn phát.")

        stream_url = info.get("url")
        if not stream_url:
            formats = [fmt for fmt in info.get("formats", []) if fmt.get("url")]
            if formats:
                stream_url = formats[-1]["url"]
        if not stream_url:
            raise ValueError("Không tìm thấy audio stream.")

        item.stream_url = stream_url
        item.title = info.get("title") or item.title
        item.webpage_url = info.get("webpage_url") or item.webpage_url
        item.duration = info.get("duration") or item.duration
        item.thumbnail = info.get("thumbnail") or item.thumbnail
        return item

    async def _create_tts_item(self, ctx, text: str) -> AudioItem:
        from gtts import gTTS

        safe_id = f"{ctx.guild.id}-{ctx.message.id}-{random.randint(1000, 9999)}"
        output_path = self.tts_dir / f"tts-{safe_id}.mp3"

        def save_tts():
            gTTS(text=text, lang="vi").save(str(output_path))

        await self.bot.loop.run_in_executor(None, save_tts)
        return AudioItem(
            title=self._short_text(text, 120),
            query=str(output_path),
            requester_id=ctx.author.id,
            requester_name=ctx.author.display_name,
            item_type="tts",
            local_file=str(output_path),
        )

    async def _start_player_if_needed(self, guild_id: int):
        state = self._get_state(guild_id)
        voice_client = state.voice_client
        if not voice_client or not voice_client.is_connected():
            return
        if voice_client.is_playing() or voice_client.is_paused():
            return
        await self._play_next(guild_id)

    async def _enqueue_autoplay(self, guild_id: int) -> bool:
        state = self._get_state(guild_id)
        previous = state.current
        if not state.autoplay or not previous or previous.item_type != "music":
            return False
        try:
            requester = self.bot.get_user(previous.requester_id)
            fake_requester = requester or SimpleNamespace(
                id=previous.requester_id,
                display_name=previous.requester_name,
            )
            items = await self._extract_music_items(f"{previous.title} music", fake_requester)
            for item in items:
                if item.webpage_url != previous.webpage_url:
                    state.queue.append(item)
                    return True
        except Exception:
            return False
        return False

    async def _play_next(self, guild_id: int):
        state = self._get_state(guild_id)
        voice_client = state.voice_client
        if not voice_client or not voice_client.is_connected():
            return

        self._cancel_idle(state)
        if state.stop_requested:
            state.stop_requested = False
            state.current = None
            self._schedule_idle_disconnect(guild_id)
            return

        if state.loop_current and state.current and not state.skip_requested:
            item = state.current
        else:
            if not state.queue:
                await self._enqueue_autoplay(guild_id)
            if not state.queue:
                state.current = None
                state.skip_requested = False
                self._schedule_idle_disconnect(guild_id)
                return
            item = state.queue.pop(0)
            state.current = item
            state.skip_requested = False

        try:
            ffmpeg_executable = self._find_ffmpeg() or "ffmpeg"
            if item.item_type == "music":
                item = await self._resolve_stream_url(item)
                source = discord.FFmpegPCMAudio(
                    item.stream_url,
                    executable=ffmpeg_executable,
                    before_options=FFMPEG_BEFORE_OPTIONS,
                    options=FFMPEG_OPTIONS,
                )
            else:
                source = discord.FFmpegPCMAudio(item.local_file, executable=ffmpeg_executable, options=FFMPEG_OPTIONS)

            source = discord.PCMVolumeTransformer(source, volume=state.volume)

            def after_play(error):
                self.bot.loop.call_soon_threadsafe(
                    asyncio.create_task,
                    self._after_play(guild_id, error),
                )

            voice_client.play(source, after=after_play)
            await self._send_now_playing(guild_id, item)
        except Exception as exc:
            error_text = str(exc) or repr(exc)
            await self._send_to_state_channel(
                guild_id,
                create_error_splash("❌ Phát Thất Bại", f"`{item.title}`\n{error_text}"),
            )
            await self._cleanup_item(item)
            state.current = None
            await self._play_next(guild_id)

    async def _after_play(self, guild_id: int, error):
        state = self._get_state(guild_id)
        finished_item = state.current

        if error:
            await self._send_to_state_channel(guild_id, create_error_splash("❌ Voice Lỗi", str(error)))

        if finished_item and finished_item.item_type == "tts":
            await self._cleanup_item(finished_item)

        if state.stop_requested:
            state.current = None
            state.stop_requested = False
            self._schedule_idle_disconnect(guild_id)
            return

        if state.loop_current and finished_item and finished_item.item_type == "music" and not state.skip_requested:
            state.current = finished_item
        elif state.skip_requested:
            state.current = None
        else:
            # Giữ bài vừa phát trong state thêm một nhịp để autoplay có context tìm bài tiếp theo.
            state.current = finished_item

        await self._play_next(guild_id)

    async def _cleanup_item(self, item: AudioItem):
        if item.local_file and os.path.exists(item.local_file):
            try:
                os.remove(item.local_file)
            except OSError:
                pass

    async def _send_now_playing(self, guild_id: int, item: AudioItem):
        requester_text = f"<@{item.requester_id}>"
        if item.item_type == "tts":
            embed = discord.Embed(
                title="🔊 Đang đọc",
                description=(
                    f"### “{item.title}”\n"
                    f"👤 Yêu cầu bởi: {requester_text}"
                ),
                color=discord.Color.from_rgb(91, 192, 235),
            )
            embed.set_footer(text="Google TTS • Bot tự rời voice sau 5 phút nếu không dùng.")
        else:
            link_text = f"[{item.title}]({item.webpage_url})" if item.webpage_url else item.title
            embed = discord.Embed(
                title="🎧 Đang phát",
                description=(
                    f"### {link_text}\n"
                    f"⏱ Thời lượng: `{self._duration_text(item.duration)}`\n"
                    f"👤 Yêu cầu bởi: {requester_text}"
                ),
                color=discord.Color.from_rgb(54, 162, 235),
            )
            embed.set_footer(text="Music player • Dùng bplay q để xem hàng chờ.")

        if item.thumbnail:
            embed.set_thumbnail(url=item.thumbnail)
        await self._send_to_state_channel(guild_id, embed)

    async def _show_play_help(self, ctx):
        prefix = ctx.clean_prefix
        embed = create_info_splash(
            "🎧 Music Bot",
            (
                f"`{prefix}join` - bot vào voice của bạn\n"
                f"`{prefix}say <nội dung>` - đọc nội dung bằng giọng Google\n"
                f"`{prefix}play <url|từ khóa|playlist>` - phát nhạc\n"
                f"`{prefix}a <url|từ khóa|playlist>` - viết tắt của play\n\n"
                "**Điều khiển trong play**\n"
                "`play q/queue`, `play sh/shuffle`, `play a/autoplay`, `play s/skip`, `play p/pause`, `play r/resume`, `play st/stop`, `play l/leave`, `play n/now`, `play lo/loop`, `play v/vol <0-200>`, `play rm <số>`, `play c/clear`"
            ),
        )
        await ctx.send(embed=embed)

    async def _show_queue(self, ctx):
        state = self._get_state(ctx.guild.id)
        lines = []
        if state.current:
            lines.append(f"**Đang phát:** `{self._short_text(state.current.title, 70)}`")
        else:
            lines.append("**Đang phát:** chưa có")

        if state.queue:
            for index, item in enumerate(state.queue[:QUEUE_PAGE_SIZE], 1):
                lines.append(f"`{index}.` {self._short_text(item.title, 80)}")
            if len(state.queue) > QUEUE_PAGE_SIZE:
                lines.append(f"... và `{len(state.queue) - QUEUE_PAGE_SIZE}` bài nữa")
        else:
            lines.append("Queue đang trống.")

        await ctx.send(embed=create_info_splash("🎶 Queue", "\n".join(lines)))

    async def _toggle_autoplay(self, ctx, raw_value: str | None):
        state = self._get_state(ctx.guild.id)
        if raw_value:
            lowered = raw_value.strip().lower()
            if lowered in {"on", "bat", "bật", "true", "1"}:
                state.autoplay = True
            elif lowered in {"off", "tat", "tắt", "false", "0"}:
                state.autoplay = False
            else:
                await ctx.send(embed=create_error_splash("❌ Sai Cú Pháp", "Dùng: `play autoplay on/off` hoặc `play a`."))
                return
        else:
            state.autoplay = not state.autoplay
        status = "bật" if state.autoplay else "tắt"
        await ctx.send(embed=create_success_splash("✅ Autoplay", f"Autoplay hiện đang **{status}**."))

    async def _handle_play_action(self, ctx, action: str, rest: str):
        state = self._get_state(ctx.guild.id)
        voice_client = ctx.voice_client or state.voice_client

        if action == "queue":
            await self._show_queue(ctx)
            return
        if action == "shuffle":
            if len(state.queue) < 2:
                await ctx.send(embed=create_error_splash("❌ Queue Ngắn", "Cần ít nhất 2 bài trong queue để shuffle."))
                return
            random.shuffle(state.queue)
            await ctx.send(embed=create_success_splash("✅ Shuffle", f"Đã trộn `{len(state.queue)}` bài trong queue."))
            return
        if action == "autoplay":
            await self._toggle_autoplay(ctx, rest or None)
            return
        if action == "skip":
            if not voice_client or not voice_client.is_playing():
                await ctx.send(embed=create_error_splash("❌ Không Có Bài", "Hiện không có bài nào đang phát."))
                return
            state.skip_requested = True
            voice_client.stop()
            await ctx.send(embed=create_success_splash("✅ Skip", "Đã bỏ qua bài hiện tại."))
            return
        if action == "pause":
            if voice_client and voice_client.is_playing():
                voice_client.pause()
                await ctx.send(embed=create_success_splash("✅ Pause", "Đã tạm dừng phát nhạc."))
            else:
                await ctx.send(embed=create_error_splash("❌ Không Phát", "Hiện không có bài nào đang phát."))
            return
        if action == "resume":
            if voice_client and voice_client.is_paused():
                voice_client.resume()
                await ctx.send(embed=create_success_splash("✅ Resume", "Đã tiếp tục phát nhạc."))
            else:
                await ctx.send(embed=create_error_splash("❌ Không Pause", "Bot không đang tạm dừng."))
            return
        if action == "stop":
            state.queue.clear()
            state.loop_current = False
            state.stop_requested = True
            if voice_client and (voice_client.is_playing() or voice_client.is_paused()):
                voice_client.stop()
            else:
                self._schedule_idle_disconnect(ctx.guild.id)
            await ctx.send(embed=create_success_splash("✅ Stop", "Đã dừng phát và xóa queue. Bot sẽ tự out sau 5 phút nếu không dùng."))
            return
        if action == "clear":
            count = len(state.queue)
            state.queue.clear()
            await ctx.send(embed=create_success_splash("✅ Clear Queue", f"Đã xóa `{count}` bài khỏi queue."))
            return
        if action == "leave":
            if state.voice_owner_id and state.voice_owner_id != ctx.author.id:
                await ctx.send(
                    embed=create_error_splash(
                        "❌ Không Được Leave",
                        f"Chỉ {self._voice_owner_text(state)} mới được cho bot rời voice.",
                    )
                )
                return
            state.queue.clear()
            state.current = None
            state.loop_current = False
            state.stop_requested = True
            self._cancel_idle(state)
            if voice_client and voice_client.is_connected():
                if voice_client.is_playing() or voice_client.is_paused():
                    voice_client.stop()
                await voice_client.disconnect(force=True)
            state.voice_client = None
            state.stop_requested = False
            self._clear_voice_owner(state)
            await ctx.send(embed=create_success_splash("✅ Đã Rời Voice", "Bot đã rời voice channel."))
            return
        if action == "now":
            if not state.current:
                await ctx.send(embed=create_error_splash("❌ Không Có Bài", "Hiện chưa có bài nào đang phát."))
                return
            await self._send_now_playing(ctx.guild.id, state.current)
            return
        if action == "volume":
            if not rest:
                await ctx.send(embed=create_info_splash("🔊 Volume", f"Volume hiện tại: `{int(state.volume * 100)}%`."))
                return
            try:
                volume = int(rest.strip())
            except ValueError:
                await ctx.send(embed=create_error_splash("❌ Sai Volume", "Volume phải là số từ 0 đến 200."))
                return
            if volume < 0 or volume > 200:
                await ctx.send(embed=create_error_splash("❌ Sai Volume", "Volume phải nằm trong khoảng 0-200."))
                return
            state.volume = volume / 100
            if voice_client and voice_client.source and isinstance(voice_client.source, discord.PCMVolumeTransformer):
                voice_client.source.volume = state.volume
            await ctx.send(embed=create_success_splash("✅ Volume", f"Đã set volume thành `{volume}%`."))
            return
        if action == "loop":
            if rest:
                lowered = rest.strip().lower()
                if lowered in {"on", "bat", "bật", "true", "1"}:
                    state.loop_current = True
                elif lowered in {"off", "tat", "tắt", "false", "0"}:
                    state.loop_current = False
                else:
                    await ctx.send(embed=create_error_splash("❌ Sai Cú Pháp", "Dùng: `play loop on/off` hoặc `play loop`."))
                    return
            else:
                state.loop_current = not state.loop_current
            status = "bật" if state.loop_current else "tắt"
            await ctx.send(embed=create_success_splash("✅ Loop", f"Loop bài hiện tại đang **{status}**."))
            return
        if action == "remove":
            if not rest:
                await ctx.send(embed=create_error_splash("❌ Thiếu Số Thứ Tự", "Dùng: `play rm <số trong queue>`."))
                return
            try:
                index = int(rest.strip())
            except ValueError:
                await ctx.send(embed=create_error_splash("❌ Sai Số", "Số thứ tự phải là số nguyên."))
                return
            if index < 1 or index > len(state.queue):
                await ctx.send(embed=create_error_splash("❌ Ngoài Queue", f"Queue hiện có `{len(state.queue)}` bài."))
                return
            removed = state.queue.pop(index - 1)
            await ctx.send(embed=create_success_splash("✅ Đã Xóa Khỏi Queue", f"Đã xóa `{removed.title}`."))

    async def _add_music(self, ctx, query: str):
        if not await self._require_ffmpeg(ctx):
            return
        if not await self._require_package(ctx, "yt_dlp", "yt-dlp"):
            return

        voice_client = await self._ensure_voice(ctx)
        if not voice_client:
            return

        state = self._get_state(ctx.guild.id)
        state.text_channel_id = ctx.channel.id

        try:
            async with ctx.typing():
                items = await self._extract_music_items(query, ctx.author)
        except Exception as exc:
            await ctx.send(
                embed=create_error_splash(
                    "❌ Không Tìm Được Nhạc",
                    f"{exc}\nNếu Spotify URL không chạy, hãy gửi tên bài hoặc link YouTube/YT Music tương ứng.",
                )
            )
            return

        if not items:
            await ctx.send(embed=create_error_splash("❌ Không Có Kết Quả", "Không tìm thấy bài/playlist phù hợp."))
            return

        state.queue.extend(items)
        await self._start_player_if_needed(ctx.guild.id)

    @commands.command(name="join", aliases=["j"])
    async def join(self, ctx):
        voice_client = await self._ensure_voice(ctx)
        if not voice_client:
            return
        state = self._get_state(ctx.guild.id)
        await ctx.send(embed=create_success_splash("✅ Đã Vào Voice", f"Bot đã vào `{voice_client.channel.name}`.\nNgười giữ quyền leave: {self._voice_owner_text(state)}."))

    @commands.command(name="say", aliases=["s"])
    async def say(self, ctx, *, text: str = None):
        if not text or not text.strip():
            await ctx.send(embed=create_error_splash("❌ Thiếu Nội Dung", "Dùng: `say <nội dung>` để bot đọc bằng giọng Google."))
            return
        if not await self._require_ffmpeg(ctx):
            return
        if not await self._require_package(ctx, "gtts", "gTTS"):
            return

        voice_client = await self._ensure_voice(ctx)
        if not voice_client:
            return

        text = text.strip()
        if len(text) > 500:
            await ctx.send(embed=create_error_splash("❌ Nội Dung Quá Dài", "Tạm giới hạn 500 ký tự mỗi lần đọc để tránh kẹt queue."))
            return

        try:
            async with ctx.typing():
                item = await self._create_tts_item(ctx, text)
        except Exception as exc:
            await ctx.send(embed=create_error_splash("❌ Tạo Giọng Đọc Thất Bại", str(exc)))
            return

        state = self._get_state(ctx.guild.id)
        state.text_channel_id = ctx.channel.id
        state.queue.append(item)
        await self._start_player_if_needed(ctx.guild.id)

    @commands.command(name="leave", aliases=["l", "disconnect", "dc"])
    async def leave(self, ctx):
        if ctx.guild is None:
            await ctx.send(embed=create_error_splash("❌ Chỉ Dùng Trong Server", "Lệnh `leave` chỉ hoạt động trong server."))
            return
        await self._handle_play_action(ctx, "leave", "")

    @commands.command(name="play", aliases=["a", "p"])
    async def play(self, ctx, *, content: str = None):
        if ctx.guild is None:
            await ctx.send(embed=create_error_splash("❌ Chỉ Dùng Trong Server", "Lệnh `play` chỉ hoạt động trong server."))
            return
        if not content or not content.strip():
            await self._show_play_help(ctx)
            return

        content = content.strip()
        first, _, rest = content.partition(" ")
        action = self.PLAY_ACTIONS.get(first.lower())
        if action:
            await self._handle_play_action(ctx, action, rest.strip())
            return

        await self._add_music(ctx, content)


async def setup(bot):
    await bot.add_cog(BotVoiceCog(bot))
