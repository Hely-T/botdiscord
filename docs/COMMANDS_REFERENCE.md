# Commands Reference

Prefix lấy từ database `bot_settings.db`, mặc định theo `BOT_PREFIX` trong `.env`.
Trong docs dùng `{prefix}` để đại diện cho prefix hiện tại.

## General

- `{prefix}help`
  - Mở help menu theo category.
- `{prefix}help <command>`
  - Xem chi tiết một lệnh.

## User

- `{prefix}profile [@user]`
  - Xem profile của bạn.
  - Xem người khác cần admin bot hoặc role có quyền `profile`.
- `{prefix}cash [@user]`
  - Xem số dư cash.
  - Xem người khác cần admin bot hoặc role có quyền `profile`.
- `{prefix}give @user <money>`
  - Chuyển cash cho member trong server.
  - Có thể đảo tham số: `{prefix}give <money> @user`.
  - Ví dụ: `{prefix}give @Yang 10k`.
- `{prefix}topusers [limit]`
  - Xem top user theo points.

## Booking

- `{prefix}luong <nội dung>`
  - Nhắn booking lên server.
- `{prefix}star`
  - Xem giờ đã book và số tiền đã tiêu của bạn.
- `{prefix}star time <hours> [@user]`
  - Ghi nhận giờ book.
  - Admin/role DB có thể ghi cho người khác.
- `{prefix}star money <money> [@user]`
  - Ghi nhận tiền nạp.
  - Admin/role DB có thể ghi cho người khác.
- `{prefix}star top`
  - Xem top giờ book và top nạp.
- `{prefix}star @user`
  - Admin/role DB xem booking của user khác.
- `{prefix}tinhluong`
  - Gửi bảng tính lương của bạn qua DM.
  - Chỉ hiện những mốc giờ đã có dữ liệu.
- `{prefix}tinhluong @user`
  - Admin/role DB gửi bảng tính lương của user qua DM.
- `{prefix}tinhluong all`
  - Admin/role DB gửi/tính bảng lương toàn bộ booking.
- `{prefix}topbook [limit]`
  - Top giờ được book nhiều nhất.
  - Quyền: admin hoặc role DB.
- `{prefix}topnap [limit]`
  - Top người nạp tiền nhiều nhất.
  - Quyền: admin hoặc role DB.
- `{prefix}topgift`
  - Xem tổng quà đang có.

## Role Management

- `{prefix}addrole @role <command>`
  - Cấp quyền dùng command cho role.
  - Alias: `{prefix}themrole`.
- `{prefix}removerole @role <command>`
  - Xóa quyền dùng command khỏi role.
  - Alias: `{prefix}rmrole`, `{prefix}xoarole`.
- `{prefix}setrole @role <key>`
  - Gán role hệ thống.
  - Ví dụ: `{prefix}setrole @Booking booking`.
- `{prefix}perms <command>`
  - Xem role nào đang có quyền dùng command.
- `{prefix}myroles [@user]`
  - Xem role của bạn hoặc user khác.
- `{prefix}rolescommands @role`
  - Xem role đang dùng được những command nào.

## Administrator

### Bot admin

- `{prefix}addadmin @user`
  - Thêm admin bot vào DB.
  - Alias: `{prefix}themadmin`.
- `{prefix}rmadmin @user`
  - Xóa admin bot khỏi DB.
  - Alias: `{prefix}xoaadmin`.

### Economy

- `{prefix}addcash @user <money>`
  - Cộng cash cho user đã tồn tại trong `users.db`.
- `{prefix}subcash @user <money>`
  - Trừ cash của user.
- `{prefix}addluong @user <money>`
  - Cộng lương cho booking.
  - User phải có role hệ thống `booking`.
- `{prefix}subluong @user <money>`
  - Trừ lương của booking.
  - User phải có role hệ thống `booking`.
- `{prefix}tongluong`
  - Xem tổng lương.
- `{prefix}addstar @user <amount>`
  - Cộng star.
- `{prefix}substar @user <amount>`
  - Trừ star.
- `{prefix}topstar [limit]`
  - Top star.
- `{prefix}addtime @user <hours>`
  - Cộng giờ.
- `{prefix}subtime @user <hours>`
  - Trừ giờ.
- `{prefix}addpoints @user <amount>`
  - Cộng points.

### Booking config

- `{prefix}bookconfig`
  - Xem giá booking và phần trăm trả tiền.
  - Alias: `{prefix}bookingconfig`, `{prefix}giabook`.
- `{prefix}setgiobook <money>`
  - Đặt giá tiền cho 1 giờ booking.
  - Alias: `{prefix}setgia`, `{prefix}giabooking`.
- `{prefix}setphantram <percent>`
  - Đặt phần trăm trả tiền cho booking.
  - Alias: `{prefix}setpayout`, `{prefix}settraluong`.
- `{prefix}setan <percent>`
  - Đặt phần trăm bot/server ăn.
  - Alias: `{prefix}setfee`, `{prefix}sethoahong`.

### Responsive profile và auto response

- `{prefix}form [key]`
  - Gửi form booking để user tự điền.
  - Có thể dùng dạng dính liền như `{prefix}formau`.
- `{prefix}ar a <res> | <content>`
  - Thêm auto response.
- `{prefix}ar a <profile_key><number>`
  - Tạo profile, số `0` dùng được.
  - Ví dụ: `{prefix}ar a ad0`.
- `{prefix}ar des <res> | <content>`
  - Sửa nội dung auto response.
- `{prefix}ar description <profile_key><number>`
  - Lấy nội dung profile từ tin nhắn reply.
- `{prefix}ar target <res|profile> @user`
  - Gắn target cho auto res hoặc profile.
- `{prefix}ar iurl <res|profile> <url|ảnh>`
  - Set ảnh lớn.
- `{prefix}ar turl <res|profile> <url|ảnh>`
  - Set ảnh nhỏ/thumbnail, bot tự crop vuông.
- `{prefix}ar d <res|profile>`
  - Xóa auto res hoặc profile.
- `{prefix}res <key>`
  - Gọi auto response theo key.
- `{prefix}up <profile_key><number> #channel`
  - Up profile lên channel chỉ định.

Placeholder auto response:

- `{user}`: người gọi lệnh.
- `{key}`: key trigger.
- `{target}`: user đã gắn target nếu có.

### Moderation và server

- `{prefix}ban @user [reason]`
  - Ban member.
- `{prefix}unban <user_id> [reason]`
  - Gỡ ban.
- `{prefix}mute @user [duration] [reason]`
  - Mute member.
- `{prefix}unmute @user [reason]`
  - Gỡ mute.
- `{prefix}color @role <hex|name>`
  - Đổi màu role.
- `{prefix}emoji ...`
  - Quản lý emoji.
- `/antiraid`
  - Bật/tắt chống raid trong server.

### Operator

- `{prefix}gitpull`
  - Pull code mới nhất từ GitHub.
  - Alias: `{prefix}pull`, `{prefix}update`.
- `{prefix}gitstatus`
  - Xem trạng thái git.
  - Alias: `{prefix}status`.
- `{prefix}reload [catalog|module]`
  - Reload một cog, một catalog hoặc toàn bộ.
- `{prefix}load <catalog|module>`
  - Load một cog hoặc catalog.
- `{prefix}unload <catalog|module>`
  - Unload một cog hoặc catalog.
- `{prefix}cogs`
  - Liệt kê các cogs đang load.
- `{prefix}prefix <value>`
  - Đổi prefix bot.

## Định dạng tiền

Các lệnh tiền dùng VNĐ:

- `100000` -> `100,000 VNĐ`
- `100k` -> `100,000 VNĐ`
- `1m` -> `1,000,000 VNĐ`
- `1b` -> `1,000,000,000 VNĐ`
- `0,5m` -> `500,000 VNĐ`
- `100.000` hoặc `100,000` đều hợp lệ.

## Ghi nhớ nhanh

- Lệnh quản trị quan trọng nằm trong catalog Administrator.
- Lệnh dùng được bởi mọi người nằm trong User hoặc Booking tùy tính năng.
- Role permission dùng `addrole`/`removerole`.
- Role hệ thống booking dùng `setrole @role booking`.
- Database tự tạo khi bot chạy, không cần commit file `.db`.
