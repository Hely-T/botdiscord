import discord
from discord.ext import commands

from cogs.admin_command_utils import AdminCommandBase, create_error_splash, create_success_splash, split_reason


class AdministratorBanCog(AdminCommandBase):
    @commands.command(name="ban")
    async def ban(self, ctx, member: discord.Member, *, reason: str = "Không có lý do"):
        if not await self.require_role_or_admin_ctx(ctx):
            return
        try:
            await member.ban(reason=split_reason(reason), delete_message_days=0)
            await ctx.send(embed=create_success_splash("✅ Ban Thành Công", f"Đã ban {member.mention}."))
        except Exception as exc:
            await ctx.send(embed=create_error_splash("❌ Ban Thất Bại", str(exc)))

    @commands.command(name="unban")
    async def unban(self, ctx, user_id: int, *, reason: str = "Không có lý do"):
        if not await self.require_role_or_admin_ctx(ctx):
            return
        try:
            await ctx.guild.unban(discord.Object(id=user_id), reason=split_reason(reason))
            await ctx.send(embed=create_success_splash("✅ Unban Thành Công", f"Đã unban user ID `{user_id}`."))
        except Exception as exc:
            await ctx.send(embed=create_error_splash("❌ Unban Thất Bại", str(exc)))


async def setup(bot):
    await bot.add_cog(AdministratorBanCog(bot))
