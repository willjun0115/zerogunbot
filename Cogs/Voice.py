
from asyncio import timeout
import discord
import random
import asyncio
from discord.utils import get
from discord.ext import commands
import os
import yt_dlp
from gtts import gTTS
import json
import csv

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

        if 'entries' in data:  # type: ignore
            data = data['entries'][0]  # type: ignore

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        assert filename is not None
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)


class Voice(commands.Cog, name="음성", description="음성 채널 및 보이스 클라이언트 조작에 관한 카테고리입니다."):

    def __init__(self, app):
        self.app = app
        self.quiz_task = None

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
            with yt_dlp.YoutubeDL(search_opts) as ydl:  # type: ignore
                data = await loop.run_in_executor(
                    None, lambda: ydl.extract_info(f"ytsearch5:{args}", download=False)
                )
        except Exception as e:
            await msg.edit(content=f":x: 검색 도중 에러가 발생했습니다: {e}")
            return

        if not data or 'entries' not in data or len(data['entries']) == 0:  # type: ignore
            await msg.edit(content=":x: 검색 결과가 없습니다.")
            return

        search_list = {}
        embed = discord.Embed(title=f"\"{args}\"의 검색 결과 :mag:",
                              description="번호를 입력해 선택하거나, x를 입력해 취소하세요.")
        
        entries = list(data['entries'])  # type: ignore
        num_results = min(5, len(entries))
        for n in range(num_results):
            entry = entries[n]
            video_id = entry.get('id')
            get_title = entry.get('title', '제목 없음')
            get_href = f"https://www.youtube.com/watch?v={video_id}"
            get_uploader = entry.get('uploader', '알 수 없음')
            duration_sec = entry.get('duration')
            
            if duration_sec:
                mins, secs = divmod(duration_sec, 60)
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
                assert isinstance(select, str)
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
        name="노래맞추기", aliases=["노래퀴즈", "musicquiz"],
        help="노래를 듣고 제목을 맞춰보세요!"
             "\n사용법: %노래맞추기 [force/f] [loop=n] [tag=kor|eng|jap|all]"
             "\n예시: %노래맞추기 loop=5"
             "\n예시: %노래맞추기 force loop=3 tag=kor+jap", usage="[force/f] [loop=n] [tag=kor|eng|jap|all]"
    )
    async def music_quiz(self, ctx, *args):
        force = False
        loop_count = 1
        tag_filters = []

        for arg in args:
            arg_lower = arg.lower()
            if arg_lower in ["force", "f"]:
                force = True
            elif arg_lower.startswith("loop="):
                try:
                    loop_count = int(arg_lower.split("=")[1])
                except ValueError:
                    pass
            elif arg_lower.startswith("tag=") or arg_lower.startswith("t="):
                val = arg_lower.split("=")[1]
                tag_filters = [t.strip() for t in val.split("+") if t.strip()]

        loop_count = max(1, min(loop_count, 30))

        if self.quiz_task and not self.quiz_task.done():
            if force:
                await ctx.send("이전 퀴즈 프로세스 및 루프 대기를 강제 종료하고 새 퀴즈를 시작합니다... :stop_sign:")
                self.quiz_task.cancel()
                try:
                    await self.quiz_task
                except asyncio.CancelledError:
                    pass
                voice = get(self.app.voice_clients, guild=ctx.guild)
                if voice and voice.is_connected() and voice.is_playing():
                    voice.stop()
            else:
                await ctx.send("이미 노래맞추기가 진행 중입니다. 강제 종료하고 다시 시작하려면 `force` 또는 `f` 옵션을 사용해 주세요. (예: `%노래맞추기 force`)")
                return

        self.quiz_task = asyncio.create_task(self._run_quiz(ctx, tag_filters, loop_count))

    async def _run_quiz(self, ctx, tag_filters, loop_count):
        loop = self.app.loop or asyncio.get_event_loop()
        try:
            await self.ensure_voice(ctx)
            channel = ctx.author.voice.channel
            members = [m for m in channel.members if m.bot is False]
            if len(members) < 1:
                await ctx.send("채널에 최소 1명 이상 있어야 시작 가능합니다.")
                return

            def normalize(t: str) -> str:
                return t.lower().replace(" ", "").replace("'", "").replace("`", "").replace('"', "")

            # 1. 파일 목록(CSV) 로딩
            csv_songs = []
            csv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "songs.csv")
            try:
                with open(csv_path, "r", encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        title = row.get("title", "").strip()
                        artist = row.get("artist", "").strip()
                        if not title:
                            continue
                        
                        synonyms_raw = row.get("synonyms") or ""
                        synonyms = [s.strip() for s in synonyms_raw.split("|") if s.strip()]
                        
                        tags_raw = row.get("tags") or ""
                        tags = [t.strip() for t in tags_raw.split("|") if t.strip()]
                        
                        link = row.get("link", "").strip()
                        
                        if tag_filters and "all" not in tag_filters:
                            if not any(f in tags for f in tag_filters):
                                continue
                        
                        csv_songs.append({
                            "type": "csv",
                            "title": title,
                            "artist": artist,
                            "synonyms": synonyms,
                            "tags": tags,
                            "link": link
                        })
            except Exception as e:
                await ctx.send(f"⚠️ 곡 데이터베이스(`songs.csv`)를 읽는 데 실패했습니다 (로컬 곡 목록 제외하고 진행): {e}")

            # 2. 플레이리스트 목록 로딩
            playlist_songs = []
            msg_load = None
            if not tag_filters or "eng" in tag_filters or "all" in tag_filters:
                url = "https://www.youtube.com/playlist?list=PLINKc5JL2InSNdUPIxLdvUWMTn0lnzpom"
                msg_load = await ctx.send("유튜브 플레이리스트 및 곡 정보를 로딩하고 있습니다... :hourglass_flowing_sand:")
                playlist_opts = {
                    'extract_flat': True,
                    'skip_download': True,
                    'quiet': True,
                    'no_warnings': True,
                }
                try:
                    with yt_dlp.YoutubeDL(playlist_opts) as ydl:  # type: ignore
                        data = await loop.run_in_executor(
                            None, lambda: ydl.extract_info(url, download=False)
                        )
                    if data and 'entries' in data:
                        for entry in data['entries']:
                            music_title = entry.get('title') or '알 수 없는 곡'
                            if "(" in music_title:
                                music_title = music_title[:music_title.index("(")]
                            music_title = music_title.strip()
                            video_id = entry.get('id')
                            music_url = f"https://www.youtube.com/watch?v={video_id}"
                            
                            playlist_songs.append({
                                "type": "playlist",
                                "title": music_title,
                                "artist": "",
                                "synonyms": [],
                                "tags": ["eng"],
                                "link": music_url
                            })
                except Exception as e:
                    await ctx.send(f"⚠️ 플레이리스트 정보를 불러오지 못했습니다: {e}")

            # 통합 목록 병합
            all_songs = csv_songs + playlist_songs

            if not all_songs:
                filter_text = "+".join(tag_filters) if tag_filters else "전체"
                if msg_load:
                    await msg_load.edit(content=f":x: '{filter_text}' 매칭되는 곡 목록이 전혀 없습니다.")
                else:
                    await ctx.send(f":x: '{filter_text}' 매칭되는 곡 목록이 전혀 없습니다.")
                return

            if msg_load:
                await msg_load.edit(content=f"로딩 완료! (로컬 곡: {len(csv_songs)}개, 플레이리스트: {len(playlist_songs)}개 | 총 {len(all_songs)}개)")
            else:
                filter_text = "+".join(tag_filters) if tag_filters else "전체"
                await ctx.send(f"📢 퀴즈 시작! (필터: {filter_text} | 총 {len(all_songs)}곡 대상)")

            for loop_idx in range(loop_count):
                if loop_count > 1:
                    await ctx.send(f"📢 **{loop_idx + 1}번째 퀴즈 시작!** (총 {loop_count}회 진행 중)")
                
                await self.ensure_voice(ctx)

                voice = get(self.app.voice_clients, guild=ctx.guild)
                if voice and voice.is_playing():
                    voice.stop()

                # 곡 무작위 선택
                song = random.choice(all_songs)
                song_type = song["type"]
                title = song["title"]
                artist = song["artist"]
                link = song["link"]
                synonyms = song["synonyms"]
                tags = song["tags"]

                if song_type == "csv":
                    official_title = f"{artist} - {title}" if artist else title
                else:
                    official_title = title

                player = None
                music_url = None

                # 재생 시도
                msg = await ctx.send(f"음원을 탐색합니다... :hourglass_flowing_sand:")
                # 1. 우선순위 링크 시도
                if link:
                    try:
                        async with ctx.typing():
                            player = await YTDLSource.from_url(link, loop=self.app.loop, stream=True)
                        music_url = link
                        await msg.edit(content=f"음원을 재생합니다! tag:{', '.join(tags)} 🎶")
                    except Exception as e:
                        if song_type == "csv":
                            await msg.edit(content=f"⚠️ 저장된 링크 재생에 실패하여 유튜브 검색으로 재시도합니다. (사유: {e})")
                        player = None

                # 2. 링크 재생 실패 및 검색 필요 시
                if not player:
                    if song_type == "csv":
                        query = f"{artist} {title}"
                        search_opts = {
                            'extract_flat': True,
                            'skip_download': True,
                            'quiet': True,
                            'no_warnings': True,
                        }
                        try:
                            with yt_dlp.YoutubeDL(search_opts) as ydl:  # type: ignore
                                data = await loop.run_in_executor(
                                    None, lambda: ydl.extract_info(f"ytsearch1:{query}", download=False)
                                )
                        except Exception as e:
                            await msg.edit(content=f":x: 음원 검색 중 에러가 발생했습니다: {e}")
                            return

                        if not data or 'entries' not in data or len(data['entries']) == 0:  # type: ignore
                            await msg.edit(content=f":x: '{query}' 검색 결과가 없습니다.")
                            return

                        entry = data['entries'][0]  # type: ignore
                        video_id = entry.get('id')
                        music_url = f"https://www.youtube.com/watch?v={video_id}"

                        await msg.edit(content=f"음원을 재생합니다! tag:{', '.join(tags)} 🎶")

                        try:
                            async with ctx.typing():
                                player = await YTDLSource.from_url(music_url, loop=self.app.loop, stream=True)
                        except Exception as e:
                            await msg.edit(content=f":x: 검색된 음원 추출 중 에러가 발생했습니다: {e}")
                            return
                    else:
                        await ctx.send(f":x: 플레이리스트 음원({title}) 재생에 실패하여 다음 곡으로 건너뜁니다.")
                        continue

                # 오디오 재생
                ctx.voice_client.play(player, after=lambda e: print(f'Player error: {e}') if e else None)

                # 정답 리스트 구축
                answers = [title] + synonyms
                normalized_answers = [normalize(ans) for ans in answers if ans]

                def check(m):
                    if m.author not in channel.members or m.channel != ctx.channel:
                        return False
                    return normalize(m.content) in normalized_answers

                try:
                    message = await self.app.wait_for("message", check=check, timeout=100.0)
                except asyncio.TimeoutError:
                    await ctx.send(f"시간 초과! (정답: {official_title})")
                else:
                    await ctx.send(f"🎉 {message.author.display_name} 님 정답! (정답: {official_title})")

                # 한 라운드가 끝나면 음성 정지 및 대기 시간 부여
                voice = get(self.app.voice_clients, guild=ctx.guild)
                if voice and voice.is_playing():
                    voice.stop()

                # 마지막 루프가 아니면 잠깐 대기 후 다음 곡 진행
                if loop_idx < loop_count - 1:
                    await ctx.send("3초 뒤 다음 퀴즈가 시작됩니다... ⏱️")
                    await asyncio.sleep(3.0)

            await ctx.send("📢 **모든 노래맞추기 퀴즈가 종료되었습니다!**")

        except asyncio.CancelledError:
            voice = get(self.app.voice_clients, guild=ctx.guild)
            if voice and voice.is_playing():
                voice.stop()
            raise
        except Exception as e:
            await ctx.send(f":x: 퀴즈 진행 중 예상치 못한 오류가 발생했습니다: {e}")
            voice = get(self.app.voice_clients, guild=ctx.guild)
            if voice and voice.is_playing():
                voice.stop()

    async def ensure_voice(self, ctx):
        if ctx.voice_client is None:
            await self.join_ch(ctx)


async def setup(app):
    await app.add_cog(Voice(app))
