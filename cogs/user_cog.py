"""
User Commands Layer
- Xử lý Discord commands
- Gọi Service Layer
- Format response
"""

import discord
from discord.ext import commands
from services.user_service import UserService
from models.user_model import User, UserRole
from models.constants import PERMISSION_DENIED, ERROR_MESSAGE

class UserCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.service = UserService()
    
    @commands.command(name='profile')
    async def profile(self, ctx, member: discord.Member = None):
        """Xem profile người dùng"""
        try:
            # Mặc định là người gửi lệnh
            if not member:
                member = ctx.author
            
            # Service Layer
            user = self.service.get_or_create_user(member.id, member.name)
            
            # Format response
            embed = discord.Embed(
                title=f"👤 Profile - {user.username}",
                color=discord.Color.blue()
            )
            embed.add_field(name="🎯 Level", value=user.level, inline=True)
            embed.add_field(name="⭐ Points", value=user.points, inline=True)
            embed.add_field(name="👑 Role", value=user.role.value.upper(), inline=True)
            
            await ctx.send(embed=embed)
        
        except Exception as e:
            await ctx.send(f"{ERROR_MESSAGE} {str(e)}")
    
    @commands.command(name='addpoints')
    @commands.has_permissions(administrator=True)
    async def add_points(self, ctx, member: discord.Member, amount: int):
        """Thêm points cho user (admin only)"""
        try:
            if amount <= 0:
                await ctx.send("❌ Amount phải > 0!")
                return
            
            # Service Layer
            user = self.service.get_or_create_user(member.id, member.name)
            self.service.add_points(member.id, amount)
            
            # Format response
            embed = discord.Embed(
                title="✅ Points Added",
                color=discord.Color.green()
            )
            embed.add_field(name="User", value=member.name)
            embed.add_field(name="Amount", value=amount)
            embed.add_field(name="New Total", value=user.points + amount)
            
            await ctx.send(embed=embed)
        
        except Exception as e:
            await ctx.send(f"{ERROR_MESSAGE} {str(e)}")
    
    @commands.command(name='topusers')
    async def top_users(self, ctx, limit: int = 10):
        """Xem top users"""
        try:
            if limit < 1 or limit > 100:
                limit = 10
            
            # Service Layer
            top = self.service.get_top_users(limit)
            
            if not top:
                await ctx.send("Chưa có ai trong database!")
                return
            
            # Format response
            embed = discord.Embed(
                title=f"🏆 Top {len(top)} Users",
                color=discord.Color.gold()
            )
            
            for i, user in enumerate(top, 1):
                embed.add_field(
                    name=f"#{i} {user['username']}",
                    value=f"⭐ {user['points']} points | Lvl {user['level']}",
                    inline=False
                )
            
            await ctx.send(embed=embed)
        
        except Exception as e:
            await ctx.send(f"{ERROR_MESSAGE} {str(e)}")
    
    @commands.command(name='setrole')
    @commands.has_permissions(administrator=True)
    async def set_role(self, ctx, member: discord.Member, role: str):
        """Thay đổi role user (admin only)"""
        try:
            role_upper = role.upper()
            
            # Validate role
            valid_roles = [r.name for r in UserRole]
            if role_upper not in valid_roles:
                await ctx.send(f"❌ Role phải là: {', '.join(valid_roles)}")
                return
            
            # Service Layer
            new_role = UserRole[role_upper]
            self.service.set_user_role(member.id, new_role)
            
            # Format response
            await ctx.send(f"✅ Đổi role {member.name} thành {new_role.value}")
        
        except Exception as e:
            await ctx.send(f"{ERROR_MESSAGE} {str(e)}")

async def setup(bot):
    await bot.add_cog(UserCog(bot))
