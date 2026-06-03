# 🚀 Quick Start - Tạo Feature Mới

**Ngắn gọn - Làm feature mới chỉ với 3 bước!**

---

## 📋 Bước 1: Model (Layer 4)

Tạo file `models/my_feature_model.py`:

```python
from dataclasses import dataclass

@dataclass
class MyData:
    id: int = None
    name: str = None
    value: int = 0
    
    def validate(self):
        if not self.name:
            raise ValueError("Name required")
```

---

## 🛠️ Bước 2: Service (Layer 3)

Tạo file `services/my_feature_service.py`:

```python
from utils import CogDatabase, get_timestamp
from models.my_feature_model import MyData

class MyFeatureService:
    def __init__(self):
        self.db = CogDatabase('myfeature')
        self._init_database()
    
    def _init_database(self):
        self.db.create_table('mydata', '''
            id INTEGER PRIMARY KEY,
            name TEXT,
            value INTEGER,
            created_at TEXT
        ''')
    
    def create_data(self, name: str, value: int) -> MyData:
        data = MyData(name=name, value=value)
        data.validate()
        
        self.db.insert('mydata', {
            'name': data.name,
            'value': data.value,
            'created_at': get_timestamp()
        })
        return data
    
    def get_data(self, name: str) -> MyData:
        result = self.db.select_one('mydata', 'name = ?', (name,))
        if not result:
            return None
        return MyData(
            id=result['id'],
            name=result['name'],
            value=result['value']
        )
```

---

## 💬 Bước 3: Command (Layer 2)

Tạo file `cogs/my_feature_cog.py`:

```python
import discord
from discord.ext import commands
from services.my_feature_service import MyFeatureService

class MyFeatureCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.service = MyFeatureService()
    
    @commands.command(name='mycommand')
    async def my_command(self, ctx, name: str, value: int):
        try:
            data = self.service.create_data(name, value)
            
            embed = discord.Embed(
                title="✅ Success",
                description=f"Created: {data.name} = {data.value}",
                color=discord.Color.green()
            )
            await ctx.send(embed=embed)
        
        except Exception as e:
            await ctx.send(f"❌ Error: {str(e)}")

async def setup(bot):
    await bot.add_cog(MyFeatureCog(bot))
```

---

## ✅ Xong!

Bot sẽ tự động:
1. ✨ Load cog
2. ✨ Tạo database
3. ✨ Tạo tables

**Không cần chỉnh sửa main.py!**

---

## 📁 Cấu Trúc Thư Mục

```
BOT DISCORD/
├── main.py
├── config.py
├── utils.py
├── requirements.txt
├── .env
│
├── cogs/
│   ├── user_cog.py          ← Existing
│   ├── example.py           ← Existing
│   └── my_feature_cog.py    ← NEW ✨
│
├── services/
│   ├── user_service.py      ← Existing
│   └── my_feature_service.py ← NEW ✨
│
├── models/
│   ├── user_model.py        ← Existing
│   ├── constants.py         ← Existing
│   └── my_feature_model.py  ← NEW ✨
│
├── database/
│   ├── users.db
│   └── myfeature.db         ← AUTO CREATED ✨
│
└── docs/
    ├── ARCHITECTURE.md
    ├── DATABASE_GUIDE.md
    ├── LAYER_EXAMPLES.md
    └── QUICK_START.md       ← File này
```

---

## 🎯 Best Practices

✅ **DO:**
- Models có validate()
- Services có _init_database()
- Commands gọi Services
- Gìn dependencies nhỏ

❌ **DON'T:**
- Database logic ở Command
- Business logic ở Model
- Hardcode values ở Cog

---

## 🔗 File Hữu Ích

- `ARCHITECTURE.md` - Chi tiết 6 layers
- `DATABASE_GUIDE.md` - Cách dùng CogDatabase
- `LAYER_EXAMPLES.md` - Ví dụ Posting System (phức tạp)

**Học xong, tạo feature mà không sợ lỗi!** 🚀

