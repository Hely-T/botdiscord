import discord
from discord.ext import commands

from cogs.admin_command_utils import AdminCommandBase, create_error_splash, create_info_splash, format_vnd, parse_vnd_amount


class AdministratorLuongCog(AdminCommandBase):
    async def _require_booking_user(self, ctx, member: discord.Member) -> bool:
        system_role = self.guild_settings.get_system_role(ctx.guild.id, "booking")
        if not system_role:
            await ctx.send(embed=create_error_splash("❌ Chưa Set Role Booking", "Dùng `setrole @role booking` trước."))
            return False

        member_role_ids = [role.id for role in member.roles if role.name != "@everyone"]
        if int(system_role["role_id"]) not in member_role_ids:
            await ctx.send(embed=create_error_splash("❌ Không Phải Booking", f"{member.mention} không phải booking."))
            return False
        return True

    @commands.command(name="addluong")
    async def addluong(self, ctx, member: discord.Member, amount: str):
        if not await self.require_role_or_admin_ctx(ctx):
            return
        if not await self._require_booking_user(ctx, member):
            return
        try:
            parsed_amount = parse_vnd_amount(amount)
        except ValueError as exc:
            await ctx.send(embed=create_error_splash("❌ Số Tiền Không Hợp Lệ", str(exc)))
            return
        await self.send_stat_update(
            ctx,
            member,
            parsed_amount,
            "luong",
            "Cộng lương",
            dm_title="💰 Lương Đã Được Cộng",
            dm_description=f"Bạn vừa được cộng `{format_vnd(parsed_amount)}` VNĐ lương bởi {ctx.author.display_name}.",
        )

    @commands.command(name="subluong")
    async def subluong(self, ctx, member: discord.Member, amount: str):
        if not await self.require_role_or_admin_ctx(ctx):
            return
        if not await self._require_booking_user(ctx, member):
            return
        try:
            parsed_amount = parse_vnd_amount(amount)
        except ValueError as exc:
            await ctx.send(embed=create_error_splash("❌ Số Tiền Không Hợp Lệ", str(exc)))
            return
        await self.send_stat_update(
            ctx,
            member,
            parsed_amount,
            "luong",
            "Trừ lương",
            dm_title="⚠️ Lương Đã Bị Trừ",
            dm_description=f"Bạn vừa bị trừ `{format_vnd(parsed_amount)}` VNĐ lương bởi {ctx.author.display_name}.",
        )

    @commands.command(name="tongluong")
    async def tongluong(self, ctx):
        if not await self.require_role_or_admin_ctx(ctx):
            return
        total_luong = self.users.get_total_luong()
        users_count = len(self.users.db.fetch("SELECT user_id FROM users"))
        await ctx.send(
            embed=create_info_splash(
                "📊 Tổng Lương",
                f"Tổng lương trong database hiện tại là `{total_luong:,}` VNĐ.\nSố user đã có dữ liệu: `{users_count}`",
            )
        )


async def setup(bot):
    await bot.add_cog(AdministratorLuongCog(bot))
