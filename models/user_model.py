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
    total_hours: float = 0.0
    total_donate: int = 0
    total_money: int = 0
    
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
        if self.total_hours < 0:
            raise ValueError("Hours không thể âm")
        if self.total_donate < 0:
            raise ValueError("Donate không thể âm")
        if self.total_money < 0:
            raise ValueError("Money không thể âm")
    
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

    def add_hours(self, hours: float):
        """Thêm giờ hoạt động"""
        if hours <= 0:
            raise ValueError("Hours phải > 0")
        self.total_hours += hours

    def add_donate(self, amount: int):
        """Thêm donate"""
        if amount <= 0:
            raise ValueError("Amount phải > 0")
        self.total_donate += amount

    def add_money(self, amount: int):
        """Thêm tiền"""
        if amount <= 0:
            raise ValueError("Amount phải > 0")
        self.total_money += amount
