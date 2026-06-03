import discord
from discord.ext import commands
from config import DISCORD_OWNER_IDS
from services.git_service import GitUpdateService
from utils import create_success_splash, create_error_splash, create_info_splash, create_warning_splash

class AdminCog(commands.Cog):
    """Cogs quản lý admin - chỉ owner sử dụng"""
    
    def __init__(self, bot):
        self.bot = bot
        self.git = GitUpdateService()
    
    def is_owner(self, user_id):
        """Kiểm tra user có phải owner không"""
        return user_id in DISCORD_OWNER_IDS
    
    @commands.command(name='gitpull', aliases=['pull', 'update'])
    async def git_pull(self, ctx):
        """
        Pull latest code từ GitHub
        Syntax: !gitpull
        """
        if not self.is_owner(ctx.author.id):
            embed = create_error_splash("❌ Quyền Bị Từ Chối", f"Chỉ {len(DISCORD_OWNER_IDS)} owner mới dùng được lệnh này!")
            await ctx.send(embed=embed)
            return
        
        # Thông báo đang pull
        embed = create_info_splash("🔄 Đang Pull Code", "Chờ xíu...")
        msg = await ctx.send(embed=embed)
        
        # Pull từ GitHub
        result = self.git.pull_latest()
        
        if result['success']:
            changed = result['changed_files']
            changed_list = "\n".join([f"  • {f}" for f in changed]) if changed else "  (Không có file nào thay đổi)"
            
            embed = create_success_splash(
                "✅ Pull Thành Công!",
                f"**Thông Tin:**\n{result['message']}\n\n**Files Thay Đổi:**\n{changed_list}"
            )
        else:
            embed = create_error_splash(
                "❌ Pull Thất Bại",
                result['message']
            )
        
        await msg.edit(embed=embed)
    
    @commands.command(name='gitstatus', aliases=['status'])
    async def git_status(self, ctx):
        """
        Kiểm tra trạng thái git
        Syntax: !gitstatus
        """
        if not self.is_owner(ctx.author.id):
            embed = create_error_splash("❌ Quyền Bị Từ Chối", f"Chỉ {len(DISCORD_OWNER_IDS)} owner mới dùng được lệnh này!")
            await ctx.send(embed=embed)
            return
        
        # Lấy thông tin
        status = self.git.get_status()
        branch = self.git.get_branch()
        commit = self.git.get_last_commit()
        remote = self.git.get_remote_url()
        
        # Build message
        status_text = status['status']
        branch_text = branch or "❌ Không lấy được"
        commit_text = commit['commit'] if commit['success'] else "❌ Không lấy được"
        remote_text = remote or "❌ Không lấy được"
        
        embed = create_info_splash(
            "📊 Git Status",
            f"**Branch:** `{branch_text}`\n"
            f"**Remote:** `{remote_text}`\n"
            f"**Commit Cuối:** `{commit_text}`\n\n"
            f"**Status:**\n```\n{status_text}\n```"
        )
        
        await ctx.send(embed=embed)
    
    @commands.command(name='reload')
    async def reload_cogs(self, ctx, cog_name=None):
        """
        Reload một cog hoặc tất cả cogs
        Syntax: !reload [cog_name]
        Example: !reload role_cog
        """
        if not self.is_owner(ctx.author.id):
            embed = create_error_splash("❌ Quyền Bị Từ Chối", f"Chỉ {len(DISCORD_OWNER_IDS)} owner mới dùng được lệnh này!")
            await ctx.send(embed=embed)
            return
        
        if cog_name:
            # Reload một cog cụ thể
            cog_path = f"cogs.{cog_name}"
            try:
                await self.bot.reload_extension(cog_path)
                embed = create_success_splash("✅ Reload Thành Công", f"Cog `{cog_name}` đã reload!")
            except Exception as e:
                embed = create_error_splash("❌ Reload Thất Bại", f"Lỗi: {str(e)}")
        else:
            # Reload tất cả cogs
            failed = []
            success = []
            
            import os
            from config import COGS_DIR
            
            for filename in os.listdir(COGS_DIR):
                if filename.endswith('.py') and filename != '__init__.py':
                    cog_name = filename[:-3]
                    cog_path = f"cogs.{cog_name}"
                    try:
                        await self.bot.reload_extension(cog_path)
                        success.append(cog_name)
                    except Exception as e:
                        failed.append(f"{cog_name}: {str(e)}")
            
            success_text = "\n".join([f"  ✅ {c}" for c in success]) if success else "  (Không có)"
            failed_text = "\n".join([f"  ❌ {f}" for f in failed]) if failed else "  (Không có)"
            
            embed = create_info_splash(
                "🔄 Reload Tất Cả Cogs",
                f"**Thành Công:**\n{success_text}\n\n**Thất Bại:**\n{failed_text}"
            )
        
        await ctx.send(embed=embed)
    
    @commands.command(name='load')
    async def load_cog(self, ctx, cog_name):
        """
        Load một cog
        Syntax: !load [cog_name]
        Example: !load new_cog
        """
        if not self.is_owner(ctx.author.id):
            embed = create_error_splash("❌ Quyền Bị Từ Chối", f"Chỉ {len(DISCORD_OWNER_IDS)} owner mới dùng được lệnh này!")
            await ctx.send(embed=embed)
            return
        
        cog_path = f"cogs.{cog_name}"
        try:
            await self.bot.load_extension(cog_path)
            embed = create_success_splash("✅ Load Thành Công", f"Cog `{cog_name}` đã load!")
        except Exception as e:
            embed = create_error_splash("❌ Load Thất Bại", f"Lỗi: {str(e)}")
        
        await ctx.send(embed=embed)
    
    @commands.command(name='unload')
    async def unload_cog(self, ctx, cog_name):
        """
        Unload một cog
        Syntax: !unload [cog_name]
        Example: !unload new_cog
        """
        if not self.is_owner(ctx.author.id):
            embed = create_error_splash("❌ Quyền Bị Từ Chối", f"Chỉ {len(DISCORD_OWNER_IDS)} owner mới dùng được lệnh này!")
            await ctx.send(embed=embed)
            return
        
        cog_path = f"cogs.{cog_name}"
        try:
            await self.bot.unload_extension(cog_path)
            embed = create_success_splash("✅ Unload Thành Công", f"Cog `{cog_name}` đã unload!")
        except Exception as e:
            embed = create_error_splash("❌ Unload Thất Bại", f"Lỗi: {str(e)}")
        
        await ctx.send(embed=embed)
    
    @commands.command(name='cogs')
    async def list_cogs(self, ctx):
        """
        Liệt kê tất cả cogs đã load
        Syntax: !cogs
        """
        if not self.is_owner(ctx.author.id):
            embed = create_error_splash("❌ Quyền Bị Từ Chối", f"Chỉ {len(DISCORD_OWNER_IDS)} owner mới dùng được lệnh này!")
            await ctx.send(embed=embed)
            return
        
        cogs_list = list(self.bot.cogs.keys())
        cogs_text = "\n".join([f"  • {c}" for c in cogs_list]) if cogs_list else "  (Không có cog nào)"
        
        embed = create_info_splash(
            f"📦 Cogs ({len(cogs_list)})",
            cogs_text
        )
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(AdminCog(bot))
