# File: ui/ticket/staff_ui.py
# Purpose: Menu thao tác nhanh dành cho Staff trong Ticket.

import discord
from discord.ui import View, Button, UserSelect, Modal, TextInput
from ui.ticket.emoji import TicketEmoji

class StaffManageMenu(View):
    def __init__(self, cog):
        super().__init__(timeout=120)
        self.cog = cog

    @discord.ui.select(cls=UserSelect, placeholder="Thêm thành viên vào vé...")
    async def select_add_user(self, interaction: discord.Interaction, select: UserSelect):
        await self.cog.adapter_trigger_add(interaction, select.values[0])

    @discord.ui.select(cls=UserSelect, placeholder="Xoá thành viên khỏi vé...")
    async def select_remove_user(self, interaction: discord.Interaction, select: UserSelect):
        await self.cog.adapter_trigger_remove(interaction, select.values[0])
        
    @discord.ui.select(cls=UserSelect, placeholder="Chuyển vé cho Staff khác...")
    async def select_transfer(self, interaction: discord.Interaction, select: UserSelect):
        await self.cog.adapter_trigger_transfer(interaction, select.values[0])

    @discord.ui.button(label="Đổi Tên", style=discord.ButtonStyle.secondary, emoji=TicketEmoji.get("rename"))
    async def btn_rename(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_modal(RenameTicketModal(self.cog))
        
    @discord.ui.button(label="Gỡ Nhận (Unclaim)", style=discord.ButtonStyle.secondary, emoji=TicketEmoji.get("cancel"))
    async def btn_unclaim(self, interaction: discord.Interaction, button: Button):
        await self.cog.adapter_trigger_unclaim(interaction)
        
    @discord.ui.button(label="Thông Tin Vé", style=discord.ButtonStyle.primary, emoji=TicketEmoji.get("log"))
    async def btn_info(self, interaction: discord.Interaction, button: Button):
        await self.cog.adapter_trigger_info(interaction)

class RenameTicketModal(Modal, title="Đổi tên Ticket"):
    def __init__(self, cog):
        super().__init__()
        self.cog = cog
        self.inp_name = TextInput(label="Tên vé mới", placeholder="Viết liền không dấu hoặc gạch ngang...", required=True, max_length=50)
        self.add_item(self.inp_name)

    async def on_submit(self, interaction: discord.Interaction):
        await self.cog.adapter_trigger_rename(interaction, self.inp_name.value)