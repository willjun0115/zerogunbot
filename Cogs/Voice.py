
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
from typing import Any
from Utils import token_cost, require_voice
from SpotifyHelper import spotify_helper

ytdl_format_options: Any = {
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
    'source_address': '0.0.0.0',
    'socket_timeout': 10,
}

ffmpeg_options: dict[str, Any] = {
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

        # If url is not an HTTP link, perform a flat search to select the first video entry
        if not url.startswith(('http://', 'https://')):
            search_opts: Any = {
                'extract_flat': True,
                'skip_download': True,
                'quiet': True,
                'no_warnings': True,
                'socket_timeout': 10,
            }
            with yt_dlp.YoutubeDL(search_opts) as ydl:
                search_data = await loop.run_in_executor(
                    None, lambda: ydl.extract_info(f"ytsearch10:{url}", download=False)
                )

            video_url = None
            if search_data and 'entries' in search_data:
                for entry in search_data['entries']:
                    ie_key = entry.get('ie_key', '')
                    entry_url = entry.get('url') or ''
                    if ie_key == 'Youtube' or 'watch?v=' in entry_url:
                        video_url = entry_url
                        break

            if not video_url:
                raise ValueError(f"'{url}'에 매칭되는 유튜브 동영상을 찾을 수 없습니다.")
            url = video_url

        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

        if 'entries' in data:  # type: ignore
            data = data['entries'][0]  # type: ignore

        filename = data.get('url') if stream else ytdl.prepare_filename(data)
        assert filename is not None
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)


class Voice(commands.Cog, name="음성", description="음성 채널 및 보이스 클라이언트 조작에 관한 카테고리입니다."):

    def __init__(self, app):
        self.app = app
        self.quiz_task = None
        self.music_queues = {}
        self.now_playing = {}
        self.queue_loop = {}       # guild_id -> bool
        self.queue_auto = {}       # guild_id -> target_n (int) or None
        self.auto_history = {}     # guild_id -> set of normalized titles
        self.auto_fetching = {}    # guild_id -> bool

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
        if not ctx.author.voice or not ctx.author.voice.channel:
            await ctx.send(":no_entry: 먼저 음성 채널에 입장해 주세요.")
            return False
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
            return False
        else:
            await ctx.send(channel.name + "에 연결합니다.")
            return True

    @commands.check_any(commands.has_role("DJ"), commands.has_permissions(administrator=True))
    @commands.command(
        name="퇴장", aliases=["연결해제", "연결끊기", "disconnect", "dc", "leave"],
        help="음성 채널을 나갑니다.", usage="*"
    )
    async def leave_ch(self, ctx):
        if ctx.guild:
            self.music_queues.pop(ctx.guild.id, None)
            self.now_playing.pop(ctx.guild.id, None)
            self.queue_loop.pop(ctx.guild.id, None)
            self.queue_auto.pop(ctx.guild.id, None)
            self.auto_history.pop(ctx.guild.id, None)
        if ctx.voice_client:
            await ctx.voice_client.disconnect()
            await ctx.send("연결을 끊습니다.")
        else:
            await ctx.send(":no_entry: 봇이 음성 채널에 연결되어 있지 않습니다.")
        self.clear_mp3()

    @commands.check_any(commands.has_role("DJ"), commands.has_permissions(administrator=True))
    @require_voice()
    @token_cost(5)
    @commands.command(
        name="tts", aliases=["TTS"],
        help="입력받은 문자열을 tts 음성으로 출력합니다. (소모: 5 :coin:)", usage="* str()"
    )
    async def _tts(self, ctx, *, msg):
        if not await self.ensure_voice(ctx):
            await self.app.db.add_coins(ctx.author.id, 5)
            return
        try:
            for file in os.listdir("./"):
                if file.startswith("tts_ko"):
                    os.remove(file)
            tts = gTTS(text=msg, lang='ko', slow=False)
            tts.save('tts_ko.mp3')
            if ctx.voice_client:
                ctx.voice_client.play(discord.FFmpegPCMAudio('tts_ko.mp3'),
                                      after=lambda e: print(f'Player error: {e}') if e else None)
        except Exception as e:
            await self.app.db.add_coins(ctx.author.id, 5)
            await ctx.send(f":x: TTS 생성 중 오류가 발생하여 5 토큰이 환불되었습니다: {e}")

    async def find_clean_audio_url(self, artist: str, title: str, target_duration_sec: float | None = None) -> str:
        """
        뮤직비디오 인트로/대사, 라이브, 직캠, 커버 등을 배제하고
        유튜브에서 가장 순수한 공식 음원(Topic / Official Audio) 영상 URL을 선별합니다.
        """
        clean_artist = (artist or "").strip()
        clean_title = (title or "").strip()
        base_query = f"{clean_artist} - {clean_title}".strip(" -")
        search_query = f"{base_query} Topic".strip()

        search_opts: Any = {
            'extract_flat': True,
            'skip_download': True,
            'quiet': True,
            'no_warnings': True,
            'socket_timeout': 10,
        }
        loop = self.app.loop or asyncio.get_event_loop()

        try:
            with yt_dlp.YoutubeDL(search_opts) as ydl:
                data = await loop.run_in_executor(
                    None, lambda: ydl.extract_info(f"ytsearch5:{search_query}", download=False)
                )
        except Exception:
            return f"ytsearch:{base_query}"

        entries = data.get('entries') if data else []
        if not entries:
            try:
                with yt_dlp.YoutubeDL(search_opts) as ydl:
                    data = await loop.run_in_executor(
                        None, lambda: ydl.extract_info(f"ytsearch5:{base_query} Audio", download=False)
                    )
                entries = data.get('entries') if data else []
            except Exception:
                return f"ytsearch:{base_query}"

        if not entries:
            return f"ytsearch:{base_query}"

        def calculate_audio_score(entry):
            v_title = (entry.get('title') or '').lower()
            uploader = (entry.get('uploader') or '').lower()
            dur = entry.get('duration') or 0

            score = 100

            # 1. 긍정 채널 및 공식 음원 가산점
            if 'topic' in uploader or 'official' in uploader:
                score += 35
            if 'audio' in v_title or '음원' in v_title:
                score += 25

            # 2. 노이즈 및 비음원 감점 (MV 인트로, 라이브, 커버 등 배제)
            for neg in ['[mv]', 'm/v', 'music video', '뮤직비디오', 'official mv']:
                if neg in v_title:
                    score -= 40
            for neg in ['live', '라이브', 'concert', 'fancam', '직캠', 'stage']:
                if neg in v_title:
                    score -= 70
            for neg in ['cover', '커버', 'reaction', '1hour', '1시간', 'mr', 'instrumental', 'karaoke', '노래방', 'dance practice', '안무']:
                if neg in v_title:
                    score -= 90

            # 3. 재생 시간(Duration) 정밀 매칭
            if target_duration_sec and dur > 0:
                diff = abs(dur - target_duration_sec)
                if diff <= 3:
                    score += 50
                elif diff <= 7:
                    score += 25
                elif diff <= 15:
                    score += 10
                elif diff > 25:
                    score -= 40
                elif diff > 60:
                    score -= 100

            return score

        best_entry = max(entries, key=calculate_audio_score)
        if best_entry and best_entry.get('id'):
            video_url = f"https://www.youtube.com/watch?v={best_entry['id']}"
            score = calculate_audio_score(best_entry)
            print(f"[Music] 선별된 유튜브 음원: {best_entry.get('title')} ({best_entry.get('uploader')}) | 점수: {score}점 | URL: {video_url}")
            return video_url

        fallback_url = f"ytsearch:{base_query}"
        print(f"[Music] 선별 실패로 기본 유튜브 검색 사용: {fallback_url}")
        return fallback_url

    async def fill_auto_queue(self, guild_id: int, target_channel=None):
        """대기열 수가 목표치 N보다 적을 때 스포티파이 추천 곡으로 대기열을 자동 보충합니다."""
        target_n = self.queue_auto.get(guild_id)
        if not target_n or target_n <= 0:
            return

        if self.auto_fetching.get(guild_id, False):
            return
        self.auto_fetching[guild_id] = True

        try:
            queue = self.music_queues.setdefault(guild_id, [])
            history = self.auto_history.setdefault(guild_id, set())

            if len(queue) >= target_n:
                return

            needed = target_n - len(queue)

            now = self.now_playing.get(guild_id)
            seed_query = None
            if queue:
                seed_query = queue[-1].get("title")
            elif now:
                seed_query = now.get("title")

            if not seed_query:
                seed_query = "K-Pop Hits"

            recs, _ = spotify_helper.get_recommendations(seed_query, limit=max(needed + 3, 5))
            if not recs:
                return

            added_count = 0
            guild = self.app.get_guild(guild_id)

            for cand in recs:
                cand_title = cand.get("title")
                cand_artist = cand.get("artist")
                if not cand_title:
                    continue

                full_name = f"{cand_artist} - {cand_title}"
                clean_name = f"{cand_artist} {cand_title}".lower().replace(" ", "")

                if clean_name in history or any(clean_name == q.get("title", "").lower().replace(" ", "") for q in queue):
                    continue

                clean_url = await self.find_clean_audio_url(cand_artist, cand_title)
                history.add(clean_name)
                if len(history) > 50:
                    history.pop()

                channel = target_channel or (now.get("channel") if now else None) or (queue[0].get("channel") if queue else None)

                queue.append({
                    "url": clean_url,
                    "title": full_name,
                    "stream": True,
                    "channel": channel,
                    "requester": self.app.user,
                    "is_auto": True
                })
                added_count += 1

                if len(queue) >= target_n:
                    break

            if added_count > 0:
                print(f"[AutoQueue] {guild.name if guild else guild_id}: 자동 추천 {added_count}곡 추가 완료 (대기열: {len(queue)}/{target_n})")
        finally:
            self.auto_fetching[guild_id] = False

    async def play_next_song(self, guild_id: int):
        """대기열에서 다음 곡을 꺼내 자동으로 이어서 재생합니다."""
        guild = self.app.get_guild(guild_id)
        if not guild:
            return
        voice = get(self.app.voice_clients, guild=guild)
        if not voice or not voice.is_connected():
            if guild_id in self.music_queues:
                self.music_queues[guild_id].clear()
            self.now_playing.pop(guild_id, None)
            return

        # 루프(loop) 모드: 직전에 끝난 곡이 있으면 대기열 맨 뒤로 재등록
        prev_track = self.now_playing.get(guild_id)
        if prev_track and self.queue_loop.get(guild_id, False):
            self.music_queues.setdefault(guild_id, []).append({
                "url": prev_track["url"],
                "title": prev_track["title"],
                "stream": prev_track.get("stream", True),
                "channel": prev_track.get("channel"),
                "requester": prev_track.get("requester"),
                "is_auto": prev_track.get("is_auto", False)
            })

        queue = self.music_queues.get(guild_id, [])

        # 대기열이 비었지만 자동 추천(Auto) 모드가 켜져 있다면 보충 시도
        if not queue and self.queue_auto.get(guild_id):
            await self.fill_auto_queue(guild_id)
            queue = self.music_queues.get(guild_id, [])

        if not queue:
            self.now_playing.pop(guild_id, None)
            return

        next_track = queue.pop(0)
        url = next_track["url"]
        stream = next_track.get("stream", True)
        channel = next_track.get("channel")
        requester = next_track.get("requester")

        # 자동 추천(Auto) 모드가 켜져 있다면, 곡이 빠져나간 만큼 백그라운드 자동 보충
        if self.queue_auto.get(guild_id):
            asyncio.create_task(self.fill_auto_queue(guild_id, target_channel=channel))

        try:
            player = await YTDLSource.from_url(url, loop=self.app.loop, stream=stream)
            self.now_playing[guild_id] = {
                "title": player.title,
                "requester": requester,
                "url": url,
                "stream": stream,
                "channel": channel,
                "is_auto": next_track.get("is_auto", False)
            }

            def after_callback(e):
                if e:
                    print(f"Player error: {e}")
                asyncio.run_coroutine_threadsafe(self.play_next_song(guild_id), self.app.loop)

            voice.play(player, after=after_callback)

            if channel:
                req_name = "🤖 자동추천" if next_track.get("is_auto") else (requester.display_name if requester else "알 수 없음")
                await channel.send(f"🎶 **다음 곡 재생:** {player.title} (신청: {req_name})")
        except Exception as e:
            print(f"[Queue Error] 다음 곡 재생 실패 ({url}): {e}")
            if channel:
                await channel.send(f":warning: 다음 곡을 재생하지 못했습니다: {e}\n그 다음 대기곡으로 넘어갑니다.")
            await self.play_next_song(guild_id)

    @commands.check_any(commands.has_role("DJ"), commands.has_permissions(administrator=True))
    @require_voice()
    @token_cost(10)
    @commands.command(
        name="재생", aliases=["play", "p"],
        help="유튜브 또는 스포티파이 url/곡명으로 음악을 재생합니다. (소모: 10 :coin:)"
             "\nurl 뒤에 -s를 붙이면 스트리밍으로 재생합니다.", usage="* str(*url 또는 곡명*) (-s)"
    )
    async def play_song(self, ctx, url: str, stream=None):
        if not await self.ensure_voice(ctx):
            await self.app.db.add_coins(ctx.author.id, 10)
            return
        if stream == '-s':
            stream = True
        else:
            stream = False
        try:
            if "spotify.com/track" in url or "spotify:track" in url:
                track_info = spotify_helper.search_track(url)
                if track_info and track_info.get("title"):
                    artist = track_info.get("artist") or ""
                    title = track_info.get("title") or ""
                    dur_ms = track_info.get("duration_ms")
                    target_dur_sec = (dur_ms / 1000.0) if dur_ms else None

                    await ctx.send(f":mag: 스포티파이 곡 감지: **{artist} - {title}**\n:headphones: 뮤비 인트로/라이브를 배제하고 공식 스튜디오 음원을 탐색합니다...")
                    url = await self.find_clean_audio_url(artist, title, target_dur_sec)
            elif not url.startswith("http://") and not url.startswith("https://"):
                await ctx.send(f":mag: **{url}** 공식 스튜디오 음원을 탐색합니다... :headphones:")
                url = await self.find_clean_audio_url("", url, None)

            voice = ctx.voice_client

            # 대기열 큐 초기화 (길드별)
            if ctx.guild.id not in self.music_queues:
                self.music_queues[ctx.guild.id] = []

            # 이미 음악이 재생 중이거나 일시 정지 중인 경우 -> 큐에 등록!
            if voice and (voice.is_playing() or voice.is_paused()):
                track_title = url
                try:
                    search_opts = {'extract_flat': True, 'skip_download': True, 'quiet': True}
                    with yt_dlp.YoutubeDL(search_opts) as ydl:
                        info = await self.app.loop.run_in_executor(None, lambda: ydl.extract_info(url, download=False))
                        if info:
                            if 'entries' in info and info['entries']:
                                track_title = info['entries'][0].get('title', url)
                            else:
                                track_title = info.get('title', url)
                except Exception:
                    pass

                self.music_queues[ctx.guild.id].append({
                    "url": url,
                    "title": track_title,
                    "stream": stream,
                    "channel": ctx.channel,
                    "requester": ctx.author
                })
                queue_len = len(self.music_queues[ctx.guild.id])
                await ctx.send(
                    f"📑 **대기열에 추가되었습니다!** (대기 순번: {queue_len}번째)\n"
                    f"곡명: **{track_title}**"
                )
                return

            # 재생 중이 아닌 경우 즉시 재생 시작
            async with ctx.typing():
                player = await YTDLSource.from_url(url, loop=self.app.loop, stream=stream)
            if voice:
                self.now_playing[ctx.guild.id] = {
                    "title": player.title,
                    "requester": ctx.author,
                    "url": url,
                    "stream": stream,
                    "channel": ctx.channel,
                    "is_auto": False
                }

                def after_callback(e):
                    if e:
                        print(f'Player error: {e}')
                    asyncio.run_coroutine_threadsafe(self.play_next_song(ctx.guild.id), self.app.loop)

                voice.play(player, after=after_callback)
                msg = f'Now playing: {player.title}'
                if stream is True:
                    msg = f'Now streaming: {player.title}'
                await ctx.send(msg)
        except Exception as e:
            await self.app.db.add_coins(ctx.author.id, 10)
            await ctx.send(f":x: 음악 재생 중 오류가 발생하여 10 토큰이 환불되었습니다: {e}")

    @commands.check_any(commands.has_role("DJ"), commands.has_permissions(administrator=True))
    @token_cost(10)
    @commands.command(
        name="검색", aliases=["search"],
        help="유튜브 검색을 통해 목록을 가져옵니다. (소모: 10 :coin:)"
             "\n채팅으로 1~5의 숫자를 치면 해당 번호의 링크를 재생합니다.", usage="* str()"
    )
    async def yt_search(self, ctx, *, args):
        msg = await ctx.send("데이터 수집 중... :mag:")
        search_opts: Any = {
            'extract_flat': True,
            'skip_download': True,
            'quiet': True,
            'no_warnings': True,
            'socket_timeout': 10,
        }
        loop = self.app.loop or asyncio.get_event_loop()
        try:
            with yt_dlp.YoutubeDL(search_opts) as ydl:
                data = await loop.run_in_executor(
                    None, lambda: ydl.extract_info(f"ytsearch10:{args}", download=False)
                )
        except Exception as e:
            await self.app.db.add_coins(ctx.author.id, 10)
            await msg.edit(content=f":x: 검색 도중 에러가 발생하여 10 토큰이 환불되었습니다: {e}")
            return

        if not data or 'entries' not in data or len(data['entries']) == 0:  # type: ignore
            await self.app.db.add_coins(ctx.author.id, 10)
            await msg.edit(content=":x: 검색 결과가 없어 10 토큰이 환불되었습니다.")
            return

        # Filter entries to only keep videos (exclude channels, playlists)
        video_entries = []
        for entry in data['entries']:
            ie_key = entry.get('ie_key', '')
            entry_url = entry.get('url') or ''
            if ie_key == 'Youtube' or 'watch?v=' in entry_url:
                video_entries.append(entry)

        if not video_entries:
            await self.app.db.add_coins(ctx.author.id, 10)
            await msg.edit(content=":x: 재생 가능한 영상 결과가 없어 10 토큰이 환불되었습니다.")
            return

        search_list = {}
        embed = discord.Embed(title=f"\"{args}\"의 검색 결과 :mag:",
                              description="번호를 입력해 선택하거나, x를 입력해 취소하세요.")

        num_results = min(5, len(video_entries))
        for n in range(num_results):
            entry = video_entries[n]
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
        help="음악 재생을 정지하고 대기열 및 옵션을 모두 초기화합니다.", usage="*"
    )
    async def stop_song(self, ctx):
        if ctx.guild:
            self.music_queues.pop(ctx.guild.id, None)
            self.now_playing.pop(ctx.guild.id, None)
            self.queue_loop.pop(ctx.guild.id, None)
            self.queue_auto.pop(ctx.guild.id, None)
            self.auto_history.pop(ctx.guild.id, None)
        voice = get(self.app.voice_clients, guild=ctx.guild)
        if voice and voice.is_connected():
            voice.stop()
        await ctx.send("⏹️ **음악 재생을 정지하고 대기열과 설정을 모두 초기화했습니다.**")

    @commands.command(
        name="대기열", aliases=["queue", "q"],
        help="대기열 목록을 조회하거나 루프/자동추천 옵션을 설정합니다.\n"
             "사용법:\n"
             "• %대기열 : 현재 재생 중인 곡과 대기 목록 및 상태 확인\n"
             "• %대기열 loop (또는 루프) : 대기열 루프 모드 ON/OFF 토글\n"
             "• %대기열 auto [n] (또는 자동 [n]) : 스포티파이 자동 추천 N곡 유지 모드 ON/OFF (기본 5곡)",
        usage="* (loop/루프 | auto/자동 (*n*))"
    )
    async def show_queue(self, ctx, *args):
        arg_str = " ".join(args).strip().lower()
        guild_id = ctx.guild.id
        queue = self.music_queues.setdefault(guild_id, [])

        # (1) loop 옵션 토글
        if arg_str.startswith("loop") or arg_str.startswith("루프"):
            current = self.queue_loop.get(guild_id, False)
            if "on" in arg_str:
                self.queue_loop[guild_id] = True
            elif "off" in arg_str:
                self.queue_loop[guild_id] = False
            else:
                self.queue_loop[guild_id] = not current

            status = "활성화(ON)" if self.queue_loop[guild_id] else "비활성화(OFF)"
            emoji = "🔁" if self.queue_loop[guild_id] else "➡️"
            note = " (곡이 끝나면 대기열 맨 뒤로 다시 등록됩니다)" if self.queue_loop[guild_id] else ""
            await ctx.send(f"{emoji} **대기열 루프 모드가 {status}되었습니다.**{note}")
            return

        # (2) auto 옵션 설정
        if arg_str.startswith("auto") or arg_str.startswith("자동"):
            tokens = arg_str.split()
            current_target = self.queue_auto.get(guild_id)

            if "off" in tokens:
                self.queue_auto[guild_id] = None
                await ctx.send("🤖 **스포티파이 자동 추천(Auto) 모드가 비활성화되었습니다.**")
                return

            target_n = None
            for tok in tokens[1:]:
                if tok.isdigit():
                    target_n = int(tok)
                    break

            if target_n is None:
                if current_target:
                    self.queue_auto[guild_id] = None
                    await ctx.send("🤖 **스포티파이 자동 추천(Auto) 모드가 비활성화되었습니다.**")
                    return
                else:
                    target_n = max(len(queue), 5)

            target_n = max(1, min(target_n, 20))
            self.queue_auto[guild_id] = target_n

            msg = await ctx.send(
                f"🤖 **스포티파이 자동 추천(Auto) 모드가 활성화되었습니다!** (대기열 `{target_n}`곡 상시 유지)\n"
                f"추천 곡을 탐색 중입니다... :hourglass_flowing_sand:"
            )
            await self.fill_auto_queue(guild_id, target_channel=ctx.channel)
            await msg.edit(
                content=f"🤖 **스포티파이 자동 추천(Auto) 모드 작동 중!** (대기열 `{len(self.music_queues[guild_id])}/{target_n}`곡 채움 완료)"
            )
            return

        # (3) 기본 대기열 목록 조회
        now = self.now_playing.get(guild_id)
        if not now and not queue:
            loop_status = "ON" if self.queue_loop.get(guild_id) else "OFF"
            auto_val = self.queue_auto.get(guild_id)
            auto_status = f"ON ({auto_val}곡 유지)" if auto_val else "OFF"
            await ctx.send(
                f"현재 재생 중이거나 대기 중인 곡이 없습니다.\n"
                f"(모드 설정: 🔁 루프 `{loop_status}` | 🤖 자동추천 `{auto_status}`)"
            )
            return

        embed = discord.Embed(title="🎵 재생 대기열", color=0x1DB954)
        if now:
            requester = now.get("requester")
            req_name = "🤖 자동추천" if now.get("is_auto") else (requester.display_name if requester else "알 수 없음")
            embed.add_field(name="▶️ 현재 재생 중", value=f"**{now['title']}** (신청: {req_name})", inline=False)

        if queue:
            q_text = ""
            for i, item in enumerate(queue[:10], 1):
                r = item.get("requester")
                r_name = "🤖 Auto" if item.get("is_auto") else (r.display_name if r else "알 수 없음")
                q_text += f"`{i}.` **{item.get('title', '알 수 없음')}** (신청: {r_name})\n"
            if len(queue) > 10:
                q_text += f"\n...외 {len(queue) - 10}곡 대기 중"
            embed.add_field(name=f"대기 목록 (총 {len(queue)}곡)", value=q_text, inline=False)
        else:
            embed.add_field(name="대기 목록", value="대기 중인 곡이 없습니다.", inline=False)

        loop_status = "ON" if self.queue_loop.get(guild_id) else "OFF"
        auto_val = self.queue_auto.get(guild_id)
        auto_status = f"ON ({auto_val}곡 유지)" if auto_val else "OFF"
        embed.set_footer(
            text=f"🔁 루프: {loop_status} | 🤖 자동추천(Auto): {auto_status} • 설정: %대기열 loop, %대기열 auto [n]"
        )

        await ctx.send(embed=embed)

    @commands.check_any(commands.has_role("DJ"), commands.has_permissions(administrator=True))
    @commands.command(
        name="스킵", aliases=["skip", "next"],
        help="현재 재생 중인 음악을 건너뛰고 다음 대기곡을 재생합니다.", usage="*"
    )
    async def skip_song(self, ctx):
        voice = get(self.app.voice_clients, guild=ctx.guild)
        if voice and (voice.is_playing() or voice.is_paused()):
            await ctx.send("⏭️ **현재 곡을 건너뛰었습니다.**")
            voice.stop()
        else:
            await ctx.send(":no_entry: 현재 재생 중인 음악이 없습니다.")

    @commands.command(
        name="곡정보", aliases=["노래정보", "spotify", "sp"],
        help="스포티파이/음원 정보를 검색하여 상세 정보(앨범아트, 발매일 등)를 조회합니다.",
        usage="* str(곡명 또는 스포티파이 링크)"
    )
    async def song_info(self, ctx, *, query: str):
        msg = await ctx.send("음원 정보를 검색하고 있습니다... :mag:")
        track = spotify_helper.search_track(query)
        if not track:
            await msg.edit(content=f":x: '{query}'에 대한 곡 정보를 찾지 못했습니다.")
            return

        embed = discord.Embed(
            title=f"🎵 {track.get('title', '제목 없음')}",
            url=track.get("spotify_url") or None,
            color=0x1DB954
        )
        embed.add_field(name="아티스트", value=track.get("artist") or "알 수 없음", inline=True)
        embed.add_field(name="앨범", value=track.get("album") or "알 수 없음", inline=True)
        embed.add_field(name="발매일", value=track.get("release_date") or "정보 없음", inline=True)

        if track.get("popularity") is not None:
            embed.add_field(name="인기도", value=f"{track['popularity']}/100", inline=True)

        if track.get("cover_url"):
            embed.set_thumbnail(url=track["cover_url"])

        footer_text = "Spotify" if track.get("source") == "spotify" else "Music Meta (Fallback)"
        if track.get("premium_required"):
            footer_text += " | ⚠️ 앱 소유자 Spotify Premium 활성화 시 전체 연동 지원"
        embed.set_footer(
            text=footer_text,
            icon_url="https://storage.googleapis.com/pr-newsroom-wp/1/2023/05/Spotify_Primary_Logo_RGB_Green.png"
        )

        await msg.edit(content=None, embed=embed)

    @commands.command(
        name="곡추천", aliases=["추천곡", "recommend"],
        help="입력한 곡을 기반으로 스포티파이 추천 곡 5곡을 조회합니다.",
        usage="* str(기준 곡명 또는 링크)"
    )
    async def recommend_songs(self, ctx, *, query: str):
        msg = await ctx.send(f"'{query}' 기반 추천 곡을 탐색 중입니다... :musical_note:")
        recs, seed_name = spotify_helper.get_recommendations(query, limit=5)
        if not recs:
            await msg.edit(content=f":warning: {seed_name}")
            return

        is_fallback = any(t.get("source") == "itunes_fallback" for t in recs)
        embed = discord.Embed(
            title=f"🎧 '{seed_name}' 기반 추천 곡",
            description="스포티파이 알고리즘이 추천하는 비슷한 분위기의 노래입니다." if not is_fallback else "해당 아티스트 및 장르 기반 인기 추천 곡 목록입니다.",
            color=0x1DB954
        )
        for i, t in enumerate(recs, 1):
            url = t.get("spotify_url")
            link_text = "Spotify에서 듣기" if t.get("source") == "spotify" else "곡 정보 보기"
            album_info = f"앨범: {t.get('album', '알 수 없음')}"
            val = f"[{link_text}]({url}) · {album_info}" if url else album_info
            embed.add_field(
                name=f"{i}. {t['title']} - {t['artist']}",
                value=val,
                inline=False
            )
        if recs and recs[0].get("cover_url"):
            embed.set_thumbnail(url=recs[0]["cover_url"])
        
        footer_text = "Spotify Recommendations" if not is_fallback else "Music Recommendations (Fallback)"
        embed.set_footer(
            text=footer_text,
            icon_url="https://storage.googleapis.com/pr-newsroom-wp/1/2023/05/Spotify_Primary_Logo_RGB_Green.png"
        )

        await msg.edit(content=None, embed=embed)

    @commands.command(
        name="노래맞추기", aliases=["노래퀴즈", "musicquiz"],
        help="노래를 듣고 제목을 맞춰보세요! (정답 시 1 :coin: 지급)"
             "\n사용법: %노래맞추기 [force/f] [loop=n] [tag=kor|eng|jap|all]"
             "\n예시: %노래맞추기 loop=5"
             "\n예시: %노래맞추기 force loop=3 tag=kor+jap", usage="[force/f] [loop=n] [tag=kor|eng|jap|all]"
    )
    async def music_quiz(self, ctx, *args):
        if not ctx.author.voice or not ctx.author.voice.channel:
            await ctx.send(":no_entry: 먼저 음성 채널에 입장한 후 명령어를 사용해 주세요.")
            return

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
            if not ctx.author.voice or not ctx.author.voice.channel:
                await ctx.send(":no_entry: 먼저 음성 채널에 입장한 후 명령어를 사용해 주세요.")
                return

            if not await self.ensure_voice(ctx):
                return

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
                playlist_opts: Any = {
                    'extract_flat': True,
                    'skip_download': True,
                    'quiet': True,
                    'no_warnings': True,
                    'socket_timeout': 10,
                }
                try:
                    with yt_dlp.YoutubeDL(playlist_opts) as ydl:
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
                
                if not await self.ensure_voice(ctx):
                    await ctx.send(":warning: 음성 채널 연결이 끊어져 퀴즈를 중단합니다.")
                    return

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
                        search_opts: Any = {
                            'extract_flat': True,
                            'skip_download': True,
                            'quiet': True,
                            'no_warnings': True,
                            'socket_timeout': 10,
                        }
                        try:
                            with yt_dlp.YoutubeDL(search_opts) as ydl:
                                data = await loop.run_in_executor(
                                    None, lambda: ydl.extract_info(f"ytsearch5:{query}", download=False)
                                )
                        except Exception as e:
                            await msg.edit(content=f":x: 음원 검색 중 에러가 발생했습니다: {e}")
                            return

                        if not data or 'entries' not in data or len(data['entries']) == 0:  # type: ignore
                            await msg.edit(content=f":x: '{query}' 검색 결과가 없습니다.")
                            return

                        # Find the first video entry
                        entry = None
                        for e in data['entries']:
                            ie_key = e.get('ie_key', '')
                            entry_url = e.get('url') or ''
                            if ie_key == 'Youtube' or 'watch?v=' in entry_url:
                                entry = e
                                break

                        if not entry:
                            await msg.edit(content=f":x: '{query}' 검색 결과가 없습니다.")
                            return

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
                if not ctx.voice_client or not ctx.voice_client.is_connected():
                    await ctx.send(":warning: 음성 채널 연결이 끊어져 퀴즈를 중단합니다.")
                    return
                ctx.voice_client.play(player, after=lambda e: print(f'Player error: {e}') if e else None)

                # 정답 리스트 구축
                answers = [title] + synonyms
                normalized_answers = [normalize(ans) for ans in answers if ans]

                def check(m):
                    current_ch = (ctx.voice_client.channel if ctx.voice_client else None) or channel
                    if current_ch and m.author not in current_ch.members:
                        return False
                    if m.channel != ctx.channel:
                        return False
                    return normalize(m.content) in normalized_answers

                try:
                    message = await self.app.wait_for("message", check=check, timeout=100.0)
                except asyncio.TimeoutError:
                    await ctx.send(f"시간 초과! (정답: {official_title})")
                else:
                    new_coins = await self.app.db.add_coins(message.author.id, 1)
                    await ctx.send(
                        f"🎉 {message.author.display_name} 님 정답! (정답: {official_title})\n"
                        f":coin: **+1 토큰 지급!** (보유: {new_coins:,}개)"
                    )

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
        if not ctx.author.voice or not ctx.author.voice.channel:
            await ctx.send(":no_entry: 먼저 음성 채널에 입장해 주세요.")
            return False
        if ctx.voice_client is None or not ctx.voice_client.is_connected():
            return await self.join_ch(ctx)
        elif ctx.voice_client.channel != ctx.author.voice.channel:
            return await self.join_ch(ctx)
        return True


async def setup(app):
    await app.add_cog(Voice(app))
