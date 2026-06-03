import discord
from discord.ext import commands
import os
from config import DISCORD_TOKEN, BOT_PREFIX, COGS_DIR, LOGS_DIR

# Tạo các thư mục nếu chưa tồn tại
os.makedirs(LOGS_DIR, exist_ok=True)

# Khởi tạo bot
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix=BOT_PREFIX, intents=intents)

@bot.event
async def on_ready():
    print(f'{bot.user} đã trực tuyến!')
    print(f'Bot ID: {bot.user.id}')
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=f'{BOT_PREFIX}help'))

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.send(f"❌ Lệnh không tồn tại! Gõ `{BOT_PREFIX}help` để xem danh sách lệnh.")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"❌ Thiếu tham số! Gõ `{BOT_PREFIX}help {ctx.command}` để xem hướng dẫn.")
    else:
        await ctx.send(f"❌ Lỗi: {error}")
        print(f"Lỗi: {error}")

# Load cogs từ thư mục cogs
async def load_cogs():
    for filename in os.listdir(COGS_DIR):
        if filename.endswith('.py') and filename != '__init__.py':
            try:
                await bot.load_extension(f'{COGS_DIR}.{filename[:-3]}')
                print(f'✅ Đã tải cog: {filename}')
            except Exception as e:
                print(f'❌ Lỗi khi tải {filename}: {e}')

async def main():
    async with bot:
        await load_cogs()
        await bot.start(DISCORD_TOKEN)

if __name__ == '__main__':
    try:
        import asyncio
        asyncio.run(main())
    except KeyboardInterrupt:
        print('\n⚠️ Bot đã dừng.')
