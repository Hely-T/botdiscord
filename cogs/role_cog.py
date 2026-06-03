"""
Role Management Cog
- Quản lý quyền commands theo role
- Commands: addrole, removerole, perms
"""

import discord
from discord.ext import commands
from services.role_permission_service import RolePermissionService

class RoleCog(commands.Cog):
    """Cog quản lý quyền commands theo role"""
    
    def __init__(self, bot):
        self.bot = bot
        self.service = RolePermissionService()
    
    @commands.command(name='addrole')
    @commands.has_permissions(administrator=True)
    async def add_role(self, ctx, role: discord.Role, *, command_name: str):
        """
        Thêm role cho command
        
        Cú pháp: !addrole @role_name command_name
        
        Ví dụ:
            !addrole @admin ban
            !addrole @moderator kick
            !addrole @trusted mute
        
        Sau khi chạy:
            - Role @admin được dùng lệnh 'ban'
            - Role @moderator được dùng lệnh 'kick'
            - Role @trusted được dùng lệnh 'mute'
        """
        try:
            if not command_name or len(command_name.strip()) == 0:
                embed = discord.Embed(
                    title="❌ Lỗi",
                    description="Tên command không được trống!",
                    color=discord.Color.red()
                )
                await ctx.send(embed=embed)
                return
            
            # Xóa spaces thừa
            command_name = command_name.strip().lower()
            
            # Add permission
            self.service.add_command_role(
                guild_id=ctx.guild.id,
                role_id=role.id,
                command_name=command_name,
                created_by=ctx.author.id
            )
            
            # Response
            embed = discord.Embed(
                title="✅ Thêm Quyền Thành Công",
                description=f"Role {role.mention} được dùng lệnh `{command_name}`",
                color=discord.Color.green()
            )
            embed.add_field(name="Role", value=role.name, inline=True)
            embed.add_field(name="Command", value=command_name, inline=True)
            embed.add_field(name="Server", value=ctx.guild.name, inline=True)
            embed.set_footer(text=f"Được tạo bởi {ctx.author.name}")
            
            await ctx.send(embed=embed)
        
        except Exception as e:
            embed = discord.Embed(
                title="❌ Lỗi",
                description=f"{str(e)}",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
    
    @commands.command(name='removerole')
    @commands.has_permissions(administrator=True)
    async def remove_role(self, ctx, role: discord.Role, *, command_name: str):
        """
        Xóa role khỏi command
        
        Cú pháp: !removerole @role_name command_name
        
        Ví dụ:
            !removerole @moderator ban
            !removerole @trusted mute
        
        Sau khi chạy:
            - Role @moderator không được dùng lệnh 'ban'
            - Role @trusted không được dùng lệnh 'mute'
        """
        try:
            if not command_name or len(command_name.strip()) == 0:
                embed = discord.Embed(
                    title="❌ Lỗi",
                    description="Tên command không được trống!",
                    color=discord.Color.red()
                )
                await ctx.send(embed=embed)
                return
            
            # Xóa spaces thừa
            command_name = command_name.strip().lower()
            
            # Remove permission
            self.service.remove_command_role(
                guild_id=ctx.guild.id,
                role_id=role.id,
                command_name=command_name
            )
            
            # Response
            embed = discord.Embed(
                title="✅ Xóa Quyền Thành Công",
                description=f"Role {role.mention} không được dùng lệnh `{command_name}` nữa",
                color=discord.Color.green()
            )
            embed.add_field(name="Role", value=role.name, inline=True)
            embed.add_field(name="Command", value=command_name, inline=True)
            embed.add_field(name="Server", value=ctx.guild.name, inline=True)
            embed.set_footer(text=f"Được xóa bởi {ctx.author.name}")
            
            await ctx.send(embed=embed)
        
        except Exception as e:
            embed = discord.Embed(
                title="❌ Lỗi",
                description=f"{str(e)}",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
    
    @commands.command(name='perms')
    async def show_permissions(self, ctx, *, command_name: str = None):
        """
        Xem quyền của một command
        
        Cú pháp: !perms command_name
        
        Ví dụ:
            !perms ban
            !perms kick
            !perms mute
        
        Kết quả:
            - Hiển thị danh sách roles có quyền dùng command
            - Nếu không có role nào thì "Chưa có role nào được phép"
        """
        try:
            if not command_name or len(command_name.strip()) == 0:
                embed = discord.Embed(
                    title="❌ Lỗi",
                    description="Vui lòng nhập tên command! Ví dụ: `!perms ban`",
                    color=discord.Color.red()
                )
                await ctx.send(embed=embed)
                return
            
            # Xóa spaces thừa
            command_name = command_name.strip().lower()
            
            # Get roles
            roles = self.service.get_roles_for_command(ctx.guild.id, command_name)
            
            # Response
            if roles:
                role_list = '\n'.join([f"• {r['role_name']}" for r in roles])
                embed = discord.Embed(
                    title=f"📋 Quyền của lệnh: {command_name}",
                    description=role_list,
                    color=discord.Color.blue()
                )
                embed.add_field(
                    name="Tổng số",
                    value=f"{len(roles)} role(s)",
                    inline=False
                )
            else:
                embed = discord.Embed(
                    title=f"📋 Quyền của lệnh: {command_name}",
                    description="❌ Chưa có role nào được phép dùng lệnh này",
                    color=discord.Color.orange()
                )
            
            embed.set_footer(text=f"Server: {ctx.guild.name}")
            await ctx.send(embed=embed)
        
        except Exception as e:
            embed = discord.Embed(
                title="❌ Lỗi",
                description=f"{str(e)}",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
    
    @commands.command(name='myroles')
    async def my_roles(self, ctx, member: discord.Member = None):
        """
        Xem roles của bạn hoặc người khác
        
        Cú pháp: !myroles [@user]
        
        Ví dụ:
            !myroles              (xem roles của bạn)
            !myroles @JohnDoe     (xem roles của JohnDoe)
        """
        try:
            if not member:
                member = ctx.author
            
            # Lấy roles (bỏ @everyone)
            roles = [role.mention for role in member.roles if role.name != "@everyone"]
            
            if not roles:
                embed = discord.Embed(
                    title=f"👤 Roles của {member.name}",
                    description="❌ Không có role nào",
                    color=discord.Color.orange()
                )
            else:
                role_text = '\n'.join(roles)
                embed = discord.Embed(
                    title=f"👤 Roles của {member.name}",
                    description=role_text,
                    color=discord.Color.blue()
                )
                embed.add_field(
                    name="Tổng số",
                    value=f"{len(roles)} role(s)",
                    inline=False
                )
            
            embed.set_thumbnail(url=member.avatar.url)
            embed.set_footer(text=f"Server: {ctx.guild.name}")
            
            await ctx.send(embed=embed)
        
        except Exception as e:
            embed = discord.Embed(
                title="❌ Lỗi",
                description=f"{str(e)}",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
    
    @commands.command(name='rolescommands')
    async def roles_commands(self, ctx, role: discord.Role):
        """
        Xem commands mà một role có quyền dùng
        
        Cú pháp: !rolescommands @role_name
        
        Ví dụ:
            !rolescommands @admin
            !rolescommands @moderator
        """
        try:
            # Get commands
            commands_list = self.service.get_commands_for_role(ctx.guild.id, role.id)
            
            # Response
            if commands_list:
                command_text = '\n'.join([f"• `{cmd}`" for cmd in commands_list])
                embed = discord.Embed(
                    title=f"📋 Commands của role {role.name}",
                    description=command_text,
                    color=discord.Color.blue()
                )
                embed.add_field(
                    name="Tổng số",
                    value=f"{len(commands_list)} command(s)",
                    inline=False
                )
            else:
                embed = discord.Embed(
                    title=f"📋 Commands của role {role.name}",
                    description="❌ Role này không có quyền dùng command nào",
                    color=discord.Color.orange()
                )
            
            embed.set_footer(text=f"Server: {ctx.guild.name}")
            await ctx.send(embed=embed)
        
        except Exception as e:
            embed = discord.Embed(
                title="❌ Lỗi",
                description=f"{str(e)}",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(RoleCog(bot))
