# Project Status

## Đã có

- `main.py`
- `config.py`
- `utils.py`
- `requirements.txt`
- `cogs/`
- `services/`
- `models/`
- `docs/`

## Tài liệu chính

- `docs/README.md`
- `docs/ARCHITECTURE.md`
- `docs/COMMANDS_REFERENCE.md`
- `docs/PROJECT_STATUS.md`

## Setup nhanh

```bash
pip install -r requirements.txt
python main.py
```

## Git workflow

- Local: sửa code -> test -> `git add` -> `git commit` -> `git push`
- Server: pull code mới -> reload cogs nếu cần
- Không commit `.env`, database `.db`, hoặc logs

## GitHub setup

- Tạo repo trên GitHub
- Add remote với `git remote add origin <url>`
- Push nhánh `main`

## Workflow cho cog mới

1. Tạo file cog trong `cogs/`
2. Nếu có logic thì tạo service trong `services/`
3. Test local
4. Commit và push
5. Cập nhật tài liệu nếu có lệnh mới

## Khi thêm feature mới

1. Tạo model nếu cần
2. Tạo service nếu có logic
3. Tạo cog để expose command
4. Cập nhật `COMMANDS_REFERENCE.md` nếu có lệnh mới
5. Cập nhật `docs/ARCHITECTURE.md` nếu thay đổi kiến trúc

## Trạng thái hiện tại

- Core bot đã có
- Hệ thống role command đã có
- Docs đã được rút gọn
- Sẵn sàng để mở rộng thêm feature

## Git workflow cho cộng đồng

- Nhánh `main` là bản ổn định
- Push code sau khi test xong
- Dùng docs rút gọn để onboarding nhanh
