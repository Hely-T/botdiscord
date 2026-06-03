# Architecture

Bot được chia theo 4 lớp chính để dễ mở rộng và tránh nhồi logic vào một chỗ.

## 1) `main.py`

- Điểm khởi động bot
- Load config và cogs
- Chỉ giữ phần bootstrapping, không chứa business logic

## 2) `cogs/`

- Nhận command từ Discord
- Validate input cơ bản
- Gọi service tương ứng
- Trả response bằng text hoặc embed

## 3) `services/`

- Chứa business logic
- Xử lý dữ liệu và quy tắc nghiệp vụ
- Gọi helper/database qua `utils.py`

## 4) `models/`

- Khai báo data structure, constant, schema nội bộ
- Giữ dữ liệu rõ ràng và dễ tái sử dụng

## 5) `utils.py`

- `CogDatabase`
- `RolePermissionManager`
- helper cho prefix, splash, logging

## Nguyên tắc

- Cogs không nên đụng trực tiếp vào SQL
- Services không nên phụ thuộc Discord-specific code
- Models không nên chứa logic nặng
- `main.py` chỉ nên là entry point

## Luồng chuẩn

`Discord command -> Cog -> Service -> Utils/Database -> Response`

