"""
Role Permission Service
- Quản lý quyền commands theo role
- Sử dụng RolePermissionManager từ utils.py
"""

from utils import RolePermissionManager
from typing import List, Dict

class RolePermissionService:
    """Service quản lý quyền commands theo role"""
    
    def __init__(self):
        self.manager = RolePermissionManager()
    
    def add_command_role(self, guild_id: int, role_id: int, command_name: str, 
                         created_by: int) -> bool:
        """
        Thêm role cho command
        
        Args:
            guild_id: Server ID
            role_id: Role ID
            command_name: Tên command
            created_by: User ID người tạo
        
        Returns:
            True nếu thành công
        
        Ví dụ:
            service.add_command_role(123456, 987654, 'ban', 111111)
            → Role 987654 được dùng lệnh 'ban' trên server 123456
        """
        return self.manager.add_permission(
            guild_id=guild_id,
            role_id=role_id,
            command_name=command_name.lower(),
            created_by=created_by
        )

    def save_role(self, guild_id: int, role_id: int, role_name: str, hierarchy_level: int = 0) -> bool:
        """Lưu tên role để các lệnh kiểm tra quyền hiển thị dễ đọc hơn."""
        return self.manager.add_role_hierarchy(
            guild_id=guild_id,
            role_id=role_id,
            role_name=role_name,
            hierarchy_level=hierarchy_level,
        )
    
    def remove_command_role(self, guild_id: int, role_id: int, command_name: str) -> bool:
        """
        Xóa role khỏi command
        
        Args:
            guild_id: Server ID
            role_id: Role ID
            command_name: Tên command
        
        Returns:
            True nếu thành công
        
        Ví dụ:
            service.remove_command_role(123456, 987654, 'ban')
            → Role 987654 không được dùng lệnh 'ban' nữa
        """
        return self.manager.remove_permission(
            guild_id=guild_id,
            role_id=role_id,
            command_name=command_name.lower()
        )
    
    def user_can_use(self, guild_id: int, user_roles: List[int], command_name: str) -> bool:
        """
        Check user có thể dùng command không
        
        Args:
            guild_id: Server ID
            user_roles: List role IDs của user
            command_name: Tên command
        
        Returns:
            True nếu user có ít nhất 1 role có quyền
        
        Ví dụ:
            user_roles = [123, 456, 789]
            can_use = service.user_can_use(100, user_roles, 'ban')
            → Nếu role 456 hoặc role nào có quyền 'ban' thì return True
        """
        return self.manager.can_use_command(
            guild_id=guild_id,
            user_roles=user_roles,
            command_name=command_name.lower()
        )
    
    def get_roles_for_command(self, guild_id: int, command_name: str) -> List[Dict]:
        """
        Lấy danh sách roles có quyền dùng command
        
        Args:
            guild_id: Server ID
            command_name: Tên command
        
        Returns:
            List dict [{'role_id': 123, 'role_name': 'Admin'}, ...]
        """
        return self.manager.get_roles_for_command(guild_id, command_name.lower())
    
    def get_commands_for_role(self, guild_id: int, role_id: int) -> List[str]:
        """
        Lấy danh sách commands mà role có quyền
        
        Args:
            guild_id: Server ID
            role_id: Role ID
        
        Returns:
            List tên commands
        """
        return self.manager.get_commands_for_role(guild_id, role_id)
