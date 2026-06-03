"""
Custom help panel
- Hiển thị danh sách command theo category
- Có nút bấm để xem chi tiết từng nhóm
"""

from __future__ import annotations

from typing import Optional

import discord
from discord.ext import commands

from config import APP_NAME, BOT_PREFIX, SUPPORT_SERVER_URL


HELP_CATEGORIES = [
    {
        "key": "general",
        "emoji": "❓",
        "title": "General",
        "description": "Lệnh cơ bản cho người dùng mới",
        "commands": [
            {
                "name": "help",
                "description": "Xem danh sách lệnh hoặc tra cứu chi tiết command",
                "usage": "[command]",
                "aliases": ["commands"],
            },
        ],
    },
    {
        "key": "user",
        "emoji": "👤",
        "title": "User",
        "description": "Thông tin tài khoản và bảng xếp hạng",
        "commands": [
            {"name": "profile", "description": "Xem profile người dùng", "usage": "[@user]", "aliases": []},
            {"name": "addpoints", "description": "Thêm points cho user", "usage": "@user amount", "aliases": []},
            {"name": "topusers", "description": "Xem top users", "usage": "[limit]", "aliases": []},
            {"name": "setrole", "description": "Thay đổi role user", "usage": "@user role", "aliases": []},
        ],
    },
    {
        "key": "role",
        "emoji": "🧩",
        "title": "Role Management",
        "description": "Phân quyền lệnh theo role",
        "commands": [
            {"name": "addrole", "description": "Cấp quyền dùng command cho role", "usage": "@role command", "aliases": []},
            {"name": "removerole", "description": "Xóa quyền của role", "usage": "@role command", "aliases": []},
            {"name": "perms", "description": "Xem role nào có quyền dùng command", "usage": "command", "aliases": []},
            {"name": "myroles", "description": "Xem role của bạn hoặc user khác", "usage": "[@user]", "aliases": []},
            {"name": "rolescommands", "description": "Xem role đang dùng được những lệnh nào", "usage": "@role", "aliases": []},
        ],
    },
    {
        "key": "admin",
        "emoji": "🛡️",
        "title": "Administrator",
        "description": "Quản lý git và reload cogs",
        "commands": [
            {"name": "gitpull", "description": "Pull code mới nhất từ GitHub", "usage": "", "aliases": ["pull", "update"]},
            {"name": "gitstatus", "description": "Xem trạng thái git hiện tại", "usage": "", "aliases": ["status"]},
            {"name": "reload", "description": "Reload một cog hoặc tất cả cogs", "usage": "[cog_name]", "aliases": []},
            {"name": "load", "description": "Load một cog mới", "usage": "cog_name", "aliases": []},
            {"name": "unload", "description": "Unload một cog", "usage": "cog_name", "aliases": []},
            {"name": "cogs", "description": "Liệt kê các cog đang load", "usage": "", "aliases": []},
        ],
    },
]


def _find_category(category_key: str) -> Optional[dict]:
    for category in HELP_CATEGORIES:
        if category["key"] == category_key:
            return category
    return None


def _find_command(command_name: str) -> tuple[Optional[dict], Optional[dict]]:
    lowered = command_name.lower()
    for category in HELP_CATEGORIES:
        for command in category["commands"]:
            if lowered == command["name"].lower() or lowered in [alias.lower() for alias in command.get("aliases", [])]:
                return category, command
    return None, None


def _format_usage(command: dict) -> str:
    usage = command["usage"].strip()
    command_text = f"{BOT_PREFIX}{command['name']}"
    if usage:
        command_text = f"{command_text} {usage}"
    return f"`{command_text}`"


class HelpCategoryButton(discord.ui.Button):
    def __init__(self, category_key: str, label: str, row: int):
        super().__init__(
            style=discord.ButtonStyle.secondary,
            label=label,
            row=row,
        )
        self.category_key = category_key

    async def callback(self, interaction: discord.Interaction):
        category = _find_category(self.category_key)
        if not category:
            await interaction.response.send_message("❌ Không tìm thấy category.", ephemeral=True)
            return

        view: HelpView = self.view  # type: ignore[assignment]
        await interaction.response.edit_message(
            embed=view.build_category_embed(category),
            view=HelpView(selected_category_key=category["key"]),
        )


class BackButton(discord.ui.Button):
    def __init__(self):
        super().__init__(
            style=discord.ButtonStyle.primary,
            label="⬅ Quay lại",
            row=0,
        )

    async def callback(self, interaction: discord.Interaction):
        view: HelpView = self.view  # type: ignore[assignment]
        await interaction.response.edit_message(
            embed=view.build_index_embed(),
            view=HelpView(),
        )


class HelpView(discord.ui.View):
    def __init__(self, selected_category_key: str | None = None):
        super().__init__(timeout=180)
        self.selected_category_key = selected_category_key

        if selected_category_key is None:
            for index, category in enumerate(HELP_CATEGORIES):
                self.add_item(
                    HelpCategoryButton(
                        category_key=category["key"],
                        label=f"↳ Xem {len(category['commands'])} lệnh",
                        row=index,
                    )
                )

            self.add_item(
                discord.ui.Button(
                    label="Support Server",
                    style=discord.ButtonStyle.link,
                    url=SUPPORT_SERVER_URL,
                    row=len(HELP_CATEGORIES),
                )
            )
        else:
            self.add_item(BackButton())
            self.add_item(
                discord.ui.Button(
                    label="Support Server",
                    style=discord.ButtonStyle.link,
                    url=SUPPORT_SERVER_URL,
                    row=1,
                )
            )

    def build_index_embed(self) -> discord.Embed:
        embed = discord.Embed(
            title=f"{APP_NAME} Commands Directory",
            color=discord.Color.from_rgb(46, 48, 53),
        )
        embed.description = (
            "Các loại lệnh:\n"
            f"• Lệnh không có dấu `/` là prefix command (sử dụng prefix `{BOT_PREFIX}`)\n"
            f"• Xem chi tiết lệnh: sử dụng `{BOT_PREFIX}help <tên-lệnh>`\n\n"
            "Category:"
        )

        for category in HELP_CATEGORIES:
            embed.add_field(
                name=f"{category['emoji']} {category['title']} [{len(category['commands'])}]",
                value=f"↳ Xem {len(category['commands'])} lệnh",
                inline=False,
            )

        return embed

    def build_category_embed(self, category: dict) -> discord.Embed:
        embed = discord.Embed(
            title=f"{category['emoji']} {category['title']}",
            color=discord.Color.from_rgb(46, 48, 53),
        )

        lines = []
        for command in category["commands"]:
            usage_text = _format_usage(command)
            alias_text = ""
            if command.get("aliases"):
                alias_list = ", ".join(f"`{BOT_PREFIX}{alias}`" for alias in command["aliases"])
                alias_text = f"\nAliases: {alias_list}"
            lines.append(
                f"• **{usage_text}**\n"
                f"  {command['description']}{alias_text}"
            )

        command_block = "\n\n".join(lines) if lines else "Chưa có command nào trong category này."
        embed.description = (
            f"{category['description']}\n\n"
            f"{command_block}"
        )
        embed.set_footer(text=f"Tổng cộng {len(category['commands'])} lệnh")
        return embed


class HelpCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='help', aliases=['commands'])
    async def help_command(self, ctx, command_name: str = None):
        if command_name:
            category, command = _find_command(command_name)
            if not command or not category:
                await ctx.send(f"❌ Không tìm thấy lệnh `{command_name}`.")
                return

            embed = discord.Embed(
                title=f"{category['emoji']} {command['name']}",
                color=discord.Color.from_rgb(46, 48, 53),
            )
            embed.add_field(
                name="Cú pháp",
                value=_format_usage(command),
                inline=False,
            )
            embed.add_field(
                name="Mô tả",
                value=command["description"],
                inline=False,
            )
            embed.add_field(
                name="Category",
                value=category["title"],
                inline=True,
            )
            if command.get("aliases"):
                embed.add_field(
                    name="Aliases",
                    value=", ".join(f"`{BOT_PREFIX}{alias}`" for alias in command["aliases"]),
                    inline=True,
                )
            await ctx.send(embed=embed)
            return

        view = HelpView()
        await ctx.send(embed=view.build_index_embed(), view=view)


async def setup(bot):
    await bot.add_cog(HelpCog(bot))
