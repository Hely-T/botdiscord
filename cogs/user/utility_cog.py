from __future__ import annotations

import random
import re

import discord
from discord.ext import commands

from services.admin_service import AdminService
from services.afk_service import AfkService
from services.role_permission_service import RolePermissionService
from utils import get_prefix


class UserUtilityCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.afk_service = AfkService()
        self.admin_service = AdminService()
        self.role_permissions = RolePermissionService()

    def cog_unload(self):
        self.afk_service.close()

    @staticmethod
    def _pick_options(raw: str) -> list[str]:
        if not raw or not raw.strip():
            return []
        separator = r"\s*,\s*" if "," in raw else r"\s+"
        return [item.strip() for item in re.split(separator, raw.strip()) if item.strip()]

    @commands.command(name="afk")
    @commands.guild_only()
    async def afk(self, ctx: commands.Context, *, reason: str = "AFK"):
        reason = reason.strip() or "AFK"
        if len(reason) > 300:
            await ctx.reply("❌ Lý do AFK tối đa 300 ký tự.", mention_author=False)
            return
        status = self.afk_service.set_afk(ctx.guild.id, ctx.author.id, reason)
        if status is None:
            await ctx.reply("❌ Không thể lưu trạng thái AFK lúc này.", mention_author=False)
            return
        await ctx.reply(
            f"||{ctx.author.display_name}|| is AFK: {reason} - <t:{status['started_at']}:R>",
            mention_author=False,
            allowed_mentions=discord.AllowedMentions.none(),
        )

    @commands.command(name="random", aliases=["rand", "rd"])
    async def random_number(self, ctx: commands.Context, maximum: int | None = None):
        if maximum is None:
            await ctx.reply("❌ Dùng: `random <số lớn nhất>`.", mention_author=False)
            return
        if maximum < 1:
            await ctx.reply("❌ Số lớn nhất phải từ 1 trở lên.", mention_author=False)
            return
        result = random.randint(1, maximum)
        await ctx.reply(
            f"✅ | Số ngẫu nhiên từ **1-{maximum:,}** là **{result:,}**.",
            mention_author=False,
        )

    @commands.command(name="pick", aliases=["choose", "chon", "chọn"])
    async def pick(self, ctx: commands.Context, *, choices: str = ""):
        options = self._pick_options(choices)
        if not options:
            await ctx.reply("❌ Dùng: `pick lựa chọn 1, lựa chọn 2, lựa chọn 3`.", mention_author=False)
            return
        selected = random.choice(options)
        await ctx.reply(f"✅ | Mình chọn **{selected}**, còn bạn?", mention_author=False)

    @commands.command(name="setname", aliases=["setnick", "nickname"])
    @commands.guild_only()
    async def setname(self, ctx: commands.Context, *, content: str = ""):
        raw = content.strip()
        member = ctx.author
        new_name = raw
        target_match = re.match(r"^<@!?(\d+)>\s*(.*)$", raw, flags=re.DOTALL)
        if target_match:
            member = ctx.guild.get_member(int(target_match.group(1)))
            if member is None:
                await ctx.reply("❌ Không tìm thấy user được tag trong server.", mention_author=False)
                return
            new_name = target_match.group(2).strip()

        if member.id != ctx.author.id:
            role_ids = [role.id for role in ctx.author.roles if role.name != "@everyone"]
            can_manage_others = self.admin_service.is_hard_admin(
                ctx.author.id
            ) or self.role_permissions.user_can_use(ctx.guild.id, role_ids, "setname")
            if not can_manage_others:
                await ctx.reply(
                    "❌ Chỉ hard admin hoặc role có quyền `setname` trong DB mới đổi tên người khác.",
                    mention_author=False,
                )
                return

        if not new_name:
            await ctx.reply(
                "❌ Dùng: `setname <tên mới>` hoặc `setname @user <tên mới>`.",
                mention_author=False,
            )
            return
        if len(new_name) > 32:
            await ctx.reply("❌ Nickname Discord tối đa 32 ký tự.", mention_author=False)
            return
        old_name = member.display_name
        try:
            await member.edit(
                nick=new_name,
                reason=f"setname bởi {ctx.author} ({ctx.author.id})",
            )
        except discord.Forbidden:
            await ctx.reply(
                "❌ Bot không thể đổi tên user này. Hãy kiểm tra quyền Manage Nicknames và thứ tự role của bot.",
                mention_author=False,
            )
            return
        except discord.HTTPException as exc:
            await ctx.reply(f"❌ Đổi tên thất bại: {exc}", mention_author=False)
            return
        await ctx.reply(
            f"✅ Đã đổi tên {member.mention} từ `{old_name}` thành `{new_name}`.",
            mention_author=False,
        )

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.guild is None or message.author.bot:
            return

        prefix = get_prefix()
        content = message.content.strip()
        invoked = ""
        if content.lower().startswith(prefix.lower()):
            invoked = content[len(prefix):].strip().split(maxsplit=1)[0].lower()

        author_status = self.afk_service.get_afk(message.guild.id, message.author.id)
        if author_status and invoked != "afk":
            self.afk_service.remove_afk(message.guild.id, message.author.id)
            await message.reply(
                f"Chào mừng ||{message.author.display_name}|| trở lại, AFK đã được gỡ.",
                mention_author=False,
                allowed_mentions=discord.AllowedMentions.none(),
            )

        notices = []
        seen_ids = set()
        for member in message.mentions:
            if member.id == message.author.id or member.id in seen_ids:
                continue
            seen_ids.add(member.id)
            status = self.afk_service.get_afk(message.guild.id, member.id)
            if status:
                notices.append(
                    f"||{member.display_name}|| is AFK: {status['reason']} - <t:{status['started_at']}:R>"
                )

        if notices:
            await message.reply(
                "\n".join(notices),
                mention_author=False,
                allowed_mentions=discord.AllowedMentions.none(),
            )


async def setup(bot: commands.Bot):
    await bot.add_cog(UserUtilityCog(bot))
