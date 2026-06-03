# 🏗️ Kiến Trúc Bot Discord - Layered Architecture

Đây là hướng dẫn chi tiết về cấu trúc từng tầng (layer) của bot Discord. **Mỗi tầng có vai trò riêng, không được phép vi phạm để tránh lỗi code.**

---

## 📊 Sơ đồ Kiến Trúc

```
┌─────────────────────────────────────────────────────────┐
│ Layer 1: ENTRY POINT (main.py)                          │
│ - Khởi động bot                                          │
│ - Load cogs                                              │
└──────────────────────┬──────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────┐
│ Layer 2: COMMANDS LAYER (cogs/)                         │
│ - Xử lý discord commands                                │
│ - Nhận input từ user                                    │
│ - Gọi Service Layer                                     │
└──────────────────────┬──────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────┐
│ Layer 3: SERVICES LAYER (services/)                     │
│ - Business logic                                        │
│ - Validation                                            │
│ - Data processing                                       │
└──────────────────────┬──────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────┐
│ Layer 4: MODELS LAYER (models/)                         │
│ - Data structures                                       │
│ - Validation schemas                                    │
│ - Constants                                             │
└──────────────────────┬──────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────┐
│ Layer 5: DATABASE LAYER (utils.py + database/)          │
│ - Database operations                                   │
│ - Query execution                                       │
└──────────────────────┬──────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────┐
│ Layer 6: CONFIG LAYER (config.py)                       │
│ - Environment variables                                 │
│ - Global settings                                       │
└─────────────────────────────────────────────────────────┘
```

---

## 📋 Chi Tiết Từng Layer

### **Layer 1: ENTRY POINT (main.py)**
**Vai trò:** Khởi động ứng dụng

**Quyền:**
- ✅ Import config, load .env
- ✅ Khởi tạo bot object
- ✅ Register event handlers
- ✅ Load cogs từ thư mục cogs/

**Cấm:**
- ❌ Implement business logic
- ❌ Trực tiếp access database
- ❌ Hardcode values

**Cấu trúc:**
```python
import discord
from discord.ext import commands
from config import DISCORD_TOKEN, BOT_PREFIX
import os

# 1. Khởi tạo intents
intents = discord.Intents.default()
intents.message_content = True

# 2. Tạo bot
bot = commands.Bot(command_prefix=BOT_PREFIX, intents=intents)

# 3. Event handlers
@bot.event
async def on_ready():
    print(f'Bot {bot.user} online!')

# 4. Load cogs
async def load_cogs():
    for filename in os.listdir('cogs'):
        if filename.endswith('.py'):
            await bot.load_extension(f'cogs.{filename[:-3]}')

# 5. Main
if __name__ == '__main__':
    bot.run(DISCORD_TOKEN)
```

---

### **Layer 2: COMMANDS LAYER (cogs/)**
**Vai trò:** Nhận user input từ Discord, gọi Service Layer

**Quyền:**
- ✅ Define commands
- ✅ Validate user input (basic)
- ✅ Call Services
- ✅ Format response embeds
- ✅ Handle Discord-specific stuff (permissions, roles)

**Cấm:**
- ❌ Database operations (trừ qua Service)
- ❌ Business logic
- ❌ Data processing

**Cấu trúc:**
```python
# cogs/mycog.py
import discord
from discord.ext import commands
from services.my_service import MyService
from models.my_model import MyModel

class MyCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.service = MyService()  # Gọi Service
    
    @commands.command(name='mycommand')
    @commands.has_permissions(administrator=True)
    async def my_command(self, ctx, arg1: str):
        """Mô tả lệnh"""
        try:
            # 1. Validate input
            if not arg1:
                await ctx.send("❌ Arg required!")
                return
            
            # 2. Call Service Layer
            result = self.service.process_data(arg1)
            
            # 3. Format response
            embed = discord.Embed(title="Result", description=result)
            await ctx.send(embed=embed)
        
        except Exception as e:
            await ctx.send(f"❌ Error: {e}")

async def setup(bot):
    await bot.add_cog(MyCog(bot))
```

---

### **Layer 3: SERVICES LAYER (services/)**
**Vai trò:** Chứa business logic, xử lý dữ liệu

**Quyền:**
- ✅ Business logic
- ✅ Data validation & processing
- ✅ Call Database Layer
- ✅ Work with Models

**Cấm:**
- ❌ Direct Discord operations
- ❌ Database operations (chỉ qua Database Layer)

**Cấu trúc:**
```python
# services/my_service.py
from models.my_model import MyModel
from utils import CogDatabase

class MyService:
    def __init__(self):
        self.db = CogDatabase('myservice')
        self.db.create_table('data', '''
            id INTEGER PRIMARY KEY,
            user_id INTEGER,
            value TEXT
        ''')
    
    def process_data(self, raw_data: str) -> str:
        """Business logic"""
        # 1. Validate
        if not self._validate_data(raw_data):
            raise ValueError("Invalid data")
        
        # 2. Process
        processed = self._transform_data(raw_data)
        
        # 3. Save to DB
        self.db.insert('data', {
            'user_id': 123,
            'value': processed
        })
        
        return processed
    
    def _validate_data(self, data: str) -> bool:
        return len(data) > 0
    
    def _transform_data(self, data: str) -> str:
        return data.upper()
```

---

### **Layer 4: MODELS LAYER (models/)**
**Vai trò:** Define data structures, constants, validation

**Quyền:**
- ✅ Data classes
- ✅ Enums
- ✅ Constants
- ✅ Validation logic (Pydantic, dataclasses)

**Cấm:**
- ❌ Database operations
- ❌ Discord operations
- ❌ External API calls

**Cấu trúc:**
```python
# models/my_model.py
from enum import Enum
from dataclasses import dataclass

class UserRole(Enum):
    ADMIN = "admin"
    MODERATOR = "moderator"
    USER = "user"

@dataclass
class User:
    user_id: int
    username: str
    role: UserRole
    points: int = 0
    
    def is_admin(self) -> bool:
        return self.role == UserRole.ADMIN
    
    def add_points(self, amount: int):
        if amount < 0:
            raise ValueError("Points must be positive")
        self.points += amount

# Constants
MIN_USERNAME_LENGTH = 3
MAX_USERNAME_LENGTH = 32
POINTS_PER_MESSAGE = 5
```

---

### **Layer 5: DATABASE LAYER (utils.py + database/)**
**Vai trò:** Quản lý tất cả database operations

**Quyền:**
- ✅ CRUD operations
- ✅ SQL queries
- ✅ Database connection management

**Cấm:**
- ❌ Business logic
- ❌ Discord operations

**Cấu trúc:**
```python
# utils.py
class CogDatabase:
    def insert(self, table, data):
        # Query execution
        pass
    
    def select(self, table, where='', params=()):
        # Query execution
        pass
    
    def update(self, table, data, where='', params=()):
        # Query execution
        pass
```

---

### **Layer 6: CONFIG LAYER (config.py)**
**Vai trò:** Centralized configuration

**Quyền:**
- ✅ Load .env variables
- ✅ Define global constants
- ✅ Path management

**Cấm:**
- ❌ Business logic
- ❌ Database operations

**Cấu trúc:**
```python
# config.py
import os
from dotenv import load_dotenv

load_dotenv()

# Environment
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
BOT_PREFIX = os.getenv('BOT_PREFIX', '!')

# Paths
DATABASE_DIR = 'database'
LOGS_DIR = 'logs'
COGS_DIR = 'cogs'

# Constants
MAX_USERNAME_LENGTH = 32
```

---

## 🏗️ Cấu Trúc Thư Mục Hoàn Chỉnh

```
BOT DISCORD/
├── main.py                    # Layer 1: Entry Point
├── config.py                  # Layer 6: Config
├── utils.py                   # Layer 5: Database Utils
├── requirements.txt
├── .env
├── .gitignore
│
├── cogs/                       # Layer 2: Commands
│   ├── __init__.py
│   ├── user_commands.py
│   └── admin_commands.py
│
├── services/                   # Layer 3: Services
│   ├── __init__.py
│   ├── user_service.py
│   └── admin_service.py
│
├── models/                     # Layer 4: Models
│   ├── __init__.py
│   ├── user_model.py
│   ├── admin_model.py
│   └── constants.py
│
├── database/                   # Layer 5: Database Files
│   ├── user_service.db
│   └── admin_service.db
│
└── docs/
    ├── ARCHITECTURE.md        # File này
    └── API.md
```

---

## 🔄 Quy Trình Thực Hiện Một Feature

### 1️⃣ **Tạo Model** (Layer 4)
```python
# models/feature_model.py
@dataclass
class Feature:
    name: str
    value: int
    
    def validate(self):
        if self.value < 0:
            raise ValueError("Value must be positive")
```

### 2️⃣ **Tạo Service** (Layer 3)
```python
# services/feature_service.py
class FeatureService:
    def __init__(self):
        self.db = CogDatabase('feature')
        self.db.create_table('features', '''
            id INTEGER PRIMARY KEY,
            name TEXT,
            value INTEGER
        ''')
    
    def create_feature(self, feature: Feature):
        feature.validate()
        self.db.insert('features', {
            'name': feature.name,
            'value': feature.value
        })
```

### 3️⃣ **Tạo Cog** (Layer 2)
```python
# cogs/feature_cog.py
class FeatureCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.service = FeatureService()
    
    @commands.command(name='createfeature')
    async def create_feature(self, ctx, name: str, value: int):
        try:
            feature = Feature(name, value)
            self.service.create_feature(feature)
            await ctx.send("✅ Feature created!")
        except Exception as e:
            await ctx.send(f"❌ Error: {e}")
```

### 4️⃣ **Cập nhật main.py** (Layer 1)
- main.py **tự động load** tất cả cogs ✨
- Không cần sửa gì cả!

---

## ⚠️ Lưu Ý Quan Trọng

| ❌ SAI | ✅ ĐÚNG |
|-------|--------|
| Database logic ở Command | Database logic ở Service |
| Direct SQL ở Service | CogDatabase wrapper ở Service |
| Business logic ở Command | Business logic ở Service |
| Hardcode values ở Cog | Constants ở models/constants.py |
| No error handling ở Command | Try-catch ở Command |
| Import từ database/ | Import từ utils |

---

## 📝 Checklist Khi Tạo Feature Mới

- [ ] Tạo Model (nếu cần)
- [ ] Tạo Service (chứa logic)
- [ ] Tạo Cog (nhận command)
- [ ] Test từng layer riêng lẻ
- [ ] Test integration
- [ ] Update docs (nếu cần)

---

## 🎯 Lợi Ích Của Kiến Trúc Này

✅ **Dễ maintain** - Mỗi layer độc lập
✅ **Dễ test** - Test từng layer riêng
✅ **Dễ scale** - Thêm feature không ảnh hưởng cũ
✅ **Dễ debug** - Biết lỗi ở layer nào
✅ **Code reuse** - Service dùng ở nhiều cog
✅ **Clean code** - Separation of concerns

