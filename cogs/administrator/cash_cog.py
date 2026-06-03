import discord
from discord.ext import commands

from cogs.admin_command_utils import AdminCommandBase, create_error_splash, parse_vnd_amount


class AdministratorCashCog(AdminCommandBase):
    @commands.command(name="addcash")
    async def addcash(self, ctx, member: discord.Member, amount: str):
        try:
            parsed_amount = parse_vnd_amount(amount)
        except ValueError as exc:
            await ctx.send(embed=create_error_splash("❌ Số Tiền Không Hợp Lệ", str(exc)))
            return
        await self.send_stat_update(ctx, member, parsed_amount, "cash", "Cộng cash")

    @commands.command(name="subcash")
    async def subcash(self, ctx, member: discord.Member, amount: str):
        try:
            parsed_amount = parse_vnd_amount(amount)
        except ValueError as exc:
            await ctx.send(embed=create_error_splash("❌ Số Tiền Không Hợp Lệ", str(exc)))
            return
        await self.send_stat_update(ctx, member, parsed_amount, "cash", "Trừ cash")


async def setup(bot):
    await bot.add_cog(AdministratorCashCog(bot))
