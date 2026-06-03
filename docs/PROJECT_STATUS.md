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

```bash
git add .
git commit -m "cập nhật tài liệu"
git push
```

## GitHub setup

- Tạo repo trên GitHub
- Add remote với `git remote add origin <url>`
- Push nhánh `main`

## Khi thêm feature mới

1. Tạo model nếu cần
2. Tạo service nếu có logic
3. Tạo cog để expose command
4. Cập nhật `COMMANDS_REFERENCE.md` nếu có lệnh mới

## Trạng thái hiện tại

- Core bot đã có
- Hệ thống role command đã có
- Docs đã được rút gọn
- Sẵn sàng để mở rộng thêm feature

