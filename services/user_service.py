"""
User Service Layer
- Chứa business logic cho user
- Giao tiếp với Database Layer
"""

from utils import CogDatabase, get_timestamp
from models.user_model import User, UserRole
from models.constants import DEFAULT_ROLE, POINTS_PER_MESSAGE

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
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        ''')
    
    def get_or_create_user(self, user_id: int, username: str) -> User:
        """Lấy user hoặc tạo mới"""
        user = self.get_user(user_id)
        
        if not user:
            user = User(
                user_id=user_id,
                username=username,
                role=UserRole.USER,
                points=0,
                level=1
            )
            user.validate()
            self.create_user(user)
        
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
            level=result['level']
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
    
    def get_top_users(self, limit: int = 10) -> list:
        """Lấy top users theo points"""
        return self.db.fetch(
            'SELECT * FROM users ORDER BY points DESC LIMIT ?',
            (limit,)
        )
    
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
