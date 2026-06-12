"""
User Service Layer
- Chứa business logic cho user
- Giao tiếp với Database Layer
"""

from utils import CogDatabase, get_timestamp
from models.user_model import User, UserRole

class UserService:
    """Service xử lý user operations"""
    
    def __init__(self):
        self.db = CogDatabase('users')
        self._init_database()
    
    def _init_database(self):
        """Khởi tạo database schema"""
        self.db.create_table('users', '''
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE NOT NULL,
            username TEXT NOT NULL,
            role TEXT DEFAULT 'user',
            points INTEGER DEFAULT 0,
            level INTEGER DEFAULT 1,
            cash INTEGER DEFAULT 0,
            luong INTEGER DEFAULT 0,
            star INTEGER DEFAULT 0,
            total_hours REAL DEFAULT 0,
            total_donate INTEGER DEFAULT 0,
            total_money INTEGER DEFAULT 0,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        ''')
        self._ensure_schema_columns()

    def _ensure_schema_columns(self):
        """Đảm bảo các cột mới tồn tại cho database cũ"""
        columns = {row['name'] for row in self.db.fetch('PRAGMA table_info(users)')}
        required_columns = {
            'total_hours': 'REAL DEFAULT 0',
            'total_donate': 'INTEGER DEFAULT 0',
            'total_money': 'INTEGER DEFAULT 0',
            'cash': 'INTEGER DEFAULT 0',
            'luong': 'INTEGER DEFAULT 0',
            'star': 'INTEGER DEFAULT 0',
        }

        for column_name, column_sql in required_columns.items():
            if column_name not in columns:
                self.db.execute(f'ALTER TABLE users ADD COLUMN {column_name} {column_sql}')
    
    def get_or_create_user(self, user_id: int, username: str) -> User:
        """Lấy user hoặc tạo mới"""
        user = self.get_user(user_id)
        
        if not user:
            user = User(
                user_id=user_id,
                username=username,
                role=UserRole.USER,
                points=0,
                level=1,
                cash=0,
                luong=0,
                star=0,
                total_hours=0,
                total_donate=0,
                total_money=0,
            )
            user.validate()
            self.create_user(user)
        
        return user

    def touch_user(self, user_id: int, username: str) -> User:
        """Tạo user nếu chưa có, hoặc cập nhật username mới nhất."""
        safe_username = str(username or user_id).strip() or str(user_id)
        user = self.get_user(user_id)
        if not user:
            return self.get_or_create_user(user_id, safe_username)

        if user.username != safe_username:
            self.db.update(
                'users',
                {'username': safe_username, 'updated_at': get_timestamp()},
                'user_id = ?',
                (user_id,)
            )
            user.username = safe_username
        return user
    
    def get_user(self, user_id: int) -> User:
        """Lấy user từ database"""
        result = self.db.select_one('users', 'user_id = ?', (user_id,))
        
        if not result:
            return None
        
        return User(
            user_id=result['user_id'],
            username=result['username'],
            role=UserRole(result['role']),
            points=result['points'],
            level=result['level'],
            cash=result['cash'] if 'cash' in result.keys() else 0,
            luong=result['luong'] if 'luong' in result.keys() else 0,
            star=result['star'] if 'star' in result.keys() else 0,
            total_hours=result['total_hours'] if 'total_hours' in result.keys() else 0,
            total_donate=result['total_donate'] if 'total_donate' in result.keys() else 0,
            total_money=result['total_money'] if 'total_money' in result.keys() else 0,
        )
    
    def create_user(self, user: User):
        """Tạo user mới"""
        user.validate()
        
        self.db.insert('users', {
            'user_id': user.user_id,
            'username': user.username,
            'role': user.role.value,
            'points': user.points,
            'level': user.level,
            'cash': user.cash,
            'luong': user.luong,
            'star': user.star,
            'total_hours': user.total_hours,
            'total_donate': user.total_donate,
            'total_money': user.total_money,
            'created_at': get_timestamp(),
            'updated_at': get_timestamp()
        })
    
    def add_points(self, user_id: int, amount: int):
        """Thêm points cho user"""
        user = self.get_user(user_id)
        if not user:
            raise ValueError(f"User {user_id} không tồn tại")
        
        user.add_points(amount)
        
        self.db.update('users',
            {'points': user.points, 'updated_at': get_timestamp()},
            'user_id = ?',
            (user_id,)
        )

    def remove_points(self, user_id: int, amount: int):
        self._update_numeric_field(user_id, 'points', -amount)

    def set_points(self, user_id: int, amount: int):
        self._set_numeric_field(user_id, 'points', amount)

    def _update_numeric_field(self, user_id: int, field_name: str, amount: float):
        user = self.get_user(user_id)
        if not user:
            raise ValueError(f"User {user_id} không tồn tại")

        current_value = getattr(user, field_name)
        new_value = current_value + amount

        if field_name == 'total_hours':
            if new_value < 0:
                raise ValueError("Hours không thể âm")
        else:
            # Cash âm từ casino được giữ nguyên và có thể nạp để bù nợ.
            # Các thao tác chi tiêu ở bot tổng không được tự tạo thêm nợ.
            if new_value < 0 and not (field_name == 'cash' and amount > 0):
                raise ValueError(f"{field_name} không thể âm")

        setattr(user, field_name, new_value)
        self.db.update('users',
            {
                field_name: new_value,
                'updated_at': get_timestamp()
            },
            'user_id = ?',
            (user_id,)
        )

    def _set_numeric_field(self, user_id: int, field_name: str, value: float):
        user = self.get_user(user_id)
        if not user:
            raise ValueError(f"User {user_id} không tồn tại")
        if value < 0 and field_name != 'cash':
            raise ValueError(f"{field_name} không thể âm")

        self.db.update('users',
            {
                field_name: value,
                'updated_at': get_timestamp()
            },
            'user_id = ?',
            (user_id,)
        )

    def add_cash(self, user_id: int, amount: int):
        self._update_numeric_field(user_id, 'cash', amount)

    def remove_cash(self, user_id: int, amount: int):
        self._update_numeric_field(user_id, 'cash', -amount)

    def set_cash(self, user_id: int, amount: int):
        self._set_numeric_field(user_id, 'cash', amount)

    def add_total_money(self, user_id: int, amount: int):
        self._update_numeric_field(user_id, 'total_money', amount)

    def remove_total_money(self, user_id: int, amount: int):
        self._update_numeric_field(user_id, 'total_money', -amount)

    def set_total_money(self, user_id: int, amount: int):
        self._set_numeric_field(user_id, 'total_money', amount)

    def add_total_donate(self, user_id: int, amount: int):
        self._update_numeric_field(user_id, 'total_donate', amount)

    def remove_total_donate(self, user_id: int, amount: int):
        self._update_numeric_field(user_id, 'total_donate', -amount)

    def set_total_donate(self, user_id: int, amount: int):
        self._set_numeric_field(user_id, 'total_donate', amount)

    def transfer_cash(self, from_user_id: int, from_username: str, to_user_id: int, to_username: str, amount: int):
        if amount <= 0:
            raise ValueError("Số tiền phải lớn hơn 0")

        sender = self.get_user(from_user_id)
        if not sender:
            raise ValueError(f"User {from_user_id} không tồn tại")
        receiver = self.get_user(to_user_id)
        if not receiver:
            raise ValueError(f"User {to_user_id} không tồn tại")

        if sender.cash < amount:
            raise ValueError("Không đủ cash để chuyển")

        self.remove_cash(from_user_id, amount)
        self.add_cash(to_user_id, amount)

        return {
            "sender_cash": self.get_user(from_user_id).cash,
            "receiver_cash": self.get_user(to_user_id).cash,
        }

    def add_luong(self, user_id: int, amount: int):
        self._update_numeric_field(user_id, 'luong', amount)

    def remove_luong(self, user_id: int, amount: int):
        self._update_numeric_field(user_id, 'luong', -amount)

    def set_luong(self, user_id: int, amount: int):
        self._set_numeric_field(user_id, 'luong', amount)

    def get_users_with_luong(self) -> list:
        return self.db.fetch(
            'SELECT * FROM users WHERE luong > 0 ORDER BY luong DESC, username ASC'
        )

    def pay_user_luong(self, user_id: int) -> dict:
        user = self.get_user(user_id)
        if not user:
            raise ValueError(f"User {user_id} không tồn tại")

        paid_amount = int(user.luong)
        if paid_amount <= 0:
            raise ValueError("Người này không còn lương cần trả")

        before = {
            "user_id": user.user_id,
            "username": user.username,
            "luong": paid_amount,
        }
        self.set_luong(user_id, 0)
        after_user = self.get_user(user_id)
        return {
            "source": "users",
            "before": before,
            "after": {
                "user_id": after_user.user_id,
                "username": after_user.username,
                "luong": int(after_user.luong),
            },
            "paid_amount": paid_amount,
        }

    def add_star(self, user_id: int, amount: int):
        self._update_numeric_field(user_id, 'star', amount)

    def remove_star(self, user_id: int, amount: int):
        self._update_numeric_field(user_id, 'star', -amount)

    def set_star(self, user_id: int, amount: int):
        self._set_numeric_field(user_id, 'star', amount)

    def add_hours(self, user_id: int, hours: float):
        self._update_numeric_field(user_id, 'total_hours', hours)

    def remove_hours(self, user_id: int, hours: float):
        self._update_numeric_field(user_id, 'total_hours', -hours)

    def set_hours(self, user_id: int, hours: float):
        self._set_numeric_field(user_id, 'total_hours', hours)

    def get_users_by_stat(self, field_name: str, limit: int = 25) -> list:
        allowed_fields = {"cash", "luong", "star", "points", "total_hours", "total_donate", "total_money"}
        if field_name not in allowed_fields:
            raise ValueError("Trường thống kê không hợp lệ")
        safe_limit = max(1, min(int(limit), 100))
        return self.db.fetch(
            f'SELECT * FROM users ORDER BY {field_name} DESC, username ASC LIMIT ?',
            (safe_limit,)
        )

    def get_top_users(self, limit: int = 10) -> list:
        """Lấy top users theo points"""
        return self.db.fetch(
            'SELECT * FROM users ORDER BY points DESC LIMIT ?',
            (limit,)
        )

    def get_top_stars(self, limit: int = 10) -> list:
        """Lấy top users theo star"""
        return self.db.fetch(
            'SELECT * FROM users ORDER BY star DESC, points DESC LIMIT ?',
            (limit,)
        )

    def get_total_luong(self) -> int:
        """Lấy tổng lương của toàn bộ users"""
        result = self.db.fetch_one('SELECT COALESCE(SUM(luong), 0) AS total_luong FROM users')
        return int(result['total_luong']) if result else 0

    def set_user_role(self, user_id: int, role: UserRole):
        """Thay đổi role user"""
        user = self.get_user(user_id)
        if not user:
            raise ValueError(f"User {user_id} không tồn tại")
        
        self.db.update('users',
            {'role': role.value, 'updated_at': get_timestamp()},
            'user_id = ?',
            (user_id,)
        )
