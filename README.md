# Discord Bot - Python

Bot Discord được xây dựng bằng `discord.py`, theo hướng module hóa để dễ mở rộng, dễ bảo trì và dễ chia sẻ cho cộng đồng.

## Tổng quan nhanh

- `main.py` - entry point để khởi động bot
- `config.py` - cấu hình và biến môi trường
- `utils.py` - helper dùng chung
- `cogs/` - nơi chứa các command
- `services/` - business logic
- `models/` - data structures
- `docs/` - tài liệu rút gọn và chuẩn hóa

## Tài liệu cho cộng đồng

- [docs/README.md](docs/README.md)
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
- [docs/COMMANDS_REFERENCE.md](docs/COMMANDS_REFERENCE.md)
- [docs/PROJECT_STATUS.md](docs/PROJECT_STATUS.md)

## Cách chạy

```bash
pip install -r requirements.txt
python main.py
```

## Cấu trúc dự án

```text
BOT DISCORD/
├── main.py
├── config.py
├── utils.py
├── requirements.txt
├── .env.example
├── .gitignore
├── cogs/
├── services/
├── models/
├── docs/
└── README.md
```

## Những gì bot đang có

- Hệ thống command theo cog
- Hệ thống service để tách business logic
- Models để chuẩn hóa dữ liệu
- Helper dùng chung cho database, prefix, embed, logging
- Bộ docs đã rút gọn để dễ đọc hơn

## Hướng phát triển

- Thêm feature mới bằng cách tạo model, service và cog tương ứng
- Cập nhật `docs/COMMANDS_REFERENCE.md` khi thêm lệnh mới
- Cập nhật `docs/PROJECT_STATUS.md` khi thay đổi tiến độ hoặc setup

## Lưu ý

- `.env` chỉ dùng local, không commit
- Database `.db` sẽ được tạo tự động khi chạy bot
- Nếu bạn muốn xem phần chi tiết hơn, đọc trong `docs/`

