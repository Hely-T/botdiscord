# File: cogs/ticket/resolvers.py
# Purpose: Xử lý parse tham số (Channel, Role, User, Category) từ input là Mention/Tag hoặc ID.
# Notes:
# - Cung cấp helper để đảm bảo mọi command support cả dạng Tag (<@123>, <#123>) và ID (123).
# - Phục vụ strict validation theo yêu cầu kĩ thuật.

import re
from typing import Optional

def extract_discord_id(input_str: str) -> Optional[int]:
    """
    Phân tích chuỗi đầu vào (có thể là tag <@123456>, <#123456>, <@&123456> hoặc ID thuần "123456").
    Trả về số nguyên (ID) nếu hợp lệ, nếu không trả về None.
    """
    if not input_str:
        return None
        
    input_str = str(input_str).strip()
    # Dùng regex tìm chuỗi số liên tiếp có độ dài từ 17-20 ký tự (chuẩn ID Discord)
    match = re.search(r'\d{17,21}', input_str)
    if match:
        return int(match.group(0))
        
    return None