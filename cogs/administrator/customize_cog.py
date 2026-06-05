import aiohttp
import discord
from discord.ext import commands

from cogs.admin_command_utils import (
    AdminCommandBase,
    create_error_splash,
    create_info_splash,
    create_success_splash,
    create_warning_splash,
    parse_color,
)


class AdministratorCustomizeCog(AdminCommandBase):
    @commands.command(name="color")
    async def color(self, ctx, role: discord.Role, color_value: str):
        if not await self.require_role_or_admin_ctx(ctx):
            return
        color = parse_color(color_value)
        if color is None:
            await ctx.send(embed=create_error_splash("❌ Màu Không Hợp Lệ", "Dùng tên màu cơ bản hoặc mã hex như `#ff00ff`."))
            return
        try:
            await role.edit(color=color, reason=f"Đổi màu bởi {ctx.author}")
            await ctx.send(embed=create_success_splash("✅ Đổi Màu Thành Công", f"Role {role.mention} đã được đổi màu."))
        except Exception as exc:
            await ctx.send(embed=create_error_splash("❌ Đổi Màu Thất Bại", str(exc)))

    @commands.command(name="emoji")
    async def emoji(self, ctx, action: str = None, arg1: str = None, *, rest: str = ""):
        if not await self.require_role_or_admin_ctx(ctx):
            return
        if not action:
            await ctx.send(embed=create_info_splash("😊 Emoji", "Dùng:\n`emoji a/add <name> <url>`\n`emoji r/rm/remove/d/delete <name|id>`\n`emoji list [limit]`"))
            return

        action = action.lower().strip()
        if action in {"a", "add"}:
            if not arg1:
                await ctx.send(embed=create_error_splash("❌ Thiếu Tên Emoji", "Dùng: `emoji a/add <name> <url>`"))
                return
            source = rest.strip() or (ctx.message.attachments[0].url if ctx.message.attachments else "")
            if not source:
                await ctx.send(embed=create_error_splash("❌ Thiếu Nguồn Ảnh", "Gửi URL ảnh hoặc đính kèm file ảnh."))
                return
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(source) as response:
                        response.raise_for_status()
                        image_bytes = await response.read()
                emoji = await ctx.guild.create_custom_emoji(name=arg1, image=image_bytes, reason=f"Emoji bởi {ctx.author}")
                await ctx.send(embed=create_success_splash("✅ Thêm Emoji Thành Công", f"Đã tạo emoji {emoji}"))
            except Exception as exc:
                await ctx.send(embed=create_error_splash("❌ Thêm Emoji Thất Bại", str(exc)))
            return

        if action in {"r", "remove", "rm", "d", "delete", "del"}:
            target = arg1 or rest.strip()
            if not target:
                await ctx.send(embed=create_error_splash("❌ Thiếu Emoji", "Dùng: `emoji r/rm/remove/d/delete <name|id>`"))
                return
            found = discord.utils.get(ctx.guild.emojis, name=target)
            if found is None and target.isdigit():
                found = discord.utils.get(ctx.guild.emojis, id=int(target))
            if found is None:
                await ctx.send(embed=create_error_splash("❌ Không Tìm Thấy Emoji", f"Không có emoji `{target}` trong server."))
                return
            try:
                await found.delete(reason=f"Emoji bị xoá bởi {ctx.author}")
                await ctx.send(embed=create_success_splash("✅ Xoá Emoji Thành Công", f"Đã xoá emoji `{found.name}`"))
            except Exception as exc:
                await ctx.send(embed=create_error_splash("❌ Xoá Emoji Thất Bại", str(exc)))
            return

        if action == "list":
            try:
                limit = int(arg1 or rest.strip() or 20)
            except ValueError:
                limit = 20
            emojis = list(ctx.guild.emojis)[:limit]
            if not emojis:
                await ctx.send(embed=create_warning_splash("⚠️ Emoji", "Server chưa có emoji custom nào."))
                return
            text = "\n".join(f"• {emoji} - `{emoji.name}`" for emoji in emojis)
            await ctx.send(embed=create_info_splash(f"😊 Emoji ({len(emojis)})", text))
            return

        await ctx.send(embed=create_error_splash("❌ Lệnh Không Hợp Lệ", "Dùng: `emoji a/add`, `emoji r/rm/remove/d/delete` hoặc `emoji list`"))


async def setup(bot):
    await bot.add_cog(AdministratorCustomizeCog(bot))
