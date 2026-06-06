from __future__ import annotations

import re
from datetime import datetime

import discord
from discord.ext import commands

from cogs.admin_command_utils import format_vnd, parse_vnd_amount
from services.note_service import NoteService


class NoteCog(commands.Cog):
    DELETE_ACTIONS = {"d", "del", "delete", "rm", "remove", "xoa", "xóa"}
    ADJUST_PATTERN = re.compile(r"^(?P<index>\d+)\s*(?P<sign>[+-])\s*(?P<amount>.+)$")

    def __init__(self, bot):
        self.bot = bot
        self.service = NoteService()

    @staticmethod
    def _guild_id(ctx) -> int | None:
        return ctx.guild.id if ctx.guild else None

    @staticmethod
    def _format_amount(amount: int | None) -> str:
        if amount is None:
            return "`Không ghi tiền`"
        return f"`{format_vnd(amount)} VNĐ`"

    @staticmethod
    def _format_amount_plain(amount: int | None) -> str:
        if amount is None:
            return ""
        return f" {format_vnd(amount)} VNĐ"

    def _format_notes_plain(self, ctx) -> str:
        notes = self.service.list_notes(self._guild_id(ctx), ctx.author.id)
        if not notes:
            return "Bạn chưa có note nào."
        lines = [
            f"{index}. {note['content']}{self._format_amount_plain(note['amount'])}"
            for index, note in enumerate(notes, 1)
        ]
        return "\n".join(lines)

    @staticmethod
    def _looks_like_amount_token(token: str) -> bool:
        cleaned = token.strip().lower()
        if re.search(r"(vnđ|vnd|đ|d|[kmb]|[.,])", cleaned):
            return True
        return bool(re.fullmatch(r"\d{4,}", cleaned))

    @classmethod
    def _parse_note_content_and_amount(cls, raw: str) -> tuple[str, int | None]:
        text = raw.strip()
        if not text:
            raise ValueError("Hãy nhập nội dung note.")

        parts = text.rsplit(maxsplit=1)
        if len(parts) == 2 and cls._looks_like_amount_token(parts[1]):
            try:
                amount = parse_vnd_amount(parts[1])
            except ValueError:
                return text, None
            content = parts[0].strip()
            if content:
                return content, amount

        return text, None

    @staticmethod
    def _parse_positions(raw: str) -> list[int]:
        positions: list[int] = []
        for chunk in re.split(r"[\s,]+", raw.strip()):
            if not chunk:
                continue
            if not chunk.isdigit():
                raise ValueError(f"Số thứ tự `{chunk}` không hợp lệ.")
            positions.append(int(chunk))
        if not positions:
            raise ValueError("Hãy nhập số thứ tự note cần xoá.")
        return positions

    def _build_notes_embed(self, ctx, title: str = "🗒️ Note") -> discord.Embed:
        notes = self.service.list_notes(self._guild_id(ctx), ctx.author.id)
        embed = discord.Embed(color=discord.Color.from_rgb(255, 184, 90))
        embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.display_avatar.url)
        embed.title = title

        if not notes:
            embed.description = "Bạn chưa có note nào."
            return embed

        lines = [
            f"{index}. {note['content']}{self._format_amount_plain(note['amount'])}"
            for index, note in enumerate(notes[:50], 1)
        ]
        embed.description = "\n".join(lines)
        footer_text = f"Hôm nay lúc {datetime.now().strftime('%H:%M')}"
        if len(notes) > 50:
            footer_text = f"Đang hiện 50/{len(notes)} note • {footer_text}"
        embed.set_footer(text=footer_text)
        return embed

    @commands.command(name="note")
    async def note(self, ctx, *, content: str = None):
        if not content:
            await ctx.reply(self._format_notes_plain(ctx), mention_author=False)
            return

        stripped = content.strip()
        action, _, rest = stripped.partition(" ")
        lowered_action = action.lower()

        if lowered_action in self.DELETE_ACTIONS:
            try:
                positions = self._parse_positions(rest)
            except ValueError as exc:
                await ctx.reply(f"❌ Xoá note lỗi: {exc}", mention_author=False)
                return
            deleted = self.service.delete_positions(self._guild_id(ctx), ctx.author.id, positions)
            if not deleted:
                await ctx.reply("❌ Không có note nào khớp số thứ tự bạn nhập.", mention_author=False)
                return
            deleted_lines = [f"#{row['position']} {row['content']}{self._format_amount_plain(row['amount'])}" for row in deleted]
            await ctx.reply(f"Đã xoá note {', '.join(deleted_lines)}.", mention_author=False)
            return

        adjust_match = self.ADJUST_PATTERN.match(stripped)
        if adjust_match:
            position = int(adjust_match.group("index"))
            sign = adjust_match.group("sign")
            try:
                amount = parse_vnd_amount(adjust_match.group("amount"))
            except ValueError as exc:
                await ctx.reply(f"❌ Sửa tiền note lỗi: {exc}", mention_author=False)
                return
            delta = amount if sign == "+" else -amount
            updated = self.service.adjust_amount(self._guild_id(ctx), ctx.author.id, position, delta)
            if not updated:
                await ctx.reply(f"❌ Không có note số {position}.", mention_author=False)
                return
            await ctx.reply(f"Đã sửa note #{position} {updated['content']}{self._format_amount_plain(updated['amount'])}.", mention_author=False)
            return

        try:
            note_content, amount = self._parse_note_content_and_amount(stripped)
        except ValueError as exc:
            await ctx.reply(f"❌ Thêm note lỗi: {exc}", mention_author=False)
            return

        created = self.service.add_note(self._guild_id(ctx), ctx.author.id, note_content, amount)
        notes = self.service.list_notes(self._guild_id(ctx), ctx.author.id)
        position = len(notes)
        note_text = created["content"] if created else note_content
        await ctx.reply(f"Đã thêm note #{position} {note_text}{self._format_amount_plain(amount)}.", mention_author=False)

    @commands.command(name="notes")
    async def notes(self, ctx):
        await ctx.reply(embed=self._build_notes_embed(ctx, "🗒️ Note Của Bạn"), mention_author=False)


async def setup(bot):
    await bot.add_cog(NoteCog(bot))
