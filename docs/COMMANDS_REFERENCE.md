# Commands Reference

Tài liệu này chỉ giữ những lệnh chính đang dùng trong bot.

## Role management

- `!addrole @role command`
  - Cấp quyền dùng command cho role
  - Quyền: Admin
- `!removerole @role command`
  - Xóa quyền của role
  - Quyền: Admin
- `!perms command`
  - Xem role nào đang có quyền dùng command
  - Quyền: mọi người
- `!myroles [@user]`
  - Xem role của bạn hoặc user khác
  - Quyền: mọi người
- `!rolescommands @role`
  - Xem role đang dùng được những lệnh nào
  - Quyền: mọi người

## User management

- `!profile [@user]`
  - Xem profile user
- `!addpoints @user amount`
  - Cộng points cho user
  - Quyền: Admin
- `!topusers [limit]`
  - Xem top user theo points

## Admin / Git management

- `!gitpull`
  - Pull code mới nhất từ GitHub
  - Alias: `!pull`, `!update`
  - Quyền: owner
- `!gitstatus`
  - Xem trạng thái git hiện tại
  - Alias: `!status`
  - Quyền: owner
- `!reload [cog_name]`
  - Reload một cog hoặc toàn bộ cogs
  - Quyền: owner
- `!load [cog_name]`
  - Load một cog mới
  - Quyền: owner
- `!unload [cog_name]`
  - Unload một cog
  - Quyền: owner
- `!cogs`
  - Liệt kê các cog đang load
  - Quyền: owner

## Ghi nhớ nhanh

- `role_cog.py` xử lý toàn bộ nhóm lệnh role
- `user_cog.py` xử lý nhóm lệnh user
- `admin_cog.py` xử lý nhóm lệnh quản lý git và reload
- `command_role.db` là database cho quyền command
