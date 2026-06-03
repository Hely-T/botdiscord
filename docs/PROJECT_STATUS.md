# Project Status

## Phiên bản hiện tại

`v0.4-dev`

Trạng thái: đang phát triển, đã refactor catalog cogs và thêm các nhóm lệnh chính cho booking/economy/responsive.

## Đã có

- Recursive cog loader cho `cogs/` và subfolder catalog.
- Help menu theo category.
- User commands: `profile`, `cash`, `give`, `topusers`.
- Booking commands: `luong`, `star`, `tinhluong`, `topbook`, `topnap`, `topgift`.
- Role commands: `addrole`, `removerole`, `setrole`, `perms`, `myroles`, `rolescommands`.
- Administrator commands theo nhóm:
  - Admin DB: `addadmin`, `rmadmin`.
  - Economy: `addcash`, `subcash`, `addluong`, `subluong`, `tongluong`, `addstar`, `substar`, `topstar`, `addtime`, `subtime`, `addpoints`.
  - Booking config: `bookconfig`, `setgiobook`, `setphantram`, `setan`.
  - Responsive: `ar`, `form`, `res`, `up`.
  - Moderation: `ban`, `unban`, `mute`, `unmute`.
  - Operator: `gitpull`, `gitstatus`, `reload`, `load`, `unload`, `cogs`, `prefix`.
  - Slash: `/antiraid`.
- Database tự tạo cho users, booking, role permission, admin, settings, guild settings và responsive.
- Định dạng tiền VNĐ thống nhất.

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
- `{prefix}cash` hiện số dư.
- `{prefix}give @user 10k` chuyển được nếu đủ cash.
- `{prefix}setrole @Booking booking` nhận role booking.
- `{prefix}tinhluong` gửi DM.
- `{prefix}ar a`, `{prefix}form`, `{prefix}res`, `{prefix}up` hoạt động đúng.

## Workflow cho feature mới

1. Chọn catalog phù hợp trong `cogs/`.
2. Gộp các lệnh liên quan vào cùng một cog.
3. Tạo hoặc cập nhật service nếu có logic/database.
4. Cập nhật `COMMANDS_REFERENCE.md` nếu thêm/sửa lệnh.
5. Chạy compile/load test.
6. Commit bằng tiếng Việt theo nhóm thay đổi.

## Git workflow

- Không commit `.env`, database `.db`, logs, `__pycache__`.
- Commit theo nhóm:
  - `v0.x: cập nhật ...`
  - `v0.x: thêm ...`
  - `v0.x: sửa ...`
- Push sau khi compile/load cogs không lỗi.

## Việc sắp tới

- Hoàn thiện casino/marry/gift nếu tiếp tục phát triển.
- Bổ sung test tự động cho service layer.
- Rà soát permission chi tiết cho từng command admin khi thêm tính năng mới.
