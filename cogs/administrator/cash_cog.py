import discord
from discord.ext import commands

from cogs.admin_command_utils import AdminCommandBase, create_error_splash, parse_vnd_amount


class AdministratorCashCog(AdminCommandBase):
    @staticmethod
    def _display_name_for_user(user) -> str:
        return (
            getattr(user, "display_name", None)
            or getattr(user, "global_name", None)
            or getattr(user, "name", None)
            or str(getattr(user, "id", "unknown"))
        )

    async def _resolve_cash_target(self, ctx, raw_target: str | None):
        if ctx.guild is not None:
            member = await self.resolve_member_target(ctx, raw_target)
            if member:
                return member
            await ctx.send(embed=create_error_splash("❌ Không Tìm Thấy User", f"User `{raw_target}` không có trong server."))
            return None

        if not await self.require_admin_ctx(ctx, "Chỉ bot admin mới được dùng `addcash/subcash` trong DMs."):
            return None

        if not raw_target:
            await ctx.send(embed=create_error_splash("❌ Thiếu User", "Hãy nhập @user hoặc user ID."))
            return None

        try:
            return await commands.UserConverter().convert(ctx, raw_target)
        except Exception:
            pass

        cleaned = str(raw_target).strip().strip("<@!>")
        if cleaned.isdigit():
            try:
                return await self.bot.fetch_user(int(cleaned))
            except (discord.NotFound, discord.Forbidden, discord.HTTPException):
                pass

        await ctx.send(embed=create_error_splash("❌ Không Tìm Thấy User", f"Không tìm thấy `{raw_target}`."))
        return None

    async def _handle_cash_update(self, ctx, raw_target: str | None, raw_amount: str | None, action_label: str):
        if not raw_target or not raw_amount:
            await ctx.send(embed=create_error_splash("❌ Thiếu tham số", f"Dùng: `{ctx.prefix}{ctx.command.name} @user <money>`."))
            return

        member = await self._resolve_cash_target(ctx, raw_target)
        if not member:
            return

        try:
            parsed_amount = parse_vnd_amount(raw_amount)
        except ValueError as exc:
            await ctx.send(embed=create_error_splash("❌ Số Tiền Không Hợp Lệ", str(exc)))
            return

        self.users.touch_user(member.id, self._display_name_for_user(member))
        await self.send_stat_update(ctx, member, parsed_amount, "cash", action_label)

    @commands.command(name="addcash", aliases=["ac"])
    async def addcash(self, ctx, member: str = None, amount: str = None):
        await self._handle_cash_update(ctx, member, amount, "Cộng cash")

    @commands.command(name="subcash", aliases=["sc"])
    async def subcash(self, ctx, member: str = None, amount: str = None):
        await self._handle_cash_update(ctx, member, amount, "Trừ cash")


async def setup(bot):
    await bot.add_cog(AdministratorCashCog(bot))
