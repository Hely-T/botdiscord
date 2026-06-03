# 🎯 MAIN DATABASES - Danh Sách Cơ Bản

## 8 Database Chính

| # | Database | Mục Đích | File |
|---|----------|----------|------|
| 1️⃣ | **autoresponders** | Lưu các auto responses khi user trigger keyword | `autoresponders.db` |
| 2️⃣ | **booking** | Lưu thông tin booking (giờ, ngày, tiền, số giờ) | `booking.db` |
| 3️⃣ | **cash** | Quản lý số dư tiền, giao dịch, rút tiền | `cash.db` |
| 4️⃣ | **chat_history** | Lịch sử chat, tin nhắn, moderation | `chat_history.db` |
| 5️⃣ | **command_role** | Quyền dùng commands dựa vào role | `command_role.db` |
| 6️⃣ | **guilds** | Cấu hình cho mỗi server Discord | `guilds.db` |
| 7️⃣ | **khach** | Thông tin user, profile, stats, reputation | `khach.db` |
| 8️⃣ | **logs** | Ghi log hệ thống, actions, errors | `logs.db` |
| ✨ | **[Custom]** | Cogs cần db sẽ tự tạo thêm | `[name].db` |

---

## 📊 Schema Tóm Tắt

### 1️⃣ autoresponders
- `trigger_keyword` - Từ khóa (vd: "hello", "help")
- `response_text` - Câu trả lời
- `is_active` - Bật/tắt

### 2️⃣ booking
- `booking_id`, `user_id`, `service_name`
- `booked_date`, `booked_time`, `duration_hours`
- `price`, `status` (pending/confirmed/completed/cancelled)

### 3️⃣ cash
- `user_id`, `balance` (số dư)
- `total_earned`, `total_spent`
- `cash_transactions`, `cash_withdrawals`

### 4️⃣ chat_history
- `message_id`, `user_id`, `channel_id`, `guild_id`
- `content` (nội dung tin nhắn)
- `chat_moderation` (deleted/edited/flagged)

### 5️⃣ command_role
- `command_name`, `role_id`, `guild_id`
- `is_allowed` (1=cho phép, 0=cấm)
- `role_hierarchy` (cấp độ role)

### 6️⃣ guilds
- `guild_id`, `guild_name`, `owner_id`
- `prefix`, `language`, `timezone`
- `guild_settings`, `guild_channels`

### 7️⃣ khach
- `user_id`, `username`, `avatar_url`
- `reputation`, `level`, `xp`
- `is_banned`, `is_active`, `last_seen`
- `user_profiles`, `user_ratings`

### 8️⃣ logs
- `system_logs` - Log hệ thống
- `action_logs` - Log actions (user created, booking completed)
- `error_logs` - Log lỗi

---

## 📁 Cấu Trúc Thư Mục Database

```
database/
├── autoresponders.db  ✨ Auto-created
├── booking.db         ✨ Auto-created
├── cash.db            ✨ Auto-created
├── chat_history.db    ✨ Auto-created
├── command_role.db    ✨ Auto-created
├── guilds.db          ✨ Auto-created
├── khach.db           ✨ Auto-created
├── logs.db            ✨ Auto-created
└── [custom].db        ✨ Auto-created nếu cogs cần
```

---

## �� Cách Tạo Service cho Database

Mỗi database sẽ có 1 service tương ứng:

```
services/
├── autoresponders_service.py
├── booking_service.py
├── cash_service.py
├── chat_history_service.py
├── command_role_service.py
├── guilds_service.py
├── khach_service.py    (khách = users)
├── logs_service.py
└── [custom]_service.py
```

---

## 💡 Ví Dụ Nhanh

### Booking Service:
```python
class BookingService:
    def __init__(self):
        self.db = CogDatabase('booking')
        self._init_database()
    
    def create_booking(self, user_id, service, date, time, hours, price):
        self.db.insert('bookings', {
            'user_id': user_id,
            'service_name': service,
            'booked_date': date,
            'booked_time': time,
            'duration_hours': hours,
            'price': price,
            'status': 'pending'
        })
```

### Khách Service:
```python
class KhachService:
    def __init__(self):
        self.db = CogDatabase('khach')
        self._init_database()
    
    def create_user(self, user_id, username):
        self.db.insert('users', {
            'user_id': user_id,
            'username': username,
            'reputation': 0,
            'level': 1
        })
```

---

## 📝 Tương Lai

Nếu tạo cogs mới cần database:
1. Tạo service mới
2. Service tự động tạo db file
3. Không cần sửa gì cả ✨

**Ví dụ:** Nếu làm `polls` cog, tạo `polls_service.py` sẽ tự tạo `polls.db`

---

## ✅ Summary

✨ **8 database chính** được lưu nhớ
✨ **Schema chi tiết** trong `DATABASE_SCHEMAS.md`
✨ **Auto-created** khi service khởi tạo
✨ **Dễ scale** - thêm database mới không ảnh hưởng cũ
✨ **Tổ chức rõ ràng** - mỗi db một service

Bạn có muốn tôi tạo services cho các database này không? 😊

