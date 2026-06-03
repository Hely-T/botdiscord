# 📖 Commands Reference - Danh Sách Lệnh

Danh sách tất cả các lệnh hiện có của bot.

---

## �� Role Management Commands (role_cog.py)

Quản lý quyền commands theo role.

### 1️⃣ `!addrole` - Thêm Quyền Cho Role

**Cú pháp:**
```
!addrole @role_name command_name
```

**Quyền:** Chỉ Admin
**Database:** command_role.db

**Ví dụ:**
```
!addrole @admin ban
!addrole @moderator kick
!addrole @trusted mute
```

**Kết quả:**
```
✅ Thêm Quyền Thành Công
Role @admin được dùng lệnh `ban`
```

**Giải thích:**
- Sau khi chạy lệnh này, chỉ user có role @admin mới được dùng lệnh `!ban`

---

### 2️⃣ `!removerole` - Xóa Quyền Của Role

**Cú pháp:**
```
!removerole @role_name command_name
```

**Quyền:** Chỉ Admin
**Database:** command_role.db

**Ví dụ:**
```
!removerole @moderator ban
!removerole @trusted mute
```

**Kết quả:**
```
✅ Xóa Quyền Thành Công
Role @moderator không được dùng lệnh `ban` nữa
```

**Giải thích:**
- Xóa quyền `ban` của role @moderator
- Nếu role khác có quyền, họ vẫn có thể dùng

---

### 3️⃣ `!perms` - Xem Quyền Của Một Command

**Cú pháp:**
```
!perms command_name
```

**Quyền:** Mọi người
**Database:** command_role.db

**Ví dụ:**
```
!perms ban
!perms kick
!perms mute
```

**Kết quả:**
```
📋 Quyền của lệnh: ban
• Admin
• Moderator
Tổng số: 2 role(s)
```

**Giải thích:**
- Xem tất cả roles có quyền dùng lệnh
- Nếu không có role nào → "Chưa có role nào được phép"

---

### 4️⃣ `!myroles` - Xem Roles Của Bạn

**Cú pháp:**
```
!myroles [@user]
```

**Quyền:** Mọi người
**Database:** Discord (không lưu)

**Ví dụ:**
```
!myroles              (xem roles của bạn)
!myroles @JohnDoe     (xem roles của JohnDoe)
```

**Kết quả:**
```
👤 Roles của JohnDoe
@admin
@moderator
@trusted
Tổng số: 3 role(s)
```

**Giải thích:**
- Xem danh sách roles của bạn hoặc người khác
- Bỏ role @everyone

---

### 5️⃣ `!rolescommands` - Xem Commands Của Một Role

**Cú pháp:**
```
!rolescommands @role_name
```

**Quyền:** Mọi người
**Database:** command_role.db

**Ví dụ:**
```
!rolescommands @admin
!rolescommands @moderator
```

**Kết quả:**
```
📋 Commands của role Admin
• ban
• kick
• mute
• warn
Tổng số: 4 command(s)
```

**Giải thích:**
- Xem tất cả commands mà role có quyền dùng
- Nếu không có command nào → "Role này không có quyền dùng command nào"

---

## 👤 User Commands (user_cog.py)

### 1️⃣ `!profile` - Xem Profile

**Cú pháp:**
```
!profile [@user]
```

**Kết quả:**
```
👤 Profile - JohnDoe
🎯 Level: 5
⭐ Points: 2500
👑 Role: user
```

---

### 2️⃣ `!addpoints` - Thêm Points

**Cú pháp:**
```
!addpoints @user amount
```

**Quyền:** Admin

**Ví dụ:**
```
!addpoints @JohnDoe 100
```

---

### 3️⃣ `!topusers` - Xem Top Users

**Cú pháp:**
```
!topusers [limit]
```

**Ví dụ:**
```
!topusers      (top 10)
!topusers 20   (top 20)
```

---

## 📝 Command Structure

```
Command Cog
    ↓
Service Layer
    ↓
Database Layer (CogDatabase)
    ↓
SQLite Database
```

---

## 🔍 Command Permission Check

Khi user dùng lệnh:

```
1. Bot check: User có @admin role không?
2. Bot check database: @admin có quyền dùng lệnh này không?
3. Nếu Yes → Cho phép chạy ✅
4. Nếu No → Từ chối ❌
```

---

## 📊 Database Liên Kết

| Command | Database | Tables |
|---------|----------|--------|
| !addrole | command_role.db | command_permissions, role_hierarchy |
| !removerole | command_role.db | command_permissions |
| !perms | command_role.db | command_permissions |
| !myroles | (None) | (Discord API) |
| !rolescommands | command_role.db | command_permissions |
| !profile | khach.db | users, user_profiles |
| !addpoints | khach.db | users |
| !topusers | khach.db | users |

---

## 🚀 Sắp Tới

Các cogs sẽ được thêm:
- [ ] Booking Management
- [ ] Cash Management
- [ ] Autoresponders
- [ ] Chat History
- [ ] Guild Settings
- [ ] Logs

