from datetime import datetime, timedelta, timezone

import discord
from discord.ext import commands

from cogs.admin_command_utils import (
    AdminCommandBase,
    create_error_splash,
    create_success_splash,
    parse_duration,
    split_reason,
)


class AdministratorMuteCog(AdminCommandBase):
    @commands.command(name="mute")
    async def mute(self, ctx, member: discord.Member, duration_or_reason: str = "60", *, reason: str = ""):
        if not await self.require_role_or_admin_ctx(ctx):
            return
        duration_seconds = parse_duration(duration_or_reason)
        if duration_seconds is None:
            duration_seconds = 3600
            reason = f"{duration_or_reason} {reason}".strip()
        timeout_until = datetime.now(timezone.utc) + timedelta(seconds=duration_seconds)
        try:
            await member.edit(timed_out_until=timeout_until, reason=split_reason(reason))
            await ctx.send(embed=create_success_splash("✅ Mute Thành Công", f"Đã mute {member.mention} trong `{duration_seconds}` giây."))
        except Exception as exc:
            await ctx.send(embed=create_error_splash("❌ Mute Thất Bại", str(exc)))

    @commands.command(name="unmute")
    async def unmute(self, ctx, member: discord.Member, *, reason: str = "Không có lý do"):
        if not await self.require_role_or_admin_ctx(ctx):
            return
        try:
            await member.edit(timed_out_until=None, reason=split_reason(reason))
            await ctx.send(embed=create_success_splash("✅ Unmute Thành Công", f"Đã gỡ mute cho {member.mention}."))
        except Exception as exc:
            await ctx.send(embed=create_error_splash("❌ Unmute Thất Bại", str(exc)))


async def setup(bot):
    await bot.add_cog(AdministratorMuteCog(bot))
