# 🎨 Prefix & Splash Helpers - Hướng Dẫn

---

## 📌 Prefix

**Prefix** là ký tự bắt đầu mỗi command. Mặc định: `!`

### Lấy Prefix từ .env

```python
from utils import get_prefix

prefix = get_prefix()
# → '!' (từ .env)
```

### Sử Dụng trong Help Text

```python
from utils import get_command_help

help_text = get_command_help('addrole')
# → '!addrole'
```

### Cập Nhật Prefix

**File:** `.env`

```env
BOT_PREFIX=!
```

Thay `!` bằng prefix khác (vd: `>`, `$`, v.v.)

---

## 🎨 Splash (Embeds) Helpers

Splash = Embed đẹp mắt để hiển thị thông tin

### 5 Loại Splash

| Loại | Hàm | Màu | Ví Dụ |
|------|-----|-----|-------|
| Lỗi | `create_error_splash()` | 🔴 Đỏ | "❌ Người dùng không tồn tại" |
| Thành Công | `create_success_splash()` | 🟢 Xanh | "✅ Tạo người dùng thành công" |
| Thông Tin | `create_info_splash()` | 🔵 Xanh Dương | "📋 Danh sách roles" |
| Cảnh Báo | `create_warning_splash()` | 🟠 Cam | "⚠️ Không tìm thấy role" |
| Custom | `create_splash_single()` | Tùy | Tự chọn |

---

## 💡 Ví Dụ Chi Tiết

### 1️⃣ Error Splash

```python
from utils import create_error_splash

embed = create_error_splash(
    error_message="User không tồn tại!",
    footer_text="ID: 12345"
)

await ctx.send(embed=embed)
```

**Kết quả:**
```
❌ Lỗi
User không tồn tại!
─────────────────
ID: 12345
```

---

### 2️⃣ Success Splash

```python
from utils import create_success_splash

embed = create_success_splash(
    title="Tạo Người Dùng",
    description="Người dùng JohnDoe đã được tạo",
    fields={
        'User ID': '12345',
        'Level': '1',
        'Points': '0'
    }
)

await ctx.send(embed=embed)
```

**Kết quả:**
```
✅ Tạo Người Dùng
Người dùng JohnDoe đã được tạo
─────────────────────────────
User ID: 12345
Level: 1
Points: 0
```

---

### 3️⃣ Info Splash

```python
from utils import create_info_splash

embed = create_info_splash(
    title="Danh Sách Quyền",
    description="Command: ban",
    fields={
        'Role 1': 'Admin',
        'Role 2': 'Moderator',
        'Total': '2 roles'
    }
)

await ctx.send(embed=embed)
```

**Kết quả:**
```
📋 Danh Sách Quyền
Command: ban
─────────────────
Role 1: Admin
Role 2: Moderator
Total: 2 roles
```

---

### 4️⃣ Warning Splash

```python
from utils import create_warning_splash

embed = create_warning_splash(
    title="Không Tìm Thấy",
    description="User không tồn tại trong database"
)

await ctx.send(embed=embed)
```

**Kết quả:**
```
⚠️ Không Tìm Thấy
User không tồn tại trong database
```

---

### 5️⃣ Custom Single Splash

```python
from utils import create_splash_single
import discord

embed = create_splash_single(
    title="👤 Profile",
    description="JohnDoe",
    color=discord.Color.purple(),
    fields={
        'Level': '5',
        'XP': '2500',
        'Role': 'user'
    },
    thumbnail_url="https://...",
    footer_text="Server: My Discord"
)

await ctx.send(embed=embed)
```

---

### 6️⃣ Double Splash (2 Embeds)

```python
from utils import create_splash_double
import discord

embed1, embed2 = create_splash_double(
    title1="📍 Người Cho",
    description1="JohnDoe",
    title2="📍 Người Nhận",
    description2="JaneDoe",
    color1=discord.Color.blue(),
    color2=discord.Color.green(),
    fields1={'Amount': '100 points'},
    fields2={'Total': '100 points'}
)

await ctx.send(embed=embed1)
await ctx.send(embed=embed2)
```

**Kết quả:**
```
📍 Người Cho
JohnDoe
─────────────────
Amount: 100 points

📍 Người Nhận
JaneDoe
─────────────────
Total: 100 points
```

---

## 🎯 Khi Nào Sử Dụng

### Error Splash
```python
# Khi user input sai, lỗi database, v.v.
if not user:
    embed = create_error_splash("User không tồn tại!")
    await ctx.send(embed=embed)
```

### Success Splash
```python
# Khi hành động hoàn tất thành công
embed = create_success_splash("Tạo Người Dùng", fields={...})
await ctx.send(embed=embed)
```

### Info Splash
```python
# Khi hiển thị thông tin, danh sách
embed = create_info_splash("Danh Sách", fields={...})
await ctx.send(embed=embed)
```

### Warning Splash
```python
# Khi có vấn đề nhưng không phải lỗi
if not roles:
    embed = create_warning_splash("Không Tìm Thấy Role")
    await ctx.send(embed=embed)
```

### Custom/Double Splash
```python
# Khi cần thiết kế đặc biệt
# Khi cần hiển thị so sánh 2 thứ
```

---

## 📚 All Helper Functions

```python
from utils import (
    get_prefix,
    get_command_help,
    create_splash_single,
    create_splash_double,
    create_error_splash,
    create_success_splash,
    create_info_splash,
    create_warning_splash
)
```

---

## 🔧 Cách Sử Dụng trong Cogs

### Ví Dụ: Role Cog

```python
from utils import (
    get_command_help,
    create_success_splash,
    create_error_splash,
    create_info_splash
)

class RoleCog(commands.Cog):
    @commands.command(name='addrole')
    async def add_role(self, ctx, role: discord.Role, *, command_name: str):
        try:
            # Business logic
            self.service.add_command_role(...)
            
            # Success splash
            embed = create_success_splash(
                title="Thêm Quyền",
                description=f"Role {role.mention} được dùng `{command_name}`",
                fields={'Role': role.name, 'Command': command_name}
            )
            await ctx.send(embed=embed)
        
        except Exception as e:
            # Error splash
            embed = create_error_splash(str(e))
            await ctx.send(embed=embed)
```

---

## 📝 Notes

✅ **Luôn sử dụng splash thay vì plain text**
✅ **Chọn màu phù hợp với loại thông báo**
✅ **Thêm footer text khi cần thiết**
✅ **Sử dụng fields để organize thông tin**
✅ **Sử dụng emojis trong title**

---

## 🚀 Sắp Tới

Khi bạn nói "thêm splash":
- **"Thêm splash"** → Mỗi command tự chọn loại splash
- **"Thêm splash mỗi"** → Mỗi command 1 splash
- **"Thêm splash cả 2"** → Mỗi command 2 splashes

