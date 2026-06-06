# File: cogs/ticket/permissions.py
# Purpose: Cung cấp helper check quyền tập trung cho hệ thống Ticket.
# Notes:
# - Dùng chung cho cả prefix và slash commands.
# - Không phụ thuộc cứng vào Interaction hay Context.

import discord
from services.admin_service import AdminService
from services.ticket_service import TicketService

def is_ticket_admin(member: discord.Member) -> bool:
    """Check nếu user là Admin của server hoặc Bot Admin."""
    if member.guild_permissions.administrator:
        return True
    return AdminService().is_admin(member.id)

def is_ticket_staff(member: discord.Member, ticket_type: str = 'all') -> bool:
    """Check nếu user có role staff cho loại vé này."""
    svc = TicketService()
    roles = svc.get_staff_roles_for_type(member.guild.id, ticket_type)
    allowed_ids = {r['role_id'] for r in roles}
    return any(r.id in allowed_ids for r in member.roles)

def can_manage_ticket(member: discord.Member, ticket: dict, config: dict) -> bool:
    """Kiểm tra quyền thao tác ticket (Claim, Staff, Admin)."""
    if is_ticket_admin(member):
        return True
    ticket_type = ticket.get('ticket_type', 'all') if ticket else 'all'
    return is_ticket_staff(member, ticket_type)

def can_view_ticket_info(member: discord.Member, ticket: dict, config: dict) -> bool:
    """Kiểm tra quyền xem info ticket (Bao gồm Owner, Staff, Admin)."""
    if int(ticket['owner_user_id']) == member.id:
        return True
    return can_manage_ticket(member, ticket, config)