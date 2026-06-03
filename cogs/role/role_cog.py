import discord
from discord.ext import commands

from cogs.role_command_utils import RoleCommandBase
from utils import create_error_splash, create_success_splash


class RoleCog(RoleCommandBase):
    async def _resolve_role(self, ctx, raw_role: str | None) -> discord.Role | None:
        if ctx.guild is None:
            await ctx.send(embed=create_error_splash("❌ Chỉ Dùng Trong Server", "Lệnh role chỉ hoạt động trong server."))
            return None
        if not raw_role:
            await ctx.send(embed=create_error_splash("❌ Thiếu Role", "Hãy nhập role mention, tên role hoặc role ID."))
            return None
        try:
            return await commands.RoleConverter().convert(ctx, raw_role)
        except Exception:
            await ctx.send(embed=create_error_splash("❌ Không Tìm Thấy Role", "Hãy nhập role mention, tên role hoặc role ID hợp lệ."))
            return None

    @commands.command(name="addrole", aliases=["themrole"])
    async def add_role(self, ctx, raw_role: str = None, *, command_name: str = None):
        if not await self.require_role_or_admin_ctx(ctx, "addrole"):
            return
        role = await self._resolve_role(ctx, raw_role)
        if not role:
            return
        if not command_name:
            await ctx.send(embed=create_error_splash("❌ Thiếu Command", "Dùng: `addrole @role command` hoặc `themrole <role_id> command`."))
            return
        command_name = command_name.strip().lower()
        if not command_name:
            await ctx.send(embed=create_error_splash("❌ Lỗi", "Tên command không được trống!"))
            return
        role_saved = self.service.save_role(ctx.guild.id, role.id, role.name, role.position)
        permission_saved = self.service.add_command_role(ctx.guild.id, role.id, command_name, ctx.author.id)
        if not role_saved or not permission_saved:
            await ctx.send(embed=create_error_splash("❌ Thêm Quyền Thất Bại", "Database chưa lưu được quyền role. Hãy thử lại hoặc kiểm tra log."))
            return
        await ctx.send(embed=create_success_splash("✅ Thêm Quyền Thành Công", f"Role {role.mention} được dùng lệnh `{command_name}`"))

    @commands.command(name="removerole", aliases=["rmrole", "xoarole"])
    async def remove_role(self, ctx, raw_role: str = None, *, command_name: str = None):
        if not await self.require_role_or_admin_ctx(ctx, "removerole"):
            return
        role = await self._resolve_role(ctx, raw_role)
        if not role:
            return
        if not command_name:
            await ctx.send(embed=create_error_splash("❌ Thiếu Command", "Dùng: `removerole @role command`, `rmrole @role command` hoặc `xoarole <role_id> command`."))
            return
        command_name = command_name.strip().lower()
        if not command_name:
            await ctx.send(embed=create_error_splash("❌ Lỗi", "Tên command không được trống!"))
            return
        self.service.remove_command_role(ctx.guild.id, role.id, command_name)
        await ctx.send(embed=create_success_splash("✅ Xóa Quyền Thành Công", f"Role {role.mention} không được dùng lệnh `{command_name}` nữa"))

    @commands.command(name="setrole")
    async def set_role(self, ctx, raw_role: str = None, role_key: str = None):
        if not await self.require_role_or_admin_ctx(ctx, "setrole"):
            return
        role = await self._resolve_role(ctx, raw_role)
        if not role:
            return
        if not role_key:
            await ctx.send(embed=create_error_splash("❌ Thiếu Key", "Dùng: `setrole @role booking` hoặc `setrole <role_id> booking`."))
            return

        try:
            normalized_key = self.guild_settings.normalize_role_key(role_key)
            saved = self.guild_settings.set_system_role(ctx.guild.id, normalized_key, role.id, role.name, ctx.author.id)
        except ValueError as exc:
            await ctx.send(embed=create_error_splash("❌ Set Role Thất Bại", str(exc)))
            return

        role_saved = self.service.save_role(ctx.guild.id, role.id, role.name, role.position)
        if not saved or not role_saved:
            await ctx.send(embed=create_error_splash("❌ Set Role Thất Bại", "Database chưa lưu được role hệ thống. Hãy thử lại hoặc kiểm tra log."))
            return
        await ctx.send(embed=create_success_splash("✅ Set Role Thành Công", f"Đã set role {role.mention} làm `{normalized_key}`."))

    @commands.command(name="perms")
    async def show_permissions(self, ctx, *, command_name: str = None):
        if not command_name or not command_name.strip():
            await ctx.send(embed=create_error_splash("❌ Lỗi", "Vui lòng nhập tên command! Ví dụ: `!perms ban`"))
            return
        command_name = command_name.strip().lower()
        roles = self.service.get_roles_for_command(ctx.guild.id, command_name)
        if roles:
            role_list = "\n".join([f"• {r['role_name']}" for r in roles])
            embed = discord.Embed(title=f"📋 Quyền của lệnh: {command_name}", description=role_list, color=discord.Color.blue())
            embed.add_field(name="Tổng số", value=f"{len(roles)} role(s)", inline=False)
        else:
            embed = discord.Embed(title=f"📋 Quyền của lệnh: {command_name}", description="❌ Chưa có role nào được phép dùng lệnh này", color=discord.Color.orange())
        embed.set_footer(text=f"Server: {ctx.guild.name}")
        await ctx.send(embed=embed)

    @commands.command(name="myroles")
    async def my_roles(self, ctx, member: discord.Member = None):
        if not member:
            member = ctx.author
        roles = [role.mention for role in member.roles if role.name != "@everyone"]
        if not roles:
            embed = discord.Embed(title=f"👤 Roles của {member.name}", description="❌ Không có role nào", color=discord.Color.orange())
        else:
            embed = discord.Embed(title=f"👤 Roles của {member.name}", description="\n".join(roles), color=discord.Color.blue())
            embed.add_field(name="Tổng số", value=f"{len(roles)} role(s)", inline=False)
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_footer(text=f"Server: {ctx.guild.name}")
        await ctx.send(embed=embed)

    @commands.command(name="rolescommands")
    async def roles_commands(self, ctx, raw_role: str = None):
        role = await self._resolve_role(ctx, raw_role)
        if not role:
            return
        self.service.save_role(ctx.guild.id, role.id, role.name, role.position)
        commands_list = self.service.get_commands_for_role(ctx.guild.id, role.id)
        if commands_list:
            command_text = "\n".join([f"• `{cmd}`" for cmd in commands_list])
            embed = discord.Embed(title=f"📋 Commands của role {role.name}", description=command_text, color=discord.Color.blue())
            embed.add_field(name="Tổng số", value=f"{len(commands_list)} command(s)", inline=False)
        else:
            embed = discord.Embed(title=f"📋 Commands của role {role.name}", description="❌ Role này không có quyền dùng command nào", color=discord.Color.orange())
        embed.set_footer(text=f"Server: {ctx.guild.name}")
        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(RoleCog(bot))
