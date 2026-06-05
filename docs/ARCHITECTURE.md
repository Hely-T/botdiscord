# Architecture

Bot được chia theo catalog cogs, service layer và database riêng theo nghiệp vụ.

## Luồng chạy chính

`main.py -> load cogs -> Discord command -> Cog -> Service -> Database -> Response`

## Entry point

`main.py` chịu trách nhiệm:

- Tạo bot instance.
- Bật `message_content`.
- Cấu hình SSL context cho Discord API.
- Load toàn bộ `_cog.py` trong `cogs/` và subfolder.
- Sync slash commands.
- Xử lý lỗi command cơ bản.

## Cog loader

`cogs/cog_loader_utils.py` load recursive theo folder:

- File hợp lệ phải kết thúc bằng `_cog.py`.
- Có thể load/reload/unload một cog riêng.
- Có thể load/reload/unload cả catalog folder.
- Alias catalog quản trị như `admin`, `mod`, `operator` được map về `administrator`.

## Catalog cogs

```text
cogs/
├── help_cog.py
├── user/
│   └── user_cog.py
├── booking/
│   ├── luong_cog.py
│   ├── star_cog.py
│   └── top_cog.py
├── role/
│   └── role_cog.py
└── administrator/
    ├── ban_cog.py
    ├── booking_settings_cog.py
    ├── caprole_cog.py
    ├── cash_cog.py
    ├── customize_cog.py
    ├── luong_cog.py
    ├── mute_cog.py
    ├── operator_cog.py
    ├── responsive_cog.py
    ├── security_cog.py
    ├── star_cog.py
    ├── time_cog.py
    └── user_admin_cog.py
```

## Quy tắc tạo cog mới

- Mỗi catalog là một folder.
- Những lệnh liên quan thì gộp chung trong cùng một cog.
- Không tách mỗi command thành một file riêng.
- Không gom toàn bộ catalog vào một file quá lớn.

Ví dụ:

- Lương: `luong`, `luong @user`, `luong all`, `luong a|r|e`, `tinhluong` nằm trong nhóm booking; `tongluong` nằm trong `administrator/luong_cog.py`.
- Ban/Kick: `ban`, `unban`, `kick` nằm trong `administrator/ban_cog.py`.
- Role permission: `addrole`, `removerole`, `setrole`, `perms`, `myroles`, `rolescommands` nằm trong `role/role_cog.py`.
- Booking lương: `luong`, `tinhluong` nằm trong `booking/luong_cog.py`.

## Services

```text
services/
├── admin_service.py
├── booking_service.py
├── git_service.py
├── guild_settings_service.py
├── responsive_service.py
├── role_permission_service.py
├── settings_service.py
└── user_service.py
```

Service xử lý business logic và làm việc với database qua `utils.CogDatabase`.

## Databases

Database tự tạo trong `database/` khi bot chạy.

- `users.db`: user profile, cash, luong, star, giờ, donate, tổng tiền.
- `booking.db`: booking stats, chi tiết mốc giờ, cấu hình giá, quà.
- `command_role.db`: quyền dùng command theo Discord role.
- `bot_admins.db`: admin mềm của bot.
- `bot_settings.db`: prefix và setting global.
- `guild_settings.db`: antiraid và role hệ thống như `booking`.
- `responsive.db`: responsive profile, auto response, submitted form.

## Quyền sử dụng

- Hard admin lấy từ `DISCORD_OWNER_IDS` trong `.env`.
- Admin mềm lưu trong `bot_admins.db`.
- Role permission lưu trong `command_role.db`.
- Role hệ thống như `booking` lưu trong `guild_settings.db`.

Với lệnh cần quản trị, điều kiện thường là:

- Là hard admin hoặc admin DB.
- Hoặc có Discord role đã được cấp quyền command trong DB.

## Economy

- Mọi giá trị tiền dùng đơn vị VNĐ.
- Hỗ trợ nhập `100000`, `100k`, `1m`, `1b`, `100.000`, `100,000`, `0,5m`.
- Hiển thị tiền dạng `100,000 VNĐ`.
- `cash`, `give` dùng chung nguồn tiền trong `users.db`.
- `cash/luong/star/points/time` đều theo mẫu: xem mình, xem user khác, xem `all`, và quản trị bằng `a|r|e`.
- Action xóa/trừ hỗ trợ `r`, `rm`, `remove`, `d`, `delete`.

## Responsive profile

`responsive_cog.py` xử lý:

- `ar`: thêm, sửa, xóa, gắn target, set ảnh, set description.
- `form`: gửi form để user tự điền.
- `res`: gọi auto response theo key.
- `up`: gửi profile lên channel chỉ định.

Profile có thể dùng số `0`, tự crop thumbnail vuông khi set `turl`, và có thể lấy nội dung từ form user đã gửi.
