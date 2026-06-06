# File: cogs/ticket/ticket_cog.py
# Purpose: Xử lý logic slash commands và button callbacks của Ticket.
# Notes:
# - Sử dụng ticket_service.py để xử lý DB atomic.
# - Mọi param string channel/role/user đều đi qua cogs.ticket.resolvers.extract_discord_id.

import discord
import re
import io
import uuid
import random
import time
from discord.ext import commands
from discord import app_commands

from ui.ticket.emoji import TicketEmoji
from ui.ticket.components import TicketPanelButtonsView, TicketCreateSelectView, TicketControlView, TicketCloseConfirmView, build_transcript
from ui.ticket.manager_ui import TicketManagerMenu, build_manager_embed
from ui.ticket.staff_ui import StaffManageMenu
from services.ticket_service import TicketService
from cogs.ticket.resolvers import extract_discord_id
from cogs.ticket.permissions import is_ticket_staff, is_ticket_admin, can_manage_ticket, can_view_ticket_info
from cogs.ticket.interaction_utils import defer_if_needed, safe_send
from utils import create_error_splash, create_success_splash, create_info_splash
import logging

logger = logging.getLogger(__name__)

TICKET_TYPE_SLUGS = {
    "support": "support", "bug": "bug", "report": "report", "payment": "payment", "contact_admin": "admin"
}

TICKET_TYPE_LABELS = {
    "support": "Hỗ trợ chung", "bug": "Báo lỗi", "report": "Tố cáo", "payment": "Thanh toán", "contact_admin": "Liên hệ Admin", "admin": "Liên hệ Admin"
}

def make_ticket_code() -> str:
    code = uuid.uuid4().hex[:6]
    return code

def build_ticket_channel_name(ticket_code: str) -> str:
    code = re.sub(r"[^a-zA-Z0-9]", "", str(ticket_code)).lower()[:8]
    if not code: code = make_ticket_code()
    return f"ticket-{code}"[:95]

class ContextAdapter:
    """Adapter thống nhất interface giữa commands.Context (Prefix) và discord.Interaction (Slash)."""
    def __init__(self, obj):
        self.is_interaction = isinstance(obj, discord.Interaction)
        self.obj = obj
        self.guild = obj.guild
        self.channel = obj.channel
        self.user = obj.user if self.is_interaction else obj.author

    async def send(self, *args, **kwargs):
        if self.is_interaction:
            if self.obj.response.is_done():
                return await self.obj.followup.send(*args, **kwargs)
            else:
                # discord.py Interaction.response.send_message không trả về message object ngay
                await self.obj.response.send_message(*args, **kwargs)
                return await self.obj.original_response()
        else:
            if 'ephemeral' in kwargs:
                del kwargs['ephemeral'] # Prefix không có ephemeral
            return await self.obj.send(*args, **kwargs)

class TicketCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.service = TicketService()
        self.bot.add_view(TicketPanelButtonsView(self))
        self.bot.add_view(TicketControlView(self.handle_claim_ticket, self.handle_request_close, self.handle_manage_open))
        from ui.ticket.components import TicketLogView
        self.bot.add_view(TicketLogView())

    # --- SLASH GROUP ---
    ticket_group = app_commands.Group(name="ticket", description="Quản lý hệ thống Ticket")

    @ticket_group.command(name="manager", description="Mở bảng điều khiển cấu hình Ticket (Luôn hiển thị Public)")
    @app_commands.default_permissions(administrator=True)
    async def ticket_manager_slash(self, interaction: discord.Interaction):
        config = self.service.ensure_config(interaction.guild.id)
        await safe_send(interaction, embed=build_manager_embed(self.service, config, interaction.guild), view=TicketManagerMenu(self), ephemeral=False)

    @ticket_group.command(name="setup", description="(Deprecated) Chuyển hướng sang /ticket manager")
    @app_commands.default_permissions(administrator=True)
    async def setup_ticket(self, interaction: discord.Interaction):
        embed = create_info_splash(TicketEmoji.text("manage", "Hệ Thống Mới"), "Hệ thống setup mới sử dụng Ticket Manager UI.\nVui lòng sử dụng lệnh `/ticket manager` để mở giao diện quản lý.")
        await interaction.response.send_message(embed=embed, ephemeral=True)
            
    async def handle_send_or_refresh_panel(self, interaction: discord.Interaction):
        config = self.service.get_config(interaction.guild.id)
        if not config or not config.get('panel_channel_id') or not config.get('ticket_category_id'):
            await interaction.response.send_message(embed=create_error_splash(TicketEmoji.text("error", "Thiếu Cấu Hình"), "Cần chọn ít nhất Kênh Panel và Category Mở Vé."), ephemeral=True)
            return
        
        channel = interaction.guild.get_channel(int(config['panel_channel_id']))
        if not channel:
            await interaction.response.send_message(embed=create_error_splash(TicketEmoji.text("error", "Lỗi"), "Kênh Panel không tồn tại."), ephemeral=True)
            return
            
        await defer_if_needed(interaction, ephemeral=True)
            
        embed = discord.Embed(
            title=TicketEmoji.text('ticket', "TRUNG TÂM HỖ TRỢ"),
            description=f"Bấm vào nút **Mở Ticket Mới** bên dưới để tạo yêu cầu hỗ trợ.\nStaff sẽ phản hồi bạn trong thời gian sớm nhất.\n\nGiới hạn: `{config.get('max_open_tickets', 1)} vé/người`.",
            color=discord.Color.blue()
        )
        
        msg_id = config.get('panel_message_id')
        if msg_id:
            try:
                msg = await channel.fetch_message(int(msg_id))
                await msg.edit(embed=embed, view=TicketPanelButtonsView(self))
                await safe_send(interaction, embed=create_success_splash(TicketEmoji.text("success", "Refresh"), "Đã refresh Panel hiện tại."), ephemeral=True)
                return
            except discord.NotFound:
                pass # Fallback to send new
                
        new_msg = await channel.send(embed=embed, view=TicketPanelButtonsView(self))
        self.service.update_single_config(interaction.guild.id, 'panel_message_id', new_msg.id)
        await safe_send(interaction, embed=create_success_splash(TicketEmoji.text("success", "Đã Gửi"), "Đã gửi Panel mới."), ephemeral=True)

    async def handle_panel_open_click(self, interaction: discord.Interaction):
        embed = create_info_splash(TicketEmoji.text("ticket", "Chọn Hạng Mục"), "Vui lòng chọn loại yêu cầu bạn cần hỗ trợ từ danh sách bên dưới:")
        await interaction.response.send_message(embed=embed, view=TicketCreateSelectView(self.handle_ticket_type_selected), ephemeral=True)

    async def handle_panel_instructions_click(self, interaction: discord.Interaction):
        embed = discord.Embed(title=TicketEmoji.text("log", "Hướng Dẫn Hệ Thống Ticket"), color=discord.Color.blue())
        embed.description = "1. Bấm nút **Mở Ticket Mới** ở bảng điều khiển.\n2. Chọn một hạng mục phù hợp với vấn đề của bạn.\n3. Xác nhận và đợi bot tạo kênh.\n4. Trình bày vấn đề thật chi tiết, có kèm hình ảnh nếu có trong kênh vừa tạo."
        await interaction.response.send_message(embed=embed, ephemeral=True)

    async def handle_ticket_type_selected(self, interaction: discord.Interaction, ticket_type: str):
        from ui.ticket.components import TicketCreateConfirmView
        embed = create_info_splash(TicketEmoji.text("ticket", "Xác nhận tạo vé"), f"Bạn đang chuẩn bị mở một ticket hỗ trợ về hạng mục: **{ticket_type.upper()}**.\nBạn có chắc chắn muốn mở vé không?")
        # Do chúng ta đang ở trong tin nhắn ẩn (ephemeral) từ Dropdown, ta update luôn nó!
        await interaction.response.edit_message(embed=embed, view=TicketCreateConfirmView(self, ticket_type, interaction.user.id))

    async def handle_create_ticket_confirmed(self, interaction: discord.Interaction, ticket_type: str):
        start = time.perf_counter()
        logger.info("[TICKET_CREATE] confirm_start guild=%s user=%s type=%s", interaction.guild.id, interaction.user.id, ticket_type)
        
        config = self.service.get_config(interaction.guild.id)
        if not config:
            await safe_send(interaction, embed=create_error_splash(TicketEmoji.text("error", "Lỗi Cấu Hình"), "Server chưa cài đặt hệ thống ticket hoàn chỉnh."), ephemeral=True)
            return
            
        # Kiểm tra max active tickets
        active_tickets = self.service.get_user_active_tickets(interaction.guild.id, interaction.user.id)
        max_allowed = int(config.get('max_open_tickets', 1))
        if len(active_tickets) >= max_allowed:
            await safe_send(interaction, embed=create_error_splash(TicketEmoji.text("error", "Vượt Giới Hạn"), "Bạn đang có Ticket chưa đóng. Vui lòng đóng trước khi mở thêm."), ephemeral=True)
            return
            
        # Kiểm tra cooldown
        cooldown = self.service.get_cooldown(interaction.guild.id, interaction.user.id, int(config.get('cooldown_seconds', 60)))
        if cooldown > 0:
            await safe_send(interaction, embed=create_error_splash(TicketEmoji.text("error", "Thao Tác Quá Nhanh"), f"Vui lòng chờ {cooldown}s trước khi tạo vé mới."), ephemeral=True)
            return
            
        # Khởi tạo Category
        category = interaction.guild.get_channel(int(config['ticket_category_id']))
        if not category or not isinstance(category, discord.CategoryChannel):
            await safe_send(interaction, embed=create_error_splash(TicketEmoji.text("error", "Lỗi Category"), "Ticket Category bị lỗi hoặc không tồn tại."), ephemeral=True)
            return
            
        # Phân quyền cho nhiều Staff Roles
        staff_configs = self.service.get_staff_roles_for_type(interaction.guild.id, ticket_type)
        staff_role_ids = {r['role_id'] for r in staff_configs}
        
        overwrites = {
            interaction.guild.default_role: discord.PermissionOverwrite(view_channel=False, read_messages=False),
            interaction.user: discord.PermissionOverwrite(view_channel=True, read_messages=True, send_messages=True, attach_files=True),
            interaction.guild.me: discord.PermissionOverwrite(view_channel=True, read_messages=True, send_messages=True, manage_channels=True, manage_permissions=True)
        }
        
        ping_roles = []
        for r_id in staff_role_ids:
            role = interaction.guild.get_role(r_id)
            if role:
                overwrites[role] = discord.PermissionOverwrite(view_channel=True, read_messages=True, send_messages=True, manage_messages=True)
                ping_roles.append(role.mention)
                
        ticket_code = make_ticket_code()
        channel_name = build_ticket_channel_name(ticket_code)
        
        try:
            ticket_channel = await interaction.guild.create_text_channel(
                name=channel_name,
                category=category,
                overwrites=overwrites
            )
        except discord.Forbidden:
            await safe_send(interaction, embed=create_error_splash(TicketEmoji.text("error", "Thiếu Quyền Bot"), "Bot không có quyền tạo kênh!"), ephemeral=True)
            return
            
        # Ghi DB + Rollback channel nếu lỗi
        try:
            self.service.create_ticket(interaction.guild.id, ticket_channel.id, interaction.user.id, ticket_type, ticket_code)
        except Exception as e:
            logger.exception("[TICKET_CREATE] DB Insert Failed")
            await ticket_channel.delete(reason="DB Insert Failed")
            await safe_send(interaction, embed=create_error_splash(TicketEmoji.text("error", "Lỗi Hệ Thống"), "Không thể ghi dữ liệu ticket. Vui lòng thử lại sau."), ephemeral=True)
            return
        
        # Gửi lời chào
        embed = discord.Embed(
            title=TicketEmoji.text("ticket", f"Ticket: {ticket_type.capitalize()}"),
            description=f"Xin chào {interaction.user.mention},\nStaff sẽ sớm có mặt để hỗ trợ bạn. Vui lòng mô tả chi tiết vấn đề.",
            color=discord.Color.green()
        )
        pings = " ".join(ping_roles)
        await ticket_channel.send(content=f"{interaction.user.mention} {pings}", embed=embed, view=TicketControlView(self.handle_claim_ticket, self.handle_request_close, self.handle_manage_open))
        logger.info("[TICKET_CREATE] phase=ticket_embed_sent elapsed=%.3fs", time.perf_counter() - start)
        await safe_send(interaction, content=TicketEmoji.text("success", f"Đã tạo ticket: {ticket_channel.mention}"), ephemeral=True)
        logger.info("[TICKET_CREATE] success channel=%s total_time=%.3fs", ticket_channel.id, time.perf_counter() - start)

    async def handle_claim_ticket(self, interaction: discord.Interaction):
        await defer_if_needed(interaction, ephemeral=True)
        config = self.service.get_config(interaction.guild.id)
        
        if not can_manage_ticket(interaction.user, {}, config):
            await safe_send(interaction, embed=create_error_splash(TicketEmoji.text("error", "Từ Chối"), "Bạn không có quyền Claim vé này!"), ephemeral=True)
            return
            
        if self.service.claim_ticket(interaction.channel.id, interaction.user.id, interaction.user.display_name):
            ticket = self.service.get_ticket(interaction.channel.id)
            self.service.log_event(ticket['ticket_id'], interaction.guild.id, interaction.channel.id, 'claimed', interaction.user.id)
            await safe_send(interaction, embed=create_success_splash(TicketEmoji.text("claim", "Đã Nhận"), f"Vé này đã được claim bởi {interaction.user.mention}."), ephemeral=False)
        else:
            await safe_send(interaction, embed=create_error_splash(TicketEmoji.text("error", "Không Thể Nhận"), "Vé đã có người claim hoặc đã đóng."), ephemeral=True)

    async def handle_manage_open(self, interaction: discord.Interaction):
        config = self.service.get_config(interaction.guild.id)
        if not can_manage_ticket(interaction.user, {}, config):
            await safe_send(interaction, embed=create_error_splash(TicketEmoji.text("error", "Từ Chối"), "Chỉ Staff mới có thể mở menu quản lý."), ephemeral=True)
            return
        await safe_send(interaction, content="Bảng điều khiển Staff:", view=StaffManageMenu(self), ephemeral=True)

    # --- PREFIX GROUP ---
    # Lưu ý: Các slash command lẻ của staff đã bị loại bỏ để giảm rác command menu.
    # Tuy nhiên, ta giữ lại command prefix nội bộ cho admin xài hardcode nếu thích.
    @commands.group(name="ticket", invoke_without_command=True)
    async def ticket_prefix(self, ctx):
        await ctx.send(embed=create_info_splash(TicketEmoji.text("ticket", "Lệnh Ticket"), "Dùng `!ticket add`, `!ticket remove`, `!ticket rename`, `!ticket info`, `!ticket transfer`, `!ticket unclaim`, `!ticket close`."))

    @ticket_prefix.command(name="add")
    async def ticket_add_prefix(self, ctx, user: discord.Member):
        await self._core_ticket_add(ContextAdapter(ctx), user)

    @ticket_prefix.command(name="remove", aliases=["rm"])
    async def ticket_remove_prefix(self, ctx, user: discord.Member):
        await self._core_ticket_remove(ContextAdapter(ctx), user)

    @ticket_prefix.command(name="rename")
    async def ticket_rename_prefix(self, ctx, *, new_name: str):
        await self._core_ticket_rename(ContextAdapter(ctx), new_name)

    @ticket_prefix.command(name="transfer")
    async def ticket_transfer_prefix(self, ctx, staff: discord.Member):
        await self._core_ticket_transfer(ContextAdapter(ctx), staff)

    @ticket_prefix.command(name="unclaim")
    async def ticket_unclaim_prefix(self, ctx):
        await self._core_ticket_unclaim(ContextAdapter(ctx))

    @ticket_prefix.command(name="info")
    async def ticket_info_prefix(self, ctx):
        await self._core_ticket_info(ContextAdapter(ctx))

    @ticket_prefix.command(name="close")
    async def ticket_close_prefix(self, ctx, *, reason: str = ""):
        await self._core_ticket_close_request(ContextAdapter(ctx), reason)

    # --- UI ADAPTER HOOKS (Dùng cho Modal / Component Callback) ---
    async def adapter_trigger_add(self, interaction, user): await self._core_ticket_add(ContextAdapter(interaction), user)
    async def adapter_trigger_remove(self, interaction, user): await self._core_ticket_remove(ContextAdapter(interaction), user)
    async def adapter_trigger_rename(self, interaction, name): await self._core_ticket_rename(ContextAdapter(interaction), name)
    async def adapter_trigger_transfer(self, interaction, staff): await self._core_ticket_transfer(ContextAdapter(interaction), staff)
    async def adapter_trigger_unclaim(self, interaction): await self._core_ticket_unclaim(ContextAdapter(interaction))
    async def adapter_trigger_info(self, interaction): await self._core_ticket_info(ContextAdapter(interaction))

    # --- CORE BUSINESS LOGIC (Adapter Pattern) ---
    def _sanitize_ticket_name(self, ticket_id: int, raw_name: str) -> str:
        safe = re.sub(r'[^a-zA-Z0-9_-]', '', raw_name.lower().replace(' ', '-'))
        safe = safe.strip('-')
        if not safe:
            return f"ticket-{ticket_id}"
        return f"ticket-{ticket_id}-{safe}"[:90]

    async def _verify_ticket_context(self, adapter: ContextAdapter, check_staff: bool = True):
        if not adapter.guild or not adapter.channel:
            return None, None
        ticket = self.service.get_ticket(adapter.channel.id)
        if not ticket or ticket['guild_id'] != adapter.guild.id or ticket['status'] in ('closing', 'closed', 'archived'):
            await adapter.send(embed=create_error_splash(TicketEmoji.text("error", "Lỗi"), "Kênh này không phải là Ticket đang mở."), ephemeral=True)
            return None, None
        
        config = self.service.get_config(adapter.guild.id)
        if check_staff and not can_manage_ticket(adapter.user, ticket, config):
            await adapter.send(embed=create_error_splash(TicketEmoji.text("error", "Lỗi Quyền"), "Bạn không có quyền thực hiện thao tác này."), ephemeral=True)
            return None, None
            
        return ticket, config

    async def _core_ticket_add(self, adapter: ContextAdapter, target_user: discord.Member):
        ticket, config = await self._verify_ticket_context(adapter, check_staff=True)
        if not ticket: return
        
        if target_user.bot or target_user.id == int(ticket['owner_user_id']):
            await adapter.send(embed=create_error_splash(TicketEmoji.text("error", "Từ chối"), "Không thể thêm Bot hoặc Chủ vé."), ephemeral=True)
            return
            
        perms = adapter.channel.overwrites_for(target_user)
        if perms.read_messages is True:
            await adapter.send(embed=create_error_splash(TicketEmoji.text("error", "Lỗi"), "Người dùng này đã có trong ticket."), ephemeral=True)
            return
            
        try:
            await adapter.channel.set_permissions(target_user, view_channel=True, read_messages=True, send_messages=True, attach_files=True, read_message_history=True)
            self.service.log_event(ticket['ticket_id'], adapter.guild.id, adapter.channel.id, 'user_added', adapter.user.id, target_user.id)
            await adapter.send(embed=create_success_splash(TicketEmoji.text("add_user", "Đã Thêm"), TicketEmoji.text("success", f"Đã thêm user {target_user.mention} vào ticket.")))
        except discord.Forbidden:
            await adapter.send(embed=create_error_splash(TicketEmoji.text("error", "Lỗi Quyền Bot"), "Bot không đủ quyền để set permissions."), ephemeral=True)
        except discord.HTTPException:
            pass

    async def _core_ticket_remove(self, adapter: ContextAdapter, target_user: discord.Member):
        ticket, config = await self._verify_ticket_context(adapter, check_staff=True)
        if not ticket: return
        
        if target_user.id == int(ticket['owner_user_id']):
            await adapter.send(embed=create_error_splash(TicketEmoji.text("error", "Từ chối"), "Không thể xóa Chủ Vé ra khỏi Ticket."), ephemeral=True)
            return
            
        if is_ticket_staff(target_user, config) or target_user.bot:
            await adapter.send(embed=create_error_splash(TicketEmoji.text("error", "Từ chối"), "Không thể xóa Staff hoặc Bot khỏi Ticket."), ephemeral=True)
            return

        perms = adapter.channel.overwrites_for(target_user)
        if perms.is_empty():
            await adapter.send(embed=create_error_splash(TicketEmoji.text("error", "Lỗi"), "Người dùng này không nằm trong ticket overwrite."), ephemeral=True)
            return
            
        try:
            await adapter.channel.set_permissions(target_user, overwrite=None)
            self.service.log_event(ticket['ticket_id'], adapter.guild.id, adapter.channel.id, 'user_removed', adapter.user.id, target_user.id)
            await adapter.send(embed=create_success_splash(TicketEmoji.text("remove_user", "Đã Xóa"), TicketEmoji.text("success", f"Đã xóa user {target_user.mention} khỏi ticket.")))
        except discord.HTTPException:
            await adapter.send(embed=create_error_splash(TicketEmoji.text("error", "Lỗi API"), "Discord API từ chối thao tác này."), ephemeral=True)

    async def _core_ticket_rename(self, adapter: ContextAdapter, new_name: str):
        ticket, config = await self._verify_ticket_context(adapter, check_staff=True)
        if not ticket: return
        
        final_name = self._sanitize_ticket_name(ticket['ticket_id'], new_name)
        try:
            await adapter.channel.edit(name=final_name, reason=f"Renamed by {adapter.user}")
            self.service.log_event(ticket['ticket_id'], adapter.guild.id, adapter.channel.id, 'renamed', adapter.user.id, message=final_name)
            await adapter.send(embed=create_success_splash(TicketEmoji.text("rename", "Đổi Tên"), TicketEmoji.text("success", f"Đã đổi tên kênh thành `{final_name}`.")))
        except discord.HTTPException:
            await adapter.send(embed=create_error_splash(TicketEmoji.text("error", "Lỗi API"), "Discord từ chối đổi tên kênh (có thể do rate limit)."), ephemeral=True)

    async def _core_ticket_transfer(self, adapter: ContextAdapter, target_staff: discord.Member):
        ticket, config = await self._verify_ticket_context(adapter, check_staff=True)
        if not ticket: return
        
        if target_staff.bot or not can_manage_ticket(target_staff, ticket, config):
            await adapter.send(embed=create_error_splash(TicketEmoji.text("error", "Từ chối"), "Người nhận phải có role Staff hoặc Admin và không phải Bot."), ephemeral=True)
            return
            
        if target_staff.id == ticket.get('claimed_by_user_id'):
            await adapter.send(embed=create_error_splash(TicketEmoji.text("error", "Lỗi"), "Người này đang là claimer hiện tại."), ephemeral=True)
            return
            
        if self.service.transfer_ticket(adapter.channel.id, target_staff.id, target_staff.display_name):
            self.service.log_event(ticket['ticket_id'], adapter.guild.id, adapter.channel.id, 'transferred', adapter.user.id, target_staff.id)
            await adapter.send(embed=create_success_splash(TicketEmoji.text("staff", "Chuyển Tiếp"), TicketEmoji.text("success", f"Ticket đã được chuyển giao cho {target_staff.mention}.")))
        else:
            await adapter.send(embed=create_error_splash(TicketEmoji.text("error", "Lỗi DB"), "Không thể cập nhật chuyển giao vào cơ sở dữ liệu."), ephemeral=True)

    async def _core_ticket_unclaim(self, adapter: ContextAdapter):
        ticket, config = await self._verify_ticket_context(adapter, check_staff=True)
        if not ticket: return
        
        if ticket['status'] != 'claimed':
            await adapter.send(embed=create_error_splash(TicketEmoji.text("error", "Lỗi"), "Ticket này hiện chưa có ai nhận."), ephemeral=True)
            return
            
        if ticket.get('claimed_by_user_id') != adapter.user.id and not is_ticket_admin(adapter.user):
            await adapter.send(embed=create_error_splash(TicketEmoji.text("error", "Từ chối"), "Bạn không thể gỡ Claim của người khác."), ephemeral=True)
            return
            
        if self.service.unclaim_ticket(adapter.channel.id):
            self.service.log_event(ticket['ticket_id'], adapter.guild.id, adapter.channel.id, 'unclaimed', adapter.user.id)
            await adapter.send(embed=create_success_splash(TicketEmoji.text("success", "Đã Gỡ Nhận"), "Ticket đã được chuyển về trạng thái chờ."))
        else:
            await adapter.send(embed=create_error_splash(TicketEmoji.text("error", "Lỗi DB"), "Không thể gỡ claim do lỗi DB."), ephemeral=True)

    async def _core_ticket_info(self, adapter: ContextAdapter):
        ticket, config = await self._verify_ticket_context(adapter, check_staff=False)
        if not ticket: return
        
        if not can_view_ticket_info(adapter.user, ticket, config):
            await adapter.send(embed=create_error_splash(TicketEmoji.text("error", "Lỗi Quyền"), "Bạn không có quyền xem thông tin."), ephemeral=True)
            return
            
        embed = discord.Embed(title=TicketEmoji.text("ticket", "Thông tin Ticket"), color=discord.Color.blue())
        embed.add_field(name="ID", value=f"`{ticket['ticket_id']}`", inline=True)
        embed.add_field(name="Chủ vé", value=f"<@{ticket['owner_user_id']}>", inline=True)
        embed.add_field(name="Loại", value=f"`{ticket['ticket_type']}`", inline=True)
        
        status_map = {'open': 'Đang chờ', 'claimed': 'Đang xử lý', 'closing': 'Đang đóng', 'closed': 'Đã đóng'}
        embed.add_field(name="Trạng thái", value=f"`{status_map.get(ticket['status'], ticket['status'])}`", inline=True)
        
        claimed_by = f"<@{ticket['claimed_by_user_id']}>" if ticket.get('claimed_by_user_id') else "`Chưa ai nhận`"
        embed.add_field(name="Người nhận", value=claimed_by, inline=True)
        
        await adapter.send(embed=embed)

    async def _core_ticket_close_request(self, adapter: ContextAdapter, reason: str = ""):
        # Wrapper dùng chung logic cho Button interaction (Close Ticket) và Command.
        # Nếu đến từ Slash Command, object .user sẽ có sẵn
        ticket = self.service.get_ticket(adapter.channel.id)
        if not ticket or ticket['status'] in ('closing', 'closed'):
            await adapter.send(embed=create_error_splash(TicketEmoji.text("error", "Đã Xử Lý"), "Vé không hợp lệ hoặc đang được đóng."), ephemeral=True)
            return
            
        config = self.service.get_config(adapter.guild.id)
        if not can_manage_ticket(adapter.user, ticket, config) and int(ticket['owner_user_id']) != adapter.user.id:
            await adapter.send(embed=create_error_splash(TicketEmoji.text("error", "Không Có Quyền"), "Bạn không có quyền đóng vé này."), ephemeral=True)
            return
            
        self.service.log_event(ticket['ticket_id'], adapter.guild.id, adapter.channel.id, 'close_requested', adapter.user.id, message=reason)
        embed = create_info_splash(TicketEmoji.text("confirm", "Xác Nhận"), f"Bạn có chắc chắn muốn đóng vé này?\nLý do: {reason or 'Không có'}")
        await adapter.send(embed=embed, view=TicketCloseConfirmView(self.handle_confirm_close, reason))

    # --- NATIVE UI INTERACTION CALLBACKS ---
    async def handle_request_close(self, interaction: discord.Interaction):
        await self._core_ticket_close_request(ContextAdapter(interaction), reason="")

    async def handle_confirm_close(self, interaction: discord.Interaction, reason: str):
        ticket = self.service.get_ticket(interaction.channel.id)
        if not ticket: return
        
        if not self.service.set_ticket_status(interaction.channel.id, 'closing', ['open', 'claimed']):
            await interaction.followup.send(embed=create_error_splash(TicketEmoji.text("error", "Lỗi"), "Vé đã được đóng bởi ai đó khác."), ephemeral=True)
            return
            
        # Lấy lịch sử tin nhắn
        try:
            messages = [m async for m in interaction.channel.history(limit=500)]
            transcript_text = build_transcript(messages)
        except Exception:
            transcript_text = "Lỗi không thể tải transcript."
            
        # Gửi log
        config = self.service.get_config(interaction.guild.id)
        if config and config.get('log_channel_id'):
            log_channel = interaction.guild.get_channel(int(config['log_channel_id']))
            if log_channel:
                from datetime import datetime
                try:
                    dt = datetime.strptime(ticket['created_at'], '%Y-%m-%d %H:%M:%S')
                    open_time_str = f"<t:{int(dt.timestamp())}:F>"
                except Exception:
                    open_time_str = ticket['created_at']
                    
                log_embed = discord.Embed(title="Ticket Closed", color=discord.Color.dark_grey(), timestamp=discord.utils.utcnow())
                log_embed.add_field(name=f"{TicketEmoji.get('id')} Ticket ID", value=f"{ticket['ticket_id']}", inline=False)
                log_embed.add_field(name=f"{TicketEmoji.get('open')} Opened By", value=f"<@{ticket['owner_user_id']}>", inline=True)
                log_embed.add_field(name=f"{TicketEmoji.get('close')} Closed By", value=interaction.user.mention, inline=True)
                log_embed.add_field(name=f"{TicketEmoji.get('opentime')} Open Time", value=open_time_str, inline=False)
                
                claimed_by = f"<@{ticket['claimed_by_user_id']}>" if ticket.get('claimed_by_user_id') else "Not claimed"
                log_embed.add_field(name=f"{TicketEmoji.get('claim')} Claimed By", value=claimed_by, inline=False)
                log_embed.add_field(name=f"{TicketEmoji.get('reason')} Reason", value=reason or "No reason specified", inline=False)

                file = discord.File(io.StringIO(transcript_text), filename=f"transcript-{ticket['ticket_id']}.txt")
                from ui.ticket.components import TicketLogView
                await log_channel.send(embed=log_embed, file=file, view=TicketLogView())
                
        self.service.set_ticket_status(interaction.channel.id, 'closed', ['closing'], close_reason=reason)
        self.service.log_event(ticket['ticket_id'], interaction.guild.id, interaction.channel.id, 'closed', interaction.user.id, message=reason)
        
        try:
            close_mode = config.get('close_mode', 'archive')
            archive_cat_id = config.get('archive_category_id')
            target_category = interaction.guild.get_channel(int(archive_cat_id)) if archive_cat_id else None
            
            if close_mode == 'archive' and target_category:
                overwrites = interaction.channel.overwrites
                owner = interaction.guild.get_member(int(ticket['owner_user_id']))
                if owner and owner in overwrites:
                    del overwrites[owner]
                
                await interaction.channel.edit(name=f"closed-{ticket['ticket_id']}", overwrites=overwrites, category=target_category, reason="Ticket Archived")
                self.service.log_event(ticket['ticket_id'], interaction.guild.id, interaction.channel.id, 'archived', interaction.user.id)
            else:
                await interaction.channel.delete(reason="Ticket Closed")
                self.service.log_event(ticket['ticket_id'], interaction.guild.id, interaction.channel.id, 'deleted', interaction.user.id)
                close_mode = 'delete'  # Cập nhật log chính xác nếu fallback xảy ra
            logger.info("[TICKET_CLOSE] delete_or_archive result=done mode=%s", close_mode)
        except discord.HTTPException:
            logger.exception("[TICKET_CLOSE] archive/delete HTTP exception")

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel: discord.abc.GuildChannel):
        """Bắt event khi Admin/Staff lỡ tay xoá kênh Ticket bằng chuột phải thay vì bấm nút."""
        if not isinstance(channel, discord.TextChannel): return
        ticket = self.service.get_ticket(channel.id)
        if ticket and ticket['status'] not in ('closed', 'deleted', 'archived'):
            self.service.set_ticket_status(channel.id, 'deleted', ['open', 'claimed', 'closing'], close_reason="Deleted manually from Discord")
            self.service.log_event(ticket['ticket_id'], channel.guild.id, channel.id, 'deleted_manually', getattr(self.bot.user, 'id', 0))
            logger.info("[TICKET_CLEANUP] Ticket channel %s (%s) was manually deleted. DB synced.", channel.name, channel.id)

async def setup(bot):
    await bot.add_cog(TicketCog(bot))