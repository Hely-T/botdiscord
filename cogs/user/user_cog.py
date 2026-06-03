from datetime import datetime

import discord
from discord.ext import commands

from config import PROFILE_HOUR_RATE_VND
from cogs.admin_command_utils import create_error_splash, create_success_splash, format_hours, format_vnd, parse_vnd_amount
from cogs.user_command_utils import UserCommandBase
from models.constants import ERROR_MESSAGE


class UserCog(UserCommandBase):
    @commands.command(name="profile")
    async def profile(self, ctx, member: discord.Member = None):
        try:
            if not member:
                member = ctx.author
            if member.id != ctx.author.id and not self.can_view_other_profile(ctx):
                await ctx.send("❌ Bạn chỉ được xem profile người khác khi là admin bot **hoặc** role của bạn có quyền dùng lệnh `profile`.")
                return
            user = self.service.get_or_create_user(member.id, member.name)
            avatar_url = member.display_avatar.url
            hours_value = format_hours(user.total_hours)
            money_from_hours = format_vnd(int(user.total_hours * PROFILE_HOUR_RATE_VND))
            embed = discord.Embed(color=discord.Color.from_rgb(46, 48, 53))
            embed.set_author(name=member.display_name, icon_url=avatar_url)
            embed.set_thumbnail(url=avatar_url)
            embed.add_field(name="• Tổng Giờ", value=f"`{hours_value} ({money_from_hours} VNĐ)`", inline=False)
            embed.add_field(name="• Tổng Donate", value=f"`{format_vnd(user.total_donate)} VNĐ`", inline=False)
            embed.add_field(name="💰 Tổng Tiền", value=f"`{format_vnd(user.total_money)} VNĐ`", inline=False)
            embed.set_footer(text=f"Hôm nay lúc {datetime.now().strftime('%H:%M')}")
            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(f"{ERROR_MESSAGE} {str(e)}")

    @commands.command(name="cash")
    async def cash(self, ctx, member: discord.Member = None):
        try:
            if ctx.guild is None:
                await ctx.send(embed=create_error_splash("❌ Chỉ Dùng Trong Server", "Lệnh `cash` chỉ hoạt động trong server."))
                return

            if not member:
                member = ctx.author
            if member.id != ctx.author.id and not self.can_view_other_profile(ctx):
                await ctx.send("❌ Bạn chỉ được xem cash người khác khi là admin bot **hoặc** role của bạn có quyền dùng lệnh `profile`.")
                return

            user = self.service.get_or_create_user(member.id, member.display_name)
            avatar_url = member.display_avatar.url
            is_self = member.id == ctx.author.id
            balance_text = (
                f"💰 | Bạn hiện đang có **{format_vnd(user.cash)} VNĐ**."
                if is_self
                else f"💰 | {member.mention} hiện đang có **{format_vnd(user.cash)} VNĐ**."
            )

            embed = discord.Embed(
                title="ACCOUNT BALANCE",
                description=balance_text,
                color=discord.Color.from_rgb(46, 48, 53),
            )
            embed.set_author(name=member.display_name, icon_url=avatar_url)
            embed.set_thumbnail(url=avatar_url)
            embed.set_footer(text=f"Hôm nay lúc {datetime.now().strftime('%H:%M')}")
            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(f"{ERROR_MESSAGE} {str(e)}")

    @commands.command(name="give")
    async def give(self, ctx, *args):
        try:
            if ctx.guild is None:
                await ctx.send(embed=create_error_splash("❌ Chỉ Dùng Trong Server", "Lệnh `give` chỉ hoạt động trong server."))
                return
            if len(args) != 2:
                await ctx.send("❌ Dùng: `give @user 100k` hoặc `give 100k @user`")
                return

            target = None
            amount = None
            for raw in args:
                if target is None:
                    try:
                        maybe_member = await commands.MemberConverter().convert(ctx, raw)
                        target = maybe_member
                        continue
                    except Exception:
                        pass

                if amount is None:
                    try:
                        amount = parse_vnd_amount(raw)
                        continue
                    except ValueError:
                        pass

            if target is None or amount is None:
                await ctx.send("❌ Dùng: `give @user 100k` hoặc `give 100k @user`")
                return

            if target.id == ctx.author.id:
                await ctx.send(embed=create_error_splash("❌ Không Hợp Lệ", "Bạn không thể tự give cho chính mình."))
                return

            result = self.service.transfer_cash(ctx.author.id, ctx.author.display_name, target.id, target.display_name, amount)
            await ctx.send(
                embed=create_success_splash(
                    "✅ Give Thành Công",
                    (
                        f"Đã chuyển `{format_vnd(amount)} VNĐ` từ {ctx.author.mention} đến {target.mention}.\n"
                        f"Cash của bạn còn: `{format_vnd(result['sender_cash'])} VNĐ`\n"
                        f"Cash của người nhận: `{format_vnd(result['receiver_cash'])} VNĐ`"
                    ),
                )
            )
        except Exception as e:
            await ctx.send(f"{ERROR_MESSAGE} {str(e)}")

    @commands.command(name="topusers")
    async def top_users(self, ctx, limit: int = 10):
        try:
            if limit < 1 or limit > 100:
                limit = 10
            top = self.service.get_top_users(limit)
            if not top:
                await ctx.send("Chưa có ai trong database!")
                return
            embed = discord.Embed(title=f"🏆 Top {len(top)} Users", color=discord.Color.gold())
            for i, user in enumerate(top, 1):
                embed.add_field(name=f"#{i} {user['username']}", value=f"⭐ {user['points']} points | Lvl {user['level']}", inline=False)
            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(f"{ERROR_MESSAGE} {str(e)}")


async def setup(bot):
    await bot.add_cog(UserCog(bot))
