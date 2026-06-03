from __future__ import annotations

import discord
from discord.ext import commands

from cogs.admin_command_utils import format_hours, format_vnd
from services.admin_service import AdminService
from services.booking_service import BookingService
from services.role_permission_service import RolePermissionService


class BookingCommandBase(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self._service = None
        self._admins = None
        self._role_permissions = None

    @property
    def service(self) -> BookingService:
        if self._service is None:
            self._service = BookingService()
        return self._service

    @property
    def admins(self) -> AdminService:
        if self._admins is None:
            self._admins = AdminService()
        return self._admins

    @property
    def role_permissions(self) -> RolePermissionService:
        if self._role_permissions is None:
            self._role_permissions = RolePermissionService()
        return self._role_permissions

    def is_admin(self, user_id: int) -> bool:
        return self.admins.is_admin(user_id)

    def can_use_role_or_admin(self, ctx, command_name: str) -> bool:
        if self.is_admin(ctx.author.id):
            return True
        if ctx.guild is None:
            return False
        user_roles = [role.id for role in ctx.author.roles if role.name != "@everyone"]
        return self.role_permissions.user_can_use(ctx.guild.id, user_roles, command_name)

    async def resolve_member(self, ctx, raw: str):
        try:
            return await commands.MemberConverter().convert(ctx, raw)
        except Exception:
            return None

    def build_star_embed(self, member: discord.Member, booking: dict) -> discord.Embed:
        embed = discord.Embed(
            title=f"📘 Booking của {member.display_name}",
            color=discord.Color.from_rgb(46, 48, 53),
        )
        embed.set_author(name=member.display_name, icon_url=member.display_avatar.url)
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="Giờ đã book", value=f"`{format_hours(booking['booking_hours'])}`", inline=False)
        embed.add_field(name="Số tiền đã tiêu", value=f"`{format_vnd(booking['booking_spent_money'])} VNĐ`", inline=False)
        return embed

    def build_tinhluong_embed(self, member: discord.Member, booking: dict) -> discord.Embed:
        embed = discord.Embed(
            title=f"📘 Booking của {member.display_name}",
            color=discord.Color.from_rgb(46, 48, 53),
        )
        embed.set_author(name=member.display_name, icon_url=member.display_avatar.url)
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="Giờ đã book", value=f"`{format_hours(booking['booking_hours'])}`", inline=False)
        embed.add_field(name="Số tiền đã tiêu", value=f"`{format_vnd(booking['booking_spent_money'])} VNĐ`", inline=False)
        embed.add_field(name="Số tiền đã trừ", value=f"`{format_vnd(booking['booking_deducted_money'])} VNĐ`", inline=False)
        embed.add_field(name="Tiền tổng được nhận", value=f"`{format_vnd(booking['booking_received_money'])} VNĐ`", inline=False)
        embed.add_field(name="Tổng hiện tại", value=f"`{format_vnd(booking['booking_current_money'])} VNĐ`", inline=False)
        embed.add_field(name="Số lần nhắn luong", value=f"`{booking['booking_messages']}`", inline=False)
        return embed

    def build_tinhluong_dm_embed(self, member: discord.Member, booking: dict, hour_details: list[dict]) -> discord.Embed:
        embed = discord.Embed(
            title=f"📘 Tính lương của {member.display_name}",
            color=discord.Color.from_rgb(46, 48, 53),
        )
        embed.set_author(name=member.display_name, icon_url=member.display_avatar.url)
        embed.set_thumbnail(url=member.display_avatar.url)

        if hour_details:
            detail_lines = [
                f"**{format_hours(row['hour_value'])}:** `{int(row['count'])}`"
                for row in hour_details
            ]
            detail_text = "\n".join(detail_lines)
        else:
            detail_text = "Chưa có dữ liệu chi tiết theo từng mốc giờ."

        embed.add_field(name="**Số giờ đã được book chi tiết**", value=detail_text, inline=False)
        embed.add_field(name="**Tổng tiền**", value=f"`{format_vnd(booking['booking_received_money'])} VNĐ`", inline=False)
        embed.add_field(name="**Số tiền đã dùng**", value=f"`{format_vnd(booking['booking_deducted_money'])} VNĐ`", inline=False)
        embed.add_field(name="**Còn lại**", value=f"`{format_vnd(booking['booking_current_money'])} VNĐ`", inline=False)
        return embed

    def build_tinhluong_all_embed(self, rows: list[dict]) -> discord.Embed:
        embed = discord.Embed(
            title="📘 Tính lương tất cả booking",
            color=discord.Color.from_rgb(46, 48, 53),
        )
        if not rows:
            embed.description = "Chưa có dữ liệu booking."
            return embed

        lines = []
        for index, row in enumerate(rows[:20], 1):
            lines.append(
                "\n".join(
                    [
                        f"**#{index} {row['username']}**",
                        f"**Tổng tiền:** `{format_vnd(row['booking_received_money'])} VNĐ`",
                        f"**Số tiền đã dùng:** `{format_vnd(row['booking_deducted_money'])} VNĐ`",
                        f"**Còn lại:** `{format_vnd(row['booking_current_money'])} VNĐ`",
                    ]
                )
            )

        embed.description = "\n\n".join(lines)
        if len(rows) > 20:
            embed.set_footer(text=f"Đang hiển thị 20/{len(rows)} booking đầu tiên.")
        return embed
