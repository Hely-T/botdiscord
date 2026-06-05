# Discord Bot - Python

Bot Discord viết bằng `discord.py`, được tổ chức theo hướng catalog cogs để dễ mở rộng, dễ reload từng nhóm lệnh và dễ bảo trì khi thêm tính năng mới.

## Tính năng chính

- Help menu theo category: User, Booking, Role Management, Administrator.
- Quản lý user: profile, cash, points, time, give, top users.
- Booking: xem/tính lương, ghi nhận giờ book, tiền nạp, top book/top nạp/top quà.
- Economy: mọi giá trị tiền dùng đơn vị VNĐ, hỗ trợ nhập nhanh `100k`, `1m`, `1b`, `100,000`.
- Role permission: cấp quyền dùng command theo Discord role trong database, hỗ trợ nhiều role và nhiều command cùng lúc.
- Admin bot: hard admin từ `.env`, admin mềm trong database.
- Responsive profile và auto response: `ar`, `form`, `res`, `up`.
- Operator: pull/status/reload/load/unload/cogs/prefix.
- Slash command hiện có: `/antiraid`.

## Cách chạy

```bash
pip install -r requirements.txt
python main.py
```

## Biến môi trường cần có

Tạo file `.env` ở thư mục gốc:

```env
DISCORD_TOKEN=your_discord_bot_token
DISCORD_OWNER_IDS=123456789,987654321
BOT_PREFIX=b
APP_NAME=Discord Bot
SUPPORT_SERVER_URL=https://discord.com
PROFILE_HOUR_RATE_VND=0
```

## Cấu trúc dự án

```text
BOT DISCORD/
├── main.py
├── config.py
├── utils.py
├── requirements.txt
├── cogs/
│   ├── help_cog.py
│   ├── user/
│   ├── booking/
│   ├── role/
│   └── administrator/
├── services/
├── models/
├── docs/
└── README.md
```

## Quy tắc cog

- Mỗi catalog là một folder trong `cogs/`.
- Những lệnh liên quan thì gộp chung một cog.
- Không tách mỗi lệnh thành một file riêng.
- Không gom toàn bộ catalog vào một file quá lớn.

Ví dụ:

- `cogs/booking/luong_cog.py`: `luong`, `luong @user`, `luong all`, `luong a|r|e`, `tinhluong`.
- `cogs/booking/star_cog.py`: `star`.
- `cogs/administrator/luong_cog.py`: `tongluong` và tương thích lệnh lương cũ.
- `cogs/administrator/ban_cog.py`: `ban`, `unban`, `kick`.
- `cogs/role/role_cog.py`: `addrole`, `removerole`, `setrole`, `perms`, `myroles`, `rolescommands`.

## Tài liệu chi tiết

- [Docs Overview](docs/README.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Commands Reference](docs/COMMANDS_REFERENCE.md)
- [Project Status](docs/PROJECT_STATUS.md)

## Lưu ý

- Không commit `.env`, database `.db`, logs hoặc `__pycache__`.
- Database sẽ tự tạo trong thư mục `database/` khi bot chạy.
- Sau khi pull code mới trên server, có thể dùng lệnh reload/load theo catalog hoặc theo cog.
Initializing repository
