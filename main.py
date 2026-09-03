import os
from pathlib import Path

import discord
from discord.ext import commands

from config import DISCORD_TOKEN, PREFIX

# Bot intents
intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

bot = commands.Bot(command_prefix=PREFIX, intents=intents)

# Load cogs
async def load_cogs():
    cogs_path = Path(__file__).parent / "cogs"
    if not cogs_path.exists():
        print("⚠️ cogs klasörü bulunamadı, uzantılar yüklenmedi.")
        return

    for filename in os.listdir(cogs_path):
        if filename.endswith('.py') and not filename.startswith('__'):
            await bot.load_extension(f'cogs.{filename[:-3]}')
            print(f'✅ Loaded {filename}')

@bot.event
async def on_ready():
    print(f'🤖 Bot "{bot.user}" olarak giriş yaptı!')
    print(f'📊 Sunucu sayısı: {len(bot.guilds)}')
    await bot.change_presence(activity=discord.Activity(
        type=discord.ActivityType.listening,
        name="🎵 Müzik"
    ))

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return
    
    embed = discord.Embed(
        title="❌ Hata!",
        description=f"```{str(error)}```",
        color=discord.Color.red()
    )
    await ctx.send(embed=embed)

async def main():
    if not DISCORD_TOKEN:
        raise RuntimeError("DISCORD_TOKEN .env dosyasında tanımlı değil.")

    await load_cogs()
    await bot.start(DISCORD_TOKEN)

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())
