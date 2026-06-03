# 📚 Hướng dẫn sử dụng CogDatabase

`CogDatabase` là hàm dùng chung để quản lý database cho mỗi cog. **Nó sẽ tự động tạo file `.db` và các bảng khi bạn khởi tạo.**

## Cách sử dụng

### 1. Import vào cog của bạn
```python
from utils import CogDatabase, get_timestamp
```

### 2. Khởi tạo database trong `__init__`
```python
class MyCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
        # Tạo database (tên file sẽ là 'mycog.db')
        self.db = CogDatabase('mycog')
        
        # Tạo bảng
        self.db.create_table('members', '''
            id INTEGER PRIMARY KEY,
            user_id INTEGER UNIQUE,
            username TEXT,
            points INTEGER DEFAULT 0,
            created_at TEXT
        ''')
```

### 3. Sử dụng các method

#### Insert dữ liệu
```python
self.db.insert('members', {
    'user_id': 12345,
    'username': 'John',
    'points': 100,
    'created_at': get_timestamp()
})
```

#### Select dữ liệu
```python
# Lấy tất cả
all_users = self.db.select('members')

# Lấy với điều kiện
user = self.db.select_one('members', 'user_id = ?', (12345,))

# Lấy nhiều với điều kiện
users = self.db.select('members', 'points > ?', (50,))
```

#### Update dữ liệu
```python
self.db.update('members', 
    {'points': 200}, 
    'user_id = ?', 
    (12345,)
)
```

#### Delete dữ liệu
```python
self.db.delete('members', 'user_id = ?', (12345,))
```

#### SQL tùy chỉnh
```python
# Execute (chỉ chạy, không lấy kết quả)
self.db.execute('DELETE FROM members WHERE points < ?', (10,))

# Fetch (lấy kết quả)
results = self.db.fetch('SELECT * FROM members ORDER BY points DESC LIMIT 5')

# Fetch one
top_user = self.db.fetch_one('SELECT * FROM members ORDER BY points DESC')
```

## Ví dụ hoàn chỉnh

```python
import discord
from discord.ext import commands
from utils import CogDatabase, get_timestamp

class Points(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = CogDatabase('points')
        
        # Tạo bảng
        self.db.create_table('user_points', '''
            id INTEGER PRIMARY KEY,
            user_id INTEGER UNIQUE,
            username TEXT,
            points INTEGER DEFAULT 0,
            created_at TEXT
        ''')
    
    @commands.command(name='points')
    async def show_points(self, ctx):
        """Xem điểm của bạn"""
        user_id = ctx.author.id
        
        user = self.db.select_one('user_points', 'user_id = ?', (user_id,))
        
        if not user:
            # Tạo user mới
            self.db.insert('user_points', {
                'user_id': user_id,
                'username': ctx.author.name,
                'points': 0,
                'created_at': get_timestamp()
            })
            user = self.db.select_one('user_points', 'user_id = ?', (user_id,))
        
        await ctx.send(f"⭐ {user['username']} có {user['points']} điểm!")
    
    @commands.command(name='addpoints')
    async def add_points(self, ctx, member: discord.Member, amount: int):
        """Thêm điểm cho thành viên (admin only)"""
        if not ctx.author.guild_permissions.administrator:
            await ctx.send("❌ Bạn không đủ quyền!")
            return
        
        user = self.db.select_one('user_points', 'user_id = ?', (member.id,))
        
        if not user:
            await ctx.send(f"❌ {member.name} chưa có record!")
            return
        
        new_points = user['points'] + amount
        self.db.update('user_points', 
            {'points': new_points}, 
            'user_id = ?', 
            (member.id,)
        )
        
        await ctx.send(f"✅ Thêm {amount} điểm cho {member.name}! Tổng: {new_points}")
    
    @commands.command(name='toppoints')
    async def top_points(self, ctx):
        """Xem top 5 người có điểm cao nhất"""
        top_users = self.db.fetch(
            'SELECT * FROM user_points ORDER BY points DESC LIMIT 5'
        )
        
        if not top_users:
            await ctx.send("Chưa có ai!")
            return
        
        embed = discord.Embed(title="🏆 Top 5 Điểm Cao Nhất", color=discord.Color.gold())
        
        for i, user in enumerate(top_users, 1):
            embed.add_field(
                name=f"#{i} {user['username']}", 
                value=f"{user['points']} điểm",
                inline=False
            )
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Points(bot))
```

## Database sẽ tự động tạo ở:
- `database/points.db`
- `database/example.db`
- `database/any_cog_name.db`

Chỉ cần thêm cog vào `cogs/` folder là xong! 🚀
