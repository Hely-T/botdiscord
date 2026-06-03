import discord
from discord.ext import commands

from cogs.admin_command_utils import AdminCommandBase


class AdministratorUserAdminCog(AdminCommandBase):
    @commands.command(name="addpoints")
    async def add_points(self, ctx, member: discord.Member, amount: int):
        if not await self.require_role_or_admin_ctx(ctx, "addpoints"):
            return
        if amount <= 0:
            await ctx.send("❌ Amount phải > 0!")
            return
        user = self.users.get_or_create_user(member.id, member.name)
        self.users.add_points(member.id, amount)
        embed = discord.Embed(title="✅ Points Added", color=discord.Color.green())
        embed.add_field(name="User", value=member.name)
        embed.add_field(name="Amount", value=amount)
        embed.add_field(name="New Total", value=user.points + amount)
        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(AdministratorUserAdminCog(bot))
