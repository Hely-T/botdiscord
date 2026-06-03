import discord
from discord.ext import commands
from utils import CogDatabase, get_timestamp

class Example(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
        # Khởi tạo database cho cog này
        self.db = CogDatabase('example')
        
        # Tạo bảng (tự động nếu chưa tồn tại)
        self.db.create_table('users', '''
            id INTEGER PRIMARY KEY,
            user_id INTEGER UNIQUE,
            username TEXT,
            level INTEGER DEFAULT 1,
            xp INTEGER DEFAULT 0,
            created_at TEXT
        ''')
    
    @commands.command(name='profile')
    async def profile(self, ctx):
        """Xem profile người dùng"""
        user_id = ctx.author.id
        
        # Tìm user trong database
        user = self.db.select_one('users', 'user_id = ?', (user_id,))
        
        if not user:
            # User mới, thêm vào database
            self.db.insert('users', {
                'user_id': user_id,
                'username': ctx.author.name,
                'level': 1,
                'xp': 0,
                'created_at': get_timestamp()
            })
            user = self.db.select_one('users', 'user_id = ?', (user_id,))
        
        # Hiển thị profile
        embed = discord.Embed(title=f"Profile - {user['username']}", color=discord.Color.blue())
        embed.add_field(name="Level", value=user['level'], inline=True)
        embed.add_field(name="XP", value=user['xp'], inline=True)
        embed.add_field(name="Ngày tạo", value=user['created_at'])
        
        await ctx.send(embed=embed)
    
    @commands.command(name='addxp')
    async def add_xp(self, ctx, amount: int = 10):
        """Thêm XP cho user"""
        user_id = ctx.author.id
        
        # Lấy XP hiện tại
        user = self.db.select_one('users', 'user_id = ?', (user_id,))
        
        if not user:
            await ctx.send("❌ User không tồn tại!")
            return
        
        new_xp = user['xp'] + amount
        
        # Cập nhật database
        self.db.update('users', {'xp': new_xp}, 'user_id = ?', (user_id,))
        
        await ctx.send(f"✅ Thêm {amount} XP! XP hiện tại: {new_xp}")

async def setup(bot):
    await bot.add_cog(Example(bot))
