# 📚 Documentation - Hướng Dẫn Toàn Bộ

Danh sách tất cả tài liệu của dự án bot Discord.

---

## 🎯 Bắt Đầu

### Dành cho người mới
1. **[QUICK_START.md](QUICK_START.md)** - Tạo feature mới chỉ 3 bước
2. **[ARCHITECTURE.md](ARCHITECTURE.md)** - Hiểu cấu trúc 6 layers

### Dành cho kỹ sư
3. **[ARCHITECTURE.md](ARCHITECTURE.md)** - Chi tiết 6 layers
4. **[DATABASE_GUIDE.md](DATABASE_GUIDE.md)** - CogDatabase helpers
5. **[UTILS_REFERENCE.md](UTILS_REFERENCE.md)** - Tất cả hàm helpers

---

## 📊 Database & Data

1. **[DATABASE_SCHEMAS.md](DATABASE_SCHEMAS.md)** - Schema chi tiết (8 databases)
2. **[MAIN_DATABASES.md](MAIN_DATABASES.md)** - Danh sách nhanh
3. **[DATABASE_GUIDE.md](DATABASE_GUIDE.md)** - Cách dùng CogDatabase

---

## 🔐 Quyền & Role Management

1. **[ROLE_PERMISSIONS_GUIDE.md](ROLE_PERMISSIONS_GUIDE.md)** - Hệ thống quyền chi tiết
2. **[PREFIX_SPLASH_GUIDE.md](PREFIX_SPLASH_GUIDE.md)** - Prefix & Embed helpers

---

## 🎨 UI & Responses

1. **[PREFIX_SPLASH_GUIDE.md](PREFIX_SPLASH_GUIDE.md)** - Tạo embeds đẹp
   - Error Splash (đỏ)
   - Success Splash (xanh)
   - Info Splash (xanh dương)
   - Warning Splash (cam)
   - Custom Splash
   - Double Splash

---

## 📚 Hàm Dùng Chung (utils.py)

### Database
- `CogDatabase` - Quản lý database

### Role Permissions
- `RolePermissionManager` - Quản lý quyền commands

### Prefix
- `get_prefix()` - Lấy prefix từ .env
- `get_command_help()` - Tạo cú pháp help

### Splashes (Embeds)
- `create_error_splash()` - Embed lỗi
- `create_success_splash()` - Embed thành công
- `create_info_splash()` - Embed thông tin
- `create_warning_splash()` - Embed cảnh báo
- `create_splash_single()` - Embed tuỳ chỉnh (1)
- `create_splash_double()` - Embed tuỳ chỉnh (2)

### Timestamps
- `get_timestamp()` - Lấy thời gian
- `log_to_file()` - Ghi log

---

## 📖 Ví Dụ Chi Tiết

1. **[LAYER_EXAMPLES.md](LAYER_EXAMPLES.md)** - Ví dụ Posting System hoàn chỉnh
   - Model
   - Service
   - Cog
   - Database schema

---

## 🗺️ Navigation

```
docs/
├── README.md (File này)
├── QUICK_START.md             ← Start here!
├── ARCHITECTURE.md             ← Hiểu cấu trúc
├── DATABASE_GUIDE.md           ← Cách dùng database
├── DATABASE_SCHEMAS.md         ← Schema chi tiết
├── MAIN_DATABASES.md           ← Danh sách databases
├── LAYER_EXAMPLES.md           ← Ví dụ complex
├── ROLE_PERMISSIONS_GUIDE.md   ← Quyền commands
├── PREFIX_SPLASH_GUIDE.md      ← UI & Embeds
└── UTILS_REFERENCE.md          ← Tất cả hàm helpers
```

---

## 📝 Tóm Tắt

| Mục | File | Mục Đích |
|-----|------|----------|
| 🚀 Quick Start | QUICK_START.md | Tạo feature 3 bước |
| 🏗️ Architecture | ARCHITECTURE.md | Hiểu cấu trúc |
| 🗄️ Database | DATABASE_SCHEMAS.md | Schema chi tiết |
| 🔐 Permissions | ROLE_PERMISSIONS_GUIDE.md | Quyền commands |
| 🎨 UI | PREFIX_SPLASH_GUIDE.md | Embeds & Prefix |
| 🛠️ Helpers | UTILS_REFERENCE.md | Hàm dùng chung |
| 📚 Examples | LAYER_EXAMPLES.md | Ví dụ phức tạp |

---

## 🎓 Learning Path

### Người mới
1. QUICK_START.md
2. ARCHITECTURE.md
3. Tạo feature đầu tiên

### Kỹ sư
1. ARCHITECTURE.md
2. DATABASE_SCHEMAS.md
3. UTILS_REFERENCE.md
4. LAYER_EXAMPLES.md

### Designer/UI
1. PREFIX_SPLASH_GUIDE.md
2. UTILS_REFERENCE.md (Splash section)

---

## ✅ Khi Cần...

| Cần... | Xem... |
|--------|--------|
| Tạo feature mới | QUICK_START.md |
| Hiểu kiến trúc | ARCHITECTURE.md |
| Làm việc với database | DATABASE_GUIDE.md |
| Lấy schema | DATABASE_SCHEMAS.md |
| Hiểu quyền commands | ROLE_PERMISSIONS_GUIDE.md |
| Tạo embeds đẹp | PREFIX_SPLASH_GUIDE.md |
| Tìm hàm helpers | UTILS_REFERENCE.md |
| Ví dụ chi tiết | LAYER_EXAMPLES.md |

---

## 🚀 Getting Started

```bash
# 1. Đọc architecture
cat ARCHITECTURE.md

# 2. Tạo feature đầu tiên
cat QUICK_START.md

# 3. Deploy bot
# (Sau khi tạo features)
```

---

## 📞 Help & Support

**Tất cả tài liệu đều có ví dụ code chi tiết!**

Mỗi file đều có:
- ✅ Giải thích chi tiết
- ✅ Ví dụ thực tế
- ✅ Best practices
- ✅ Checklist

---

