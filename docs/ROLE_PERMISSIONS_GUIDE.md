# 🔐 Role Permissions System - Hướng Dẫn

Hệ thống quản lý quyền commands dựa vào role Discord.

---

## 🎯 Ý Tưởng

**Bạn muốn:**
- `!addrole @admin ban` → Chỉ role @admin được dùng lệnh ban
- `!addrole @moderator kick` → Chỉ role @moderator được dùng lệnh kick
- Nếu không thiết lập, sẽ dùng quyền mặc định của lệnh

---

## 📚 RolePermissionManager - Class Quản Lý

**Import:**
```python
from utils import RolePermissionManager

manager = RolePermissionManager()
```

---

## 🔧 Các Method

### 1️⃣ `add_permission()` - Thêm Quyền

**Cú pháp:**
```python
manager.add_permission(
    guild_id=123,           # Server ID
    role_id=456,            # Role ID
    command_name='ban',     # Tên command
    created_by=789          # User ID người tạo (optional)
)
```

**Ví dụ:**
```python
# Thêm quyền cho role @admin (ID: 987654) dùng lệnh 'ban' trên server (ID: 123456)
manager.add_permission(
    guild_id=123456,
    role_id=987654,
    command_name='ban',
    created_by=ctx.author.id
)
```

**Kết quả:**
- ✅ Role @admin được dùng lệnh ban
- ❌ Các role khác không dùng được

---

### 2️⃣ `remove_permission()` - Xóa Quyền

**Cú pháp:**
```python
manager.remove_permission(
    guild_id=123,
    role_id=456,
    command_name='ban'
)
```

**Ví dụ:**
```python
# Xóa quyền 'ban' của role @moderator
manager.remove_permission(
    guild_id=123456,
    role_id=987654,
    command_name='ban'
)
```

---

### 3️⃣ `can_use_command()` - Check Quyền

**Cú pháp:**
```python
can_use = manager.can_use_command(
    guild_id=123,
    user_roles=[456, 789],  # List role IDs của user
    command_name='ban'
)
```

**Ví dụ:**
```python
# Check xem user có thể dùng lệnh 'ban' không
user_roles = [role.id for role in ctx.author.roles]

if manager.can_use_command(
    guild_id=ctx.guild.id,
    user_roles=user_roles,
    command_name='ban'
):
    await ctx.send("✅ Bạn có quyền dùng lệnh này!")
else:
    await ctx.send("❌ Bạn không có quyền dùng lệnh này!")
```

---

### 4️⃣ `get_roles_for_command()` - Lấy Roles Cho Command

**Cú pháp:**
```python
roles = manager.get_roles_for_command(
    guild_id=123,
    command_name='ban'
)
```

**Kết quả:**
```python
[
    {'role_id': 456, 'role_name': 'Admin'},
    {'role_id': 789, 'role_name': 'Moderator'}
]
```

**Ví dụ:**
```python
# Lấy danh sách roles có quyền dùng 'ban'
roles = manager.get_roles_for_command(
    guild_id=ctx.guild.id,
    command_name='ban'
)

if roles:
    role_names = [r['role_name'] for r in roles]
    await ctx.send(f"📋 Roles có quyền: {', '.join(role_names)}")
else:
    await ctx.send("Chưa ai được phép dùng lệnh này!")
```

---

### 5️⃣ `get_commands_for_role()` - Lấy Commands Cho Role

**Cú pháp:**
```python
commands = manager.get_commands_for_role(
    guild_id=123,
    role_id=456
)
```

**Kết quả:**
```python
['ban', 'kick', 'mute', 'warn']
```

**Ví dụ:**
```python
# Lấy danh sách commands mà role @admin có quyền
admin_role = discord.utils.find(lambda r: r.name == 'Admin', ctx.guild.roles)

if admin_role:
    commands = manager.get_commands_for_role(
        guild_id=ctx.guild.id,
        role_id=admin_role.id
    )
    await ctx.send(f"📋 Admin có quyền dùng: {', '.join(commands)}")
```

---

### 6️⃣ `set_command_default()` - Set Default Permission

**Cú pháp:**
```python
manager.set_command_default(
    command_name='ban',
    default_permission='admin',  # 'everyone', 'admin', 'moderator'
    description='Cấm user khỏi server'
)
```

**Ví dụ:**
```python
# Set lệnh 'ban' chỉ admin mặc định có thể dùng
manager.set_command_default(
    command_name='ban',
    default_permission='admin',
    description='Cấm user khỏi server'
)
```

---

### 7️⃣ `add_role_hierarchy()` - Thêm Role Hierarchy

**Cú pháp:**
```python
manager.add_role_hierarchy(
    guild_id=123,
    role_id=456,
    role_name='Admin',
    hierarchy_level=10  # 0=thấp, 10=cao
)
```

---

## 💡 Ví Dụ Hoàn Chỉnh - addrole/removerole Commands

### Service:
```python
# services/role_permission_service.py
from utils import RolePermissionManager

class RolePermissionService:
    def __init__(self):
        self.manager = RolePermissionManager()
    
    def add_command_role(self, guild_id: int, role_id: int, command_name: str, 
                         created_by: int) -> bool:
        """Thêm role cho command"""
        return self.manager.add_permission(
            guild_id=guild_id,
            role_id=role_id,
            command_name=command_name,
            created_by=created_by
        )
    
    def remove_command_role(self, guild_id: int, role_id: int, command_name: str) -> bool:
        """Xóa role khỏi command"""
        return self.manager.remove_permission(guild_id, role_id, command_name)
    
    def user_can_use(self, guild_id: int, user_roles: list, command_name: str) -> bool:
        """Check user có thể dùng command không"""
        return self.manager.can_use_command(guild_id, user_roles, command_name)
```

### Cog/Commands:
```python
# cogs/role_management_cog.py
import discord
from discord.ext import commands
from services.role_permission_service import RolePermissionService

class RoleManagementCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.service = RolePermissionService()
    
    @commands.command(name='addrole')
    @commands.has_permissions(administrator=True)
    async def add_role(self, ctx, role: discord.Role, *, command_name: str):
        """
        Thêm role cho command
        
        Ví dụ: !addrole @admin ban
        """
        try:
            self.service.add_command_role(
                guild_id=ctx.guild.id,
                role_id=role.id,
                command_name=command_name.lower(),
                created_by=ctx.author.id
            )
            
            embed = discord.Embed(
                title="✅ Thêm Quyền",
                description=f"Role {role.mention} được dùng lệnh `{command_name}`",
                color=discord.Color.green()
            )
            await ctx.send(embed=embed)
        
        except Exception as e:
            await ctx.send(f"❌ Lỗi: {str(e)}")
    
    @commands.command(name='removerole')
    @commands.has_permissions(administrator=True)
    async def remove_role(self, ctx, role: discord.Role, *, command_name: str):
        """
        Xóa role khỏi command
        
        Ví dụ: !removerole @moderator ban
        """
        try:
            self.service.remove_command_role(
                guild_id=ctx.guild.id,
                role_id=role.id,
                command_name=command_name.lower()
            )
            
            embed = discord.Embed(
                title="✅ Xóa Quyền",
                description=f"Role {role.mention} không được dùng lệnh `{command_name}`",
                color=discord.Color.green()
            )
            await ctx.send(embed=embed)
        
        except Exception as e:
            await ctx.send(f"❌ Lỗi: {str(e)}")
    
    @commands.command(name='perms')
    async def show_permissions(self, ctx, *, command_name: str = None):
        """
        Xem quyền của lệnh hoặc role
        
        Ví dụ: !perms ban
        Ví dụ: !perms @admin
        """
        try:
            if command_name:
                # Nếu là tên command
                roles = self.service.manager.get_roles_for_command(
                    ctx.guild.id,
                    command_name.lower()
                )
                
                if roles:
                    role_list = '\n'.join([f"• {r['role_name']}" for r in roles])
                    embed = discord.Embed(
                        title=f"Quyền của lệnh: {command_name}",
                        description=role_list,
                        color=discord.Color.blue()
                    )
                else:
                    embed = discord.Embed(
                        title=f"Quyền của lệnh: {command_name}",
                        description="Chưa ai được phép dùng lệnh này",
                        color=discord.Color.blue()
                    )
                
                await ctx.send(embed=embed)
        
        except Exception as e:
            await ctx.send(f"❌ Lỗi: {str(e)}")

async def setup(bot):
    await bot.add_cog(RoleManagementCog(bot))
```

---

## 🗄️ Database Schema

```sql
-- Table lưu quyền commands theo role
CREATE TABLE command_permissions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    guild_id INTEGER NOT NULL,          -- Server ID
    role_id INTEGER,                    -- Role ID (NULL = @everyone)
    command_name TEXT NOT NULL,         -- Tên command (vd: 'ban')
    is_allowed BOOLEAN DEFAULT 1,       -- Cho phép hay cấm
    created_by INTEGER,                 -- User tạo
    created_at TEXT NOT NULL
);

-- Ví dụ dữ liệu:
-- guild_id: 123456 (Server ID)
-- role_id: 987654 (Admin role ID)
-- command_name: 'ban'
-- is_allowed: 1
```

---

## 📋 Flowchart

```
User dùng lệnh !ban
    ↓
Cog intercept command
    ↓
Check can_use_command()
    ↓
    ├─ True → Cho phép dùng ✅
    │
    └─ False → Không cho phép ❌
```

---

## 🎯 Summary

✅ **RolePermissionManager** trong `utils.py`
✅ **Database:** `command_role.db`
✅ **Service:** `role_permission_service.py`
✅ **Commands:** `!addrole`, `!removerole`, `!perms`

**Sắp tới:** Bạn sẽ tạo cog với những lệnh này! 🚀

