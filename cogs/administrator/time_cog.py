import discord
from discord.ext import commands

from cogs.admin_command_utils import AdminCommandBase


class AdministratorTimeCog(AdminCommandBase):
    @commands.command(name="addtime")
    async def addtime(self, ctx, member: discord.Member, hours: float):
        await self.send_stat_update(ctx, member, hours, "total_hours", "Cộng giờ")

    @commands.command(name="subtime")
    async def subtime(self, ctx, member: discord.Member, hours: float):
        await self.send_stat_update(ctx, member, hours, "total_hours", "Trừ giờ")


async def setup(bot):
    await bot.add_cog(AdministratorTimeCog(bot))
