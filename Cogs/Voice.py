
import discord
import random
import asyncio
from discord.utils import get
from discord.ext import commands
from discord import FFmpegPCMAudio
import os
import yt_dlp
from gtts import gTTS

ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0'
}

ffmpeg_options = {
    'options': '-vn'
}

ytdl = yt_dlp.YoutubeDL(ytdl_format_options)


class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)

        self.data = data

        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

        if 'entries' in data:
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)


class Voice(commands.Cog, name="음성", description="음성 채널 및 보이스 클라이언트 조작에 관한 카테고리입니다."):

    def __init__(self, app):
        self.app = app

    def clear_mp3(self):
        for file in os.listdir("./"):
            if file.endswith(".mp3"):
                os.remove(file)

    @commands.check_any(commands.has_role("DJ"), commands.has_permissions(administrator=True))
    @commands.command(
        name="연결", aliases=["connect", "c", "join"],
        help="음성 채널에 연결합니다.", usage="*"
    )
    async def join_ch(self, ctx):
        voice = get(self.app.voice_clients, guild=ctx.guild)
        channel = ctx.author.voice.channel
        try:
            if voice:
                if voice.is_connected():
                    await voice.move_to(channel)
                else:
                    await voice.disconnect(force=True)
                    voice = await channel.connect()
            else:
                voice = await channel.connect()
        except Exception as e:
            print(f"Connection error: {e}")
            await ctx.send(":no_entry: 연결 오류가 발생했습니다.")
        else:
            await ctx.send(channel.name + "에 연결합니다.")

    @commands.check_any(commands.has_role("DJ"), commands.has_permissions(administrator=True))
    @commands.command(
        name="퇴장", aliases=["연결해제", "연결끊기", "disconnect", "dc", "leave"],
        help="음성 채널을 나갑니다.", usage="*"
    )
    async def leave_ch(self, ctx):
        await ctx.voice_client.disconnect()
        await ctx.send("연결을 끊습니다.")
        self.clear_mp3()

    @commands.check_any(commands.has_role("DJ"), commands.has_permissions(administrator=True))
    @commands.command(
        name="tts", aliases=["TTS"],
        help="입력받은 문자열을 tts 음성으로 출력합니다.", usage="* str()"
    )
    async def _tts(self, ctx, *, msg):
        await self.ensure_voice(ctx)
        for file in os.listdir("./"):
            if file.startswith("tts_ko"):
                os.remove(file)
        tts = gTTS(text=msg, lang='ko', slow=False)
        tts.save('tts_ko.mp3')
        ctx.voice_client.play(discord.FFmpegPCMAudio('tts_ko.mp3'),
                              after=lambda e: print(f'Player error: {e}') if e else None)

    @commands.check_any(commands.has_role("DJ"), commands.has_permissions(administrator=True))
    @commands.command(
        name="재생", aliases=["play", "p"],
        help="유튜브 url을 통해 음악을 재생합니다."
             "\nurl 뒤에 -s를 붙이면 스트리밍으로 재생합니다.", usage="* str(*url*) (-s)"
    )
    async def play_song(self, ctx, url: str, stream=None):
        await self.ensure_voice(ctx)
        if stream == '-s':
            stream = True
        else:
            stream = False
        async with ctx.typing():
            player = await YTDLSource.from_url(url, loop=self.app.loop, stream=stream)
        ctx.voice_client.play(player, after=lambda e: print(f'Player error: {e}') if e else None)
        msg = f'Now playing: {player.title}'
        if stream is True:
            msg = f'Now streaming: {player.title}'
        await ctx.send(msg)

    @commands.check_any(commands.has_role("DJ"), commands.has_permissions(administrator=True))
    @commands.command(
        name="검색", aliases=["search"],
        help="유튜브 검색을 통해 목록을 가져옵니다."
             "\n채팅으로 1~5의 숫자를 치면 해당 번호의 링크를 재생합니다.", usage="* str()"
    )
    async def yt_search(self, ctx, *, args):
        msg = await ctx.send("데이터 수집 중... :mag:")
        search_opts = {
            'extract_flat': True,
            'skip_download': True,
            'quiet': True,
            'no_warnings': True,
        }
        loop = self.app.loop or asyncio.get_event_loop()
        try:
            with yt_dlp.YoutubeDL(search_opts) as ydl:
                data = await loop.run_in_executor(
                    None, lambda: ydl.extract_info(f"ytsearch5:{args}", download=False)
                )
        except Exception as e:
            await msg.edit(content=f":x: 검색 도중 에러가 발생했습니다: {e}")
            return

        if not data or 'entries' not in data or len(data['entries']) == 0:
            await msg.edit(content=":x: 검색 결과가 없습니다.")
            return

        search_list = {}
        embed = discord.Embed(title=f"\"{args}\"의 검색 결과 :mag:",
                              description="번호를 입력해 선택하거나, x를 입력해 취소하세요.")
        
        entries = data['entries']
        num_results = min(5, len(entries))
        for n in range(num_results):
            entry = entries[n]
            video_id = entry.get('id')
            get_title = entry.get('title', '제목 없음')
            get_href = f"https://www.youtube.com/watch?v={video_id}"
            get_uploader = entry.get('uploader', '알 수 없음')
            duration_sec = entry.get('duration')
            
            if duration_sec:
                mins, secs = divmod(int(duration_sec), 60)
                hours, mins = divmod(mins, 60)
                if hours > 0:
                    duration_str = f"{hours}:{mins:02d}:{secs:02d}"
                else:
                    duration_str = f"{mins}:{secs:02d}"
            else:
                duration_str = "길이 정보 없음"

            get_info = f"게시자: {get_uploader} | 길이: {duration_str}"
            search_list[n+1] = get_href
            embed.add_field(name=f"> {str(n+1)}. {get_title}", value=get_info, inline=False)
            
        await msg.edit(content=None, embed=embed)

        answer_list = ["X", "x"] + [str(i) for i in range(1, num_results + 1)]

        def check(m):
            return m.content in answer_list and m.author == ctx.author and m.channel == ctx.channel

        try:
            message = await self.app.wait_for("message", check=check, timeout=60.0)
        except asyncio.TimeoutError:
            await msg.edit(content="시간 초과!", delete_after=2)
        else:
            if message.content in ["x", "X"]:
                await msg.edit(content=":x: 취소했습니다.", delete_after=2)
            else:
                await msg.delete()
                select = search_list.get(int(message.content))
                await self.ensure_voice(ctx)
                await self.play_song(ctx, select)

    @commands.check_any(commands.has_role("DJ"), commands.has_permissions(administrator=True))
    @commands.command(
        name="정지", aliases=["stop", "s"],
        help="음악 재생을 정지합니다.", usage="*"
    )
    async def stop_song(self, ctx):
        voice = get(self.app.voice_clients, guild=ctx.guild)
        if voice and voice.is_connected():
            voice.stop()

    @commands.command(
        name="노래맞추기", aliases=["musicquiz"],
        help="유튜브 플레이리스트에서 랜덤으로 곡을 재생합니다."
             "\n 곡의 제목을 맞춰보세요!", usage="* str()"
    )
    async def music_quiz(self, ctx):
        await self.ensure_voice(ctx)
        channel = ctx.author.voice.channel
        members = [m for m in channel.members if m.bot is False]
        if len(members) < 1:
            await ctx.send("채널에 최소 1명 이상 있어야 시작 가능합니다.")
        else:
            url = "https://www.youtube.com/playlist?list=PLINKc5JL2InSNdUPIxLdvUWMTn0lnzpom"
            msg = await ctx.send("플레이리스트 정보를 불러오고 있습니다... :hourglass_flowing_sand:")
            playlist_opts = {
                'extract_flat': True,
                'skip_download': True,
                'quiet': True,
                'no_warnings': True,
            }
            loop = self.app.loop or asyncio.get_event_loop()
            try:
                with yt_dlp.YoutubeDL(playlist_opts) as ydl:
                    data = await loop.run_in_executor(
                        None, lambda: ydl.extract_info(url, download=False)
                    )
            except Exception as e:
                await msg.edit(content=f":x: 플레이리스트 조회 중 에러가 발생했습니다: {e}")
                return

            if not data or 'entries' not in data or len(data['entries']) == 0:
                await msg.edit(content=":x: 플레이리스트 항목이 없거나 비어 있습니다.")
                return

            entries = data['entries']
            max_video = len(entries)
            await msg.edit(content=f"{max_video} 개의 곡 중 하나를 재생합니다.")
            
            n = random.randint(0, max_video - 1)
            video = entries[n]
            music_title = video.get('title', '알 수 없는 곡')
            if "(" in music_title:
                music_title = music_title[:music_title.index("(")]
            music_title = music_title.strip()
            
            video_id = video.get('id')
            music_url = f"https://www.youtube.com/watch?v={video_id}"

            async with ctx.typing():
                player = await YTDLSource.from_url(music_url, loop=self.app.loop, stream=True)

            ctx.voice_client.play(player, after=lambda e: print(f'Player error: {e}') if e else None)

            def check(m):
                return m.content.lower() == music_title.lower() and m.author in channel.members and m.channel == ctx.channel

            try:
                message = await self.app.wait_for("message", check=check, timeout=100.0)
            except asyncio.TimeoutError:
                await ctx.send(f"시간 초과! (정답: {music_title})")
            else:
                await ctx.send(message.author.display_name + " 님 정답!")

    async def ensure_voice(self, ctx):
        if ctx.voice_client is None:
            await self.join_ch(ctx)


async def setup(app):
    await app.add_cog(Voice(app))
