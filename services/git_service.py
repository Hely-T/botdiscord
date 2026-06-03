import subprocess
import os
from utils import log_to_file, get_timestamp

class GitUpdateService:
    """
    Dịch vụ quản lý cập nhật code từ GitHub
    - Pull latest code từ remote
    - Reload cogs tự động
    - Kiểm tra trạng thái git
    """
    
    def __init__(self, repo_path='.'):
        self.repo_path = repo_path
        self.log_prefix = "[GIT_SERVICE]"
    
    def _run_git_command(self, command):
        """Chạy lệnh git và trả về kết quả"""
        try:
            result = subprocess.run(
                command,
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=30
            )
            return {
                'success': result.returncode == 0,
                'stdout': result.stdout.strip(),
                'stderr': result.stderr.strip(),
                'returncode': result.returncode
            }
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'stdout': '',
                'stderr': 'Git command timeout',
                'returncode': -1
            }
        except Exception as e:
            return {
                'success': False,
                'stdout': '',
                'stderr': str(e),
                'returncode': -1
            }
    
    def pull_latest(self):
        """Pull latest code từ GitHub"""
        log_to_file(f"{self.log_prefix} Đang pull code từ GitHub...")
        
        result = self._run_git_command(['git', 'pull', 'origin', 'main'])
        
        if result['success']:
            log_to_file(f"{self.log_prefix} ✅ Pull thành công!")
            return {
                'success': True,
                'message': f"✅ Pull thành công!\n{result['stdout']}",
                'changed_files': self._get_changed_files()
            }
        else:
            error_msg = result['stderr'] or result['stdout']
            log_to_file(f"{self.log_prefix} ❌ Pull thất bại: {error_msg}")
            return {
                'success': False,
                'message': f"❌ Pull thất bại!\n{error_msg}",
                'changed_files': []
            }
    
    def get_status(self):
        """Kiểm tra trạng thái git"""
        result = self._run_git_command(['git', 'status', '-s'])
        
        if result['success']:
            return {
                'success': True,
                'status': result['stdout'] or '✅ Không có thay đổi (clean)',
                'has_changes': bool(result['stdout'])
            }
        else:
            return {
                'success': False,
                'status': result['stderr'],
                'has_changes': False
            }
    
    def get_last_commit(self):
        """Lấy thông tin commit cuối cùng"""
        result = self._run_git_command(['git', 'log', '-1', '--oneline'])
        
        if result['success']:
            return {
                'success': True,
                'commit': result['stdout']
            }
        else:
            return {
                'success': False,
                'commit': None
            }
    
    def _get_changed_files(self):
        """Lấy danh sách files đã thay đổi"""
        result = self._run_git_command(['git', 'diff', '--name-only', 'HEAD@{1}', 'HEAD'])
        
        if result['success']:
            files = result['stdout'].split('\n') if result['stdout'] else []
            return [f for f in files if f.strip()]
        return []
    
    def get_branch(self):
        """Lấy tên branch hiện tại"""
        result = self._run_git_command(['git', 'rev-parse', '--abbrev-ref', 'HEAD'])
        
        if result['success']:
            return result['stdout']
        return None
    
    def get_remote_url(self):
        """Lấy URL của remote repository"""
        result = self._run_git_command(['git', 'config', '--get', 'remote.origin.url'])
        
        if result['success']:
            return result['stdout']
        return None
