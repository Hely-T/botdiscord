from dataclasses import dataclass
from enum import Enum
from models.constants import MIN_USERNAME_LENGTH, MAX_USERNAME_LENGTH

class UserRole(Enum):
    """Vai trò người dùng"""
    ADMIN = "admin"
    MODERATOR = "moderator"
    USER = "user"

@dataclass
class User:
    """Model đại diện cho một user"""
    user_id: int
    username: str
    role: UserRole = UserRole.USER
    points: int = 0
    level: int = 1
    
    def validate(self):
        """Validate dữ liệu user"""
        if len(self.username) < MIN_USERNAME_LENGTH:
            raise ValueError(f"Username phải có ít nhất {MIN_USERNAME_LENGTH} ký tự")
        if len(self.username) > MAX_USERNAME_LENGTH:
            raise ValueError(f"Username không được vượt quá {MAX_USERNAME_LENGTH} ký tự")
        if self.points < 0:
            raise ValueError("Points không thể âm")
        if self.level < 1:
            raise ValueError("Level phải >= 1")
    
    def is_admin(self) -> bool:
        return self.role == UserRole.ADMIN
    
    def is_moderator(self) -> bool:
        return self.role == UserRole.MODERATOR
    
    def add_points(self, amount: int):
        """Thêm points"""
        if amount <= 0:
            raise ValueError("Amount phải > 0")
        self.points += amount
    
    def remove_points(self, amount: int):
        """Trừ points"""
        if amount <= 0:
            raise ValueError("Amount phải > 0")
        if self.points < amount:
            raise ValueError("Không đủ points")
        self.points -= amount
