import discord
from discord import app_commands

from cogs.admin_command_utils import AdminCommandBase


class AdministratorSecurityCog(AdminCommandBase):
    @app_commands.command(name="antiraid", description="Bật/tắt chế độ chống raid trong server")
    async def antiraid(self, interaction: discord.Interaction):
        if interaction.guild is None:
            await interaction.response.send_message("❌ Lệnh này chỉ dùng trong server.", ephemeral=True)
            return
        if not await self.require_role_or_admin_interaction(interaction, "antiraid"):
            return
        enabled = self.guild_settings.toggle_antiraid(interaction.guild.id)
        status_text = "đã bật" if enabled else "đã tắt"
        await interaction.response.send_message(
            f"✅ Chế độ chống raid {status_text} cho server **{interaction.guild.name}**.",
            ephemeral=True,
        )


async def setup(bot):
    await bot.add_cog(AdministratorSecurityCog(bot))
