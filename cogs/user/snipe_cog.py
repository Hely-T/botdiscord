from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass
from datetime import datetime

import discord
from discord.ext import commands


MAX_SNIPES_PER_CHANNEL = 50


@dataclass
class DeletedMessage:
    author_id: int
    author_name: str
    author_avatar: str
    content: str
    channel_id: int
    channel_name: str
    deleted_at: datetime
    attachments: list[str]


class SnipeHistoryView(discord.ui.View):
    def __init__(self, entries: list[DeletedMessage], requester_id: int):
        super().__init__(timeout=180)
        self.entries = entries
        self.requester_id = requester_id
        self.page = 0
        self._sync_buttons()

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.requester_id:
            await interaction.response.send_message("❌ Menu này không phải của bạn.", ephemeral=True)
            return False
        return True

    def _sync_buttons(self):
        last_index = len(self.entries) - 1
        self.first_page.disabled = self.page <= 0
        self.previous_page.disabled = self.page <= 0
        self.next_page.disabled = self.page >= last_index
        self.last_page.disabled = self.page >= last_index

    def build_embed(self) -> discord.Embed:
        entry = self.entries[self.page]
        description = entry.content.strip() if entry.content.strip() else "*Tin nhắn không có nội dung text.*"
        if len(description) > 3900:
            description = description[:3897] + "..."

        embed = discord.Embed(
            title="🕵️ Snipe",
            description=description,
            color=discord.Color.from_rgb(46, 48, 53),
            timestamp=entry.deleted_at,
        )
        embed.set_author(name=entry.author_name, icon_url=entry.author_avatar)
        embed.add_field(name="Kênh", value=f"<#{entry.channel_id}>", inline=True)
        embed.add_field(name="Trang", value=f"`{self.page + 1}/{len(self.entries)}`", inline=True)
        embed.add_field(name="Đã xoá lúc", value=f"<t:{int(entry.deleted_at.timestamp())}:R>", inline=True)

        image_url = next((url for url in entry.attachments if _is_image_url(url)), None)
        if image_url:
            embed.set_image(url=image_url)
        other_attachments = [url for url in entry.attachments if url != image_url]
        if other_attachments:
            links = "\n".join(f"[File {index}]({url})" for index, url in enumerate(other_attachments[:8], 1))
            embed.add_field(name="File đính kèm", value=links, inline=False)

        embed.set_footer(text="Tin mới xoá nhất nằm ở trang 1")
        return embed

    async def _update(self, interaction: discord.Interaction):
        self._sync_buttons()
        await interaction.response.edit_message(embed=self.build_embed(), view=self)

    @discord.ui.button(label="Đầu", style=discord.ButtonStyle.secondary, emoji="⏮️")
    async def first_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.page = 0
        await self._update(interaction)

    @discord.ui.button(label="Lùi", style=discord.ButtonStyle.secondary, emoji="◀️")
    async def previous_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.page = max(0, self.page - 1)
        await self._update(interaction)

    @discord.ui.button(label="Tiếp", style=discord.ButtonStyle.secondary, emoji="▶️")
    async def next_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.page = min(len(self.entries) - 1, self.page + 1)
        await self._update(interaction)

    @discord.ui.button(label="Cuối", style=discord.ButtonStyle.secondary, emoji="⏭️")
    async def last_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.page = len(self.entries) - 1
        await self._update(interaction)


def _is_image_url(url: str) -> bool:
    lowered = url.lower().split("?")[0]
    return lowered.endswith((".png", ".jpg", ".jpeg", ".gif", ".webp"))


class SnipeCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.deleted_messages: dict[int, deque[DeletedMessage]] = defaultdict(
            lambda: deque(maxlen=MAX_SNIPES_PER_CHANNEL)
        )

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        if message.guild is None or message.author == self.bot.user:
            return

        attachments = [attachment.url for attachment in message.attachments]
        entry = DeletedMessage(
            author_id=message.author.id,
            author_name=getattr(message.author, "display_name", message.author.name),
            author_avatar=message.author.display_avatar.url,
            content=message.content or "",
            channel_id=message.channel.id,
            channel_name=getattr(message.channel, "name", str(message.channel.id)),
            deleted_at=datetime.now().astimezone(),
            attachments=attachments,
        )
        self.deleted_messages[message.channel.id].appendleft(entry)

    @commands.command(name="snipe", aliases=["sn"])
    async def snipe(self, ctx: commands.Context, amount: str = "1"):
        if ctx.guild is None:
            await ctx.send("❌ Lệnh này chỉ dùng trong server.")
            return

        history = list(self.deleted_messages.get(ctx.channel.id, []))
        if not history:
            await ctx.send("❌ Chưa có tin nhắn nào bị xoá trong kênh này.")
            return

        amount_text = str(amount or "1").strip().lower()
        if amount_text == "all":
            limit = MAX_SNIPES_PER_CHANNEL
        else:
            try:
                limit = int(amount_text)
            except ValueError:
                await ctx.send("❌ Dùng: `snipe [số|all]`, ví dụ `sn`, `sn 10`, `sn all`.")
                return
            if limit <= 0:
                await ctx.send("❌ Số lượng phải lớn hơn 0.")
                return

        entries = history[: min(limit, MAX_SNIPES_PER_CHANNEL)]
        view = SnipeHistoryView(entries, ctx.author.id)
        await ctx.send(embed=view.build_embed(), view=view, allowed_mentions=discord.AllowedMentions.none())


async def setup(bot: commands.Bot):
    await bot.add_cog(SnipeCog(bot))
