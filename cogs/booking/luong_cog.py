from datetime import datetime

import discord
from discord.ext import commands

from cogs.admin_command_utils import create_error_splash, create_success_splash
from cogs.booking.booking_command_utils import BookingCommandBase
from models.constants import ERROR_MESSAGE


class BookingLuongCog(BookingCommandBase):
    async def _send_private_salary(self, ctx, embed: discord.Embed):
        try:
            await ctx.author.send(embed=embed)
        except discord.Forbidden:
            await ctx.send(embed=create_error_splash("❌ Không Gửi Được DM", "Bạn đang tắt DM từ server này, hãy mở DM rồi thử lại."))
            return
        except discord.HTTPException as exc:
            await ctx.send(embed=create_error_splash("❌ Không Gửi Được DM", str(exc)))
            return

        await ctx.send(embed=create_success_splash("✅ Đã Gửi DM", "Mình đã gửi bảng tính lương riêng cho bạn."))

    @commands.command(name="luong")
    async def luong(self, ctx, *, content: str = None):
        try:
            if not content or not content.strip():
                await ctx.send("❌ Dùng: `luong <nội dung>`")
                return
            self.service.add_booking_message(ctx.author.id, ctx.author.display_name)
            embed = discord.Embed(color=discord.Color.from_rgb(46, 48, 53))
            embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.display_avatar.url)
            embed.description = content.strip()
            embed.set_footer(text=f"Hôm nay lúc {datetime.now().strftime('%H:%M')}")
            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(f"{ERROR_MESSAGE} {str(e)}")

    @commands.command(name="tinhluong")
    async def tinhluong(self, ctx, *, target_text: str = None):
        try:
            target_text = (target_text or "").strip()

            if target_text.lower() == "all":
                if not self.can_use_role_or_admin(ctx, "tinhluong"):
                    await ctx.send(embed=create_error_splash("❌ Quyền Bị Từ Chối", "Chỉ admin bot hoặc role có quyền `tinhluong` trong DB mới xem được tất cả."))
                    return
                rows = self.service.get_all_bookings()
                await self._send_private_salary(ctx, self.build_tinhluong_all_embed(rows))
                return

            if target_text:
                member = await self.resolve_member(ctx, target_text)
                if not member:
                    await ctx.send(embed=create_error_splash("❌ Không Tìm Thấy User", f"Không tìm thấy `{target_text}` trong server."))
                    return
            else:
                member = ctx.author

            if member.id != ctx.author.id and not self.can_use_role_or_admin(ctx, "tinhluong"):
                await ctx.send(embed=create_error_splash("❌ Quyền Bị Từ Chối", "Chỉ admin bot hoặc role có quyền `tinhluong` trong DB mới xem booking của người khác."))
                return

            booking = self.service.get_or_create_booking(member.id, member.display_name)
            hour_details = self.service.get_booking_hour_details(member.id)
            await self._send_private_salary(ctx, self.build_tinhluong_dm_embed(member, booking, hour_details))
        except Exception as e:
            await ctx.send(f"{ERROR_MESSAGE} {str(e)}")


async def setup(bot):
    await bot.add_cog(BookingLuongCog(bot))
