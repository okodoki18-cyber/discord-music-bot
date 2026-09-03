from __future__ import annotations

import asyncio
import re
from collections import deque
from dataclasses import dataclass, field
from typing import Deque, Optional

import discord
import yt_dlp
from discord.ext import commands

URL_REGEX = re.compile(r"https?://")

YTDL_OPTIONS = {
    "format": "bestaudio/best",
    "noplaylist": True,
    "quiet": True,
    "default_search": "ytsearch1",
    "source_address": "0.0.0.0",
}

FFMPEG_OPTIONS = {
    "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
    "options": "-vn",
}


ytdl = yt_dlp.YoutubeDL(YTDL_OPTIONS)


@dataclass
class Track:
    title: str
    webpage_url: str
    duration: int
    requester: str


@dataclass
class GuildMusicState:
    queue: Deque[Track] = field(default_factory=deque)
    current: Optional[Track] = None
    text_channel_id: Optional[int] = None


class Music(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.states: dict[int, GuildMusicState] = {}

    def get_state(self, guild_id: int) -> GuildMusicState:
        if guild_id not in self.states:
            self.states[guild_id] = GuildMusicState()
        return self.states[guild_id]

    async def _extract_info(self, query: str) -> dict:
        loop = asyncio.get_running_loop()

        def run() -> dict:
            return ytdl.extract_info(query, download=False)

        return await loop.run_in_executor(None, run)

    async def _ensure_voice(self, ctx: commands.Context) -> Optional[discord.VoiceClient]:
        if not ctx.author.voice or not ctx.author.voice.channel:
            await ctx.send("❌ Önce bir ses kanalına katılmalısın.")
            return None

        voice_client = ctx.guild.voice_client
        if voice_client and voice_client.channel != ctx.author.voice.channel:
            await voice_client.move_to(ctx.author.voice.channel)
            return voice_client

        if voice_client is None:
            voice_client = await ctx.author.voice.channel.connect()

        return voice_client

    async def _play_next(self, guild: discord.Guild):
        state = self.get_state(guild.id)
        voice_client = guild.voice_client

        if not voice_client or not voice_client.is_connected():
            state.current = None
            state.queue.clear()
            return

        if not state.queue:
            state.current = None
            return

        track = state.queue.popleft()

        try:
            info = await self._extract_info(track.webpage_url)
            if "entries" in info:
                info = info["entries"][0]

            source = discord.FFmpegPCMAudio(info["url"], **FFMPEG_OPTIONS)
        except Exception:
            await self._send_message(guild, "❌ Şarkı oynatılırken hata oluştu, sıradaki şarkıya geçiliyor.")
            await self._play_next(guild)
            return

        state.current = track

        def after_playback(error: Optional[Exception]):
            if error:
                print(f"Playback error: {error}")
            self.bot.loop.call_soon_threadsafe(lambda: asyncio.create_task(self._play_next(guild)))

        voice_client.play(source, after=after_playback)

        await self._send_message(
            guild,
            f"🎶 Şimdi çalıyor: **{track.title}** (isteyen: {track.requester})",
        )

    async def _send_message(self, guild: discord.Guild, content: str):
        state = self.get_state(guild.id)
        if not state.text_channel_id:
            return

        channel = guild.get_channel(state.text_channel_id)
        if channel and isinstance(channel, discord.TextChannel):
            await channel.send(content)

    @commands.command(name="join", aliases=["katil"])
    async def join(self, ctx: commands.Context):
        voice_client = await self._ensure_voice(ctx)
        if voice_client:
            await ctx.send(f"✅ {voice_client.channel.mention} kanalına katıldım.")

    @commands.command(name="leave", aliases=["ayril"])
    async def leave(self, ctx: commands.Context):
        voice_client = ctx.guild.voice_client
        state = self.get_state(ctx.guild.id)
        state.queue.clear()
        state.current = None

        if not voice_client:
            await ctx.send("❌ Bot zaten bir ses kanalında değil.")
            return

        await voice_client.disconnect()
        await ctx.send("👋 Ses kanalından ayrıldım.")

    @commands.command(name="play", aliases=["çal", "p"])
    async def play(self, ctx: commands.Context, *, query: str):
        voice_client = await self._ensure_voice(ctx)
        if not voice_client:
            return

        state = self.get_state(ctx.guild.id)
        state.text_channel_id = ctx.channel.id

        lookup = query if URL_REGEX.search(query) else f"ytsearch1:{query}"

        try:
            info = await self._extract_info(lookup)
            if "entries" in info:
                info = info["entries"][0]
        except Exception:
            await ctx.send("❌ Şarkı bulunamadı veya yüklenemedi.")
            return

        track = Track(
            title=info.get("title", "Bilinmeyen Şarkı"),
            webpage_url=info.get("webpage_url", query),
            duration=info.get("duration") or 0,
            requester=ctx.author.display_name,
        )

        state.queue.append(track)
        await ctx.send(f"➕ Kuyruğa eklendi: **{track.title}**")

        if not voice_client.is_playing() and not voice_client.is_paused() and state.current is None:
            await self._play_next(ctx.guild)

    @commands.command(name="skip", aliases=["geç"])
    async def skip(self, ctx: commands.Context):
        voice_client = ctx.guild.voice_client
        if not voice_client or not voice_client.is_playing():
            await ctx.send("❌ Şu an çalan bir şarkı yok.")
            return

        voice_client.stop()
        await ctx.send("⏭️ Şarkı geçildi.")

    @commands.command(name="stop", aliases=["dur"])
    async def stop(self, ctx: commands.Context):
        voice_client = ctx.guild.voice_client
        state = self.get_state(ctx.guild.id)
        state.queue.clear()
        state.current = None

        if voice_client and (voice_client.is_playing() or voice_client.is_paused()):
            voice_client.stop()

        await ctx.send("⏹️ Çalma durduruldu ve kuyruk temizlendi.")

    @commands.command(name="pause", aliases=["beklet"])
    async def pause(self, ctx: commands.Context):
        voice_client = ctx.guild.voice_client
        if not voice_client or not voice_client.is_playing():
            await ctx.send("❌ Duraklatılacak bir şarkı yok.")
            return

        voice_client.pause()
        await ctx.send("⏸️ Şarkı duraklatıldı.")

    @commands.command(name="resume", aliases=["devam"])
    async def resume(self, ctx: commands.Context):
        voice_client = ctx.guild.voice_client
        if not voice_client or not voice_client.is_paused():
            await ctx.send("❌ Devam ettirilecek bir şarkı yok.")
            return

        voice_client.resume()
        await ctx.send("▶️ Şarkı devam ediyor.")

    @commands.command(name="queue", aliases=["kuyruk", "q"])
    async def queue(self, ctx: commands.Context):
        state = self.get_state(ctx.guild.id)

        if not state.current and not state.queue:
            await ctx.send("📭 Kuyruk boş.")
            return

        lines = []
        if state.current:
            lines.append(f"🎵 Şu an: **{state.current.title}**")

        if state.queue:
            lines.append("\n📜 Sıradaki şarkılar:")
            for idx, track in enumerate(list(state.queue)[:10], start=1):
                lines.append(f"{idx}. {track.title} ({track.requester})")

        await ctx.send("\n".join(lines))

    @commands.command(name="np", aliases=["nowplaying"])
    async def now_playing(self, ctx: commands.Context):
        state = self.get_state(ctx.guild.id)
        if not state.current:
            await ctx.send("❌ Şu an çalan bir şarkı yok.")
            return

        await ctx.send(f"🎶 Şu an çalıyor: **{state.current.title}**")


async def setup(bot: commands.Bot):
    await bot.add_cog(Music(bot))
