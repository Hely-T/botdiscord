# Project Status

## Phiên bản hiện tại

`v1.7-dev`

Trạng thái: đang phát triển, đã chuẩn hóa catalog cog, service/database, role permission và UI theo feature.

## Đã có

- Recursive cog loader cho `cogs/` và subfolder catalog.
- Help menu theo category.
- User commands: `profile`, `cash`, `naptien`, `donate`, `points`, `time`, `give`, `topusers`.
- Booking commands: `luong`, `star`, `tinhluong`, `topbook`, `topnap`, `topgift`.
- Role commands: `addrole`, `removerole`, `setrole`, `perms`, `myroles`, `rolescommands`.
- Administrator commands theo nhóm:
  - Admin DB: `addadmin`, `rmadmin`.
  - Economy: `cash a|r|e`, `luong a|r|e`, `star a|r|e`, `points a|r|e`, `time a|r|e`, `tongluong`, `topstar`, `addtime a|r|e`, `subtime`, `addpoints a|r|e`.
  - Booking config: `bookconfig`, `setgiobook`, `setphantram`, `setan`.
  - Responsive: `ar`, `form`, `res`, `up`.
  - Moderation: `ban`, `unban`, `kick`, `role`, `mute`, `unmute`.
  - Operator: `gitpull`, `gitstatus`, `reload`, `load`, `unload`, `cogs`, `prefix`.
  - Slash: `/antiraid`, `/giveaway`, `/group`, `/level`, `/naptien`, `/donate`, `/ticket`.
- Bank/VietQR: tạo QR nạp tiền/donate, reload số dư, auto check ACB, cộng cash và gửi log cash.
- Log system có `chat`, `voice`, `server`, `join` và `cash`.
- Database tự tạo cho users, booking, role permission, admin, settings, guild settings, responsive, bank payments và log system.
- Định dạng tiền VNĐ thống nhất.
- Ticket dùng một cog tại `cogs/administrator/ticket_cog.py`.
- Ticket dùng `TicketService` và `ticket_system.db`.
- Ticket dùng chung quyền `ticket` trong `command_role.db`, không còn staff-role DB riêng.
- UI feature được tách thành `components.py`, `ui.py`, `emoji.py`.

## Setup nhanh

```bash
pip install -r requirements.txt
python main.py
```

## Test trước khi push

```bash
.venv/bin/python -m compileall cogs services utils.py main.py
```

Nên test thêm:

- Bot khởi động không lỗi cog.
- `{prefix}help` mở menu.
- `{prefix}cash`, `{prefix}points`, `{prefix}time` hiện dữ liệu của bạn.
- `{prefix}luong` hiện bảng lương ở kênh hiện tại.
- `{prefix}give @user 10k` chuyển được nếu đủ cash.
- `{prefix}naptien 10k` tạo QR, bấm reload số dư hoặc `{prefix}naptien reload`.
- `{prefix}donate 10k` tạo QR donate, gửi cảm ơn nếu đã set channel.
- `{prefix}log cash #log-cash` nhận log tiền, nạp, donate và give. Nếu chưa set, bot tự tìm kênh `log_cash`, `log-cash` hoặc `cash-log`.
- `{prefix}setrole @Booking booking` nhận role booking.
- `{prefix}tinhluong` gửi DM.
- `{prefix}ar a`, `{prefix}form`, `{prefix}res`, `{prefix}up` hoạt động đúng.

## Workflow cho feature mới

1. Chọn catalog phù hợp trong `cogs/`.
2. Gộp các lệnh liên quan vào cùng một cog.
3. Kế thừa `AdminCommandBase` nếu cần hard admin/admin DB/role DB.
4. Tạo hoặc cập nhật service nếu có logic/database; dùng `CogDatabase`.
5. Tách UI thành `components.py`, `ui.py`, `emoji.py` nếu có giao diện.
6. Cập nhật `COMMANDS_REFERENCE.md` nếu thêm/sửa lệnh.
7. Chạy compile/load test.
8. Commit bằng tiếng Việt theo nhóm thay đổi.

## Git workflow

- Không commit `.env`, database `.db`, logs, `__pycache__`.
- Commit theo nhóm:
  - `v1.x: cập nhật ...`
  - `v1.x: thêm ...`
  - `v1.x: sửa ...`
- Push sau khi compile/load cogs không lỗi.

## Việc sắp tới

- Hoàn thiện casino/marry/gift nếu tiếp tục phát triển.
- Bổ sung test tự động cho service layer.
- Rà soát permission chi tiết cho từng command admin khi thêm tính năng mới.
- Tiếp tục chuyển UI đang hardcode trong cog cũ sang cấu trúc UI theo feature.
