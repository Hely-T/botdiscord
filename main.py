import discord
from discord.ext import commands
import os
import ssl
import aiohttp
import sys
from config import DISCORD_TOKEN, COGS_DIR, LOGS_DIR
from cogs.cog_loader_utils import iter_cog_modules
from utils import get_prefix

# Tạo các thư mục nếu chưa tồn tại
os.makedirs(LOGS_DIR, exist_ok=True)

if COGS_DIR not in sys.path:
    sys.path.insert(0, COGS_DIR)

# Load cogs từ thư mục cogs và các subfolder catalog
async def load_cogs(bot):
    for module_name in iter_cog_modules():
        try:
            await bot.load_extension(module_name)
            print(f'✅ Đã tải cog: {module_name}')
        except Exception as e:
            print(f'❌ Lỗi khi tải {module_name}: {e}')


async def sync_slash_commands(bot):
    try:
        synced = await bot.tree.sync()
        print(f"✅ Đã sync global slash commands: {len(synced)}")
    except Exception as e:
        print(f"❌ Lỗi sync global slash commands: {e}")

    for guild in bot.guilds:
        try:
            bot.tree.clear_commands(guild=guild)
            bot.tree.copy_global_to(guild=guild)
            synced = await bot.tree.sync(guild=guild)
            print(f"✅ Đã sync guild slash commands mới cho {guild.name} ({guild.id}): {len(synced)}")
        except Exception as e:
            print(f"❌ Lỗi sync guild slash commands cho {guild.name} ({guild.id}): {e}")


def prefix_callable(bot, message):
    prefix = get_prefix()
    return commands.when_mentioned_or(prefix)(bot, message)

async def main():
    intents = discord.Intents.default()
    intents.message_content = True
    ssl_context = ssl.create_default_context(cafile='/etc/ssl/cert.pem')
    connector = aiohttp.TCPConnector(ssl=ssl_context)
    bot = commands.Bot(
        command_prefix=prefix_callable,
        intents=intents,
        connector=connector,
        help_command=None,
    )

    @bot.event
    async def on_ready():
        if not getattr(bot, "_tree_synced", False):
            await sync_slash_commands(bot)
            bot._tree_synced = True

        current_prefix = get_prefix()
        print(f'{bot.user} đã trực tuyến!')
        print(f'Bot ID: {bot.user.id}')
        await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=f'{current_prefix}help'))

    @bot.event
    async def on_command_error(ctx, error):
        current_prefix = get_prefix()
        if isinstance(error, commands.CommandNotFound):
            invoked = (ctx.invoked_with or "").lower()
            if invoked.startswith("form") and len(invoked) > len("form"):
                return
            await ctx.send(f"❌ Lệnh không tồn tại! Gõ `{current_prefix}help` để xem danh sách lệnh.")
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"❌ Thiếu tham số! Gõ `{current_prefix}help {ctx.command}` để xem hướng dẫn.")
        else:
            await ctx.send(f"❌ Lỗi: {error}")
            print(f"Lỗi: {error}")

    async with bot:
        await load_cogs(bot)
        await bot.start(DISCORD_TOKEN)

if __name__ == '__main__':
    try:
        import asyncio
        asyncio.run(main())
    except KeyboardInterrupt:
        print('\n⚠️ Bot đã dừng.')
