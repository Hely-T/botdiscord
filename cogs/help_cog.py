"""
Custom help menu
- Index page with category overview
- Dropdown navigation for categories
- Detailed command cards per category
"""

from __future__ import annotations

from typing import Optional

import discord
from discord.ext import commands

from config import APP_NAME, SUPPORT_SERVER_URL
from utils import get_prefix


HELP_CATEGORIES = [
    {
        "key": "general",
        "emoji": "❓",
        "title": "General",
        "description": "Lệnh cơ bản và tra cứu nhanh",
        "commands": [
            {
                "name": "help",
                "description": "Mở bảng lệnh hoặc xem chi tiết một command",
                "usage": "[command]",
                "aliases": ["commands"],
            },
        ],
    },
    {
        "key": "user",
        "emoji": "👤",
        "title": "User",
        "description": "Lệnh cho mọi người dùng",
        "commands": [
            {"name": "cash", "description": "Xem số dư cash của bạn", "usage": "[@user]", "aliases": []},
            {"name": "give", "description": "Chuyển cash cho user khác", "usage": "@user amount hoặc amount @user", "aliases": []},
            {"name": "profile", "description": "Xem profile của bạn hoặc người khác", "usage": "[@user]", "aliases": []},
            {"name": "topusers", "description": "Xem top users", "usage": "[limit]", "aliases": []},
        ],
    },
    {
        "key": "booking",
        "emoji": "📘",
        "title": "Booking",
        "description": "Lệnh booking, thống kê giờ, nạp tiền và quà",
        "commands": [
            {"name": "luong", "description": "Nhắn booking lên server", "usage": "<nội dung>", "aliases": []},
            {"name": "star", "description": "Xem booking, ghi nhận giờ book hoặc tiền nạp", "usage": "time|money|top|@user", "aliases": []},
            {"name": "tinhluong", "description": "Gửi bảng tính lương booking qua DM", "usage": "[@user|all]", "aliases": []},
            {"name": "topbook", "description": "Xem top giờ được book nhất (admin/role DB)", "usage": "[limit]", "aliases": []},
            {"name": "topnap", "description": "Xem top người nạp tiền nhiều nhất (admin/role DB)", "usage": "[limit]", "aliases": []},
            {"name": "topgift", "description": "Xem tổng quà đang có", "usage": "", "aliases": []},
        ],
    },
    {
        "key": "role",
        "emoji": "🧩",
        "title": "Role Management",
        "description": "Xem quyền theo role trong server",
        "commands": [
            {"name": "addrole", "description": "Cấp quyền dùng command cho role", "usage": "@role|role_id command", "aliases": ["themrole"]},
            {"name": "removerole", "description": "Xóa quyền dùng command khỏi role", "usage": "@role|role_id command", "aliases": ["rmrole", "xoarole"]},
            {"name": "setrole", "description": "Gán Discord role làm role hệ thống", "usage": "@role|role_id <key>", "aliases": []},
            {"name": "perms", "description": "Xem role nào đang có quyền", "usage": "command", "aliases": []},
            {"name": "myroles", "description": "Xem role của bạn hoặc user khác", "usage": "[@user]", "aliases": []},
            {"name": "rolescommands", "description": "Xem role đang dùng được lệnh nào", "usage": "@role|role_id", "aliases": []},
        ],
    },
    {
        "key": "administrator",
        "emoji": "🛡️",
        "title": "Administrator",
        "description": "Danh sách lệnh trong danh mục Administrator",
        "commands": [
            {"name": "addadmin", "description": "Thêm admin bot", "usage": "@user", "aliases": ["themadmin"]},
            {"name": "addcash", "description": "Thêm tiền cho user", "usage": "@user amount", "aliases": []},
            {"name": "addluong", "description": "Thêm lương cho user", "usage": "@user amount", "aliases": []},
            {"name": "addpoints", "description": "Thêm points cho user", "usage": "@user amount", "aliases": []},
            {"name": "addstar", "description": "Thêm star cho user", "usage": "@user amount", "aliases": []},
            {"name": "addtime", "description": "Thêm giờ cho user", "usage": "@user hours", "aliases": []},
            {"name": "ar", "description": "Quản lý auto res và responsive profile", "usage": "a|d|e|set|description|iurl|turl ...", "aliases": []},
            {"name": "ban", "description": "Ban một thành viên", "usage": "@user [reason]", "aliases": []},
            {"name": "bookconfig", "description": "Xem cấu hình giá booking", "usage": "", "aliases": ["bookingconfig", "giabook"]},
            {"name": "cogs", "description": "Liệt kê các cog đang load", "usage": "", "aliases": []},
            {"name": "color", "description": "Đổi màu role", "usage": "@role <hex|name>", "aliases": []},
            {"name": "emoji", "description": "Quản lý emoji", "usage": "add/remove/list ...", "aliases": []},
            {"name": "form", "description": "Gửi mẫu form booking để booking tự điền", "usage": "[key]", "aliases": ["form<key>"]},
            {"name": "gitpull", "description": "Pull code mới nhất từ GitHub", "usage": "", "aliases": ["pull", "update"]},
            {"name": "gitstatus", "description": "Xem trạng thái git hiện tại", "usage": "", "aliases": ["status"]},
            {"name": "load", "description": "Load một cog hoặc cả catalog", "usage": "<catalog|module>", "aliases": []},
            {"name": "mute", "description": "Mute một thành viên", "usage": "@user [duration] [reason]", "aliases": []},
            {"name": "prefix", "description": "Đổi prefix của bot", "usage": "<value>", "aliases": []},
            {"name": "reload", "description": "Reload một cog, một catalog hoặc tất cả", "usage": "[catalog|module]", "aliases": []},
            {"name": "res", "description": "Gọi auto res theo key tùy chỉnh", "usage": "<key>", "aliases": []},
            {"name": "rmadmin", "description": "Xóa admin bot", "usage": "@user", "aliases": ["xoaadmin"]},
            {"name": "setan", "description": "Đặt phần trăm bot/server ăn từ booking", "usage": "<percent>", "aliases": ["setfee", "sethoahong"]},
            {"name": "setgiobook", "description": "Đặt giá tiền cho 1h booking", "usage": "<amount>", "aliases": ["setgia", "giabooking"]},
            {"name": "setphantram", "description": "Đặt phần trăm tiền trả cho booking", "usage": "<percent>", "aliases": ["setpayout", "settraluong"]},
            {"name": "subcash", "description": "Trừ tiền của user", "usage": "@user amount", "aliases": []},
            {"name": "subluong", "description": "Trừ lương của user", "usage": "@user amount", "aliases": []},
            {"name": "substar", "description": "Trừ star của user", "usage": "@user amount", "aliases": []},
            {"name": "subtime", "description": "Trừ giờ của user", "usage": "@user hours", "aliases": []},
            {"name": "tongluong", "description": "Xem tổng lương", "usage": "", "aliases": []},
            {"name": "topstar", "description": "Xem top star", "usage": "[limit]", "aliases": []},
            {"name": "unban", "description": "Gỡ ban một thành viên", "usage": "user_id [reason]", "aliases": []},
            {"name": "unload", "description": "Unload một cog hoặc cả catalog", "usage": "<catalog|module>", "aliases": []},
            {"name": "unmute", "description": "Gỡ mute một thành viên", "usage": "@user [reason]", "aliases": []},
            {"name": "up", "description": "Up responsive profile lên channel chỉ định", "usage": "<key><số> #channel", "aliases": []},
        ],
        "slash_commands": [
            {"name": "antiraid", "description": "Bật chế độ chống raid", "usage": "", "aliases": []},
        ],
    },
]


THEME_COLOR = discord.Color.from_rgb(46, 48, 53)
ACCENT_COLOR = discord.Color.from_rgb(180, 205, 255)


def _find_category(category_key: str) -> Optional[dict]:
    for category in HELP_CATEGORIES:
        if category["key"] == category_key:
            return category
    return None


def _find_command(command_name: str) -> tuple[Optional[dict], Optional[dict]]:
    lowered = command_name.lower()
    for category in HELP_CATEGORIES:
        for command in category["commands"]:
            aliases = [alias.lower() for alias in command.get("aliases", [])]
            if lowered == command["name"].lower() or lowered in aliases:
                return category, command
    return None, None


def _format_usage(command: dict) -> str:
    usage = command["usage"].strip()
    prefix = get_prefix()
    command_text = f"{prefix}{command['name']}"
    if usage:
        command_text = f"{command_text} {usage}"
    return f"`{command_text}`"


def _category_total_commands(category: dict) -> int:
    return len(category.get("commands", [])) + len(category.get("slash_commands", []))


def _build_support_button() -> discord.ui.Button:
    return discord.ui.Button(
        label="Support Server",
        style=discord.ButtonStyle.link,
        url=SUPPORT_SERVER_URL,
        emoji="↗",
    )


async def _safe_edit_help(interaction: discord.Interaction, embed: discord.Embed, view: discord.ui.View):
    try:
        if interaction.response.is_done():
            await interaction.edit_original_response(embed=embed, view=view)
        else:
            await interaction.response.edit_message(embed=embed, view=view)
    except Exception as exc:
        print(f"❌ Lỗi tương tác help menu: {exc}")
        if interaction.response.is_done():
            await interaction.followup.send("❌ Menu help cũ bị lỗi. Gõ lại `help` để mở menu mới.", ephemeral=True)
        else:
            await interaction.response.send_message("❌ Menu help cũ bị lỗi. Gõ lại `help` để mở menu mới.", ephemeral=True)


class HelpCategorySelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(
                label=category["title"],
                value=category["key"],
                description=category["description"][:100],
                emoji=category["emoji"],
            )
            for category in HELP_CATEGORIES
        ]
        super().__init__(
            placeholder="Chọn category để xem chi tiết...",
            min_values=1,
            max_values=1,
            options=options,
            custom_id="help:category_select",
        )

    async def callback(self, interaction: discord.Interaction):
        category = _find_category(self.values[0])
        if not category:
            await interaction.response.send_message("❌ Không tìm thấy category.", ephemeral=True)
            return

        await _safe_edit_help(
            interaction,
            embed=HelpView.build_category_embed(category, interaction.guild),
            view=CategoryView(category["key"]),
        )


class HomeButton(discord.ui.Button):
    def __init__(self):
        super().__init__(
            label="Trang chủ",
            style=discord.ButtonStyle.primary,
            emoji="🏠",
            custom_id="help:home",
        )

    async def callback(self, interaction: discord.Interaction):
        await _safe_edit_help(
            interaction,
            embed=HelpView.build_index_embed(interaction.guild),
            view=IndexView(),
        )


class BackButton(discord.ui.Button):
    def __init__(self):
        super().__init__(
            label="Quay lại",
            style=discord.ButtonStyle.secondary,
            emoji="⬅",
            custom_id="help:back",
        )

    async def callback(self, interaction: discord.Interaction):
        await _safe_edit_help(
            interaction,
            embed=HelpView.build_index_embed(interaction.guild),
            view=IndexView(),
        )


class IndexView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(HelpCategorySelect())
        self.add_item(_build_support_button())


class CategoryView(discord.ui.View):
    def __init__(self, category_key: str):
        super().__init__(timeout=None)
        self.category_key = category_key
        self.add_item(BackButton())
        self.add_item(HomeButton())
        self.add_item(_build_support_button())


class HelpView:
    @staticmethod
    def build_index_embed(guild: discord.Guild | None = None) -> discord.Embed:
        prefix = get_prefix()
        title_name = guild.name if guild else APP_NAME
        embed = discord.Embed(
            title=f"{title_name} Commands Directory",
            color=THEME_COLOR,
        )
        embed.description = (
            f"Dùng menu bên dưới để xem category.\n"
            f"Prefix hiện tại: `{prefix}`\n"
            f"Xem chi tiết một lệnh: `{prefix}help <command>`"
        )

        for category in HELP_CATEGORIES:
            embed.add_field(
                name=f"{category['emoji']} **{category['title']}** [{_category_total_commands(category)}]",
                value=category["description"],
                inline=False,
            )

        embed.set_author(name=APP_NAME)
        if guild and guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
        else:
            embed.set_thumbnail(url="https://cdn.discordapp.com/embed/avatars/0.png")
        embed.set_footer(text=f"{len(HELP_CATEGORIES)} categories • {prefix}help")
        return embed

    @staticmethod
    def build_category_embed(category: dict, guild: discord.Guild | None = None) -> discord.Embed:
        prefix = get_prefix()
        category_title = category["title"]
        embed = discord.Embed(
            title=f"{category['emoji']} {category_title}",
            description=(
                f"Danh sách lệnh trong danh mục **{category_title}**"
                if category["key"] == "administrator"
                else category["description"]
            ),
            color=ACCENT_COLOR,
        )

        if category["key"] == "administrator":
            prefix_commands = ", ".join(f"`{command['name']}`" for command in category["commands"])
            slash_commands = ", ".join(f"`{command['name']}`" for command in category.get("slash_commands", []))

            embed.add_field(
                name="**Prefix:**",
                value=prefix_commands,
                inline=False,
            )
            if slash_commands:
                embed.add_field(
                    name="**Slash:**",
                    value=slash_commands,
                    inline=False,
                )
        else:
            for command in category["commands"]:
                alias_text = ""
                if command.get("aliases"):
                    alias_list = ", ".join(f"`{prefix}{alias}`" for alias in command["aliases"])
                    alias_text = f"\nAliases: {alias_list}"

                embed.add_field(
                    name=_format_usage(command),
                    value=f"{command['description']}{alias_text}",
                    inline=False,
                )

        embed.set_author(name=guild.name if guild else APP_NAME)
        embed.set_footer(text=f"Tổng cộng {_category_total_commands(category)} lệnh • {prefix}help <command>")
        return embed

    @staticmethod
    def build_command_embed(category: dict, command: dict, guild: discord.Guild | None = None) -> discord.Embed:
        prefix = get_prefix()
        embed = discord.Embed(
            title=f"{category['emoji']} {command['name']}",
            color=ACCENT_COLOR,
        )
        embed.add_field(name="Cú pháp", value=_format_usage(command), inline=False)
        embed.add_field(name="Mô tả", value=command["description"], inline=False)
        embed.add_field(name="Category", value=category["title"], inline=True)
        if command.get("aliases"):
            embed.add_field(
                name="Aliases",
                value=", ".join(f"`{prefix}{alias}`" for alias in command["aliases"]),
                inline=True,
            )
        if command["name"] == "star":
            embed.add_field(
                name="Cách dùng",
                value=(
                    "`star` - xem giờ book và số tiền đã tiêu của bạn\n"
                    "`star time <hours> [@user]` - ghi nhận giờ book, tự tính tiền theo config\n"
                    "`star money <amount> [@user]` - ghi nhận tiền nạp, hỗ trợ `100k`, `1m`, `1b`\n"
                    "`star top` - top giờ được book và top nạp tiền\n"
                    "`star @user` - admin xem booking người khác"
                ),
                inline=False,
            )
        if command["name"] in {"topstar", "topbook", "topnap"}:
            embed.add_field(
                name="Quyền",
                value="Chỉ admin hoặc role được cấp trong database mới dùng được.",
                inline=False,
            )
        if command["name"] == "give":
            embed.add_field(
                name="Cách dùng",
                value="`give @user 100k` hoặc `give 100k @user`\nChỉ dùng trong server. Hỗ trợ tiền VND: `100000`, `100k`, `1m`, `1b`, `100.000`, `100,000`, `0,01vnđ`.",
                inline=False,
            )
        if command["name"] == "ar":
            embed.add_field(
                name="Cách dùng",
                value=(
                    "`ar a <res> | <nội dung>` thêm auto res\n"
                    "`ar a <res>` tạo auto res rỗng\n"
                    "`ar des <res> | <nội dung>` sửa nội dung auto res\n"
                    "`ar des <res>` lấy nội dung auto res từ tin nhắn reply\n"
                    "`ar a <key> <số>` hoặc `ar a <key><số>` thêm profile/form, số `0` dùng được\n"
                    "`ar e <key> <text>` sửa auto res\n"
                    "`ar e <key> <số> <text>` sửa nội dung profile\n"
                    "`ar d <key> [số]` xóa auto res hoặc profile\n"
                    "`ar set <key> <số> @user` gắn profile\n"
                    "`ar up <key><số> #channel` up profile sang channel chỉ định\n"
                    "`ar description <key> <số>` hoặc `ar description <key><số>` lấy nội dung từ tin nhắn reply\n"
                    "`ar description <key> <số> | <form>` nhập form thủ công\n"
                    "`ar target <res|profile> @user` gắn target cho auto res hoặc profile, ví dụ `ar target yang @user`, `ar target ad1 @user`\n"
                    "`ar iurl/turl <res> <url|ảnh>` set ảnh auto res\n"
                    "`ar iurl/turl <key> <số> <url|ảnh>` set ảnh profile\n"
                    "`turl` là ảnh đại diện/thumbnail và bot sẽ tự crop vuông khi hiển thị\n"
                    "`ar list <key>` xem các profile đã tạo theo key"
                ),
                inline=False,
            )
            embed.add_field(
                name="Placeholder auto res",
                value="Dùng `{user}` cho người gọi, `{key}` cho key trigger. `{target}` vẫn hỗ trợ nếu đã gắn, nhưng không bắt buộc.",
                inline=False,
            )
        if command["name"] == "form":
            embed.add_field(
                name="Cách dùng",
                value=(
                    "`form` gửi nút **Điền form** để user tự nhập và lưu form của họ.\n"
                    "Sau đó admin dùng `ar a ad1 @user` để tạo profile từ form đã lưu và gắn profile luôn.\n"
                    "`form ad1` sẽ hiện nút mở ô nhập và lưu trực tiếp vào profile `ad1`. Có thể gọi dính liền kiểu `formau` để gửi mẫu theo key."
                ),
                inline=False,
            )
        if command["name"] == "res":
            embed.add_field(
                name="Cách dùng",
                value="`res yang` sẽ gọi nội dung auto res của key `yang`. Có thể dùng `{user}`, `{target}`, `{key}` trong nội dung.",
                inline=False,
            )
        if command["name"] == "setrole":
            embed.add_field(
                name="Cách dùng",
                value="`setrole @Booking booking` hoặc `setrole <role_id> booking`. Ai có Discord role đó sẽ được bot nhận là booking.",
                inline=False,
            )
        if command["name"] == "up":
            embed.add_field(
                name="Cách dùng",
                value="`up ad1 #booking` hoặc `ar up ad1 #booking` để gửi profile `ad1` lên channel chỉ định.",
                inline=False,
            )
        if command["name"] in {"setgiobook", "addcash", "subcash", "addluong", "subluong"}:
            embed.add_field(
                name="Định dạng tiền",
                value="Hỗ trợ `100000`, `100k`, `1m`, `1b`, `100.000`, `100,000`, `0,5m`. Đơn vị mặc định là VNĐ.",
                inline=False,
            )
        embed.set_author(name=guild.name if guild else APP_NAME)
        embed.set_footer(text=f"Dùng {prefix}help để quay lại bảng lệnh")
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

            await ctx.send(embed=HelpView.build_command_embed(category, command, ctx.guild))
            return

        await ctx.send(embed=HelpView.build_index_embed(ctx.guild), view=IndexView())


async def setup(bot):
    await bot.add_cog(HelpCog(bot))
