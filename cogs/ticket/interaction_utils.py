# File: cogs/ticket/interaction_utils.py
# Purpose: Helper an toàn cho Discord interaction Ticket.

import logging
import discord
from ui.ticket.emoji import TicketEmoji
from utils import create_error_splash

logger = logging.getLogger(__name__)

def clean_kwargs(**kwargs) -> dict:
    cleaned = {}
    for k, v in kwargs.items():
        if v is not None:
            if k == 'view' and not hasattr(v, 'to_components'):
                continue # Protect against invalid views
            cleaned[k] = v
    return cleaned

async def defer_if_needed(interaction: discord.Interaction, *, ephemeral: bool = True, thinking: bool = True) -> None:
    if not interaction.response.is_done():
        try:
            await interaction.response.defer(ephemeral=ephemeral, thinking=thinking)
        except discord.InteractionResponded:
            pass
        except Exception:
            logger.exception(
                "[TICKET_INTERACTION] defer failed phase=defer guild=%s user=%s channel=%s custom_id=%s",
                getattr(interaction.guild, "id", None), getattr(interaction.user, "id", None),
                getattr(interaction.channel, "id", None), interaction.data.get("custom_id") if isinstance(interaction.data, dict) else None
            )
            raise

async def safe_send(interaction: discord.Interaction, *, content=None, embed=None, view=None, ephemeral: bool = True):
    kwargs = clean_kwargs(content=content, embed=embed, view=view, ephemeral=ephemeral)
    try:
        if interaction.response.is_done():
            return await interaction.followup.send(**kwargs)
        return await interaction.response.send_message(**kwargs)
    except discord.InteractionResponded:
        return await interaction.followup.send(**kwargs)
    except Exception:
        logger.exception(
            "[TICKET_INTERACTION] safe_send failed phase=send guild=%s user=%s keys=%s",
            getattr(interaction.guild, "id", None), getattr(interaction.user, "id", None), list(kwargs.keys())
        )
        raise

async def safe_edit_message(message: discord.Message, *, content=None, embed=None, view=None):
    kwargs = clean_kwargs(content=content, embed=embed, view=view)
    try:
        return await message.edit(**kwargs)
    except discord.NotFound:
        logger.debug("[TICKET_INTERACTION] safe_edit_message ignored: Message Not Found (404) msg_id=%s", getattr(message, "id", None))
        return None
    except Exception:
        logger.exception("[TICKET_INTERACTION] safe_edit_message failed msg_id=%s", message.id)
        raise
        
async def safe_error(interaction: discord.Interaction, *, embed=None, content=None):
    try:
        return await safe_send(interaction, content=content, embed=embed, ephemeral=True)
    except Exception:
        logger.exception(
            "[TICKET_UI] failed to send safe error custom_id=%s guild=%s user=%s",
            interaction.data.get("custom_id") if isinstance(interaction.data, dict) else None,
            getattr(interaction.guild, "id", None),
            getattr(interaction.user, "id", None),
        )

async def update_config_and_verify(cog, interaction: discord.Interaction, key: str, value, action: str) -> tuple[bool, dict]:
    guild_id = interaction.guild.id
    
    before = cog.service.get_config(guild_id)
    logger.info("[TICKET_CONFIG] before action=%s guild=%s config=%s", action, guild_id, before)
    
    ok = cog.service.update_single_config(guild_id, key, value)
    after = cog.service.get_config(guild_id)
    
    actual = after.get(key) if after else None
    
    logger.info(
        "[TICKET_CONFIG] after action=%s guild=%s key=%s expected=%s actual=%s ok=%s config=%s",
        action, guild_id, key, value, actual, ok, after
    )
    
    if str(actual or "") != str(value or ""):
        logger.error(
            "[TICKET_CONFIG] sync failed action=%s guild=%s key=%s expected=%s actual=%s",
            action, guild_id, key, value, actual
        )
        await safe_send(
            interaction,
            embed=create_error_splash(TicketEmoji.text("error", "Lỗi Đồng Bộ"), f"DB không lưu đúng `{key}`. Expected `{value}`, actual `{actual}`."),
            ephemeral=True
        )
        return False, after
        
    return True, after