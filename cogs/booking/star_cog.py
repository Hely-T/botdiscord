from discord.ext import commands

from cogs.admin_command_utils import (
    create_error_splash,
    create_success_splash,
    create_warning_splash,
    format_hours,
    format_vnd,
    parse_vnd_amount,
)
from cogs.booking.booking_command_utils import BookingCommandBase
from models.constants import ERROR_MESSAGE


class BookingStarCog(BookingCommandBase):
    @commands.command(name="star")
    async def star(self, ctx, *args):
        try:
            if not args:
                booking = self.service.get_or_create_booking(ctx.author.id, ctx.author.display_name)
                await ctx.send(embed=self.build_star_embed(ctx.author, booking))
                return

            action = args[0].lower()
            if action in {"all", "top"}:
                if not (self.can_use_role_or_admin(ctx, "topbook") or self.can_use_role_or_admin(ctx, "topnap")):
                    await ctx.send(embed=create_error_splash("❌ Quyền Bị Từ Chối", "Chỉ admin hoặc role trong DB mới dùng `star top`."))
                    return
                hour_rows = self.service.get_top_booking_hours(10)
                recharge_rows = self.service.get_top_recharges(10)
                hour_lines = [
                    f"**#{index}** `{row['username']}` - `{format_hours(row['booking_hours'])}`"
                    for index, row in enumerate(hour_rows, 1)
                ]
                recharge_lines = [
                    f"**#{index}** `{row['username']}` - `{format_vnd(row['booking_received_money'])} VNĐ`"
                    for index, row in enumerate(recharge_rows, 1)
                ]
                description = (
                    "**Top giờ được book**\n"
                    f"{chr(10).join(hour_lines) if hour_lines else 'Chưa có dữ liệu.'}\n\n"
                    "**Top nạp tiền**\n"
                    f"{chr(10).join(recharge_lines) if recharge_lines else 'Chưa có dữ liệu.'}"
                )
                await ctx.send(embed=create_success_splash("⭐ Top", description))
                return

            if action in {"time", "money"}:
                if len(args) < 2:
                    await ctx.send("❌ Dùng: `star time <hours> [@user]` hoặc `star money <amount> [@user]`")
                    return

                target = ctx.author
                if len(args) >= 3:
                    maybe_member = await self.resolve_member(ctx, args[2])
                    if maybe_member:
                        target = maybe_member
                if target.id != ctx.author.id and not self.is_admin(ctx.author.id):
                    await ctx.send(embed=create_error_splash("❌ Quyền Bị Từ Chối", "Chỉ admin bot mới được thao tác trên người khác."))
                    return

                if action == "time":
                    amount = float(args[1])
                    money = self.service.add_booking_session(target.id, target.display_name, amount)
                    booking = self.service.get_or_create_booking(target.id, target.display_name)
                    await ctx.send(
                        embed=create_success_splash(
                            "✅ Ghi Nhận Giờ Book",
                            (
                                f"Đã cộng `{format_hours(amount)}` cho {target.mention}.\n"
                                f"Giá khách trả: `{format_vnd(money['spent_money'])} VNĐ`\n"
                                f"Booking nhận: `{format_vnd(money['received_money'])} VNĐ`\n"
                                f"Tổng giờ hiện tại: `{format_hours(booking['booking_hours'])}`"
                            ),
                        )
                    )
                    return

                amount = parse_vnd_amount(args[1])
                self.service.add_booking_received_money(target.id, target.display_name, amount)
                booking = self.service.get_or_create_booking(target.id, target.display_name)
                await ctx.send(embed=create_success_splash("✅ Ghi Nhận Tiền Nạp", f"Đã cộng `{format_vnd(amount)} VNĐ` cho {target.mention}.\nTổng tiền hiện tại: `{format_vnd(booking['booking_received_money'])} VNĐ`"))
                return

            target = await self.resolve_member(ctx, args[0])
            if target:
                if target.id != ctx.author.id and not self.is_admin(ctx.author.id):
                    await ctx.send(embed=create_error_splash("❌ Quyền Bị Từ Chối", "Chỉ admin bot mới được xem booking của người khác."))
                    return
                booking = self.service.get_or_create_booking(target.id, target.display_name)
                await ctx.send(embed=self.build_star_embed(target, booking))
                return

            await ctx.send("❌ Dùng: `star time <hours> [@user]`, `star money <amount> [@user]`, `star top`, hoặc `star @user`")
        except Exception as e:
            await ctx.send(f"{ERROR_MESSAGE} {str(e)}")


async def setup(bot):
    await bot.add_cog(BookingStarCog(bot))
