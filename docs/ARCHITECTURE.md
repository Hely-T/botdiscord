# Architecture

Tài liệu này là quy chuẩn bắt buộc khi team hoặc AI thêm tính năng mới. Mục tiêu là giữ code dễ tìm, không đăng ký trùng command, không tạo nhiều nguồn database và không tự viết thêm một hệ thống quyền riêng.

## Luồng chuẩn

```text
Discord command/interaction
        ↓
cogs/<catalog>/<feature>_cog.py
        ↓
services/<feature>_service.py
        ↓
utils.CogDatabase
        ↓
database/<name>.db
```

Nếu tính năng có giao diện:

```text
cog nghiệp vụ
  ├── gọi ui/<feature>/components.py
  ├── gọi ui/<feature>/ui.py
  └── giao diện lấy icon từ ui/<feature>/emoji.py
```

## Trách nhiệm từng layer

### Cog

Cog chỉ chứa:

- Prefix command và slash command.
- Kiểm tra quyền qua helper dùng chung.
- Điều phối luồng nghiệp vụ.
- Gọi service để đọc/ghi dữ liệu.
- Gọi UI để gửi embed, button, select hoặc modal.

Cog không được:

- Kết nối SQLite trực tiếp.
- Tự tạo một database quyền riêng.
- Chứa hàng loạt class `View`, `Select`, `Modal` hoặc mẫu embed.
- Tách mỗi command liên quan thành một file riêng.
- Để service hoặc UI import trực tiếp class cog, gây vòng phụ thuộc.

### Service

Service chịu trách nhiệm:

- Tạo và migrate bảng.
- Đọc/ghi database.
- Business logic dùng chung.
- Validate dữ liệu ở mức nghiệp vụ.
- Cung cấp API ổn định cho cog.

Mỗi service tạo database bằng:

```python
from utils import CogDatabase


class ExampleService:
    def __init__(self):
        self.db = CogDatabase("example")
        self._init_database()

    def _init_database(self):
        self.db.create_table(
            "items",
            """
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guild_id INTEGER NOT NULL,
            name TEXT NOT NULL
            """,
        )
```

`CogDatabase("example")` tự dùng đường dẫn `database/example.db`. Không nối chuỗi đường dẫn database thủ công và không đặt DB trong `cogs/`.

### UI

Tính năng có giao diện tạo folder:

```text
ui/<feature>/
├── __init__.py
├── emoji.py
├── components.py
└── ui.py
```

Quy ước:

- `emoji.py`: fallback emoji, Discord emoji ID và hàm resolve emoji.
- `components.py`: `View`, `Button`, `Select`, `Modal`, `TextInput`.
- `ui.py`: embed, splash, nội dung trình bày và helper gửi interaction.
- Không đặt business logic hoặc truy vấn database trong UI.
- UI nhận đối tượng cog qua constructor và chỉ gọi public callback mà cog cung cấp.
- Service không được truyền thẳng vào UI nếu UI có thể gọi callback của cog.
- Cog không tự dựng embed nếu tính năng đã có folder UI.

Ví dụ emoji:

```python
FALLBACK_EMOJIS = {"ticket": "🎫"}
DISCORD_EMOJI_IDS = {"ticket": ""}


def ticket_emoji(key: str) -> str:
    ...
```

Khi thêm emoji Discord, chỉ cập nhật `DISCORD_EMOJI_IDS` hoặc biến môi trường tương ứng. Không hardcode ID emoji ở button/embed.

## Quy tắc catalog và cog

Loader tự tìm đệ quy mọi file kết thúc bằng `_cog.py`.

```text
cogs/
├── help_cog.py
├── user/
├── booking/
├── bot/
├── level/
├── role/
└── administrator/
```

Quy tắc nhóm file:

- Một catalog là một folder.
- Một nhóm nghiệp vụ liên quan là một cog.
- Không tách mỗi command thành một cog.
- Không gom toàn bộ catalog vào một cog khổng lồ.
- Các quyền quản trị như admin, mod, operator và staff nằm trong `administrator`.

Ví dụ đúng:

- `administrator/ban_cog.py`: `ban`, `unban`, `kick`.
- `booking/luong_cog.py`: `luong`, `tinhluong`, `traluong`.
- `role/role_cog.py`: `role`, `addrole`, `removerole`, `setrole`, `perms`, `myroles`, `rolescommands`.
- `administrator/ticket_cog.py`: toàn bộ command và nghiệp vụ Ticket.

Ví dụ sai:

```text
cogs/ticket/add_user_cog.py
cogs/ticket/remove_user_cog.py
cogs/ticket/claim_cog.py
cogs/ticket/close_cog.py
```

Các command trên cùng thuộc Ticket nên phải nằm trong một `ticket_cog.py`. Button/embed của chúng đặt trong `ui/ticket/`.

## Quyền admin và role DB

Nguồn quyền dùng chung:

- Hard admin: `DISCORD_OWNER_IDS` trong `.env`.
- Admin mềm: `database/bot_admins.db`.
- Quyền command theo Discord role: `database/command_role.db`.
- Role hệ thống như `booking`: `database/guild_settings.db`.

Cog quản trị phải kế thừa:

```python
from cogs.admin_command_utils import AdminCommandBase


class ExampleCog(AdminCommandBase):
    ...
```

Prefix command:

```python
@commands.command(name="example")
async def example(self, ctx):
    if not await self.require_role_or_admin_ctx(ctx, "example"):
        return
```

Interaction, button hoặc slash command:

```python
if not await self.require_role_or_admin_interaction(interaction, "example"):
    return
```

Kiểm tra không cần gửi lỗi ngay:

```python
allowed = self.can_use_role_or_admin(ctx, "example")
```

Không được:

- Chỉ dùng `member.guild_permissions.administrator`.
- Tự tạo `example_staff_roles`.
- Tạo một `AdminService`/`RolePermissionService` mới trong từng callback.
- Kiểm tra role bằng tên cố định.
- Ghi role permission vào database nghiệp vụ.

Role được cấp quyền bằng:

```text
baddrole @role example
bremoverole @role example
```

Một nhóm command dùng chung quyền phải thống nhất một key. Ví dụ toàn bộ Ticket dùng key `ticket`, kể cả manager, panel, claim, add/remove user và transfer.

## Database và liên kết dữ liệu

Trước khi tạo DB mới phải kiểm tra dữ liệu đã có nguồn chung chưa:

- User, cash, lương cơ bản: `users.db` qua `UserService`.
- Booking, mốc giờ, trả lương: `booking.db` qua `BookingService`.
- Quyền command: `command_role.db` qua `RolePermissionService`.
- Admin mềm: `bot_admins.db` qua `AdminService`.
- Prefix: `bot_settings.db` qua `SettingsService`.
- Role hệ thống: `guild_settings.db` qua `GuildSettingsService`.
- Ticket: `ticket_system.db` qua `TicketService`.
- Bank/nạp tiền/donate: `bank_payments.db` qua `BankPaymentService`.
- Log cash/chat/voice/server/member: `log_system.db` qua `LogService`.

Không nhân đôi dữ liệu. Ví dụ Ticket không tạo bảng staff role riêng vì quyền staff đã có trong `command_role.db`.

### Bank, nạp tiền và donate

Luồng bank dùng chung:

```text
cogs/user/naptien_cog.py hoặc cogs/user/donate_cog.py
        ↓
services/bank_service.py
        ↓
database/bank_payments.db
        ↓
services/user_service.py cộng cash vào users.db
        ↓
cogs/cash_log_utils.py gửi log cash qua LogService
```

Quy tắc:

- `naptien` và `donate` là hai cog riêng trong catalog `user` vì người dùng gọi trực tiếp.
- Cấu hình ACB nằm trong `BankPaymentService`, không đọc `.env` rải rác trong cog.
- `.env` chỉ là giá trị mặc định; admin có thể đổi bằng command Discord.
- QR/card/embed nằm trong `ui/user/payment_ui.py`.
- Button xác nhận chuyển tiền dùng callback trong `cogs/user/payment_common.py`; reload số dư ngân hàng là luồng admin-only trong cog nạp/donate.
- Giao dịch thành công phải cộng vào `UserService` để toàn server dùng chung cash.
- Donate cộng thêm `total_donate` để profile/top sau này có thể đọc cùng nguồn.
- Log nạp, donate, chuyển, cộng/trừ cash gửi về channel `log cash` qua `LogService`.
- Nếu chưa set `log cash`, helper log tiền tự tìm kênh `log_cash`, `log-cash` hoặc `cash-log`.
- Không tạo DB cash riêng cho bank và không cộng tiền bằng SQL trực tiếp trong cog.

Các biến cấu hình hỗ trợ:

```text
ACB_USERNAME
ACB_PASSWORD
ACB_ACCOUNT_NUMBER
ACB_ACCOUNT_NAME
ACB_CLIENT_ID
ACB_BANK_CODE
NAPTIEN_DECOR_URL
DONATE_DECOR_URL
DONATE_THANK_TEMPLATE
```

Khi dữ liệu phải liên kết:

- Lưu Discord ID dưới dạng `INTEGER`.
- Mọi query theo server phải có `guild_id`.
- Mọi table cần tính theo user phải dùng `user_id`.
- Tên hiển thị chỉ là dữ liệu phụ, không dùng thay ID.
- Migration cột mới đặt trong service, dùng kiểm tra `PRAGMA table_info`.

## Mẫu feature chuẩn

```text
cogs/administrator/example_cog.py
services/example_service.py
ui/example/__init__.py
ui/example/emoji.py
ui/example/components.py
ui/example/ui.py
test/test_example.py
```

Không bắt buộc tạo đủ mọi file:

- Không có DB: không cần service.
- Không có button/embed riêng: không cần folder UI.
- Chỉ tạo file thực sự có trách nhiệm rõ ràng.
- Không tạo `helpers.py`, `permissions.py`, `resolvers.py` riêng nếu helper nhỏ chỉ dùng cho một cog.

## Ticket là mẫu tham chiếu

Ticket hiện dùng cấu trúc:

```text
cogs/administrator/ticket_cog.py
services/ticket_service.py
ui/ticket/
├── emoji.py
├── components.py
└── ui.py
```

- `ticket_cog.py`: command, callback nghiệp vụ, kiểm tra quyền và gọi service.
- `ticket_service.py`: config, ticket, event, trạng thái và transcript metadata.
- `components.py`: panel, control, manager, select và modal.
- `ui.py`: toàn bộ embed/splash Ticket.
- `emoji.py`: fallback và Discord emoji ID.
- Tất cả thao tác quản trị dùng quyền `ticket` trong `command_role.db`.

## Checklist trước khi code

1. Tính năng thuộc catalog nào?
2. Có cog liên quan để bổ sung chưa?
3. Dữ liệu đã tồn tại trong service/DB nào?
4. Command có cần admin hoặc role DB không?
5. Nếu có quyền, key quyền dùng chung là gì?
6. Có button/select/modal/embed không? Nếu có, tạo hoặc dùng `ui/<feature>/`.
7. Có đang tạo file nhỏ chỉ để chứa một helper không cần thiết không?
8. Help và command reference đã cập nhật chưa?

## Checklist trước khi commit

```bash
python3 -m py_compile cogs/<catalog>/<feature>_cog.py
python3 -m unittest discover -s test -p 'test_<feature>*.py'
```

Kiểm tra thêm:

- Loader chỉ thấy một cog cho feature.
- Không có command/slash trùng.
- Không còn import đường dẫn cũ.
- DB tự tạo trong `database/`.
- Role DB thật sự điều khiển được command và button.
- UI không truy vấn DB trực tiếp.

## Chỉ dẫn ngắn cho AI

Khi giao việc cho AI, yêu cầu AI đọc file này trước và tuân thủ:

> Giữ command liên quan trong một cog theo catalog. Cog chỉ xử lý command/quyền/nghiệp vụ. Database đặt trong service và dùng `CogDatabase`. Lệnh quản trị kế thừa `AdminCommandBase`, dùng hard admin hoặc role permission trong `command_role.db`. Giao diện tách thành `ui/<feature>/components.py`, `ui.py`, `emoji.py`. Không tạo database quyền riêng và không tách mỗi command thành một file.
