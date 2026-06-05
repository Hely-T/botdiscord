import discord
from discord.ext import commands

from config import DISCORD_OWNER_IDS
from cogs.admin_command_utils import (
    AdminCommandBase,
    create_error_splash,
    create_info_splash,
    create_success_splash,
)
from cogs.cog_loader_utils import resolve_cog_modules
from services.git_service import GitUpdateService


class AdministratorOperatorCog(AdminCommandBase):
    def __init__(self, bot: commands.Bot):
        super().__init__(bot)
        self.git = GitUpdateService()

    def is_owner(self, user_id: int) -> bool:
        return user_id in DISCORD_OWNER_IDS

    def is_hard_admin(self, user_id: int) -> bool:
        return self.admins.is_hard_admin(user_id)

    async def _require_owner(self, ctx) -> bool:
        if self.is_owner(ctx.author.id):
            return True
        await ctx.send(embed=create_error_splash("❌ Quyền Bị Từ Chối", "Chỉ owner mới dùng được lệnh này!"))
        return False

    async def _run_extension_action(self, action: str, target: str | None):
        modules = resolve_cog_modules(target)
        success, failed = [], []

        for module_name in modules:
            try:
                if action == "load":
                    await self.bot.load_extension(module_name)
                elif action == "reload":
                    await self.bot.reload_extension(module_name)
                elif action == "unload":
                    await self.bot.unload_extension(module_name)
                success.append(module_name)
            except Exception as exc:
                failed.append(f"{module_name}: {exc}")

        return success, failed

    @commands.command(name="gitpull", aliases=["pull", "update"])
    async def git_pull(self, ctx):
        if not await self._require_owner(ctx):
            return
        msg = await ctx.send(embed=create_info_splash("🔄 Đang Pull Code", "Chờ xíu..."))
        result = self.git.pull_latest()
        if result["success"]:
            changed = result["changed_files"]
            changed_list = "\n".join([f"  • {f}" for f in changed]) if changed else "  (Không có file nào thay đổi)"
            embed = create_success_splash("✅ Pull Thành Công!", f"**Thông Tin:**\n{result['message']}\n\n**Files Thay Đổi:**\n{changed_list}")
        else:
            embed = create_error_splash("❌ Pull Thất Bại", result["message"])
        await msg.edit(embed=embed)

    @commands.command(name="gitstatus", aliases=["status"])
    async def git_status(self, ctx):
        if not await self._require_owner(ctx):
            return
        status = self.git.get_status()
        branch = self.git.get_branch() or "❌ Không lấy được"
        commit = self.git.get_last_commit()
        remote = self.git.get_remote_url() or "❌ Không lấy được"
        await ctx.send(
            embed=create_info_splash(
                "📊 Git Status",
                f"**Branch:** `{branch}`\n**Remote:** `{remote}`\n**Commit Cuối:** `{commit['commit'] if commit['success'] else '❌ Không lấy được'}`\n\n**Status:**\n```\n{status['status']}\n```",
            )
        )

    @commands.command(name="reload")
    async def reload_cogs(self, ctx, cog_name: str = None):
        if not await self._require_owner(ctx):
            return
        success, failed = await self._run_extension_action("reload", cog_name)
        success_text = "\n".join([f"  ✅ {c}" for c in success]) if success else "  (Không có)"
        failed_text = "\n".join([f"  ❌ {f}" for f in failed]) if failed else "  (Không có)"
        await ctx.send(embed=create_info_splash("🔄 Reload Cogs", f"**Thành Công:**\n{success_text}\n\n**Thất Bại:**\n{failed_text}"))

    @commands.command(name="load")
    async def load_cog(self, ctx, cog_name: str):
        if not await self._require_owner(ctx):
            return
        success, failed = await self._run_extension_action("load", cog_name)
        title = "✅ Load Thành Công" if success and not failed else "❌ Load Có Lỗi"
        detail = "\n".join([f"✅ {c}" for c in success] + [f"❌ {f}" for f in failed])
        await ctx.send(embed=(create_success_splash if success and not failed else create_error_splash)(title, detail))

    @commands.command(name="unload")
    async def unload_cog(self, ctx, cog_name: str):
        if not await self._require_owner(ctx):
            return
        success, failed = await self._run_extension_action("unload", cog_name)
        title = "✅ Unload Thành Công" if success and not failed else "❌ Unload Có Lỗi"
        detail = "\n".join([f"✅ {c}" for c in success] + [f"❌ {f}" for f in failed])
        await ctx.send(embed=(create_success_splash if success and not failed else create_error_splash)(title, detail))

    @commands.command(name="cogs")
    async def list_cogs(self, ctx):
        if not await self._require_owner(ctx):
            return
        extensions = sorted(self.bot.extensions.keys())
        cogs_text = "\n".join([f"  • {c}" for c in extensions]) if extensions else "  (Không có cog nào)"
        await ctx.send(embed=create_info_splash(f"📦 Cogs ({len(extensions)})", cogs_text))

    @commands.command(name="addadmin", aliases=["themadmin"])
    async def add_admin(self, ctx, member: discord.Member):
        if not self.is_hard_admin(ctx.author.id):
            await ctx.send(embed=create_error_splash("❌ Quyền Bị Từ Chối", "Bạn không có quyền dùng lệnh này."))
            return
        try:
            self.admins.add_admin(member.id, ctx.author.id)
            await ctx.send(embed=create_success_splash("✅ Thêm Admin Thành Công", f"{member.mention} đã trở thành bot admin."))
        except Exception as e:
            await ctx.send(embed=create_error_splash("❌ Thêm Admin Thất Bại", str(e)))

    @commands.command(name="rmadmin", aliases=["xoaadmin"])
    async def remove_admin(self, ctx, member: discord.Member):
        if not self.is_hard_admin(ctx.author.id):
            await ctx.send(embed=create_error_splash("❌ Quyền Bị Từ Chối", "Bạn không có quyền dùng lệnh này."))
            return
        try:
            self.admins.remove_admin(member.id)
            await ctx.send(embed=create_success_splash("✅ Xoá Admin Thành Công", f"{member.mention} đã bị xoá khỏi danh sách bot admin."))
        except Exception as e:
            await ctx.send(embed=create_error_splash("❌ Xoá Admin Thất Bại", str(e)))

    @commands.command(name="prefix")
    async def prefix(self, ctx, new_prefix: str = None):
        if not await self._require_owner(ctx):
            return
        if new_prefix is None:
            await ctx.send(embed=create_info_splash("📌 Prefix Hiện Tại", f"Prefix hiện tại của bot là `{self.settings.get_prefix()}`"))
            return
        try:
            self.settings.set_prefix(new_prefix)
            await ctx.send(embed=create_success_splash("✅ Đổi Prefix Thành Công", f"Prefix mới của bot là `{new_prefix}`"))
            await self.bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=f"{new_prefix}help"))
        except Exception as exc:
            await ctx.send(embed=create_error_splash("❌ Đổi Prefix Thất Bại", str(exc)))


async def setup(bot):
    await bot.add_cog(AdministratorOperatorCog(bot))
