from __future__ import annotations

import asyncio
import random
import re
import shlex
import time
from dataclasses import dataclass
from datetime import datetime

import discord
from discord import app_commands
from discord.ext import commands

from cogs.admin_command_utils import (
    AdminCommandBase,
    create_error_splash,
    create_info_splash,
    create_success_splash,
    format_duration_seconds,
    parse_duration,
)
from services.giveaway_service import GiveawayService


MAX_GIVEAWAY_QUANTITY = 20
GIVEAWAY_EMOJI = "🎉"
CUSTOM_EMOJI_RE = re.compile(r"<a?:[A-Za-z0-9_~]+:(\d+)>")


@dataclass
class GiveawayCreatePayload:
    reward: str
    duration_seconds: int
    winners_count: int
    quantity: int = 1
    template: str = ""


class GiveawayWinnerSelect(discord.ui.Select):
    def __init__(self, cog: "AdministratorGiveawayCog", giveaway: dict, participants: list[dict]):
        self.cog = cog
        self.giveaway = giveaway
        winners_count = int(giveaway["winners_count"])
        options = [
            discord.SelectOption(
                label=str(row["username"])[:100],
                value=str(row["user_id"]),
                description=f"ID {row['user_id']}"[:100],
                emoji=cog.giveaway_entry_emoji(giveaway),
            )
            for row in participants[:25]
        ]
        super().__init__(
            placeholder=f"Chọn {min(winners_count, len(options))} winner thủ công...",
            min_values=1,
            max_values=max(1, min(winners_count, len(options))),
            options=options,
            custom_id=f"giveaway:set_winner:{giveaway['giveaway_id']}",
        )

    async def callback(self, interaction: discord.Interaction):
        winner_ids = [int(value) for value in self.values]
        await self.cog._save_selected_winners_interaction(interaction, int(self.giveaway["giveaway_id"]), winner_ids)


class GiveawayManualSetView(discord.ui.View):
    def __init__(self, cog: "AdministratorGiveawayCog", giveaway: dict, participants: list[dict]):
        super().__init__(timeout=900)
        self.cog = cog
        self.giveaway = giveaway
        if participants:
            self.add_item(GiveawayWinnerSelect(cog, giveaway, participants))

    @discord.ui.button(label="Random winner", style=discord.ButtonStyle.primary, emoji="🎲", custom_id="giveaway:manual_random")
    async def random_winner(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.cog._random_winners_interaction(interaction, int(self.giveaway["giveaway_id"]))


class AdministratorGiveawayCog(AdminCommandBase):
    def __init__(self, bot: commands.Bot):
        super().__init__(bot)
        self.service = GiveawayService()
        self._end_tasks: dict[int, asyncio.Task] = {}
        self._restored = False

    def cog_unload(self):
        for task in self._end_tasks.values():
            task.cancel()
        self._end_tasks.clear()

    @commands.Cog.listener()
    async def on_ready(self):
        await self.restore_active_giveaways()

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        if payload.user_id == self.bot.user.id:
            return
        giveaway = self.service.get_giveaway_by_message_id(int(payload.message_id))
        if not giveaway:
            return
        if not self._emoji_matches(payload.emoji, self.giveaway_entry_emoji(giveaway)):
            return
        giveaway_id = int(giveaway["giveaway_id"])
        if giveaway["status"] != "active":
            return
        if int(giveaway["ends_at"]) <= int(time.time()):
            await self._end_giveaway(giveaway_id, automatic=True)
            return

        username = None
        if payload.member:
            username = payload.member.display_name
        if not username:
            try:
                user = self.bot.get_user(payload.user_id) or await self.bot.fetch_user(payload.user_id)
                username = getattr(user, "display_name", user.name)
            except (discord.NotFound, discord.HTTPException):
                username = str(payload.user_id)

        self.service.add_participant(giveaway_id, payload.user_id, username)
        await self.refresh_giveaway_message(giveaway_id)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent):
        if payload.user_id == self.bot.user.id:
            return
        giveaway = self.service.get_giveaway_by_message_id(int(payload.message_id))
        if not giveaway or giveaway["status"] != "active":
            return
        if not self._emoji_matches(payload.emoji, self.giveaway_entry_emoji(giveaway)):
            return
        self.service.remove_participant(int(giveaway["giveaway_id"]), payload.user_id)
        await self.refresh_giveaway_message(int(giveaway["giveaway_id"]))

    async def restore_active_giveaways(self):
        if self._restored:
            return
        self._restored = True
        for giveaway in self.service.get_active_giveaways():
            giveaway_id = int(giveaway["giveaway_id"])
            await self.refresh_giveaway_message(giveaway_id)
            self._schedule_end(giveaway)

    @staticmethod
    async def _delete_invocation_message(ctx):
        try:
            await ctx.message.delete()
        except (discord.Forbidden, discord.NotFound, discord.HTTPException):
            pass

    @staticmethod
    def _is_duration_token(token: str) -> bool:
        return bool(re.fullmatch(r"\d+(?:\.\d+)?[smhd]", token.strip().lower()))

    @staticmethod
    def _is_positive_int_token(token: str) -> bool:
        return bool(re.fullmatch(r"\d+", token.strip()))

    def _parse_prefix_payload(self, content: str) -> GiveawayCreatePayload:
        raw = (content or "").strip()
        if not raw:
            raise ValueError("Dùng: `ga 1d 1 100k 10`.")

        tokens = shlex.split(raw)
        if tokens and tokens[0].lower() in {"create", "c", "tao", "tạo"}:
            tokens = tokens[1:]
        if len(tokens) < 3:
            raise ValueError("Thiếu dữ liệu. Dùng: `ga <thời gian> <số người win> <nội dung> [số lượng ga]`.")

        duration_index = None
        duration_seconds = None
        for index, token in enumerate(tokens):
            if not self._is_duration_token(token):
                continue
            duration_seconds = parse_duration(token)
            duration_index = index
            break
        if duration_index is None or not duration_seconds:
            raise ValueError("Thiếu thời gian. Ví dụ: `10m`, `1h`, `1d`.")

        remaining = [(index, token) for index, token in enumerate(tokens) if index != duration_index]
        int_positions = [
            (position, token)
            for position, token in remaining
            if self._is_positive_int_token(token)
        ]
        if not int_positions:
            raise ValueError("Thiếu số lượng người win. Ví dụ: `ga 1d 1 100k`.")

        winners_position, winners_token = int_positions[0]
        quantity = 1
        quantity_position = None
        if len(int_positions) >= 2 and int_positions[-1][0] == remaining[-1][0]:
            quantity_position, quantity_token = int_positions[-1]
            quantity = int(quantity_token)

        winners_count = int(winners_token)
        reward_tokens = [
            token
            for position, token in remaining
            if position not in {winners_position, quantity_position}
        ]
        reward = " ".join(reward_tokens).strip()

        return self._validate_payload(
            GiveawayCreatePayload(
                reward=reward,
                duration_seconds=int(duration_seconds),
                winners_count=winners_count,
                quantity=quantity,
            )
        )

    def _validate_payload(self, payload: GiveawayCreatePayload) -> GiveawayCreatePayload:
        payload.reward = payload.reward.strip()
        payload.template = (payload.template or "").strip()
        if not payload.reward:
            raise ValueError("Nội dung phần thưởng không được để trống.")
        if payload.duration_seconds <= 0:
            raise ValueError("Thời gian giveaway phải lớn hơn 0.")
        if payload.winners_count <= 0:
            raise ValueError("Số người win phải lớn hơn 0.")
        if payload.quantity <= 0:
            raise ValueError("Số lượng giveaway phải lớn hơn 0.")
        if payload.quantity > MAX_GIVEAWAY_QUANTITY:
            raise ValueError(f"Tối đa chỉ tạo `{MAX_GIVEAWAY_QUANTITY}` giveaway một lần để tránh spam.")
        if len(payload.reward) > 250:
            raise ValueError("Nội dung phần thưởng tối đa 250 ký tự.")
        if len(payload.template) > 500:
            raise ValueError("Template tối đa 500 ký tự.")
        return payload

    @staticmethod
    def _local_footer_text() -> str:
        now = datetime.now().astimezone()
        return f"Giveaway • {now.strftime('%d/%m/%Y %H:%M')}"

    @staticmethod
    def _custom_emoji_id(raw: str) -> int | None:
        match = CUSTOM_EMOJI_RE.fullmatch(str(raw or "").strip())
        return int(match.group(1)) if match else None

    def normalize_entry_emoji(self, guild: discord.Guild | None, raw_emoji: str) -> str:
        raw = str(raw_emoji or "").strip()
        if not raw:
            return GIVEAWAY_EMOJI
        if CUSTOM_EMOJI_RE.fullmatch(raw):
            return raw
        if guild and raw.isdigit():
            emoji = guild.get_emoji(int(raw))
            if emoji:
                return str(emoji)
        if guild:
            lowered = raw.strip(":").lower()
            for emoji in guild.emojis:
                if emoji.name.lower() == lowered:
                    return str(emoji)
        return raw

    def get_entry_emoji(self, guild_id: int) -> str:
        return self.service.get_entry_emoji(guild_id)

    def giveaway_entry_emoji(self, giveaway: dict) -> str:
        return str(giveaway.get("entry_emoji") or self.get_entry_emoji(int(giveaway["guild_id"])) or GIVEAWAY_EMOJI)

    def _emoji_matches(self, payload_emoji: discord.PartialEmoji, expected_emoji: str) -> bool:
        expected = str(expected_emoji or GIVEAWAY_EMOJI)
        expected_id = self._custom_emoji_id(expected)
        if expected_id is not None:
            return int(payload_emoji.id or 0) == expected_id
        return str(payload_emoji) == expected

    async def _send_interaction_splash(self, interaction: discord.Interaction, embed: discord.Embed, ephemeral: bool = True):
        if interaction.response.is_done():
            await interaction.followup.send(embed=embed, ephemeral=ephemeral)
        else:
            await interaction.response.send_message(embed=embed, ephemeral=ephemeral)

    def _build_giveaway_embed(self, giveaway: dict, ended: bool = False) -> discord.Embed:
        winner_ids = self.service.decode_winner_ids(giveaway)
        selected_winner_ids = self.service.decode_selected_winner_ids(giveaway)
        entry_emoji = self.giveaway_entry_emoji(giveaway)
        status_text = "Đã kết thúc" if ended or giveaway["status"] == "ended" else "Đang mở"
        color = discord.Color.from_rgb(255, 136, 190) if status_text == "Đang mở" else discord.Color.from_rgb(89, 96, 110)

        embed = discord.Embed(
            title="🌸 GIVEAWAY BẮT ĐẦU 🌸" if status_text == "Đang mở" else "🏁 GIVEAWAY ĐÃ KẾT THÚC",
            description=(
                f"## {giveaway['reward']}\n\n"
                + (
                    "Kết quả winner ở bên dưới."
                    if status_text == "Đã kết thúc"
                    else f"Nhấn vào {entry_emoji} để tham gia."
                )
            ),
            color=color,
        )
        if status_text == "Đã kết thúc":
            winners_text = ", ".join(f"<@{user_id}>" for user_id in winner_ids) if winner_ids else "`Không có`"
            embed.add_field(name="🏆 Người thắng", value=winners_text, inline=True)
        else:
            embed.add_field(name="⏳ Kết thúc", value=f"<t:{int(giveaway['ends_at'])}:R>", inline=True)
        embed.add_field(name="👑 Host", value=f"<@{int(giveaway['creator_id'])}>", inline=True)
        if selected_winner_ids and status_text == "Đang mở":
            embed.add_field(name="🎯 Winner đã chọn", value=f"`{len(selected_winner_ids)}` người", inline=True)

        if int(giveaway.get("quantity_total") or 1) > 1:
            embed.add_field(
                name="🎁 Gói",
                value=f"`{int(giveaway['quantity_index'])}/{int(giveaway['quantity_total'])}`",
                inline=True,
            )
        if giveaway.get("template"):
            embed.add_field(name="📝 Template", value=str(giveaway["template"])[:1024], inline=False)

        embed.set_footer(text=self._local_footer_text())
        return embed

    def _build_result_embed(self, giveaway: dict, winner_ids: list[int], title: str) -> discord.Embed:
        if winner_ids:
            winners_text = ", ".join(f"<@{user_id}>" for user_id in winner_ids)
            description = f"{winners_text}\nBạn đã thắng **{giveaway['reward']}**."
            color = discord.Color.green()
        else:
            description = "Không có người tham gia nên giveaway không có winner."
            color = discord.Color.red()
        embed = discord.Embed(title=title, description=description, color=color)
        embed.add_field(name="Phần thưởng", value=str(giveaway["reward"])[:1024], inline=False)
        return embed

    async def _send_winner_dms(self, giveaway: dict, winner_ids: list[int], reroll: bool = False, reroll_round: int | None = None):
        if not winner_ids:
            return

        guild = self.bot.get_guild(int(giveaway["guild_id"]))
        guild_name = guild.name if guild else "server"
        action_text = f"trúng thưởng reroll lần {reroll_round}" if reroll and reroll_round else "trúng thưởng"
        for user_id in winner_ids:
            try:
                user = self.bot.get_user(int(user_id)) or await self.bot.fetch_user(int(user_id))
                await user.send(
                    f"🎉 Chúc mừng! Bạn đã {action_text} giveaway **{giveaway['reward']}** tại **{guild_name}**.\n"
                    "Hãy quay lại server để nhận thưởng nhé."
                )
            except (discord.Forbidden, discord.NotFound, discord.HTTPException):
                continue

    async def _send_result_message(self, channel, giveaway: dict, winner_ids: list[int], reroll: bool = False, reroll_round: int | None = None):
        if winner_ids:
            winners_text = ", ".join(f"<@{user_id}>" for user_id in winner_ids)
            prefix = f"🔄 Giveaway đã reroll lần {reroll_round}!" if reroll and reroll_round else "🎉 Giveaway đã kết thúc!"
            content = (
                f"{prefix}\n"
                f"Chúc mừng {winners_text} đã trúng **{giveaway['reward']}**.\n"
                "Liên hệ host để nhận thưởng nhé."
            )
        else:
            content = (
                f"🎉 Giveaway **{giveaway['reward']}** đã kết thúc.\n"
                "Không có người tham gia nên không có winner."
            )
        try:
            await channel.send(content)
        except discord.HTTPException:
            pass

    async def _finish_giveaway_with_winners(self, giveaway_id: int, winner_ids: list[int], reroll: bool = False) -> tuple[bool, str]:
        giveaway = self.service.get_giveaway(giveaway_id)
        if not giveaway:
            return False, "Giveaway không tồn tại."

        if giveaway["status"] == "active":
            self.service.mark_ended(giveaway_id, winner_ids)
            task = self._end_tasks.pop(giveaway_id, None)
            current_task = asyncio.current_task()
            if task and task is not current_task and not task.done():
                task.cancel()
        else:
            self.service.update_winners(giveaway_id, winner_ids)
            reroll = True

        updated = self.service.get_giveaway(giveaway_id)
        message = await self._fetch_giveaway_message(updated)
        if message:
            await message.edit(embed=self._build_giveaway_embed(updated, ended=True), view=None)
            await self._send_result_message(message.channel, updated, winner_ids, reroll=reroll)
        await self._send_winner_dms(updated, winner_ids, reroll=reroll)
        return True, "Đã chọn winner và kết thúc giveaway."

    def _build_manual_set_embed(self, giveaway: dict, participants: list[dict]) -> discord.Embed:
        winners_count = int(giveaway["winners_count"])
        selected_winner_ids = self.service.decode_selected_winner_ids(giveaway)
        embed = create_info_splash(
            "🎯 Set Winner Giveaway",
            (
                f"**Phần thưởng:** {giveaway['reward']}\n"
                f"**Số winner cần chọn:** `{winners_count}`\n"
                "Chọn winner trong menu hoặc bấm **Random winner**.\n"
                "Winner chỉ được lưu lại, giveaway vẫn chạy tới hết giờ mới trả thưởng."
            ),
        )
        if selected_winner_ids:
            embed.add_field(
                name="Winner đã lưu",
                value=", ".join(f"<@{user_id}>" for user_id in selected_winner_ids),
                inline=False,
            )
        if not participants:
            embed.add_field(name="Người tham gia", value="Chưa có ai tham gia.", inline=False)
            return embed

        lines = [
            f"`{index}.` <@{int(row['user_id'])}> - `{row['username']}`"
            for index, row in enumerate(participants[:40], 1)
        ]
        if len(participants) > 40:
            lines.append(f"... và `{len(participants) - 40}` người nữa")
        embed.add_field(name=f"Người tham gia ({len(participants)})", value="\n".join(lines), inline=False)
        if len(participants) > 25:
            embed.add_field(
                name="Lưu ý",
                value="Discord chỉ cho menu chọn tối đa 25 người đầu. Nếu cần chọn người ngoài danh sách này, dùng random hoặc reroll sau.",
                inline=False,
            )
        return embed

    async def _show_manual_set_panel(self, interaction: discord.Interaction, giveaway_id: int):
        if not self.admins.is_hard_admin(interaction.user.id):
            await self._send_interaction_splash(
                interaction,
                create_error_splash("❌ Quyền Bị Từ Chối", "Bạn không có quyền dùng lệnh này."),
            )
            return

        giveaway = self.service.get_giveaway(giveaway_id)
        if not giveaway:
            await self._send_interaction_splash(
                interaction,
                create_error_splash("❌ Giveaway Không Tồn Tại", f"Không tìm thấy giveaway `{giveaway_id}`."),
            )
            return

        participants = self.service.get_participants(giveaway_id)
        embed = self._build_manual_set_embed(giveaway, participants)
        view = GiveawayManualSetView(self, giveaway, participants)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=interaction.guild is not None)

    async def _save_selected_winners_interaction(self, interaction: discord.Interaction, giveaway_id: int, winner_ids: list[int]):
        if not self.admins.is_hard_admin(interaction.user.id):
            await self._send_interaction_splash(
                interaction,
                create_error_splash("❌ Quyền Bị Từ Chối", "Bạn không có quyền dùng thao tác này."),
            )
            return
        giveaway = self.service.get_giveaway(giveaway_id)
        if not giveaway:
            await interaction.response.edit_message(
                embed=create_error_splash("❌ Giveaway Không Tồn Tại", f"Không tìm thấy giveaway `{giveaway_id}`."),
                view=None,
            )
            return
        if giveaway["status"] != "active":
            await interaction.response.edit_message(
                embed=create_error_splash("❌ Giveaway Đã Kết Thúc", "Giveaway đã kết thúc. Hãy dùng reroll nếu muốn quay lại winner."),
                view=None,
            )
            return

        if not interaction.response.is_done():
            await interaction.response.defer()
        self.service.set_selected_winners(giveaway_id, winner_ids)
        await self.refresh_giveaway_message(giveaway_id)
        winners_text = ", ".join(f"<@{user_id}>" for user_id in winner_ids)
        await interaction.edit_original_response(
            embed=create_success_splash(
                "✅ Đã Lưu Winner",
                f"Winner đã chọn: {winners_text}\nGiveaway vẫn chạy tới hết giờ rồi mới trả thưởng.",
            ),
            view=None,
        )

    async def _random_winners_interaction(self, interaction: discord.Interaction, giveaway_id: int):
        if not self.admins.is_hard_admin(interaction.user.id):
            await self._send_interaction_splash(
                interaction,
                create_error_splash("❌ Quyền Bị Từ Chối", "Bạn không có quyền dùng thao tác này."),
            )
            return

        giveaway = self.service.get_giveaway(giveaway_id)
        if not giveaway:
            await self._send_interaction_splash(
                interaction,
                create_error_splash("❌ Giveaway Không Tồn Tại", f"Không tìm thấy giveaway `{giveaway_id}`."),
            )
            return

        if giveaway["status"] != "active":
            await interaction.response.edit_message(
                embed=create_error_splash("❌ Giveaway Đã Kết Thúc", "Giveaway đã kết thúc. Hãy dùng reroll nếu muốn quay lại winner."),
                view=None,
            )
            return

        participants = self.service.get_participants(giveaway_id)
        winner_ids = self._pick_winners(participants, int(giveaway["winners_count"]))
        if not winner_ids:
            await interaction.response.edit_message(
                embed=create_error_splash("❌ Chưa Có Người Tham Gia", "Không có ai trong danh sách tham gia để random."),
                view=None,
            )
            return
        await self._save_selected_winners_interaction(interaction, giveaway_id, winner_ids)

    async def _fetch_giveaway_message(self, giveaway: dict) -> discord.Message | None:
        channel = self.bot.get_channel(int(giveaway["channel_id"]))
        if channel is None:
            try:
                channel = await self.bot.fetch_channel(int(giveaway["channel_id"]))
            except (discord.NotFound, discord.Forbidden, discord.HTTPException):
                return None
        try:
            return await channel.fetch_message(int(giveaway["message_id"]))
        except (discord.NotFound, discord.Forbidden, discord.HTTPException):
            return None

    async def refresh_giveaway_message(self, giveaway_id: int):
        giveaway = self.service.get_giveaway(giveaway_id)
        if not giveaway:
            return
        message = await self._fetch_giveaway_message(giveaway)
        if message:
            ended = giveaway["status"] == "ended"
            await message.edit(embed=self._build_giveaway_embed(giveaway, ended), view=None)
            if not ended:
                try:
                    await message.add_reaction(self.giveaway_entry_emoji(giveaway))
                except (discord.Forbidden, discord.HTTPException):
                    pass

    async def _create_one_giveaway(
        self,
        channel: discord.abc.Messageable,
        guild_id: int,
        creator_id: int,
        payload: GiveawayCreatePayload,
        quantity_index: int,
    ) -> int:
        ends_at = int(time.time()) + int(payload.duration_seconds)
        placeholder = discord.Embed(
            title="🌸 GIVEAWAY",
            description="Đang khởi tạo giveaway...",
            color=discord.Color.from_rgb(255, 136, 190),
        )
        message = await channel.send(embed=placeholder)
        giveaway_id = int(message.id)
        self.service.create_giveaway(
            giveaway_id=giveaway_id,
            guild_id=guild_id,
            channel_id=message.channel.id,
            message_id=message.id,
            creator_id=creator_id,
            reward=payload.reward,
            duration_seconds=payload.duration_seconds,
            winners_count=payload.winners_count,
            ends_at=ends_at,
            quantity_total=payload.quantity,
            quantity_index=quantity_index,
            template=payload.template,
            entry_emoji=self.get_entry_emoji(guild_id),
        )
        giveaway = self.service.get_giveaway(giveaway_id)
        await message.edit(embed=self._build_giveaway_embed(giveaway), view=None)
        try:
            await message.add_reaction(self.giveaway_entry_emoji(giveaway))
        except (discord.Forbidden, discord.HTTPException):
            pass
        self._schedule_end(giveaway)
        return giveaway_id

    async def _create_giveaways(self, channel, guild_id: int, creator_id: int, payload: GiveawayCreatePayload) -> list[int]:
        giveaway_ids = []
        for index in range(1, payload.quantity + 1):
            giveaway_ids.append(
                await self._create_one_giveaway(
                    channel=channel,
                    guild_id=guild_id,
                    creator_id=creator_id,
                    payload=payload,
                    quantity_index=index,
                )
            )
        return giveaway_ids

    def _schedule_end(self, giveaway: dict):
        giveaway_id = int(giveaway["giveaway_id"])
        existing = self._end_tasks.pop(giveaway_id, None)
        if existing:
            existing.cancel()

        async def runner():
            try:
                delay = max(0, int(giveaway["ends_at"]) - int(time.time()))
                await asyncio.sleep(delay)
                await self._end_giveaway(giveaway_id, automatic=True)
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                print(f"❌ Lỗi auto end giveaway {giveaway_id}: {exc}")

        self._end_tasks[giveaway_id] = self.bot.loop.create_task(runner())

    def _pick_winners(self, participants: list[dict], winners_count: int, exclude_ids: set[int] | None = None) -> list[int]:
        exclude_ids = exclude_ids or set()
        pool = [row for row in participants if int(row["user_id"]) not in exclude_ids]
        if not pool:
            pool = participants
        if not pool:
            return []
        selected = random.sample(pool, min(winners_count, len(pool)))
        return [int(row["user_id"]) for row in selected]

    async def _end_giveaway(self, giveaway_id: int, automatic: bool = False) -> tuple[bool, str]:
        giveaway = self.service.get_giveaway(giveaway_id)
        if not giveaway:
            return False, "Giveaway không tồn tại."
        if giveaway["status"] == "ended":
            return False, "Giveaway đã kết thúc."

        participants = self.service.get_participants(giveaway_id)
        selected_winner_ids = self.service.decode_selected_winner_ids(giveaway)
        winner_ids = selected_winner_ids or self._pick_winners(participants, int(giveaway["winners_count"]))
        self.service.mark_ended(giveaway_id, winner_ids)
        updated = self.service.get_giveaway(giveaway_id)

        task = self._end_tasks.pop(giveaway_id, None)
        current_task = asyncio.current_task()
        if task and task is not current_task and not task.done():
            task.cancel()

        message = await self._fetch_giveaway_message(updated)
        if message:
            await message.edit(embed=self._build_giveaway_embed(updated, ended=True), view=None)
            await self._send_result_message(message.channel, updated, winner_ids)
        await self._send_winner_dms(updated, winner_ids)
        return True, "Giveaway đã kết thúc." if automatic else "Đã end giveaway."

    async def _reroll_giveaway(self, giveaway_id: int) -> tuple[bool, str, list[int]]:
        giveaway = self.service.get_giveaway(giveaway_id)
        if not giveaway:
            return False, "Giveaway không tồn tại.", []
        if giveaway["status"] != "ended":
            return False, "Giveaway chưa kết thúc, không thể reroll.", []

        participants = self.service.get_participants(giveaway_id)
        previous_winners = set(self.service.decode_winner_ids(giveaway))
        winner_ids = self._pick_winners(participants, int(giveaway["winners_count"]), exclude_ids=previous_winners)
        reroll_round = int(giveaway.get("reroll_count") or 0) + 1
        self.service.update_winners(giveaway_id, winner_ids, reroll_count=reroll_round)
        updated = self.service.get_giveaway(giveaway_id)

        message = await self._fetch_giveaway_message(updated)
        if message:
            await message.edit(embed=self._build_giveaway_embed(updated, ended=True), view=None)
            await self._send_result_message(message.channel, updated, winner_ids, reroll=True, reroll_round=reroll_round)
        await self._send_winner_dms(updated, winner_ids, reroll=True, reroll_round=reroll_round)
        return True, f"Đã reroll giveaway lần {reroll_round}.", winner_ids

    @commands.command(name="giveaway", aliases=["ga"])
    async def giveaway(self, ctx, *, content: str = None):
        if ctx.guild is None:
            await ctx.send(embed=create_error_splash("❌ Chỉ Dùng Trong Server", "Giveaway chỉ hoạt động trong server."))
            return
        if not await self.require_role_or_admin_ctx(ctx, "giveaway"):
            return

        content = (content or "").strip()
        first, _, rest = content.partition(" ")
        lowered = first.lower()
        if lowered in {"end", "stop", "gastop"}:
            await self._handle_end_command(ctx, rest.strip())
            return
        if lowered in {"reroll", "gareroll"}:
            await self._handle_reroll_command(ctx, rest.strip())
            return
        if lowered in {"config", "cfg", "emoji", "icon", "reaction"}:
            await self._handle_config_command(ctx, rest.strip(), lowered)
            return

        try:
            payload = self._parse_prefix_payload(content)
            giveaway_ids = await self._create_giveaways(ctx.channel, ctx.guild.id, ctx.author.id, payload)
        except ValueError as exc:
            await ctx.send(embed=create_error_splash("❌ Sai Cú Pháp", str(exc)))
            return
        except Exception as exc:
            await ctx.send(embed=create_error_splash("❌ Tạo Giveaway Thất Bại", str(exc)))
            return

        await self._delete_invocation_message(ctx)
        if payload.quantity > 1:
            await ctx.send(
                embed=create_info_splash(
                    "🎉 Đã Tạo Giveaway",
                    f"Đã tạo `{len(giveaway_ids)}` giveaway.\nMuốn end/reroll/set thì chuột phải tin giveaway rồi chọn **Sao chép ID Tin Nhắn**.",
                )
            )

    async def _handle_end_command(self, ctx, giveaway_id_text: str):
        if not giveaway_id_text or not giveaway_id_text.strip().isdigit():
            await ctx.send(embed=create_error_splash("❌ Thiếu ID", "Dùng: `end <id giveaway>` hoặc `gastop <id giveaway>`."))
            return
        ok, message = await self._end_giveaway(int(giveaway_id_text.strip()))
        embed_factory = create_success_splash if ok else create_error_splash
        await ctx.send(embed=embed_factory("🎉 End Giveaway", message))

    async def _handle_reroll_command(self, ctx, giveaway_id_text: str):
        if not giveaway_id_text or not giveaway_id_text.strip().isdigit():
            await ctx.send(embed=create_error_splash("❌ Thiếu ID", "Dùng: `reroll <id giveaway>` hoặc `gareroll <id giveaway>`."))
            return
        ok, message, _ = await self._reroll_giveaway(int(giveaway_id_text.strip()))
        embed_factory = create_success_splash if ok else create_error_splash
        await ctx.send(embed=embed_factory("🔄 Reroll Giveaway", message))

    async def _handle_config_command(self, ctx, content: str, action: str = "config"):
        raw = (content or "").strip()
        if action in {"config", "cfg"}:
            first, _, rest = raw.partition(" ")
            if first.lower() in {"emoji", "icon", "reaction"}:
                raw = rest.strip()

        if not raw:
            current = self.get_entry_emoji(ctx.guild.id)
            await ctx.send(
                embed=create_info_splash(
                    "🎉 Giveaway Emoji",
                    f"Emoji tham gia hiện tại: {current}\nDùng: `ga config emoji <emoji>` hoặc `ga emoji <emoji>`.",
                )
            )
            return

        normalized = self.normalize_entry_emoji(ctx.guild, raw)
        self.service.set_entry_emoji(ctx.guild.id, normalized)
        await ctx.send(
            embed=create_success_splash(
                "✅ Đã Đổi Emoji Giveaway",
                f"Giveaway mới sẽ dùng {normalized} để tham gia.\nCác giveaway đang chạy vẫn giữ emoji cũ.",
            )
        )

    @commands.command(name="end")
    async def end(self, ctx, giveaway_id: str = None):
        if not await self.require_role_or_admin_ctx(ctx, "giveaway"):
            return
        await self._handle_end_command(ctx, giveaway_id or "")

    @commands.command(name="gastop")
    async def gastop(self, ctx, giveaway_id: str = None):
        if not await self.require_role_or_admin_ctx(ctx, "giveaway"):
            return
        await self._handle_end_command(ctx, giveaway_id or "")

    @commands.command(name="reroll")
    async def reroll(self, ctx, giveaway_id: str = None):
        if not await self.require_role_or_admin_ctx(ctx, "giveaway"):
            return
        await self._handle_reroll_command(ctx, giveaway_id or "")

    @commands.command(name="gareroll")
    async def gareroll(self, ctx, giveaway_id: str = None):
        if not await self.require_role_or_admin_ctx(ctx, "giveaway"):
            return
        await self._handle_reroll_command(ctx, giveaway_id or "")

    @app_commands.command(name="giveaway", description="Tạo, set, end hoặc reroll giveaway")
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.choices(
        action=[
            app_commands.Choice(name="create", value="create"),
            app_commands.Choice(name="set", value="set"),
            app_commands.Choice(name="end", value="end"),
            app_commands.Choice(name="reroll", value="reroll"),
            app_commands.Choice(name="config", value="config"),
        ]
    )
    @app_commands.describe(
        action="Chọn thao tác giveaway",
        reward="Nội dung/phần thưởng giveaway",
        duration="Thời gian: 10m, 1h, 1d",
        winners="Số lượng người thắng",
        quantity="Số lượng giveaway cần tạo",
        template="Template riêng nếu có",
        giveaway_id="ID giveaway/message ID khi set/end/reroll",
        emoji="Emoji tham gia khi action là config",
    )
    async def slash_giveaway(
        self,
        interaction: discord.Interaction,
        action: str,
        reward: str = "",
        duration: str = "",
        winners: int = 1,
        quantity: int = 1,
        template: str = "",
        giveaway_id: str = "",
        emoji: str = "",
    ):
        action = (action or "").strip().lower()
        if action == "config":
            if interaction.guild is None:
                await self._send_interaction_splash(
                    interaction,
                    create_error_splash("❌ Chỉ Dùng Trong Server", "Config emoji giveaway chỉ dùng trong server."),
                )
                return
            if not await self.require_role_or_admin_interaction(interaction, "giveaway"):
                return
            if not str(emoji or "").strip():
                current = self.get_entry_emoji(interaction.guild.id)
                await self._send_interaction_splash(
                    interaction,
                    create_info_splash("🎉 Giveaway Emoji", f"Emoji tham gia hiện tại: {current}"),
                )
                return
            normalized = self.normalize_entry_emoji(interaction.guild, emoji)
            self.service.set_entry_emoji(interaction.guild.id, normalized)
            await self._send_interaction_splash(
                interaction,
                create_success_splash(
                    "✅ Đã Đổi Emoji Giveaway",
                    f"Giveaway mới sẽ dùng {normalized} để tham gia.\nCác giveaway đang chạy vẫn giữ emoji cũ.",
                ),
            )
            return
        if action in {"set", "end", "reroll"}:
            if not str(giveaway_id).strip().isdigit():
                await self._send_interaction_splash(
                    interaction,
                    create_error_splash("❌ ID Không Hợp Lệ", "ID giveaway phải là số."),
                )
                return
            parsed_id = int(str(giveaway_id).strip())
            if action == "set":
                await self._show_manual_set_panel(interaction, parsed_id)
                return
            if interaction.guild is None:
                await self._send_interaction_splash(
                    interaction,
                    create_error_splash("❌ Chỉ Dùng Trong Server", "End/reroll giveaway bằng slash chỉ dùng trong server."),
                )
                return
            if not await self.require_role_or_admin_interaction(interaction, "giveaway"):
                return
            if action == "end":
                ok, message = await self._end_giveaway(parsed_id)
                embed_factory = create_success_splash if ok else create_error_splash
                await self._send_interaction_splash(interaction, embed_factory("🎉 End Giveaway", message))
                return
            ok, message, _ = await self._reroll_giveaway(parsed_id)
            embed_factory = create_success_splash if ok else create_error_splash
            await self._send_interaction_splash(interaction, embed_factory("🔄 Reroll Giveaway", message))
            return

        if interaction.guild is None or interaction.channel is None:
            await self._send_interaction_splash(
                interaction,
                create_error_splash("❌ Chỉ Dùng Trong Server", "Giveaway chỉ hoạt động trong server."),
            )
            return
        if not await self.require_role_or_admin_interaction(interaction, "giveaway"):
            return

        duration_seconds = parse_duration(duration) if self._is_duration_token(duration) else None
        if not duration_seconds:
            await self._send_interaction_splash(
                interaction,
                create_error_splash("❌ Thời Gian Không Hợp Lệ", "Ví dụ hợp lệ: `10m`, `1h`, `1d`."),
            )
            return

        try:
            payload = self._validate_payload(
                GiveawayCreatePayload(
                    reward=reward,
                    duration_seconds=int(duration_seconds),
                    winners_count=int(winners),
                    quantity=int(quantity),
                    template=template or "",
                )
            )
        except ValueError as exc:
            await self._send_interaction_splash(
                interaction,
                create_error_splash("❌ Sai Dữ Liệu Giveaway", str(exc)),
            )
            return

        await interaction.response.defer(ephemeral=True)
        try:
            giveaway_ids = await self._create_giveaways(interaction.channel, interaction.guild.id, interaction.user.id, payload)
        except Exception as exc:
            await interaction.followup.send(
                embed=create_error_splash("❌ Tạo Giveaway Thất Bại", str(exc)),
                ephemeral=True,
            )
            return

        await interaction.followup.send(
            embed=create_success_splash(
                "✅ Đã Tạo Giveaway",
                f"Đã tạo `{len(giveaway_ids)}` giveaway.\nMuốn end/reroll/set thì chuột phải tin giveaway rồi chọn **Sao chép ID Tin Nhắn**.",
            ),
                ephemeral=True,
            )


async def setup(bot):
    cog = AdministratorGiveawayCog(bot)
    await bot.add_cog(cog)
    if bot.is_ready():
        await cog.restore_active_giveaways()
