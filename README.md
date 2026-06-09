# Discord Bot - Python

Bot Discord viết bằng `discord.py`, được tổ chức theo hướng catalog cogs để dễ mở rộng, dễ reload từng nhóm lệnh và dễ bảo trì khi thêm tính năng mới.

## Tính năng chính

- Help menu theo category: User, Booking, Role Management, Administrator.
- Quản lý user: profile, cash, nạp tiền, donate, points, time, give, top users.
- Booking: xem/tính lương, ghi nhận giờ book, tiền nạp, top book/top nạp/top quà.
- Economy: mọi giá trị tiền dùng đơn vị VNĐ, hỗ trợ nhập nhanh `100k`, `1m`, `1b`, `100,000`.
- Bank/VietQR: tạo QR nạp cash hoặc donate, kiểm tra giao dịch, admin reload số dư ACB và gửi log cash.
- Role permission: cấp quyền dùng command theo Discord role trong database, hỗ trợ nhiều role và nhiều command cùng lúc.
- Admin bot: hard admin từ `.env`, admin mềm trong database.
- Responsive profile và auto response: `ar`, `form`, `res`, `up`.
- Ticket: panel, manager, claim, transcript, archive và quyền staff qua role DB.
- Operator: pull/status/reload/load/unload/cogs/prefix.
- Slash command theo nhóm: `/antiraid`, `/giveaway`, `/group`, `/level`, `/naptien`, `/donate`, `/ticket`.

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
ACB_USERNAME=
ACB_PASSWORD=
ACB_ACCOUNT_NUMBER=
ACB_ACCOUNT_NAME=
ACB_CLIENT_ID=
ACB_BANK_CODE=ACB
NAPTIEN_DECOR_URL=
DONATE_DECOR_URL=
DONATE_THANK_TEMPLATE=Cảm ơn {user} đã donate {amount} VNĐ!
```

Các thông tin ACB cũng có thể cài trực tiếp trong Discord bằng lệnh quản trị:

```text
bnaptien config username <tài_khoản_acb>
bnaptien config password <mật_khẩu_acb>
bnaptien config account <số_tài_khoản>
bnaptien config name <tên_chủ_tài_khoản>
bnaptien config bank ACB
bnaptien config auto on
bdonate config channel #kenh-cam-on
bdonate config thanks Cảm ơn {user} đã donate {amount} VNĐ!
blog cash #log-cash
```

Nếu chưa cấu hình `log cash`, bot sẽ tự tìm kênh `log_cash`, `log-cash` hoặc `cash-log` để gửi log tiền.

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
├── ui/
│   └── <feature>/
│       ├── components.py
│       ├── ui.py
│       └── emoji.py
├── models/
├── docs/
└── README.md
```

## Quy tắc cog

- Mỗi catalog là một folder trong `cogs/`.
- Những lệnh liên quan thì gộp chung một cog.
- Không tách mỗi lệnh thành một file riêng.
- Không gom toàn bộ catalog vào một file quá lớn.
- Cog chỉ chứa command, quyền và nghiệp vụ điều phối.
- Database đặt trong `services/` và phải dùng `utils.CogDatabase`.
- Lệnh quản trị dùng `AdminCommandBase` để check hard admin/admin DB/role DB.
- Button, select và modal đặt trong `ui/<feature>/components.py`.
- Embed và giao diện đặt trong `ui/<feature>/ui.py`.
- Discord emoji ID và fallback đặt trong `ui/<feature>/emoji.py`.

Ví dụ:

- `cogs/booking/luong_cog.py`: `luong`, `luong @user`, `luong all`, `luong a|r|e`, `tinhluong`.
- `cogs/booking/star_cog.py`: `star`.
- `cogs/administrator/luong_cog.py`: `tongluong` và tương thích lệnh lương cũ.
- `cogs/administrator/ban_cog.py`: `ban`, `unban`, `kick`.
- `cogs/role/role_cog.py`: `addrole`, `removerole`, `setrole`, `perms`, `myroles`, `rolescommands`.
- `cogs/administrator/ticket_cog.py`: toàn bộ command Ticket; UI nằm trong `ui/ticket/`, DB nằm trong `services/ticket_service.py`.
- `cogs/user/naptien_cog.py`: tạo QR nạp cash, kiểm tra giao dịch, admin xem số dư ACB và auto check giao dịch.
- `cogs/user/donate_cog.py`: tạo QR donate, cộng cash/donate và gửi lời cảm ơn.
- `ui/user/payment_ui.py`: card QR, embed nạp tiền/donate và giao diện thanh toán.
- `services/bank_service.py`: cấu hình ACB, pending payment, match giao dịch và trạng thái thanh toán.

## Quy chuẩn cho team và AI

Trước khi thêm tính năng, đọc [Architecture](docs/ARCHITECTURE.md). Không tạo database hoặc hệ thống quyền mới nếu đã có nguồn dùng chung.

Mẫu bắt buộc cho lệnh quản trị:

```python
class ExampleCog(AdminCommandBase):
    @commands.command(name="example")
    async def example(self, ctx):
        if not await self.require_role_or_admin_ctx(ctx, "example"):
            return
```

Role dùng lệnh được cấu hình bằng `baddrole @role example` và lưu trong `command_role.db`.

## Tài liệu chi tiết

- [Docs Overview](docs/README.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Commands Reference](docs/COMMANDS_REFERENCE.md)
- [Project Status](docs/PROJECT_STATUS.md)

## Lưu ý

- Không commit `.env`, database `.db`, logs hoặc `__pycache__`.
- Database sẽ tự tạo trong thư mục `database/` khi bot chạy.
- Sau khi pull code mới trên server, có thể dùng lệnh reload/load theo catalog hoặc theo cog.
