# File: test/test_ticket_manager.py
# Purpose: Kiểm thử Ticket Manager Menu mới (UI driven).

import unittest
import discord
from unittest.mock import MagicMock, AsyncMock
from cogs.ticket.ticket_cog import TicketCog
from ui.ticket.manager_ui import TicketManagerMenu, ConfigChannelMenu, ConfigLogMenu, LogIdModal, safe_reply, safe_edit_menu
from services.ticket_service import TicketService
from ui.ticket.emoji import TicketEmoji

class TestTicketManager(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.mock_bot = MagicMock()
        self.cog = TicketCog(self.mock_bot)
        self.cog.service = MagicMock()
        
        self.interaction = MagicMock(spec=discord.Interaction)
        self.interaction.guild.id = 777
        self.interaction.user = MagicMock()
        self.interaction.user.guild_permissions.administrator = True
        self.interaction.response.send_message = AsyncMock()
        self.interaction.response.edit_message = AsyncMock()
        self.interaction.response.defer = AsyncMock()
        self.interaction.response.send_modal = AsyncMock()
        self.interaction.followup.send = AsyncMock()
        self.interaction.response.is_done = MagicMock(return_value=False)
        self.interaction.edit_original_response = AsyncMock()

    def test_ticket_config_schema_has_updated_at(self):
        svc = TicketService()
        svc.db = MagicMock()
        svc.db.fetch.return_value = [] # Giả lập bảng trống để test trigger alter table
        svc._ensure_column("ticket_config", "updated_at", "TEXT")
        svc.db.execute.assert_called_with("ALTER TABLE ticket_config ADD COLUMN updated_at TEXT")

    def test_update_single_config_creates_config_when_missing(self):
        svc = TicketService()
        svc.db = MagicMock()
        svc.get_config = MagicMock(side_effect=[None, {'guild_id': 777}])
        svc.update_single_config(777, 'max_open_tickets', 2)
        svc.db.insert.assert_called_once()

    def test_update_single_config_rejects_invalid_key(self):
        svc = TicketService()
        with self.assertRaises(ValueError):
            svc.update_single_config(777, 'invalid_sql_injection_key', 1)

    def test_update_single_config_allows_none_for_log_channel(self):
        svc = TicketService()
        svc.db = MagicMock()
        svc.ensure_config = MagicMock()
        svc.update_single_config(777, 'log_channel_id', None)
        args, kwargs = svc.db.execute.call_args
        # Value is passed via execute args
        self.assertIsNone(args[1][0])

    async def test_ticket_manager_interaction_check_rejects_non_admin_with_response(self):
        menu = TicketManagerMenu(self.cog)
        self.interaction.user.guild_permissions.administrator = False # Non-admin
        # Mock admin_service check
        with patch('cogs.ticket.permissions.AdminService.is_admin', return_value=False):
            res = await menu.interaction_check(self.interaction)
            self.assertFalse(res)
            self.interaction.response.send_message.assert_called_once()
            self.assertIn("Chỉ admin", str(self.interaction.response.send_message.call_args))

    async def test_ticket_manager_menu_shows_current_config(self):
        self.cog.service.ensure_config.return_value = {'panel_channel_id': 123, 'updated_at': '2023-01-01'}
        await self.cog.ticket_manager_slash(self.interaction)
        self.interaction.response.send_message.assert_called_once()
        args, kwargs = self.interaction.response.send_message.call_args
        self.assertIn("123", str(kwargs['embed'].to_dict()))
        self.assertIn("2023-01-01", str(kwargs['embed'].to_dict()))

    async def test_ticket_channel_select_saves_panel_channel(self):
        menu = ConfigChannelMenu(self.cog, MagicMock())
        menu.parent_menu.refresh_menu = AsyncMock()
        select = MagicMock()
        select.values = [MagicMock(id=999)]
        self.cog.service.get_config.return_value = {'panel_channel_id': 999} # Mock read-back
        await menu.select_panel(self.interaction, select)
        self.interaction.response.defer.assert_called_once()
        self.cog.service.update_single_config.assert_called_with(777, 'panel_channel_id', 999)
        self.interaction.followup.send.assert_called_once() # Verify safe_reply used followup after defer
        menu.parent_menu.refresh_menu.assert_called_once()

    async def test_disable_log_only_updates_log_channel(self):
        menu = ConfigLogMenu(self.cog, MagicMock())
        menu.parent_menu.refresh_menu = AsyncMock()
        await menu.btn_disable_log(self.interaction, MagicMock())
        self.cog.service.update_single_config.assert_any_call(777, 'log_channel_id', None)
        menu.parent_menu.refresh_menu.assert_called_once()

    async def test_log_id_modal_accepts_valid_text_channel_id(self):
        modal = LogIdModal(self.cog, MagicMock())
        modal.parent_menu.refresh_menu = AsyncMock()
        modal.inp_log.value = "111111"
        self.interaction.guild.get_channel.return_value = MagicMock(spec=discord.TextChannel)
        self.cog.service.get_config.return_value = {'log_channel_id': 111111}
        await modal.on_submit(self.interaction)
        self.cog.service.update_single_config.assert_called_with(777, 'log_channel_id', 111111)
        
    async def test_log_id_modal_zero_disables_log_channel(self):
        modal = LogIdModal(self.cog, MagicMock())
        modal.parent_menu.refresh_menu = AsyncMock()
        modal.inp_log.value = "0"
        await modal.on_submit(self.interaction)
        self.cog.service.update_single_config.assert_called_with(777, 'log_channel_id', None)

    async def test_update_success_not_sent_when_backend_value_mismatch(self):
        menu = ConfigChannelMenu(self.cog, MagicMock())
        menu.parent_menu.refresh_menu = AsyncMock()
        select = MagicMock()
        select.values = [MagicMock(id=999)]
        self.cog.service.get_config.return_value = {'panel_channel_id': 123} # Read-back mismatch!
        await menu.select_panel(self.interaction, select)
        # Asserts it sent an error message instead of success
        args, kwargs = self.interaction.followup.send.call_args
        self.assertIn("Lỗi Backend", str(kwargs.get('content')))

    async def test_ticket_panel_refresh_edits_existing_message(self):
        self.cog.service.get_config.return_value = {'panel_channel_id': 123, 'ticket_category_id': 456, 'panel_message_id': 789}
        mock_channel = AsyncMock()
        mock_msg = AsyncMock()
        mock_channel.fetch_message.return_value = mock_msg
        self.interaction.guild.get_channel.return_value = mock_channel
        
        await self.cog.handle_send_or_refresh_panel(self.interaction)
        mock_msg.edit.assert_called_once()