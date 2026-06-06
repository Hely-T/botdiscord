# File: ui/ticket/manager_ui.py
# Purpose: Giao diện quản lý cấu hình hệ thống Ticket dành cho Admin.
# Notes: Sử dụng Component Select & Modal để loại bỏ input chuỗi thủ công.

import discord
from discord.ui import View, Button, ChannelSelect, Modal, TextInput
from ui.ticket.emoji import TicketEmoji
from cogs.ticket.permissions import is_ticket_admin
from cogs.ticket.resolvers import extract_discord_id
from cogs.ticket.interaction_utils import defer_if_needed, safe_send, safe_edit_message, update_config_and_verify, safe_error
from utils import create_error_splash, create_success_splash
import logging

logger = logging.getLogger(__name__)

TICKET_TYPE_ORDER = ["all", "admin", "payment", "report", "support", "bug"]

def normalize_ticket_type_label(ticket_type: str) -> str:
    value = str(ticket_type or "all").strip().lower()
    if value == "contact_admin":
        return "admin"
    return value

def group_staff_roles_by_role_id(rows: list[dict]) -> list[dict]:
    grouped = {}
    for row in rows:
        role_id = int(row["role_id"])
        t_type = normalize_ticket_type_label(row.get("ticket_type"))
        
        if role_id not in grouped:
            grouped[role_id] = {"role_id": role_id, "types": set()}
        grouped[role_id]["types"].add(t_type)

    result = []
    for role_id, data in grouped.items():
        types = sorted(
            data["types"],
            key=lambda x: TICKET_TYPE_ORDER.index(x) if x in TICKET_TYPE_ORDER else 999,
        )
        if "all" in types:
            types = ["all"]
        result.append({"role_id": role_id, "types": types})
    return result

def build_manager_embed(svc, config: dict, guild: discord.Guild) -> discord.Embed:
    embed = discord.Embed(title=TicketEmoji.text("settings", "Ticket System Manager"), color=discord.Color.blurple())
    
    def _get_ch(id_str): return f"<#{id_str}>" if id_str else "Chưa chọn"
    
    cfg = config or {}
    embed.add_field(name="Panel Channel", value=f"{_get_ch(cfg.get('panel_channel_id'))}\n*(Kênh đặt bảng điều khiển cho user)*", inline=False)
    embed.add_field(name="Ticket Category", value=f"{_get_ch(cfg.get('ticket_category_id'))}\n*(Danh mục chứa ticket mới)*", inline=False)
    embed.add_field(name="Archive Category", value=f"{_get_ch(cfg.get('archive_category_id')) if cfg.get('archive_category_id') else 'Tắt'}\n*(Danh mục lưu ticket đã đóng)*", inline=False)
    
    roles = svc.get_staff_roles(guild.id)
    if not roles:
        role_str = "⚠️ Chưa có Role nào"
    else:
        grouped = group_staff_roles_by_role_id(roles)
        lines = []
        for item in grouped:
            role = guild.get_role(item["role_id"])
            role_text = role.mention if role else f"`Role đã mất: {item['role_id']}`"
            type_text = "/".join(item["types"])
            lines.append(f"{role_text} (`{type_text}`)")
        role_str = "\n".join(lines)
        
    embed.add_field(name="Staff Roles", value=role_str, inline=False)
    
    embed.add_field(name="Log Channel", value=_get_ch(cfg.get('log_channel_id')) if cfg.get('log_channel_id') else "Tắt", inline=True)
    embed.add_field(name="Transcript Channel", value=_get_ch(cfg.get('transcript_channel_id')) if cfg.get('transcript_channel_id') else "Dùng chung Log", inline=True)
    
    embed.add_field(name="Max Open", value=f"`{cfg.get('max_open_tickets', 1)}` vé/user", inline=True)
    embed.add_field(name="Cooldown", value=f"`{cfg.get('cooldown_seconds', 60)}s`", inline=True)
    embed.add_field(name="Close Mode", value=f"`{cfg.get('close_mode', 'archive').upper()}`", inline=True)
    
    if cfg.get('updated_at'):
        embed.set_footer(text=f"Cập nhật lần cuối: {cfg['updated_at']}")
    return embed

async def try_refresh_manager_message(cog, interaction: discord.Interaction, view: View) -> bool:
    if not getattr(interaction, "message", None):
        return False
    try:
        config = cog.service.get_config(interaction.guild.id)
        await safe_edit_message(interaction.message, content="", embed=build_manager_embed(cog.service, config, interaction.guild), view=view)
        return True
    except Exception as e:
        logger.debug("[TICKET_MANAGER] realtime refresh failed gracefully: %s", e)
        return False

class TicketManagerMenu(View):
    def __init__(self, cog):
        super().__init__(timeout=None)
        self.cog = cog

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if not is_ticket_admin(interaction.user):
            await safe_error(interaction, content=TicketEmoji.text("error", "Chỉ admin mới có quyền sử dụng menu quản lý."))
            return False
        return True

    @discord.ui.button(label="Kênh & Danh mục", style=discord.ButtonStyle.primary, emoji=TicketEmoji.get("channel"))
    async def btn_channels(self, interaction: discord.Interaction, button: Button):
        await safe_send(interaction, content=TicketEmoji.text("channel", "**Cấu hình Kênh & Danh mục Ticket:**"), view=ConfigChannelMenu(self.cog, self), ephemeral=True)

    @discord.ui.button(label="Log & Transcript", style=discord.ButtonStyle.primary, emoji=TicketEmoji.get("log"))
    async def btn_logs(self, interaction: discord.Interaction, button: Button):
        await safe_send(interaction, content=TicketEmoji.text("log", "**Cấu hình Kênh Log và Transcript:**"), view=ConfigLogMenu(self.cog, self), ephemeral=True)

    @discord.ui.button(label="Thêm Staff Role", style=discord.ButtonStyle.primary, emoji=TicketEmoji.get("role"))
    async def btn_roles(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_modal(StaffRoleAddModal(self.cog, self))

    @discord.ui.button(label="Cấu Hình Giới Hạn", style=discord.ButtonStyle.secondary, emoji=TicketEmoji.get("settings"))
    async def btn_limits(self, interaction: discord.Interaction, button: Button):
        config = self.cog.service.get_config(interaction.guild.id) or {}
        await interaction.response.send_modal(LimitConfigModal(self.cog, self, config))

    @discord.ui.button(label="Gửi / Refresh Panel", style=discord.ButtonStyle.success, emoji=TicketEmoji.get("refresh"))
    async def btn_send_panel(self, interaction: discord.Interaction, button: Button):
        await self.cog.handle_send_or_refresh_panel(interaction)
        
    @discord.ui.button(label="Xoá Staff Role", style=discord.ButtonStyle.danger, emoji=TicketEmoji.get("remove_user"))
    async def btn_remove_role(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_modal(StaffRoleRemoveModal(self.cog, self))
        
    @discord.ui.button(label="Reload Ticket DB", style=discord.ButtonStyle.secondary, emoji=TicketEmoji.get("refresh"))
    async def btn_reload_db(self, interaction: discord.Interaction, button: Button):
        await defer_if_needed(interaction, ephemeral=True, thinking=True)
        active_tickets = self.cog.service.get_all_active_tickets(interaction.guild.id)
        deleted_count = 0
        for t in active_tickets:
            channel = interaction.guild.get_channel(int(t['channel_id']))
            if not channel:
                try:
                    await interaction.guild.fetch_channel(int(t['channel_id']))
                except discord.NotFound:
                    self.cog.service.mark_ticket_deleted(int(t['channel_id']))
                    deleted_count += 1
                    logger.info("[TICKET_RELOAD] Ticket %s detected as deleted manually.", t['channel_id'])
        
        msg = f"Đã quét {len(active_tickets)} vé đang active.\nPhát hiện và xóa {deleted_count} vé bị xóa tay khỏi Database."
        await try_refresh_manager_message(self.cog, interaction, self)
        await safe_send(interaction, embed=create_success_splash(TicketEmoji.text("success", "Resync Database"), msg), ephemeral=True)

class ConfigChannelMenu(View):
    def __init__(self, cog, parent_menu):
        super().__init__(timeout=None)
        self.cog = cog
        self.parent_menu = parent_menu

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if not is_ticket_admin(interaction.user):
            await safe_error(interaction, content=TicketEmoji.text("error", "Chỉ admin mới có quyền sử dụng menu quản lý."))
            return False
        return True

    @discord.ui.select(cls=ChannelSelect, channel_types=[discord.ChannelType.text], placeholder="Chọn Kênh Panel...")
    async def select_panel(self, interaction: discord.Interaction, select: ChannelSelect):
        action = "select_panel_channel"
        await defer_if_needed(interaction, ephemeral=True, thinking=True)
        try:
            selected_id = select.values[0].id
            resolved_channel = interaction.guild.get_channel(selected_id)
            if not resolved_channel or resolved_channel.type != discord.ChannelType.text:
                await safe_error(interaction, embed=create_error_splash(TicketEmoji.text("error", "Sai Loại Kênh"), "Kênh Panel phải là kênh Text."))
                return
            ok, after = await update_config_and_verify(self.cog, interaction, key='panel_channel_id', value=resolved_channel.id, action=action)
            if not ok: return
            await try_refresh_manager_message(self.cog, interaction, self.parent_menu)
            await safe_send(interaction, embed=create_success_splash(TicketEmoji.text("success", "Đã Lưu"), f"Kênh Panel được cập nhật thành: {resolved_channel.mention}"), ephemeral=True)
        except Exception:
            logger.exception("[TICKET_UI] callback failed action=%s", action)
            await safe_error(interaction, embed=create_error_splash(TicketEmoji.text("error", "Lỗi Runtime"), "Callback bị lỗi. Xem log console."))

    @discord.ui.select(cls=ChannelSelect, channel_types=[discord.ChannelType.category], placeholder="Chọn Danh Mục chứa ticket mới...")
    async def select_category(self, interaction: discord.Interaction, select: ChannelSelect):
        action = "select_ticket_category"
        await defer_if_needed(interaction, ephemeral=True, thinking=True)
        try:
            selected_id = select.values[0].id
            resolved_channel = interaction.guild.get_channel(selected_id)
            if not resolved_channel or resolved_channel.type != discord.ChannelType.category:
                await safe_error(interaction, embed=create_error_splash(TicketEmoji.text("error", "Sai Loại Kênh"), "Bạn phải chọn một Danh Mục (Category), không phải kênh Text/Voice."))
                return
            ok, after = await update_config_and_verify(self.cog, interaction, key='ticket_category_id', value=resolved_channel.id, action=action)
            if not ok: return
            await try_refresh_manager_message(self.cog, interaction, self.parent_menu)
            await safe_send(interaction, embed=create_success_splash(TicketEmoji.text("success", "Đã Lưu"), f"Danh mục chứa ticket mới được cập nhật thành: `{resolved_channel.name}`"), ephemeral=True)
        except Exception:
            logger.exception("[TICKET_UI] callback failed action=%s", action)
            await safe_error(interaction, embed=create_error_splash(TicketEmoji.text("error", "Lỗi Runtime"), "Callback bị lỗi. Xem log console."))
        
    @discord.ui.select(cls=ChannelSelect, channel_types=[discord.ChannelType.category], placeholder="Chọn Danh Mục lưu ticket đã đóng...")
    async def select_archive(self, interaction: discord.Interaction, select: ChannelSelect):
        action = "select_archive_category"
        await defer_if_needed(interaction, ephemeral=True, thinking=True)
        try:
            selected_id = select.values[0].id
            resolved_channel = interaction.guild.get_channel(selected_id)
            if not resolved_channel or resolved_channel.type != discord.ChannelType.category:
                await safe_error(interaction, embed=create_error_splash(TicketEmoji.text("error", "Sai Loại Kênh"), "Bạn phải chọn một Danh Mục (Category)."))
                return
            ok, after = await update_config_and_verify(self.cog, interaction, key='archive_category_id', value=resolved_channel.id, action=action)
            if not ok: return
            self.cog.service.update_single_config(interaction.guild.id, 'close_mode', 'archive')
            await try_refresh_manager_message(self.cog, interaction, self.parent_menu)
            await safe_send(interaction, embed=create_success_splash(TicketEmoji.text("success", "Đã Lưu"), f"Danh mục lưu trữ cập nhật thành: `{resolved_channel.name}`"), ephemeral=True)
        except Exception:
            logger.exception("[TICKET_UI] callback failed action=%s", action)
            await safe_error(interaction, embed=create_error_splash(TicketEmoji.text("error", "Lỗi Runtime"), "Callback bị lỗi. Xem log console."))

    @discord.ui.button(label="Tắt Archive", style=discord.ButtonStyle.danger, emoji=TicketEmoji.get("disable_archive"))
    async def btn_disable_archive(self, interaction: discord.Interaction, button: Button):
        action = "disable_archive_category"
        await defer_if_needed(interaction, ephemeral=True, thinking=True)
        try:
            ok, after = await update_config_and_verify(self.cog, interaction, key='archive_category_id', value=None, action=action)
            if not ok: return
            self.cog.service.update_single_config(interaction.guild.id, 'close_mode', 'delete')
            await try_refresh_manager_message(self.cog, interaction, self.parent_menu)
            await safe_send(interaction, embed=create_success_splash(TicketEmoji.text("success", "Đã Lưu"), "Đã tắt Archive Category."), ephemeral=True)
        except Exception:
            logger.exception("[TICKET_UI] callback failed action=%s", action)
            await safe_error(interaction, embed=create_error_splash(TicketEmoji.text("error", "Lỗi Runtime"), "Callback bị lỗi."))

class ConfigLogMenu(View):
    def __init__(self, cog, parent_menu):
        super().__init__(timeout=None)
        self.cog = cog
        self.parent_menu = parent_menu

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if not is_ticket_admin(interaction.user):
            await safe_error(interaction, content=TicketEmoji.text("error", "Chỉ admin mới có quyền sử dụng menu quản lý."))
            return False
        return True
        
    @discord.ui.select(cls=ChannelSelect, channel_types=[discord.ChannelType.text], placeholder="Chọn Kênh Log...")
    async def select_log(self, interaction: discord.Interaction, select: ChannelSelect):
        action = "select_log_channel"
        await defer_if_needed(interaction, ephemeral=True, thinking=True)
        try:
            selected_id = select.values[0].id
            resolved_channel = interaction.guild.get_channel(selected_id)
            if not resolved_channel or resolved_channel.type != discord.ChannelType.text:
                await safe_error(interaction, embed=create_error_splash(TicketEmoji.text("error", "Sai Loại Kênh"), "Kênh Log phải là một kênh Text."))
                return
            ok, after = await update_config_and_verify(self.cog, interaction, key='log_channel_id', value=resolved_channel.id, action=action)
            if not ok: return
            await try_refresh_manager_message(self.cog, interaction, self.parent_menu)
            await safe_send(interaction, embed=create_success_splash(TicketEmoji.text("success", "Đã Lưu"), f"Đã cập nhật kênh Log thành: {resolved_channel.mention}"), ephemeral=True)
        except Exception:
            logger.exception("[TICKET_UI] callback failed action=%s", action)
            await safe_error(interaction, embed=create_error_splash(TicketEmoji.text("error", "Lỗi Runtime"), "Callback bị lỗi."))

    @discord.ui.button(label="Dán ID Kênh Log", style=discord.ButtonStyle.secondary, emoji=TicketEmoji.get("paste_id"))
    async def btn_paste_log_id(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_modal(LogIdModal(self.cog, self.parent_menu))

    @discord.ui.button(label="Tắt Kênh Log", style=discord.ButtonStyle.danger, emoji=TicketEmoji.get("disable_log"))
    async def btn_disable_log(self, interaction: discord.Interaction, button: Button):
        action = "disable_log_channel"
        await defer_if_needed(interaction, ephemeral=True, thinking=True)
        try:
            ok, after = await update_config_and_verify(self.cog, interaction, key='log_channel_id', value=None, action=action)
            if not ok: return
            await try_refresh_manager_message(self.cog, interaction, self.parent_menu)
            await safe_send(interaction, embed=create_success_splash(TicketEmoji.text("success", "Đã Lưu"), "Đã tắt Kênh Log."), ephemeral=True)
        except Exception:
            logger.exception("[TICKET_UI] callback failed action=%s", action)
            await safe_error(interaction, embed=create_error_splash(TicketEmoji.text("error", "Lỗi Runtime"), "Callback bị lỗi."))

class StaffRoleAddModal(Modal, title="Thêm Staff Role"):
    def __init__(self, cog, parent_menu):
        super().__init__()
        self.cog = cog
        self.parent_menu = parent_menu
        self.role_id = TextInput(label="Staff Role ID", placeholder="Dán ID role, ví dụ: 123456789012345678", required=True, max_length=25)
        self.ticket_type = TextInput(label="Loại (all/payment/bug/report/support/admin)", default="all", required=True, max_length=15)
        self.add_item(self.role_id)
        self.add_item(self.ticket_type)

    async def on_submit(self, interaction: discord.Interaction):
        action = "submit_staff_role_id"
        await defer_if_needed(interaction, ephemeral=True, thinking=True)
        try:
            raw = str(self.role_id.value).strip()
            if not raw.isdigit():
                await safe_error(interaction, embed=create_error_splash(TicketEmoji.text("error", "ID Không Hợp Lệ"), "Staff Role ID phải là chuỗi số."))
                return
            role = interaction.guild.get_role(int(raw))
            if role is None:
                await safe_error(interaction, embed=create_error_splash(TicketEmoji.text("error", "Không Tìm Thấy"), "Role ID này không tồn tại trong server."))
                return
            if role.id == interaction.guild.default_role.id:
                await safe_error(interaction, embed=create_error_splash(TicketEmoji.text("error", "Không Hợp Lệ"), "Không thể chọn @everyone làm Staff Role."))
                return
                
            ttype = self.ticket_type.value.strip().lower()
            valid_types = ['all', 'payment', 'bug', 'report', 'support', 'admin']
            if ttype not in valid_types:
                await safe_error(interaction, embed=create_error_splash(TicketEmoji.text("error", "Sai Loại"), "Ticket type không hợp lệ."))
                return
                
            ok = self.cog.service.add_staff_role(interaction.guild.id, role.id, ttype)
            if ok:
                logger.info("[TICKET_STAFF_ROLE] added guild=%s role=%s type=%s", interaction.guild.id, role.id, ttype)
                await try_refresh_manager_message(self.cog, interaction, self.parent_menu)
                await safe_send(interaction, embed=create_success_splash(TicketEmoji.text("success", "Đã Thêm"), f"Đã thêm Staff Role: {role.mention} (Loại: {ttype})"), ephemeral=True)
            else:
                await safe_error(interaction, embed=create_error_splash(TicketEmoji.text("error", "Lỗi DB"), "Role này đã có quyền này rồi hoặc lỗi Database."))
        except Exception:
            logger.exception("[TICKET_UI] callback failed action=%s", action)
            await safe_error(interaction, embed=create_error_splash(TicketEmoji.text("error", "Lỗi Runtime"), "Không thể lưu Staff Role."))
            
class StaffRoleRemoveModal(Modal, title="Xoá Staff Role"):
    def __init__(self, cog, parent_menu):
        super().__init__()
        self.cog = cog
        self.parent_menu = parent_menu
        self.role_id = TextInput(label="Staff Role ID", placeholder="Dán ID role cần xoá...", required=True, max_length=25)
        self.ticket_type = TextInput(label="Loại cần xoá (như lúc add)", default="all", required=True, max_length=15)
        self.add_item(self.role_id)
        self.add_item(self.ticket_type)

    async def on_submit(self, interaction: discord.Interaction):
        await defer_if_needed(interaction, ephemeral=True, thinking=True)
        raw = str(self.role_id.value).strip()
        if not raw.isdigit(): return
        ok = self.cog.service.remove_staff_role(interaction.guild.id, int(raw), self.ticket_type.value.strip().lower())
        if ok:
            await try_refresh_manager_message(self.cog, interaction, self.parent_menu)
            await safe_send(interaction, embed=create_success_splash(TicketEmoji.text("success", "Đã Xóa"), f"Đã xóa cấu hình role <@&{raw}>."), ephemeral=True)
        else:
            await safe_error(interaction, embed=create_error_splash(TicketEmoji.text("error", "Lỗi"), "Không tìm thấy cấu hình này trong DB."))

class LogIdModal(Modal, title="Dán ID kênh Log"):
    def __init__(self, cog, parent_menu):
        super().__init__()
        self.cog = cog
        self.parent_menu = parent_menu
        
        self.inp_log = TextInput(label="Log Channel ID (Nhập 0 để tắt)", required=True, placeholder="VD: 123456789012345678")
        self.add_item(self.inp_log)

    async def on_submit(self, interaction: discord.Interaction):
        action = "submit_log_id"
        await defer_if_needed(interaction, ephemeral=True, thinking=True)
        try:
            log_val = self.inp_log.value.strip()
            
            if log_val == "0":
                ok, after = await update_config_and_verify(self.cog, interaction, key='log_channel_id', value=None, action=action)
                if ok: 
                    await try_refresh_manager_message(self.cog, interaction, self.parent_menu)
                    await safe_send(interaction, embed=create_success_splash(TicketEmoji.text("success", "Đã Tắt"), "Hệ thống kênh Log đã được tắt."), ephemeral=True)
                return
                
            log_id = extract_discord_id(log_val)
            if not log_id:
                await safe_error(interaction, embed=create_error_splash(TicketEmoji.text("error", "Lỗi ID"), "ID kênh không hợp lệ."))
                return
                
            channel = interaction.guild.get_channel(log_id)
            if not channel or not isinstance(channel, discord.TextChannel):
                await safe_error(interaction, embed=create_error_splash(TicketEmoji.text("error", "Lỗi Kênh"), "Kênh không tồn tại hoặc không phải Text Channel."))
                return
                
            ok, after = await update_config_and_verify(self.cog, interaction, key='log_channel_id', value=log_id, action=action)
            if ok: 
                await try_refresh_manager_message(self.cog, interaction, self.parent_menu)
                await safe_send(interaction, embed=create_success_splash(TicketEmoji.text("success", "Đã Lưu"), f"Đã cập nhật kênh Log thành <#{log_id}>."), ephemeral=True)
        except Exception:
            logger.exception("[TICKET_UI] callback failed action=%s", action)
            await safe_error(interaction, embed=create_error_splash(TicketEmoji.text("error", "Lỗi Runtime"), "Không thể lưu kênh Log."))

class LimitConfigModal(Modal, title="Cấu hình giới hạn & chế độ Ticket"):
    def __init__(self, cog, parent_menu, config):
        super().__init__()
        self.cog = cog
        self.parent_menu = parent_menu
        
        self.inp_max = TextInput(label="Max vé đang mở/user (1-10)", default=str(config.get('max_open_tickets', 1)), required=True)
        self.inp_cd = TextInput(label="Cooldown mở vé (giây)", default=str(config.get('cooldown_seconds', 60)), required=True)
        
        self.add_item(self.inp_max)
        self.add_item(self.inp_cd)

    async def on_submit(self, interaction: discord.Interaction):
        action = "submit_limit_config"
        await defer_if_needed(interaction, ephemeral=True, thinking=True)
        try:
            max_open = int(self.inp_max.value)
            cd = int(self.inp_cd.value)
            
            if not (1 <= max_open <= 10): raise ValueError()
            if cd < 0: raise ValueError()
                
            self.cog.service.update_single_config(interaction.guild.id, 'max_open_tickets', max_open)
            self.cog.service.update_single_config(interaction.guild.id, 'cooldown_seconds', cd)
            
            await try_refresh_manager_message(self.cog, interaction, self.parent_menu)
            await safe_send(interaction, embed=create_success_splash(TicketEmoji.text("success", "Thành Công"), "Đã lưu cấu hình Max vé và Cooldown."), ephemeral=True)
        except ValueError:
            await safe_error(interaction, embed=create_error_splash(TicketEmoji.text("error", "Lỗi Dữ Liệu"), "Dữ liệu nhập vào không hợp lệ."))
        except Exception:
            logger.exception("[TICKET_UI] callback failed action=%s", action)
            await safe_error(interaction, embed=create_error_splash(TicketEmoji.text("error", "Lỗi Runtime"), "Lỗi khi lưu cấu hình giới hạn."))