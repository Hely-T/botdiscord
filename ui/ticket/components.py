# File: ui/ticket/components.py
# Purpose: Chứa các giao diện tương tác (Button, Select) cho Ticket.
# Notes:
# - Sử dụng ui/ticket/emoji.py để không hardcode icon.
# - Tách bạch UI Layer với Database Layer (gọi service gián tiếp hoặc qua callback).

import discord
from discord.ui import View, Select, Button, Modal, TextInput
from ui.ticket.emoji import TicketEmoji
from utils import create_error_splash, create_info_splash
from cogs.ticket.interaction_utils import safe_send, defer_if_needed
import logging

class TicketTypeSelect(Select):
    def __init__(self, create_callback):
        options = [
            discord.SelectOption(label="Hỗ trợ chung/event", value="support", emoji=TicketEmoji.get("support")),
            discord.SelectOption(label="Báo lỗi", value="bug", emoji=TicketEmoji.get("bug")),
            discord.SelectOption(label="Tố cáo", value="report", emoji=TicketEmoji.get("report")),
            discord.SelectOption(label="Thanh toán", value="payment", emoji=TicketEmoji.get("payment")),
            discord.SelectOption(label="Liên hệ Admin", value="contact_admin", emoji=TicketEmoji.get("contact_admin"))
        ]
        super().__init__(placeholder="Chọn loại yêu cầu hỗ trợ...", min_values=1, max_values=1, options=options, custom_id="ticket_panel_select")
        self.create_callback = create_callback

    async def callback(self, interaction: discord.Interaction):
        await self.create_callback(interaction, self.values[0])

class TicketCreateConfirmView(View):
    def __init__(self, cog, ticket_type: str, owner_id: int):
        super().__init__(timeout=120)
        self.cog = cog
        self.ticket_type = ticket_type
        self.owner_id = owner_id

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.owner_id:
            await safe_send(interaction, embed=create_error_splash(TicketEmoji.text("error", "Từ chối"), "Chỉ người mở vé mới có thể xác nhận."), ephemeral=True)
            return False
        return True

    @discord.ui.button(label="Xác nhận tạo ticket", style=discord.ButtonStyle.success, emoji=TicketEmoji.get("confirm"))
    async def confirm(self, interaction: discord.Interaction, button: Button):
        try:
            await interaction.response.edit_message(
                embed=create_info_splash(TicketEmoji.text("ticket", "Đang xử lý..."), "Hệ thống đang thiết lập vé cho bạn, vui lòng đợi trong giây lát..."), 
                view=None
            )
        except Exception:
            logging.getLogger(__name__).exception("[TICKET_CREATE] failed to disable confirm buttons")
            
        await self.cog.handle_create_ticket_confirmed(interaction, self.ticket_type)

    @discord.ui.button(label="Hủy", style=discord.ButtonStyle.secondary, emoji=TicketEmoji.get("cancel"))
    async def cancel(self, interaction: discord.Interaction, button: Button):
        await interaction.response.edit_message(embed=create_info_splash(TicketEmoji.text("cancel", "Đã Hủy"), "Thao tác mở vé đã bị hủy bỏ."), view=None)

class TicketCreateSelectView(View):
    def __init__(self, create_callback):
        super().__init__(timeout=120)
        self.add_item(TicketTypeSelect(create_callback))
        
class TicketPanelButtonsView(View):
    def __init__(self, cog):
        super().__init__(timeout=None)
        self.cog = cog

    @discord.ui.button(label="Mở Ticket Mới", style=discord.ButtonStyle.primary, custom_id="panel_open_ticket", emoji=TicketEmoji.get("ticket"))
    async def btn_open(self, interaction: discord.Interaction, button: Button):
        await self.cog.handle_panel_open_click(interaction)

    @discord.ui.button(label="Hướng Dẫn", style=discord.ButtonStyle.secondary, custom_id="panel_instructions", emoji=TicketEmoji.get("log"))
    async def btn_instructions(self, interaction: discord.Interaction, button: Button):
        await self.cog.handle_panel_instructions_click(interaction)

class TicketControlView(View):
    def __init__(self, claim_cb, close_cb, manage_cb):
        super().__init__(timeout=None)
        self.claim_cb = claim_cb
        self.close_cb = close_cb
        self.manage_cb = manage_cb
        
        self.btn_claim = Button(label="Claim", style=discord.ButtonStyle.success, custom_id="ticket_claim", emoji=TicketEmoji.get("claim"))
        self.btn_claim.callback = self.on_claim
        
        self.btn_manage = Button(label="Quản lý", style=discord.ButtonStyle.secondary, custom_id="ticket_manage", emoji=TicketEmoji.get("manage"))
        self.btn_manage.callback = self.on_manage

        self.btn_close = Button(label="Close", style=discord.ButtonStyle.danger, custom_id="ticket_close", emoji=TicketEmoji.get("close"))
        self.btn_close.callback = self.on_close
        
        self.add_item(self.btn_claim)
        self.add_item(self.btn_manage)
        self.add_item(self.btn_close)

    async def on_claim(self, interaction: discord.Interaction):
        await self.claim_cb(interaction)

    async def on_manage(self, interaction: discord.Interaction):
        await self.manage_cb(interaction)

    async def on_close(self, interaction: discord.Interaction):
        await self.close_cb(interaction)

class TicketCloseConfirmView(View):
    def __init__(self, confirm_cb, reason: str = ""):
        super().__init__(timeout=120)
        self.confirm_cb = confirm_cb
        self.reason = reason
        
        btn_confirm = Button(label="Xác nhận đóng", style=discord.ButtonStyle.danger, custom_id="ticket_confirm_close", emoji=TicketEmoji.get("confirm"))
        btn_confirm.callback = self.on_confirm
        
        btn_cancel = Button(label="Hủy", style=discord.ButtonStyle.secondary, custom_id="ticket_cancel_close", emoji=TicketEmoji.get("cancel"))
        btn_cancel.callback = self.on_cancel
        
        self.add_item(btn_confirm)
        self.add_item(btn_cancel)

    async def on_confirm(self, interaction: discord.Interaction):
        try:
            await interaction.response.edit_message(embed=create_info_splash(TicketEmoji.text("lock", "Đang xử lý..."), "Hệ thống đang lưu trữ và đóng vé..."), view=None)
        except discord.HTTPException:
            pass
        await self.confirm_cb(interaction, self.reason)

    async def on_cancel(self, interaction: discord.Interaction):
        try:
            await interaction.response.edit_message(embed=create_info_splash(TicketEmoji.text("cancel", "Đã Hủy"), "Thao tác đóng vé đã bị hủy bỏ."), view=None)
        except discord.HTTPException:
            pass
            
class EditReasonModal(Modal, title="Cập nhật lý do đóng Ticket"):
    reason_input = TextInput(
        label="Lý do mới",
        style=discord.TextStyle.paragraph,
        required=True,
        max_length=1000
    )

    async def on_submit(self, interaction: discord.Interaction):
        new_reason = self.reason_input.value.strip()
        embed = interaction.message.embeds[0]
        
        ticket_id = None
        for i, field in enumerate(embed.fields):
            if "Reason" in field.name:
                embed.set_field_at(i, name=field.name, value=new_reason, inline=field.inline)
            elif "Ticket ID" in field.name:
                ticket_id = int(field.value)
        
        await interaction.response.edit_message(embed=embed)
        
        if ticket_id:
            from services.ticket_service import TicketService
            TicketService().db.execute("UPDATE tickets SET close_reason = ? WHERE ticket_id = ?", (new_reason, ticket_id))

class TicketLogView(View):
    def __init__(self):
        super().__init__(timeout=None)
        
    @discord.ui.button(label="Sửa Lý Do", style=discord.ButtonStyle.secondary, custom_id="ticket_log_edit_reason", emoji=TicketEmoji.get("rename"))
    async def btn_edit_reason(self, interaction: discord.Interaction, button: Button):
        modal = EditReasonModal()
        for field in interaction.message.embeds[0].fields:
            if "Reason" in field.name and field.value != "No reason specified":
                modal.reason_input.default = field.value
                break
        await interaction.response.send_modal(modal)
        
def build_transcript(messages: list[discord.Message]) -> str:
    """Tạo văn bản lưu lại nội dung hội thoại gọn gàng, tinh gọn."""
    lines = [
        "==================================================",
        "              TICKET TRANSCRIPT LOG               ",
        "==================================================",
        f"Time: {discord.utils.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC",
        f"Messages: {len(messages)}",
        "=============================\n"
    ]
    for msg in reversed(messages):
        # Bỏ qua tin nhắn (ví dụ của bot) mà không có nội dung text hay đính kèm file
        if not msg.content and not msg.attachments:
            continue
            
        time_str = msg.created_at.strftime("%Y-%m-%d %H:%M")
        author = msg.author.name
        content = msg.clean_content.replace('\n', '\n    ')
        atts = " | ".join([a.url for a in msg.attachments])
        
        line = f"[{time_str}] {author}: {content}" if content else f"[{time_str}] {author}:"
        lines.append(line)
        if atts: lines.append(f"    [Files: {atts}]")
        
    return "\n".join(lines)