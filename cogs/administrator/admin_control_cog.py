from __future__ import annotations

import discord
from discord import app_commands
from discord.ext import commands

from cogs.admin_command_utils import AdminCommandBase
from utils import create_error_splash, create_success_splash


class AdminControlCog(AdminCommandBase):
    admin_group = app_commands.Group(name="admin", description="Quản trị bot")

    def _is_hard_admin(self, user: discord.abc.User) -> bool:
        return self.admins.is_hard_admin(user.id)

    @admin_group.command(name="command", description="Bật/tắt quyền dùng lệnh")
    @app_commands.choices(
        mode=[
            app_commands.Choice(name="on", value="on"),
            app_commands.Choice(name="off", value="off"),
        ]
    )
    async def command_lock(self, interaction: discord.Interaction, mode: app_commands.Choice[str]):
        if interaction.guild is None:
            await interaction.response.send_message("❌ Lệnh này chỉ dùng trong server.", ephemeral=True)
            return
        if not self._is_hard_admin(interaction.user):
            await interaction.response.send_message(
                embed=create_error_splash("Chỉ hard admin mới dùng được lệnh này."),
                ephemeral=True,
            )
            return

        locked = mode.value == "off"
        self.guild_settings.set_commands_locked(interaction.guild.id, locked)
        if locked:
            title = "Đã khoá quyền dùng lệnh"
            description = "Non-hardadmin sẽ không dùng được command cho tới khi bật lại."
        else:
            title = "Đã mở quyền dùng lệnh"
            description = "Command đã hoạt động lại cho server này."

        await interaction.response.send_message(
            embed=create_success_splash(title, description),
            ephemeral=True,
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(AdminControlCog(bot))
