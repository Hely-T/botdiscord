# Discord Bot - Python

Bot Discord được tạo bằng discord.py

## Cấu trúc dự án

```
BOT DISCORD/
├── main.py              # File chính để chạy bot
├── config.py            # Cấu hình bot
├── requirements.txt     # Các thư viện cần thiết
├── .env                 # Biến môi trường (Token, Admin ID, v.v.)
├── .gitignore          # Bỏ qua các file không cần commit
├── cogs/               # Thư mục chứa các plugin (cogs)
│   └── __init__.py
├── database/           # Thư mục chứa các database (.db)
├── logs/               # Thư mục chứa log files
└── README.md           # File này
```

## Cài đặt

### 1. Cài đặt Python dependencies

```bash
pip install -r requirements.txt
```

### 2. Cấu hình Discord Token

1. Tạo ứng dụng Discord tại [Discord Developer Portal](https://discord.com/developers/applications)
2. Tạo Bot và sao chép Token
3. Mở file `.env` và thay `your_token_here` bằng token của bạn
4. Thay `your_admin_id_here` bằng Discord ID của bạn

### 3. Chạy bot

```bash
python main.py
```

## Cách tạo Cogs (Plugins)

Tạo file mới trong thư mục `cogs/` với tên `your_feature.py`:

```python
import discord
from discord.ext import commands

class YourFeature(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='hello')
    async def hello(self, ctx):
        await ctx.send(f'Xin chào {ctx.author.name}!')

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user:
            return
        print(f'{message.author}: {message.content}')

async def setup(bot):
    await bot.add_cog(YourFeature(bot))
```

Bot sẽ tự động tải tất cả các cogs từ thư mục `cogs/`.

## Ghi chú

- Luôn giữ file `.env` an toàn và không commit lên Git
- Mỗi cog nên có `async def setup(bot)` ở cuối file
- Sử dụng SQLite (`database/`) để lưu dữ liệu
