# 🔐 Environment Setup - Cấu Hình .env

---

## 📝 File .env Structure

```env
# ============================================
# Application Configuration
# ============================================
APP_NAME=Discord Bot

# ============================================
# Discord Bot - REQUIRED
# Get from https://discord.com/developers/applications
# ============================================
DISCORD_TOKEN=your_bot_token_here
DISCORD_OWNER_IDS=123456789,987654321

# ============================================
# Bot Settings
# ============================================
BOT_PREFIX=!

# ============================================
# Admin Information (Optional)
# ============================================
ADMIN_ID=your_admin_id_here
ADMIN_USERNAME=your_admin_username
ADMIN_EMAIL=your_email@example.com
```

---

## 🔑 Lấy Credentials

### 1. DISCORD_TOKEN
1. Vào https://discord.com/developers/applications
2. Tạo hoặc chọn ứng dụng
3. Vào tab "Bot"
4. Click "Reset Token"
5. Copy token vào `DISCORD_TOKEN=`

**Lưu ý:** Giữ token bí mật! Không commit lên Git!

---

### 2. DISCORD_OWNER_IDS
Danh sách Discord ID của bot owners (có quyền cao nhất)

**Cách lấy Discord ID:**
1. Bật Developer Mode trong Discord
2. Click chuột phải vào username → Copy User ID
3. Thêm ID vào `DISCORD_OWNER_IDS=` (cách nhau bằng dấu phẩy)

**Ví dụ:**
```env
DISCORD_OWNER_IDS=123456789,987654321,555666777
```

---

### 3. APP_NAME
Tên ứng dụng của bạn (hiển thị trong logs/console)

```env
APP_NAME=My Discord Bot
```

---

### 4. BOT_PREFIX
Ký tự bắt đầu command

```env
BOT_PREFIX=!       # !addrole
BOT_PREFIX=>       # >addrole
BOT_PREFIX=$       # $addrole
BOT_PREFIX=.       # .addrole
```

---

### 5. Admin Info (Optional)
Thông tin admin (không bắt buộc)

```env
ADMIN_ID=123456789
ADMIN_USERNAME=YourName
ADMIN_EMAIL=your@email.com
```

---

## ✅ Bắt Buộc vs Optional

| Variable | Bắt Buộc | Mặc Định |
|----------|----------|----------|
| DISCORD_TOKEN | ✅ Yes | - |
| DISCORD_OWNER_IDS | ✅ Yes | - |
| APP_NAME | ❌ No | Discord Bot |
| BOT_PREFIX | ❌ No | ! |
| ADMIN_ID | ❌ No | 0 |
| ADMIN_USERNAME | ❌ No | (empty) |
| ADMIN_EMAIL | ❌ No | (empty) |

---

## 🔒 Security

### Trong .env (Local)
✅ Sử dụng token thật
✅ Danh sách owner ID thật
✅ Giữ bí mật

### Trong Git
❌ Không commit `.env`
✅ `.env` đã được thêm vào `.gitignore`
✅ Commit `.env.example` thay thế

---

## 📤 Khi Deploy

### Trên GitHub
1. **Push:** Code + `.gitignore`
2. **Không push:** `.env` (bảo mật)
3. **Tạo:** `.env.example` (template)

### Trên Server/Host
1. Tạo `.env` từ `.env.example`
2. Điền credentials thực
3. Chạy bot

---

## 🔍 Verify Setup

```python
# config.py sẽ validate:
if not DISCORD_TOKEN:
    raise ValueError("❌ DISCORD_TOKEN không được để trống!")

# Nếu cấu hình đúng:
# ✅ Bot name: My Discord Bot
# ✅ Owner IDs: [123456789, 987654321]
# ✅ Prefix: !
```

---

## 📝 Ví Dụ Đầy Đủ

```env
# ============================================
# Application Configuration
# ============================================
APP_NAME=My Awesome Discord Bot

# ============================================
# Discord Bot - REQUIRED
# ============================================
DISCORD_TOKEN=MzI4OTk4MTk4NzAyNjk1NDI0.DLJoXA.bV8K-y_-CDJNS3Rd
DISCORD_OWNER_IDS=123456789,987654321

# ============================================
# Bot Settings
# ============================================
BOT_PREFIX=!

# ============================================
# Admin Information
# ============================================
ADMIN_ID=123456789
ADMIN_USERNAME=JohnDoe
ADMIN_EMAIL=john@example.com
```

---

## ⚠️ Lưu Ý Quan Trọng

1. **Token bí mật** - Không share token của bạn
2. **`.env` không commit** - Đã có `.gitignore`
3. **Multiple owner IDs** - Dùng dấu phẩy phân cách
4. **Thay sau** - Có thể cập nhật `.env` mà không cần deploy lại

---

## 🚀 Quick Setup

```bash
# 1. Copy .env.example (tạo nếu chưa có)
cp .env.example .env

# 2. Edit .env
nano .env
# Điền DISCORD_TOKEN và DISCORD_OWNER_IDS

# 3. Kiểm tra
python -c "from config import APP_NAME, BOT_PREFIX; print(f'App: {APP_NAME}, Prefix: {BOT_PREFIX}')"

# 4. Chạy bot
python main.py
```

