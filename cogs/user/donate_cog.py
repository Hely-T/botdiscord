from __future__ import annotations

import asyncio

import discord
from discord import app_commands
from discord.ext import commands

from cogs.admin_command_utils import create_error_splash, create_success_splash, parse_vnd_amount
from cogs.user.payment_common import PaymentReloadView, finalize_paid_payment
from cogs.user_command_utils import UserCommandBase
from services.bank_service import BankPaymentService
from ui.user.payment_ui import build_config_status_embed, build_payment_embed, render_payment_card


CHECK_WORDS = {"reload", "check", "sodu", "sốdư", "số-dư", "balance", "kiemtra", "kiểmtra", "kt"}
CONFIG_WORDS = {"config", "cfg", "setup", "cauhinh", "cấuhình", "cấu-hình"}


class DonateCog(UserCommandBase):
    def __init__(self, bot: commands.Bot):
        super().__init__(bot)
        self.bank = BankPaymentService()

    async def _send_payment(self, target, amount_text: str):
        guild = target.guild
        if guild is None:
            await target.send(embed=create_error_splash("❌ Chỉ Dùng Trong Server", "Lệnh donate chỉ hoạt động trong server."))
            return None
        if not self.bank.is_configured(guild.id):
            await target.send(
                embed=create_error_splash(
                    "❌ Chưa Cấu Hình ACB",
                    "Bot admin cần dùng `donate config username|password|account|name ...` trước.",
                )
            )
            return None

        try:
            amount = parse_vnd_amount(amount_text)
        except ValueError as exc:
            await target.send(embed=create_error_splash("❌ Số Tiền Không Hợp Lệ", str(exc)))
            return None

        settings = self.bank.get_settings(guild.id) or {}
        user = target.author if isinstance(target, commands.Context) else target.user
        payment = self.bank.create_payment(guild.id, user.id, user.display_name, "donate", amount)
        card = await asyncio.to_thread(render_payment_card, payment, settings, "donate")
        embed = build_payment_embed(payment, settings, "donate", card is not None)
        view = PaymentReloadView(self, int(payment["id"]), user.id)

        if isinstance(target, commands.Context):
            message = await target.send(embed=embed, file=card, view=view) if card else await target.send(embed=embed, view=view)
        else:
            message = (
                await target.followup.send(embed=embed, file=card, view=view, wait=True)
                if card
                else await target.followup.send(embed=embed, view=view, wait=True)
            )
        self.bank.mark_message(int(payment["id"]), message.channel.id, message.id)
        return payment

    async def _resolve_payment_for_reload(self, guild_id: int, user_id: int, raw: str | None) -> dict | None:
        if raw:
            raw = raw.strip()
            return self.bank.get_payment(int(raw)) if raw.isdigit() else self.bank.get_payment_by_code(raw)
        pending = [
            payment
            for payment in self.bank.get_user_pending_payments(guild_id, user_id, limit=10)
            if payment.get("kind") == "donate"
        ]
        return pending[0] if pending else None

    async def _reload_payment(self, target, raw: str | None = None):
        guild = target.guild
        user = target.author if isinstance(target, commands.Context) else target.user
        if guild is None:
            await target.send(embed=create_error_splash("❌ Chỉ Dùng Trong Server", "Reload donate chỉ hoạt động trong server."))
            return

        payment = await self._resolve_payment_for_reload(guild.id, user.id, raw)
        if not payment:
            await target.send(embed=create_error_splash("❌ Không Có Payment", "Bạn chưa có QR donate pending để reload số dư."))
            return
        if int(payment["guild_id"]) != guild.id:
            await target.send(embed=create_error_splash("❌ Sai Server", "Payment này không thuộc server hiện tại."))
            return
        if int(payment["user_id"]) != user.id and not self.admins.is_admin(user.id):
            await target.send(embed=create_error_splash("❌ Quyền Bị Từ Chối", "Bạn không thể reload payment của người khác."))
            return

        result = await self.bank.check_payment_online(guild.id, payment["code"], int(payment["amount"]))
        if result.get("matched"):
            paid = await finalize_paid_payment(
                self.bot,
                self.bank,
                self.service,
                payment,
                transaction=result.get("transaction"),
            )
            if paid:
                await target.send(embed=create_success_splash("✅ Đã Cộng Cash", "Donate đã được xác nhận và cộng vào cash."))
            return
        detail = result.get("error") or "Chưa thấy giao dịch khớp số tiền và nội dung chuyển khoản."
        await target.send(embed=create_error_splash("❌ Chưa Nhận Được Tiền", detail))

    async def check_and_finalize_payment(self, interaction: discord.Interaction, payment_id: int):
        payment = self.bank.get_payment(payment_id)
        if not payment:
            await interaction.followup.send(embed=create_error_splash("❌ Không Tìm Thấy", "Không tìm thấy payment này."), ephemeral=True)
            return
        result = await self.bank.check_payment_online(int(payment["guild_id"]), payment["code"], int(payment["amount"]))
        if result.get("matched"):
            await finalize_paid_payment(
                self.bot,
                self.bank,
                self.service,
                payment,
                transaction=result.get("transaction"),
                interaction=interaction,
            )
            return
        detail = result.get("error") or "Chưa thấy giao dịch khớp số tiền và nội dung chuyển khoản."
        await interaction.followup.send(embed=create_error_splash("❌ Chưa Nhận Được Tiền", detail), ephemeral=True)

    async def _handle_config(self, ctx: commands.Context, args: tuple[str, ...]):
        if not await self.require_admin_ctx(ctx, "Chỉ bot admin mới được cấu hình donate/ngân hàng."):
            return
        if not args or args[0].lower() in {"show", "status", "info"}:
            await ctx.send(embed=build_config_status_embed(self.bank.get_settings(ctx.guild.id) or {}))
            return

        key = args[0].lower()
        value = " ".join(args[1:]).strip()
        if key in {"channel", "thankchannel", "thankschannel", "kenh", "kênh"}:
            if not value or value.lower() in {"off", "none", "xoa", "xoá"}:
                self.bank.set_donate_channel(ctx.guild.id, None)
                await ctx.send(embed=create_success_splash("✅ Đã Tắt Kênh Cảm Ơn", "Donate vẫn cộng cash nhưng không gửi lời cảm ơn ra kênh."))
                return
            try:
                channel = await commands.TextChannelConverter().convert(ctx, value)
            except commands.BadArgument:
                await ctx.send(embed=create_error_splash("❌ Không Tìm Thấy Kênh", "Dùng: `donate config channel #channel`."))
                return
            self.bank.set_donate_channel(ctx.guild.id, channel.id)
            await ctx.send(embed=create_success_splash("✅ Đã Set Kênh Cảm Ơn", f"Donate sẽ cảm ơn tại {channel.mention}."))
            return

        if key in {"thank", "thanks", "template", "thanks_template", "camon", "cảmơn"}:
            if not value:
                await ctx.send(
                    embed=create_error_splash(
                        "❌ Thiếu Nội Dung",
                        "Dùng: `donate config thanks Cảm ơn {user} đã donate {amount} VNĐ!`.",
                    )
                )
                return
            self.bank.set_donate_template(ctx.guild.id, value)
            await ctx.send(embed=create_success_splash("✅ Đã Set Lời Cảm Ơn", value))
            return

        if key == "decor":
            key = "donate_decor"
        if key == "auto":
            value = value or "on"
        if not value:
            await ctx.send(embed=create_error_splash("❌ Thiếu Giá Trị", "Dùng: `donate config <key> <value>`."))
            return
        try:
            self.bank.set_setting(ctx.guild.id, key, value)
        except Exception as exc:
            await ctx.send(embed=create_error_splash("❌ Config Lỗi", str(exc)))
            return
        shown = "`Đã set`" if key in {"password", "pass"} else f"`{value}`"
        await ctx.send(embed=create_success_splash("✅ Đã Cập Nhật Donate Config", f"`{key}` = {shown}"))

    @commands.command(name="donate", aliases=["dn"])
    async def donate(self, ctx: commands.Context, *args):
        if ctx.guild is None:
            await ctx.send(embed=create_error_splash("❌ Chỉ Dùng Trong Server", "Lệnh donate chỉ hoạt động trong server."))
            return
        if not args:
            await ctx.send(embed=create_error_splash("❌ Thiếu Số Tiền", "Dùng: `donate 100k` hoặc `donate reload`."))
            return

        first = args[0].lower()
        if first in CONFIG_WORDS:
            await self._handle_config(ctx, args[1:])
            return
        if first in CHECK_WORDS:
            await self._reload_payment(ctx, args[1] if len(args) > 1 else None)
            return
        await self._send_payment(ctx, " ".join(args))

    @app_commands.command(name="donate", description="Tạo QR donate")
    @app_commands.describe(amount="Số tiền donate, ví dụ 100k hoặc 100,000")
    async def slash_donate(self, interaction: discord.Interaction, amount: str):
        if interaction.guild is None:
            await interaction.response.send_message("❌ Chỉ dùng trong server.", ephemeral=True)
            return
        await interaction.response.defer(thinking=True)
        await self._send_payment(interaction, amount)


async def setup(bot):
    await bot.add_cog(DonateCog(bot))
