# 🛠️ Utils Reference - Hàm Dùng Chung

Danh sách tất cả các hàm helper trong `utils.py`.

---

## 📚 Database Management

### CogDatabase Class
```python
from utils import CogDatabase

db = CogDatabase('myfeature')

# Create table
db.create_table('users', '''
    id INTEGER PRIMARY KEY,
    name TEXT
''')

# Insert
db.insert('users', {'name': 'John'})

# Select
users = db.select('users')
user = db.select_one('users', 'id = ?', (1,))

# Update
db.update('users', {'name': 'Jane'}, 'id = ?', (1,))

# Delete
db.delete('users', 'id = ?', (1,))

# Custom SQL
db.execute('DELETE FROM users WHERE age < 18')
results = db.fetch('SELECT * FROM users')
```

---

## 🔐 Role Permissions

### RolePermissionManager Class
```python
from utils import RolePermissionManager

manager = RolePermissionManager()

# Add permission
manager.add_permission(guild_id=123, role_id=456, command='ban')

# Remove permission
manager.remove_permission(guild_id=123, role_id=456, command='ban')

# Check permission
can_use = manager.can_use_command(guild_id=123, user_roles=[456], command='ban')

# Get roles for command
roles = manager.get_roles_for_command(guild_id=123, command='ban')

# Get commands for role
commands = manager.get_commands_for_role(guild_id=123, role_id=456)

# Set default permission
manager.set_command_default('ban', 'admin', 'Ban user')

# Add role hierarchy
manager.add_role_hierarchy(guild_id=123, role_id=456, role_name='Admin', level=10)
```

---

## 📌 Prefix Helpers

### get_prefix()
Lấy prefix từ .env
```python
from utils import get_prefix

prefix = get_prefix()  # → '!'
```

### get_command_help()
Tạo cú pháp help
```python
from utils import get_command_help

help_text = get_command_help('addrole')  # → '!addrole'
help_text = get_command_help('ban', prefix='>')  # → '>ban'
```

---

## 🎨 Splash (Embed) Helpers

### create_error_splash()
Tạo embed lỗi (màu đỏ)
```python
from utils import create_error_splash

embed = create_error_splash(
    error_message="User không tồn tại!",
    footer_text="Server: My Discord"
)
await ctx.send(embed=embed)
```

### create_success_splash()
Tạo embed thành công (màu xanh)
```python
from utils import create_success_splash

embed = create_success_splash(
    title="Tạo User",
    description="User JohnDoe tạo thành công",
    fields={'User ID': '12345', 'Level': '1'}
)
await ctx.send(embed=embed)
```

### create_info_splash()
Tạo embed thông tin (màu xanh dương)
```python
from utils import create_info_splash

embed = create_info_splash(
    title="Danh Sách Quyền",
    description="Command: ban",
    fields={'Role 1': 'Admin', 'Role 2': 'Moderator'}
)
await ctx.send(embed=embed)
```

### create_warning_splash()
Tạo embed cảnh báo (màu cam)
```python
from utils import create_warning_splash

embed = create_warning_splash(
    title="Không Tìm Thấy",
    description="User không tồn tại"
)
await ctx.send(embed=embed)
```

### create_splash_single()
Tạo embed tuỳ chỉnh (1 embed)
```python
from utils import create_splash_single
import discord

embed = create_splash_single(
    title="👤 Profile",
    description="JohnDoe",
    color=discord.Color.purple(),
    fields={'Level': '5', 'XP': '2500'},
    thumbnail_url="https://...",
    footer_text="Server: My Discord"
)
await ctx.send(embed=embed)
```

### create_splash_double()
Tạo 2 embeds tuỳ chỉnh
```python
from utils import create_splash_double

embed1, embed2 = create_splash_double(
    title1="📍 From",
    description1="JohnDoe",
    title2="📍 To",
    description2="JaneDoe"
)
await ctx.send(embed=embed1)
await ctx.send(embed=embed2)
```

---

## ⏰ Timestamp Helpers

### get_timestamp()
Lấy timestamp hiện tại
```python
from utils import get_timestamp

time_str = get_timestamp()  # → '2026-06-03 15:30:45'
```

### log_to_file()
Ghi log vào file
```python
from utils import log_to_file

log_to_file("User 123 joined", filename='bot.log')
# → Ghi vào logs/bot.log
```

---

## 📊 Complete Import Reference

```python
# Database
from utils import CogDatabase

# Role Permissions
from utils import RolePermissionManager

# Prefix
from utils import get_prefix, get_command_help

# Splashes (Embeds)
from utils import (
    create_splash_single,
    create_splash_double,
    create_error_splash,
    create_success_splash,
    create_info_splash,
    create_warning_splash
)

# Timestamps
from utils import get_timestamp, log_to_file
```

---

## 🎯 Quick Examples

### Example 1: Create & Insert Data
```python
from utils import CogDatabase, get_timestamp, create_success_splash

db = CogDatabase('mydata')
db.create_table('users', 'id INTEGER PRIMARY KEY, name TEXT, created_at TEXT')

db.insert('users', {
    'name': 'John',
    'created_at': get_timestamp()
})

embed = create_success_splash(
    title="Tạo User",
    description="User John đã được tạo",
    fields={'Name': 'John', 'Time': get_timestamp()}
)
```

### Example 2: Check Permission & Response
```python
from utils import RolePermissionManager, create_error_splash, create_success_splash

manager = RolePermissionManager()

user_roles = [role.id for role in ctx.author.roles]

if manager.can_use_command(ctx.guild.id, user_roles, 'ban'):
    embed = create_success_splash("Bạn có quyền dùng lệnh ban")
else:
    embed = create_error_splash("Bạn không có quyền dùng lệnh ban")

await ctx.send(embed=embed)
```

### Example 3: Get Prefix in Command
```python
from utils import get_prefix, create_info_splash

prefix = get_prefix()

embed = create_info_splash(
    title="Help",
    description=f"Gõ {prefix}commands để xem danh sách lệnh"
)
await ctx.send(embed=embed)
```

