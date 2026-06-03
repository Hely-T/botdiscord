# Commands Reference

Tài liệu này chỉ giữ những lệnh chính đang dùng trong bot.
Prefix của bot lấy từ biến môi trường `BOT_PREFIX`.

## Help

- `{prefix}help`
  - Mở command directory dạng category + nút bấm
- `{prefix}help <command>`
  - Xem hướng dẫn chi tiết của một lệnh

## Role management

- `{prefix}addrole @role command`
  - Cấp quyền dùng command cho role
  - Quyền: Admin
- `{prefix}removerole @role command`
  - Xóa quyền của role
  - Quyền: Admin
- `{prefix}perms command`
  - Xem role nào đang có quyền dùng command
  - Quyền: mọi người
- `{prefix}myroles [@user]`
  - Xem role của bạn hoặc user khác
  - Quyền: mọi người
- `{prefix}rolescommands @role`
  - Xem role đang dùng được những lệnh nào
  - Quyền: mọi người

## User management

- `{prefix}profile [@user]`
  - Xem profile user theo card mới: avatar + tổng giờ/donate/tiền
- `{prefix}addpoints @user amount`
  - Cộng points cho user
  - Quyền: Admin
- `{prefix}topusers [limit]`
  - Xem top user theo points

## Admin / Git management

- `{prefix}gitpull`
  - Pull code mới nhất từ GitHub
  - Alias: `{prefix}pull`, `{prefix}update`
  - Quyền: owner
- `{prefix}gitstatus`
  - Xem trạng thái git hiện tại
  - Alias: `{prefix}status`
  - Quyền: owner
- `{prefix}reload [cog_name]`
  - Reload một cog hoặc toàn bộ cogs
  - Quyền: owner
- `{prefix}load [cog_name]`
  - Load một cog mới
  - Quyền: owner
- `{prefix}unload [cog_name]`
  - Unload một cog
  - Quyền: owner
- `{prefix}cogs`
  - Liệt kê các cog đang load
  - Quyền: owner

## Ghi nhớ nhanh

- `role_cog.py` xử lý toàn bộ nhóm lệnh role
- `user_cog.py` xử lý nhóm lệnh user
- `help_cog.py` xử lý command directory + tra cứu lệnh
- `admin_cog.py` xử lý nhóm lệnh quản lý git và reload
- `command_role.db` là database cho quyền command
