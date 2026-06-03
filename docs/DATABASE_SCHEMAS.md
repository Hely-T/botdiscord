# 📊 Database Schemas - Cấu Trúc Chi Tiết

Danh sách các database chính mà bot sẽ quản lý. **Mỗi database có file `.db` riêng.**

---

## 1️⃣ **autoresponders.db** - Auto Responses

**Mục đích:** Lưu các câu trả lời tự động khi user trigger keyword

### Schema:
```sql
CREATE TABLE autoresponders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    trigger_keyword TEXT UNIQUE NOT NULL,      -- Từ khóa trigger (vd: "hello", "hi")
    response_text TEXT NOT NULL,                -- Câu trả lời
    response_type TEXT DEFAULT 'text',          -- 'text', 'embed', 'file'
    is_active BOOLEAN DEFAULT 1,                -- Bật/tắt
    created_by INTEGER NOT NULL,                -- User ID người tạo
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
```

### Dữ liệu ví dụ:
```
trigger: "!help" → response: "Gõ !commands để xem danh sách lệnh"
trigger: "hello bot" → response: "Xin chào! 👋"
```

---

## 2️⃣ **booking.db** - Quản Lý Booking

**Mục đích:** Lưu thông tin booking (giờ, ngày, tiền, số giờ booked)

### Schema:
```sql
CREATE TABLE bookings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    booking_id TEXT UNIQUE NOT NULL,            -- Mã booking
    user_id INTEGER NOT NULL,                   -- User booking
    username TEXT NOT NULL,
    service_name TEXT NOT NULL,                 -- Tên dịch vụ
    booked_date TEXT NOT NULL,                  -- Ngày booking (YYYY-MM-DD)
    booked_time TEXT NOT NULL,                  -- Giờ booking (HH:MM)
    duration_hours REAL NOT NULL,               -- Số giờ
    price REAL NOT NULL,                        -- Giá tiền
    status TEXT DEFAULT 'pending',              -- pending, confirmed, completed, cancelled
    notes TEXT,                                 -- Ghi chú
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE booking_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    booking_id TEXT NOT NULL,
    old_status TEXT,
    new_status TEXT,
    changed_by INTEGER,
    changed_at TEXT NOT NULL,
    FOREIGN KEY (booking_id) REFERENCES bookings(booking_id)
);
```

### Dữ liệu ví dụ:
```
booking_id: BK001
user_id: 123456
service_name: "Design Service"
booked_date: "2026-06-10"
booked_time: "14:00"
duration_hours: 2.5
price: 500000
status: "confirmed"
```

---

## 3️⃣ **cash.db** - Quản Lý Số Dư Tiền

**Mục đích:** Lưu thông tin số dư, giao dịch, lịch sử rút tiền

### Schema:
```sql
CREATE TABLE cash_accounts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER UNIQUE NOT NULL,            -- User ID
    username TEXT NOT NULL,
    balance REAL DEFAULT 0,                     -- Số dư hiện tại
    total_earned REAL DEFAULT 0,                -- Tổng tiền kiếm được
    total_spent REAL DEFAULT 0,                 -- Tổng tiền đã dùng
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE cash_transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    transaction_id TEXT UNIQUE NOT NULL,        -- Mã giao dịch
    user_id INTEGER NOT NULL,
    amount REAL NOT NULL,                       -- Số tiền (+ nộp, - rút)
    transaction_type TEXT,                      -- 'earning', 'spending', 'withdrawal', 'deposit'
    description TEXT,                           -- Mô tả
    created_at TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES cash_accounts(user_id)
);

CREATE TABLE cash_withdrawals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    withdrawal_id TEXT UNIQUE NOT NULL,         -- Mã rút tiền
    user_id INTEGER NOT NULL,
    amount REAL NOT NULL,
    status TEXT DEFAULT 'pending',              -- pending, approved, rejected, completed
    withdrawal_method TEXT,                     -- 'bank', 'crypto', 'paypal'
    account_info TEXT,                          -- Thông tin tài khoản (mã hóa)
    requested_at TEXT NOT NULL,
    processed_at TEXT,
    processed_by INTEGER,                       -- Admin xử lý
    notes TEXT,
    FOREIGN KEY (user_id) REFERENCES cash_accounts(user_id)
);
```

### Dữ liệu ví dụ:
```
user_id: 123456
balance: 1000000
total_earned: 2000000
total_spent: 1000000

transaction: +500000 "Hoàn tất booking BK001"
```

---

## 4️⃣ **chat_history.db** - Lịch Sử Chat

**Mục đích:** Lưu lại các tin nhắn để tracking/moderating

### Schema:
```sql
CREATE TABLE messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    message_id INTEGER UNIQUE NOT NULL,         -- Discord message ID
    channel_id INTEGER NOT NULL,                -- Channel ID
    guild_id INTEGER NOT NULL,                  -- Server ID
    user_id INTEGER NOT NULL,
    username TEXT NOT NULL,
    content TEXT NOT NULL,                      -- Nội dung tin nhắn
    message_type TEXT,                          -- 'text', 'embed', 'attachment'
    has_attachment BOOLEAN DEFAULT 0,
    attachment_url TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE chat_moderation (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    message_id INTEGER NOT NULL,
    action TEXT,                                -- 'deleted', 'edited', 'flagged'
    reason TEXT,
    moderator_id INTEGER,
    action_at TEXT NOT NULL,
    FOREIGN KEY (message_id) REFERENCES messages(message_id)
);
```

### Dữ liệu ví dụ:
```
message: "Hello mọi người!"
user: "JohnDoe#1234"
timestamp: "2026-06-03 15:30:45"
```

---

## 5️⃣ **command_role.db** - Quyền Hạn Commands

**Mục đích:** Quyền ai dùng command gì dựa vào role

### Schema:
```sql
CREATE TABLE command_permissions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    command_name TEXT NOT NULL,                 -- Tên command (vd: "!kick", "!ban")
    role_id INTEGER,                            -- Role ID (None = @everyone)
    guild_id INTEGER NOT NULL,                  -- Server ID
    is_allowed BOOLEAN DEFAULT 1,               -- Cho phép hay cấm
    created_at TEXT NOT NULL,
    UNIQUE(command_name, role_id, guild_id)
);

CREATE TABLE role_hierarchy (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    role_id INTEGER UNIQUE NOT NULL,            -- Discord role ID
    role_name TEXT NOT NULL,
    hierarchy_level INTEGER,                    -- Cấp độ (0=lowest, 10=highest)
    guild_id INTEGER NOT NULL,
    created_at TEXT NOT NULL
);
```

### Dữ liệu ví dụ:
```
command: "!kick"
role_id: 987654 (Moderator)
is_allowed: 1 (Moderator được dùng)

command: "!ban"
role_id: 123456 (Admin)
is_allowed: 1 (Chỉ Admin dùng được)
```

---

## 6️⃣ **guilds.db** - Cấu Hình Servers

**Mục đích:** Lưu cấu hình cho mỗi server Discord

### Schema:
```sql
CREATE TABLE guilds (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    guild_id INTEGER UNIQUE NOT NULL,           -- Discord Guild ID
    guild_name TEXT NOT NULL,
    owner_id INTEGER NOT NULL,
    member_count INTEGER DEFAULT 0,
    prefix TEXT DEFAULT '!',                    -- Command prefix cho server này
    language TEXT DEFAULT 'vi',                 -- Ngôn ngữ
    timezone TEXT DEFAULT 'UTC+7',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE guild_settings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    guild_id INTEGER NOT NULL UNIQUE,
    welcome_enabled BOOLEAN DEFAULT 1,
    welcome_message TEXT,
    welcome_channel_id INTEGER,
    
    moderation_enabled BOOLEAN DEFAULT 1,
    log_channel_id INTEGER,
    
    autorespond_enabled BOOLEAN DEFAULT 1,
    booking_enabled BOOLEAN DEFAULT 1,
    
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (guild_id) REFERENCES guilds(guild_id)
);

CREATE TABLE guild_channels (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    guild_id INTEGER NOT NULL,
    channel_id INTEGER NOT NULL,
    channel_name TEXT,
    channel_type TEXT,                          -- 'text', 'voice', 'category'
    purpose TEXT,                               -- 'logs', 'welcome', 'announcements'
    created_at TEXT NOT NULL,
    UNIQUE(guild_id, channel_id)
);
```

### Dữ liệu ví dụ:
```
guild_id: 987654321
guild_name: "My Discord Server"
owner_id: 123456
prefix: "!"
language: "vi"
```

---

## 7️⃣ **khach.db** - Thông Tin Người Dùng

**Mục đích:** Lưu profile, stats, reputation của users

### Schema:
```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER UNIQUE NOT NULL,            -- Discord User ID
    username TEXT NOT NULL,
    avatar_url TEXT,
    discriminator TEXT,                         -- #1234
    is_bot BOOLEAN DEFAULT 0,
    
    -- Stats
    reputation INTEGER DEFAULT 0,               -- Điểm danh tiếng
    level INTEGER DEFAULT 1,
    xp INTEGER DEFAULT 0,
    
    -- Status
    is_banned BOOLEAN DEFAULT 0,
    is_active BOOLEAN DEFAULT 1,
    last_seen TEXT,
    
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE user_profiles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER UNIQUE NOT NULL,
    bio TEXT,                                   -- Tiểu sử
    location TEXT,                              -- Vị trí
    website TEXT,
    verified BOOLEAN DEFAULT 0,                 -- Xác minh
    
    total_bookings INTEGER DEFAULT 0,           -- Số booking đã làm
    total_earnings REAL DEFAULT 0,              -- Tổng tiền kiếm
    average_rating REAL DEFAULT 0,              -- Đánh giá trung bình
    
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

CREATE TABLE user_ratings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    from_user_id INTEGER NOT NULL,              -- Ai đánh giá
    to_user_id INTEGER NOT NULL,                -- Ai bị đánh giá
    booking_id TEXT,                            -- Booking liên quan
    rating INTEGER NOT NULL,                    -- 1-5 stars
    review TEXT,                                -- Nhận xét
    created_at TEXT NOT NULL,
    FOREIGN KEY (to_user_id) REFERENCES users(user_id)
);
```

### Dữ liệu ví dụ:
```
user_id: 123456789
username: "JohnDoe#1234"
reputation: 45
level: 5
xp: 2500
total_bookings: 10
average_rating: 4.8
```

---

## 8️⃣ **logs.db** - Ghi Log Hệ Thống

**Mục đích:** Lưu các sự kiện quan trọng để tracking, debugging

### Schema:
```sql
CREATE TABLE system_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    log_type TEXT NOT NULL,                     -- 'info', 'warning', 'error', 'debug'
    module TEXT,                                -- Module nào (vd: 'booking', 'auth')
    message TEXT NOT NULL,
    details TEXT,                               -- JSON với chi tiết
    severity TEXT DEFAULT 'info',               -- 'critical', 'warning', 'info'
    created_at TEXT NOT NULL
);

CREATE TABLE action_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    action_type TEXT NOT NULL,                  -- 'user_created', 'booking_completed', 'payment_received'
    actor_id INTEGER,                           -- User thực hiện action
    target_user_id INTEGER,                     -- User bị tác động (nếu có)
    target_id TEXT,                             -- ID của object (booking_id, message_id)
    metadata TEXT,                              -- JSON với thông tin thêm
    created_at TEXT NOT NULL
);

CREATE TABLE error_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    error_type TEXT,
    error_message TEXT,
    traceback TEXT,
    context TEXT,                               -- JSON context
    resolved BOOLEAN DEFAULT 0,
    created_at TEXT NOT NULL
);
```

### Dữ liệu ví dụ:
```
action: "user_created" → "User 123456 đã join"
action: "booking_completed" → "Booking BK001 hoàn tất"
action: "payment_received" → "Nhận 500000 từ user 123456"
```

---

## 📝 Database Tóm Tắt

| Database | Mục Đích | File |
|----------|----------|------|
| autoresponders | Auto responses | `autoresponders.db` |
| booking | Quản lý booking | `booking.db` |
| cash | Quản lý tiền | `cash.db` |
| chat_history | Lịch sử chat | `chat_history.db` |
| command_role | Quyền commands | `command_role.db` |
| guilds | Cấu hình servers | `guilds.db` |
| khach | Thông tin users | `khach.db` |
| logs | Ghi log hệ thống | `logs.db` |
| ... | Thêm nếu cung cấp | `.db` |

---

## 🎯 Cách Dùng

### 1. Tạo Services cho mỗi database:

```python
# services/autoresponders_service.py
from utils import CogDatabase

class AutorespondersService:
    def __init__(self):
        self.db = CogDatabase('autoresponders')
        self._init_database()
    
    def _init_database(self):
        self.db.create_table('autoresponders', '''
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            trigger_keyword TEXT UNIQUE NOT NULL,
            response_text TEXT NOT NULL,
            response_type TEXT DEFAULT 'text',
            is_active BOOLEAN DEFAULT 1,
            created_by INTEGER NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        ''')
```

### 2. Bot sẽ tự động:
- ✨ Tạo file `.db`
- ✨ Tạo tables
- ✨ Quản lý connections

---

## 🚀 Cấu Trúc Thư Mục

```
database/
├── autoresponders.db     (auto-created)
├── booking.db            (auto-created)
├── cash.db               (auto-created)
├── chat_history.db       (auto-created)
├── command_role.db       (auto-created)
├── guilds.db             (auto-created)
├── khach.db              (auto-created)
├── logs.db               (auto-created)
└── [new_feature].db      (auto-created khi cần)
```

**Không cần tạo thủ công - tất cả tự động!** ✨

