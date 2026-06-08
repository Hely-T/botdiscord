from __future__ import annotations

import discord
from discord.ext import commands

from cogs.admin_command_utils import create_error_splash, create_success_splash, format_vnd
from cogs.cash_log_utils import send_cash_log
from services.bank_service import BankPaymentService
from services.user_service import UserService
from ui.user.payment_ui import build_paid_embed


async def send_interaction_notice(
    interaction: discord.Interaction,
    *,
    embed: discord.Embed | None = None,
    content: str | None = None,
    ephemeral: bool = True,
) -> None:
    if interaction.response.is_done():
        await interaction.followup.send(content=content, embed=embed, ephemeral=ephemeral)
    else:
        await interaction.response.send_message(content=content, embed=embed, ephemeral=ephemeral)


async def _resolve_payment_user(bot: commands.Bot, guild: discord.Guild | None, payment: dict):
    user_id = int(payment["user_id"])
    if guild:
        member = guild.get_member(user_id)
        if member:
            return member
    try:
        return await bot.fetch_user(user_id)
    except (discord.NotFound, discord.HTTPException):
        return None


async def finalize_paid_payment(
    bot: commands.Bot,
    bank: BankPaymentService,
    users: UserService,
    payment: dict,
    *,
    transaction: dict | None = None,
    interaction: discord.Interaction | None = None,
) -> dict | None:
    latest = bank.get_payment(int(payment["id"]))
    if not latest:
        if interaction:
            await send_interaction_notice(
                interaction,
                embed=create_error_splash("❌ Không Tìm Thấy", "Không tìm thấy payment này trong database."),
            )
        return None
    if latest.get("status") == "paid":
        if interaction:
            await send_interaction_notice(
                interaction,
                embed=create_success_splash("✅ Đã Thanh Toán", "Payment này đã được cộng cash trước đó."),
            )
        return latest

    paid = bank.mark_paid(int(latest["id"]), transaction)
    if not paid:
        current = bank.get_payment(int(latest["id"]))
        if current and current.get("status") == "paid":
            if interaction:
                await send_interaction_notice(
                    interaction,
                    embed=create_success_splash("✅ Đã Thanh Toán", "Payment này đã được cộng cash trước đó."),
                )
            return current
        if interaction:
            await send_interaction_notice(
                interaction,
                embed=create_error_splash("❌ Không Thể Cộng Cash", "Payment này không còn ở trạng thái chờ."),
            )
        return current

    guild = bot.get_guild(int(paid["guild_id"]))
    user = await _resolve_payment_user(bot, guild, paid)
    username = getattr(user, "display_name", paid.get("username") or str(paid["user_id"]))
    users.get_or_create_user(int(paid["user_id"]), username)
    users.add_cash(int(paid["user_id"]), int(paid["amount"]))
    users.add_total_money(int(paid["user_id"]), int(paid["amount"]))
    if paid.get("kind") == "donate":
        users.add_total_donate(int(paid["user_id"]), int(paid["amount"]))

    await _edit_payment_message(bot, paid, user)
    await _send_donate_thanks(bot, bank, paid, user)

    tx_id = bank._transaction_id(transaction or {}) if transaction else paid.get("bank_transaction_id")
    tx_note = bank._transaction_text(transaction or {}) if transaction else paid.get("bank_description")
    await send_cash_log(
        guild,
        title="💝 Donate Thành Công" if paid.get("kind") == "donate" else "💳 Nạp Tiền Thành Công",
        actor=user,
        target=user,
        amount=int(paid["amount"]),
        action="donate" if paid.get("kind") == "donate" else "naptien",
        code=paid.get("code"),
        note=tx_note,
        transaction_id=tx_id,
    )

    if interaction:
        await send_interaction_notice(
            interaction,
            embed=create_success_splash(
                "✅ Đã Cộng Cash",
                f"Đã cộng `{format_vnd(int(paid['amount']))} VNĐ` vào cash của {user.mention if user else paid['username']}.",
            ),
        )
    return paid


async def _edit_payment_message(bot: commands.Bot, payment: dict, user) -> None:
    channel_id = payment.get("channel_id")
    message_id = payment.get("message_id")
    if not channel_id or not message_id:
        return
    channel = bot.get_channel(int(channel_id))
    if not hasattr(channel, "fetch_message"):
        return
    try:
        message = await channel.fetch_message(int(message_id))
        await message.edit(embed=build_paid_embed(payment, payment.get("kind") or "naptien", user), view=None)
    except (discord.NotFound, discord.Forbidden, discord.HTTPException):
        pass


async def _send_donate_thanks(bot: commands.Bot, bank: BankPaymentService, payment: dict, user) -> None:
    if payment.get("kind") != "donate":
        return
    guild = bot.get_guild(int(payment["guild_id"]))
    if not guild:
        return
    settings = bank.get_settings(guild.id) or {}
    channel_id = settings.get("donate_channel_id")
    if not channel_id:
        return
    channel = guild.get_channel(int(channel_id))
    if not isinstance(channel, discord.TextChannel):
        return

    mention = user.mention if user else f"<@{int(payment['user_id'])}>"
    username = getattr(user, "display_name", payment.get("username") or str(payment["user_id"]))
    template = settings.get("donate_thank_template") or "Cảm ơn {user} đã donate {amount} VNĐ cho {server}!"
    try:
        text = template.format(
            user=mention,
            username=username,
            amount=format_vnd(int(payment["amount"])),
            server=guild.name,
            code=payment.get("code") or "",
        )
    except KeyError:
        text = f"Cảm ơn {mention} đã donate {format_vnd(int(payment['amount']))} VNĐ cho {guild.name}!"

    try:
        await channel.send(text)
    except (discord.Forbidden, discord.HTTPException):
        pass


class PaymentReloadView(discord.ui.View):
    def __init__(self, cog, payment_id: int, user_id: int, *, timeout: float | None = 86400):
        super().__init__(timeout=timeout)
        self.cog = cog
        self.payment_id = int(payment_id)
        self.user_id = int(user_id)

    @discord.ui.button(label="Reload số dư / Đã chuyển tiền", emoji="🔄", style=discord.ButtonStyle.success)
    async def reload_payment(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id and not self.cog.admins.is_admin(interaction.user.id):
            await interaction.response.send_message("❌ Chỉ người tạo QR hoặc bot admin mới reload payment này.", ephemeral=True)
            return
        await interaction.response.defer(ephemeral=True, thinking=True)
        await self.cog.check_and_finalize_payment(interaction, self.payment_id)
