# File: test/test_ticket_staff.py
# Purpose: Kiểm thử toàn bộ các Staff Commands (Add, Remove, Rename, Transfer, Info, v.v.).
# Notes: Sử dụng mock để giả lập Hybrid Adapter (Slash + Prefix context).

import unittest
from unittest.mock import MagicMock, AsyncMock, patch
from cogs.ticket.permissions import is_ticket_staff, is_ticket_admin
from cogs.ticket.ticket_cog import ContextAdapter, TicketCog

class TestTicketStaffCommands(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        self.mock_bot = MagicMock()
        self.cog = TicketCog(self.mock_bot)
        self.cog.service = MagicMock()
        self.cog.service.get_ticket.return_value = {
            'ticket_id': 1, 'status': 'open', 'owner_user_id': 999, 'claimed_by_user_id': None
        }
        self.cog.service.get_config.return_value = {'staff_role_id': '111'}

        self.mock_user = MagicMock()
        self.mock_user.id = 888
        self.mock_user.bot = False
        self.mock_role = MagicMock()
        self.mock_role.id = 111
        self.mock_user.roles = [self.mock_role]
        self.mock_user.guild_permissions.administrator = False

        self.mock_channel = AsyncMock()
        self.mock_channel.id = 123
        self.mock_channel.set_permissions = AsyncMock()
        self.mock_channel.edit = AsyncMock()

        self.mock_adapter = MagicMock()
        self.mock_adapter.user = self.mock_user
        self.mock_adapter.channel = self.mock_channel
        self.mock_adapter.guild.id = 777
        self.mock_adapter.send = AsyncMock()

    async def test_ticket_add_user_rejects_outside_ticket_channel(self):
        self.cog.service.get_ticket.return_value = None
        await self.cog._core_ticket_add(self.mock_adapter, MagicMock())
        self.mock_adapter.send.assert_called_once()
        args, kwargs = self.mock_adapter.send.call_args
        self.assertIn("Lỗi", str(kwargs.get('embed').to_dict()))

    async def test_ticket_add_user_rejects_when_ticket_closed(self):
        self.cog.service.get_ticket.return_value = {'status': 'closed'}
        await self.cog._core_ticket_add(self.mock_adapter, MagicMock())
        self.mock_adapter.send.assert_called_once()

    async def test_ticket_add_user_requires_staff_or_admin(self):
        self.mock_user.roles = [] # Normal user
        await self.cog._core_ticket_add(self.mock_adapter, MagicMock())
        args, kwargs = self.mock_adapter.send.call_args
        self.assertIn("Lỗi Quyền", str(kwargs.get('embed').to_dict()))

    async def test_ticket_add_user_applies_permission_overwrite(self):
        target = MagicMock(); target.bot = False
        await self.cog._core_ticket_add(self.mock_adapter, target)
        self.mock_channel.set_permissions.assert_called_once_with(target, read_messages=True, send_messages=True, attach_files=True, read_message_history=True)

    async def test_ticket_add_user_writes_audit_event(self):
        target = MagicMock(); target.id = 555; target.bot = False
        await self.cog._core_ticket_add(self.mock_adapter, target)
        self.cog.service.log_event.assert_called_once_with(1, 777, 123, 'add_user', 888, 555)

    async def test_ticket_remove_user_rejects_owner_remove_by_normal_staff(self):
        target = MagicMock(); target.id = 999; target.bot = False # Owner
        await self.cog._core_ticket_remove(self.mock_adapter, target)
        args, kwargs = self.mock_adapter.send.call_args
        self.assertIn("Chỉ Admin", str(kwargs.get('embed').to_dict()))

    async def test_ticket_remove_user_rejects_bot_remove(self):
        target = MagicMock(); target.bot = True
        await self.cog._core_ticket_remove(self.mock_adapter, target)
        args, kwargs = self.mock_adapter.send.call_args
        self.assertIn("Bot", str(kwargs.get('embed').to_dict()))

    async def test_ticket_remove_user_removes_permission_overwrite(self):
        target = MagicMock(); target.id = 444; target.bot = False
        await self.cog._core_ticket_remove(self.mock_adapter, target)
        self.mock_channel.set_permissions.assert_called_once_with(target, overwrite=None)

    async def test_ticket_remove_user_writes_audit_event(self):
        target = MagicMock(); target.id = 444; target.bot = False
        await self.cog._core_ticket_remove(self.mock_adapter, target)
        self.cog.service.log_event.assert_called_once_with(1, 777, 123, 'remove_user', 888, 444)

    async def test_ticket_rename_sanitizes_channel_name(self):
        await self.cog._core_ticket_rename(self.mock_adapter, "HeLLo WORLD %$#")
        self.mock_channel.edit.assert_called_once_with(name="ticket-hello-world-", reason=f"Renamed by {self.mock_user}")

    async def test_ticket_rename_rejects_empty_name(self):
        await self.cog._core_ticket_rename(self.mock_adapter, "   @#$  ")
        self.mock_channel.edit.assert_not_called()

    async def test_ticket_rename_rejects_closed_ticket(self):
        self.cog.service.get_ticket.return_value = {'status': 'closed'}
        await self.cog._core_ticket_rename(self.mock_adapter, "test")
        self.mock_channel.edit.assert_not_called()

    async def test_ticket_rename_writes_audit_event(self):
        await self.cog._core_ticket_rename(self.mock_adapter, "valid")
        self.cog.service.log_event.assert_called_once_with(1, 777, 123, 'rename', 888, message="ticket-valid")

    async def test_ticket_transfer_requires_staff_target(self):
        target = MagicMock(); target.roles = [] # Not staff
        target.guild_permissions.administrator = False
        await self.cog._core_ticket_transfer(self.mock_adapter, target)
        self.cog.service.transfer_ticket.assert_not_called()

    async def test_ticket_transfer_updates_claimed_by(self):
        target = MagicMock(); target.id = 222; target.roles = [self.mock_role]; target.display_name = "Jane"
        await self.cog._core_ticket_transfer(self.mock_adapter, target)
        self.cog.service.transfer_ticket.assert_called_once_with(123, 222, "Jane")

    async def test_ticket_transfer_writes_audit_event(self):
        target = MagicMock(); target.id = 222; target.roles = [self.mock_role]; target.display_name = "Jane"
        await self.cog._core_ticket_transfer(self.mock_adapter, target)
        self.cog.service.log_event.assert_called_once_with(1, 777, 123, 'transfer', 888, 222)

    async def test_ticket_unclaim_rejects_when_unclaimed(self):
        await self.cog._core_ticket_unclaim(self.mock_adapter) # Default status is 'open'
        self.cog.service.unclaim_ticket.assert_not_called()

    async def test_ticket_unclaim_rejects_non_claimed_staff_without_admin(self):
        self.cog.service.get_ticket.return_value = {'status': 'claimed', 'claimed_by_user_id': 123} # Claimed by someone else
        await self.cog._core_ticket_unclaim(self.mock_adapter)
        self.cog.service.unclaim_ticket.assert_not_called()

    async def test_ticket_unclaim_sets_status_open(self):
        self.cog.service.get_ticket.return_value = {'status': 'claimed', 'claimed_by_user_id': 888} # Claimed by me
        await self.cog._core_ticket_unclaim(self.mock_adapter)
        self.cog.service.unclaim_ticket.assert_called_once_with(123)

    async def test_ticket_unclaim_writes_audit_event(self):
        self.cog.service.get_ticket.return_value = {'status': 'claimed', 'claimed_by_user_id': 888}
        await self.cog._core_ticket_unclaim(self.mock_adapter)
        self.cog.service.log_event.assert_called_once_with(1, 777, 123, 'unclaim', 888)

    async def test_ticket_info_rejects_non_ticket_channel(self):
        self.cog.service.get_ticket.return_value = None
        await self.cog._core_ticket_info(self.mock_adapter)
        self.mock_adapter.send.assert_called_once()

    # Extra checks handled by previous mock compliance test file.

if __name__ == '__main__':
    unittest.main()