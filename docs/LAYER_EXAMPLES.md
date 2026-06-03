# 📖 Ví Dụ Chi Tiết - Cách Tạo Feature Theo Layered Architecture

Đây là ví dụ step-by-step để tạo một feature **"Posting System"** hoàn chỉnh.

---

## 🎯 Feature: Posting System

Users có thể tạo posts, xem posts, like/unlike posts.

---

## Step 1️⃣: Tạo Models (Layer 4)

**File:** `models/post_model.py`

```python
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

@dataclass
class Post:
    """Model cho một bài post"""
    post_id: int = None
    author_id: int = None
    author_name: str = None
    content: str = None
    likes: int = 0
    created_at: str = None
    updated_at: str = None
    
    def validate(self):
        """Validate post data"""
        if not self.author_id or not self.author_name:
            raise ValueError("Author info required")
        
        if not self.content or len(self.content) == 0:
            raise ValueError("Content required")
        
        if len(self.content) > 500:
            raise ValueError("Content tối đa 500 ký tự")
    
    def to_dict(self):
        """Convert to dict"""
        return {
            'post_id': self.post_id,
            'author_id': self.author_id,
            'author_name': self.author_name,
            'content': self.content,
            'likes': self.likes,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }
```

**File:** `models/constants.py` (thêm vào)

```python
# Posts
MAX_POST_LENGTH = 500
POSTS_PER_PAGE = 10
```

---

## Step 2️⃣: Tạo Service (Layer 3)

**File:** `services/post_service.py`

```python
"""Post Service - Business Logic"""

from utils import CogDatabase, get_timestamp
from models.post_model import Post
from models.constants import MAX_POST_LENGTH

class PostService:
    """Service xử lý post operations"""
    
    def __init__(self):
        self.db = CogDatabase('posts')
        self._init_database()
    
    def _init_database(self):
        """Khởi tạo database schema"""
        self.db.create_table('posts', '''
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            post_id INTEGER UNIQUE NOT NULL,
            author_id INTEGER NOT NULL,
            author_name TEXT NOT NULL,
            content TEXT NOT NULL,
            likes INTEGER DEFAULT 0,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        ''')
        
        self.db.create_table('post_likes', '''
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            post_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            UNIQUE(post_id, user_id)
        ''')
    
    def create_post(self, author_id: int, author_name: str, content: str) -> Post:
        """Tạo post mới"""
        post = Post(
            author_id=author_id,
            author_name=author_name,
            content=content,
            likes=0,
            created_at=get_timestamp()
        )
        
        # Validate
        post.validate()
        
        # Insert vào database
        self.db.insert('posts', {
            'author_id': post.author_id,
            'author_name': post.author_name,
            'content': post.content,
            'likes': post.likes,
            'created_at': post.created_at,
            'updated_at': get_timestamp()
        })
        
        # Lấy post_id
        result = self.db.fetch_one(
            'SELECT id FROM posts WHERE author_id = ? ORDER BY id DESC LIMIT 1',
            (author_id,)
        )
        post.post_id = result['id']
        
        return post
    
    def get_post(self, post_id: int) -> Post:
        """Lấy post"""
        result = self.db.select_one('posts', 'post_id = ?', (post_id,))
        
        if not result:
            return None
        
        return Post(
            post_id=result['post_id'],
            author_id=result['author_id'],
            author_name=result['author_name'],
            content=result['content'],
            likes=result['likes'],
            created_at=result['created_at'],
            updated_at=result['updated_at']
        )
    
    def get_all_posts(self, limit: int = 10, offset: int = 0) -> list:
        """Lấy tất cả posts (phân trang)"""
        return self.db.fetch(
            'SELECT * FROM posts ORDER BY created_at DESC LIMIT ? OFFSET ?',
            (limit, offset)
        )
    
    def like_post(self, post_id: int, user_id: int):
        """Like post"""
        post = self.get_post(post_id)
        if not post:
            raise ValueError(f"Post {post_id} không tồn tại")
        
        try:
            self.db.insert('post_likes', {
                'post_id': post_id,
                'user_id': user_id
            })
            
            # Update likes count
            self.db.update('posts',
                {'likes': post.likes + 1},
                'post_id = ?',
                (post_id,)
            )
        except:
            raise ValueError("Bạn đã like post này rồi")
    
    def unlike_post(self, post_id: int, user_id: int):
        """Unlike post"""
        post = self.get_post(post_id)
        if not post:
            raise ValueError(f"Post {post_id} không tồn tại")
        
        # Check if liked
        liked = self.db.select_one('post_likes',
            'post_id = ? AND user_id = ?',
            (post_id, user_id)
        )
        
        if not liked:
            raise ValueError("Bạn chưa like post này")
        
        self.db.delete('post_likes',
            'post_id = ? AND user_id = ?',
            (post_id, user_id)
        )
        
        # Update likes count
        self.db.update('posts',
            {'likes': post.likes - 1},
            'post_id = ?',
            (post_id,)
        )
    
    def delete_post(self, post_id: int, user_id: int):
        """Xóa post (chỉ author hoặc admin)"""
        post = self.get_post(post_id)
        if not post:
            raise ValueError(f"Post {post_id} không tồn tại")
        
        if post.author_id != user_id:
            raise ValueError("Chỉ author có thể xóa post")
        
        self.db.delete('posts', 'post_id = ?', (post_id,))
        self.db.delete('post_likes', 'post_id = ?', (post_id,))
```

---

## Step 3️⃣: Tạo Commands (Layer 2)

**File:** `cogs/post_cog.py`

```python
"""Post Commands - Discord Interface"""

import discord
from discord.ext import commands
from services.post_service import PostService
from models.constants import ERROR_MESSAGE, PERMISSION_DENIED

class PostCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.service = PostService()
    
    @commands.command(name='post')
    async def create_post(self, ctx, *, content: str):
        """Tạo post mới
        
        Usage: !post Hello world
        """
        try:
            if not content:
                await ctx.send("❌ Content không được trống!")
                return
            
            # Call Service
            post = self.service.create_post(
                ctx.author.id,
                ctx.author.name,
                content
            )
            
            # Format response
            embed = discord.Embed(
                title="✅ Post Created",
                description=post.content,
                color=discord.Color.green()
            )
            embed.set_author(name=post.author_name)
            embed.add_field(name="Post ID", value=post.post_id, inline=False)
            embed.set_footer(text=f"Created at {post.created_at}")
            
            await ctx.send(embed=embed)
        
        except Exception as e:
            await ctx.send(f"{ERROR_MESSAGE} {str(e)}")
    
    @commands.command(name='posts')
    async def view_posts(self, ctx, page: int = 1):
        """Xem tất cả posts
        
        Usage: !posts [page]
        """
        try:
            if page < 1:
                page = 1
            
            offset = (page - 1) * 10
            
            # Call Service
            posts = self.service.get_all_posts(limit=10, offset=offset)
            
            if not posts:
                await ctx.send("❌ Chưa có post nào!")
                return
            
            # Format response
            embed = discord.Embed(
                title=f"📝 Posts (Page {page})",
                color=discord.Color.blue()
            )
            
            for post in posts:
                embed.add_field(
                    name=f"#{post['post_id']} by {post['author_name']}",
                    value=f"{post['content'][:100]}...\n❤️ {post['likes']} likes",
                    inline=False
                )
            
            await ctx.send(embed=embed)
        
        except Exception as e:
            await ctx.send(f"{ERROR_MESSAGE} {str(e)}")
    
    @commands.command(name='like')
    async def like_post(self, ctx, post_id: int):
        """Like post
        
        Usage: !like <post_id>
        """
        try:
            # Call Service
            self.service.like_post(post_id, ctx.author.id)
            
            await ctx.send(f"❤️ Bạn đã like post #{post_id}!")
        
        except Exception as e:
            await ctx.send(f"{ERROR_MESSAGE} {str(e)}")
    
    @commands.command(name='unlike')
    async def unlike_post(self, ctx, post_id: int):
        """Unlike post
        
        Usage: !unlike <post_id>
        """
        try:
            # Call Service
            self.service.unlike_post(post_id, ctx.author.id)
            
            await ctx.send(f"💔 Bạn đã unlike post #{post_id}!")
        
        except Exception as e:
            await ctx.send(f"{ERROR_MESSAGE} {str(e)}")
    
    @commands.command(name='deletepost')
    async def delete_post(self, ctx, post_id: int):
        """Xóa post của bạn
        
        Usage: !deletepost <post_id>
        """
        try:
            # Call Service
            self.service.delete_post(post_id, ctx.author.id)
            
            await ctx.send(f"✅ Post #{post_id} đã bị xóa!")
        
        except Exception as e:
            await ctx.send(f"{ERROR_MESSAGE} {str(e)}")

async def setup(bot):
    await bot.add_cog(PostCog(bot))
```

---

## Step 4️⃣: Xong!

Bot sẽ **tự động load** cog mới từ `cogs/post_cog.py` ✨

**Không cần chỉnh sửa `main.py`!**

---

## 🔄 Flow Khi User Dùng Lệnh

```
User gõ: !post "Hello World"
    ↓
[Layer 2] post_cog.py (create_post command)
    - Validate input
    - Call service
    ↓
[Layer 3] post_service.py (create_post)
    - Validate business logic
    - Create Post object
    - Call database
    ↓
[Layer 5] utils.py (CogDatabase.insert)
    - Execute SQL
    - Save to posts.db
    ↓
Response sent back to Discord
```

---

## 📝 Database Files Tạo Ra

```
database/
├── users.db      # Từ user service
├── posts.db      # Từ post service (auto-created!)
└── [any_other_service].db
```

**Tất cả tự động tạo!** 🚀

---

## ✅ Checklist Khi Tạo Feature

- [ ] Tạo Models (models/xxx_model.py)
- [ ] Thêm Constants (models/constants.py)
- [ ] Tạo Service (services/xxx_service.py)
  - [ ] _init_database()
  - [ ] CRUD methods
- [ ] Tạo Cog (cogs/xxx_cog.py)
  - [ ] Commands
  - [ ] Error handling
  - [ ] Pretty embeds
- [ ] Test từng command
- [ ] Verify database tạo ở database/

**Done! Không cần edit main.py!** ✨

