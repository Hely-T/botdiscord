from datetime import datetime

import discord
from discord.ext import commands

from config import PROFILE_HOUR_RATE_VND
from cogs.admin_command_utils import create_error_splash, create_success_splash, format_hours, format_vnd, parse_vnd_amount, parse_vnd_amount_or_zero
from cogs.user_command_utils import UserCommandBase
from models.constants import ERROR_MESSAGE


class UserCog(UserCommandBase):
    STAT_ACTIONS = {
        "a": "add",
        "add": "add",
        "d": "remove",
        "del": "remove",
        "delete": "remove",
        "r": "remove",
        "rm": "remove",
        "remove": "remove",
        "e": "edit",
        "edit": "edit",
    }

    def _can_manage_stat(self, ctx, command_name: str) -> bool:
        if ctx.guild is None:
            return False
        if self.admins.is_admin(ctx.author.id):
            return True
        user_role_ids = [role.id for role in ctx.author.roles if role.name != "@everyone"]
        return self.role_permissions.user_can_use(ctx.guild.id, user_role_ids, command_name)

    def _can_view_other_stat(self, ctx, command_name: str) -> bool:
        return self._can_manage_stat(ctx, command_name) or self.can_view_other_profile(ctx)

    async def _resolve_member_arg(self, ctx, raw_member: str) -> discord.Member | None:
        try:
            return await commands.MemberConverter().convert(ctx, raw_member)
        except Exception:
            await ctx.send(embed=create_error_splash("❌ Không Tìm Thấy User", f"Không tìm thấy `{raw_member}` trong server."))
            return None

    async def _apply_cash_action(self, ctx, action: str, member: discord.Member, raw_amount: str):
        if not self._can_manage_stat(ctx, "cash"):
            await ctx.send(embed=create_error_splash("❌ Quyền Bị Từ Chối", "Chỉ bot admin hoặc role có quyền `cash` trong DB mới quản trị cash."))
            return

        try:
            amount = parse_vnd_amount_or_zero(raw_amount) if action == "edit" else parse_vnd_amount(raw_amount)
            if action in {"add", "edit"}:
                self.service.get_or_create_user(member.id, member.display_name)
            if action == "add":
                self.service.add_cash(member.id, amount)
                title = "✅ Cộng Cash Thành Công"
                detail = f"Đã cộng `{format_vnd(amount)} VNĐ` cho {member.mention}."
            elif action == "remove":
                self.service.remove_cash(member.id, amount)
                title = "✅ Trừ Cash Thành Công"
                detail = f"Đã trừ `{format_vnd(amount)} VNĐ` của {member.mention}."
            else:
                self.service.set_cash(member.id, amount)
                title = "✅ Sửa Cash Thành Công"
                detail = f"Đã set cash của {member.mention} thành `{format_vnd(amount)} VNĐ`."
        except Exception as exc:
            await ctx.send(embed=create_error_splash("❌ Cập Nhật Thất Bại", str(exc)))
            return

        await ctx.send(embed=create_success_splash(title, detail))

    @staticmethod
    def _parse_int_amount(raw_amount: str, allow_zero: bool = False, label: str = "Số lượng") -> int:
        try:
            amount = int(str(raw_amount).strip().replace(",", "").replace(".", ""))
        except ValueError as exc:
            raise ValueError(f"{label} `{raw_amount}` không hợp lệ") from exc
        if allow_zero:
            if amount < 0:
                raise ValueError(f"{label} không thể âm")
        elif amount <= 0:
            raise ValueError(f"{label} phải lớn hơn 0")
        return amount

    @staticmethod
    def _parse_hours_amount(raw_amount: str, allow_zero: bool = False) -> float:
        try:
            amount = float(str(raw_amount).strip().replace(",", "."))
        except ValueError as exc:
            raise ValueError(f"Số giờ `{raw_amount}` không hợp lệ") from exc
        if allow_zero:
            if amount < 0:
                raise ValueError("Giờ không thể âm")
        elif amount <= 0:
            raise ValueError("Số giờ phải lớn hơn 0")
        return amount

    async def _send_all_users_stat(self, ctx, field_name: str, title: str, value_builder, command_name: str):
        if not self._can_manage_stat(ctx, command_name):
            await ctx.send(embed=create_error_splash("❌ Quyền Bị Từ Chối", f"Chỉ bot admin hoặc role có quyền `{command_name}` trong DB mới xem được tất cả."))
            return
        rows = self.service.get_users_by_stat(field_name, 25)
        if not rows:
            await ctx.send(embed=create_error_splash("❌ Chưa Có Dữ Liệu", "Chưa có user nào trong database."))
            return
        lines = [
            f"**#{index}** `{row['username']}` - {value_builder(row)}"
            for index, row in enumerate(rows, 1)
        ]
        await ctx.send(embed=create_success_splash(title, "\n".join(lines)))

    async def _apply_points_action(self, ctx, action: str, member: discord.Member, raw_amount: str):
        if not self._can_manage_stat(ctx, "points") and not self._can_manage_stat(ctx, "addpoints"):
            await ctx.send(embed=create_error_splash("❌ Quyền Bị Từ Chối", "Chỉ bot admin hoặc role có quyền `points` trong DB mới quản trị points."))
            return
        try:
            amount = self._parse_int_amount(raw_amount, allow_zero=action == "edit", label="Points")
            if action in {"add", "edit"}:
                self.service.get_or_create_user(member.id, member.display_name)
            if action == "add":
                self.service.add_points(member.id, amount)
                title = "✅ Cộng Points Thành Công"
                detail = f"Đã cộng `{amount:,}` points cho {member.mention}."
            elif action == "remove":
                self.service.remove_points(member.id, amount)
                title = "✅ Trừ Points Thành Công"
                detail = f"Đã trừ `{amount:,}` points của {member.mention}."
            else:
                self.service.set_points(member.id, amount)
                title = "✅ Sửa Points Thành Công"
                detail = f"Đã set points của {member.mention} thành `{amount:,}`."
        except Exception as exc:
            await ctx.send(embed=create_error_splash("❌ Cập Nhật Thất Bại", str(exc)))
            return
        current_points = self.service.get_user(member.id).points
        await ctx.send(embed=create_success_splash(title, f"{detail}\nPoints hiện tại: `{int(current_points):,}`"))

    async def _apply_time_action(self, ctx, action: str, member: discord.Member, raw_amount: str):
        if not self._can_manage_stat(ctx, "time") and not self._can_manage_stat(ctx, "addtime"):
            await ctx.send(embed=create_error_splash("❌ Quyền Bị Từ Chối", "Chỉ bot admin hoặc role có quyền `time` trong DB mới quản trị giờ."))
            return
        try:
            hours = self._parse_hours_amount(raw_amount, allow_zero=action == "edit")
            if action in {"add", "edit"}:
                self.service.get_or_create_user(member.id, member.display_name)
            if action == "add":
                self.service.add_hours(member.id, hours)
                title = "✅ Cộng Giờ Thành Công"
                detail = f"Đã cộng `{format_hours(hours)}` cho {member.mention}."
            elif action == "remove":
                self.service.remove_hours(member.id, hours)
                title = "✅ Trừ Giờ Thành Công"
                detail = f"Đã trừ `{format_hours(hours)}` của {member.mention}."
            else:
                self.service.set_hours(member.id, hours)
                title = "✅ Sửa Giờ Thành Công"
                detail = f"Đã set giờ của {member.mention} thành `{format_hours(hours)}`."
        except Exception as exc:
            await ctx.send(embed=create_error_splash("❌ Cập Nhật Thất Bại", str(exc)))
            return
        current_hours = self.service.get_user(member.id).total_hours
        await ctx.send(embed=create_success_splash(title, f"{detail}\nGiờ hiện tại: `{format_hours(current_hours)}`"))

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
    async def cash(self, ctx, *args):
        try:
            if ctx.guild is None:
                await ctx.send(embed=create_error_splash("❌ Chỉ Dùng Trong Server", "Lệnh `cash` chỉ hoạt động trong server."))
                return

            if args:
                action = self.STAT_ACTIONS.get(args[0].lower())
                if action:
                    if len(args) != 3:
                        await ctx.send(embed=create_error_splash("❌ Sai Cú Pháp", "Dùng: `cash a/add @user <money>`, `cash r/rm/remove/d/delete @user <money>` hoặc `cash e/edit @user <money>`."))
                        return
                    member = await self._resolve_member_arg(ctx, args[1])
                    if not member:
                        return
                    await self._apply_cash_action(ctx, action, member, args[2])
                    return

                if args[0].lower() == "all":
                    await self._send_all_users_stat(
                        ctx,
                        "cash",
                        "💰 Tất Cả Cash",
                        lambda row: f"`{format_vnd(row['cash'])} VNĐ`",
                        "cash",
                    )
                    return

                member = await self._resolve_member_arg(ctx, args[0])
                if not member:
                    return
            else:
                member = ctx.author

            if not member:
                member = ctx.author
            if member.id != ctx.author.id and not self._can_view_other_stat(ctx, "cash"):
                await ctx.send("❌ Bạn chỉ được xem cash người khác khi là admin bot **hoặc** role của bạn có quyền dùng lệnh `cash`.")
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

    @commands.command(name="points")
    async def points(self, ctx, *args):
        try:
            if ctx.guild is None:
                await ctx.send(embed=create_error_splash("❌ Chỉ Dùng Trong Server", "Lệnh `points` chỉ hoạt động trong server."))
                return
            if args:
                action = self.STAT_ACTIONS.get(args[0].lower())
                if action:
                    if len(args) != 3:
                        await ctx.send(embed=create_error_splash("❌ Sai Cú Pháp", "Dùng: `points a/add @user <amount>`, `points r/rm/remove/d/delete @user <amount>` hoặc `points e/edit @user <amount>`."))
                        return
                    member = await self._resolve_member_arg(ctx, args[1])
                    if not member:
                        return
                    await self._apply_points_action(ctx, action, member, args[2])
                    return
                if args[0].lower() == "all":
                    await self._send_all_users_stat(
                        ctx,
                        "points",
                        "⭐ Tất Cả Points",
                        lambda row: f"`{int(row['points']):,}` points",
                        "points",
                    )
                    return
                member = await self._resolve_member_arg(ctx, args[0])
                if not member:
                    return
            else:
                member = ctx.author

            if member.id != ctx.author.id and not self._can_view_other_stat(ctx, "points"):
                await ctx.send("❌ Bạn chỉ được xem points người khác khi là admin bot **hoặc** role của bạn có quyền dùng lệnh `points`.")
                return
            user = self.service.get_or_create_user(member.id, member.display_name)
            embed = discord.Embed(
                title="POINTS",
                description=f"⭐ | {member.mention} hiện đang có **{int(user.points):,} points**.",
                color=discord.Color.from_rgb(46, 48, 53),
            )
            embed.set_author(name=member.display_name, icon_url=member.display_avatar.url)
            embed.set_thumbnail(url=member.display_avatar.url)
            embed.set_footer(text=f"Hôm nay lúc {datetime.now().strftime('%H:%M')}")
            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(f"{ERROR_MESSAGE} {str(e)}")

    @commands.command(name="time")
    async def time(self, ctx, *args):
        try:
            if ctx.guild is None:
                await ctx.send(embed=create_error_splash("❌ Chỉ Dùng Trong Server", "Lệnh `time` chỉ hoạt động trong server."))
                return
            if args:
                action = self.STAT_ACTIONS.get(args[0].lower())
                if action:
                    if len(args) != 3:
                        await ctx.send(embed=create_error_splash("❌ Sai Cú Pháp", "Dùng: `time a/add @user <hours>`, `time r/rm/remove/d/delete @user <hours>` hoặc `time e/edit @user <hours>`."))
                        return
                    member = await self._resolve_member_arg(ctx, args[1])
                    if not member:
                        return
                    await self._apply_time_action(ctx, action, member, args[2])
                    return
                if args[0].lower() == "all":
                    await self._send_all_users_stat(
                        ctx,
                        "total_hours",
                        "⏱️ Tất Cả Giờ",
                        lambda row: f"`{format_hours(row['total_hours'])}`",
                        "time",
                    )
                    return
                member = await self._resolve_member_arg(ctx, args[0])
                if not member:
                    return
            else:
                member = ctx.author

            if member.id != ctx.author.id and not self._can_view_other_stat(ctx, "time"):
                await ctx.send("❌ Bạn chỉ được xem giờ người khác khi là admin bot **hoặc** role của bạn có quyền dùng lệnh `time`.")
                return
            user = self.service.get_or_create_user(member.id, member.display_name)
            embed = discord.Embed(
                title="TIME",
                description=f"⏱️ | {member.mention} hiện đang có **{format_hours(user.total_hours)}**.",
                color=discord.Color.from_rgb(46, 48, 53),
            )
            embed.set_author(name=member.display_name, icon_url=member.display_avatar.url)
            embed.set_thumbnail(url=member.display_avatar.url)
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

            self.service.transfer_cash(ctx.author.id, ctx.author.display_name, target.id, target.display_name, amount)
            await ctx.send(
                embed=create_success_splash(
                    "✅ Give Thành Công",
                    f"Đã chuyển `{format_vnd(amount)} VNĐ` từ {ctx.author.mention} đến {target.mention}.",
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
