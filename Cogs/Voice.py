import discord
import random
import asyncio
from discord.utils import get
from discord.ext import commands
from discord import FFmpegPCMAudio
import os
import opuslib
import youtube_dl
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
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

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)


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

    @commands.check_any(commands.has_role("DJ"), commands.is_owner(), commands.has_permissions(administrator=True))
    @commands.command(
        name="연결", aliases=["connect", "c", "join"],
        help="음성 채널에 연결합니다.", usage="*"
    )
    async def join_ch(self, ctx):
        voice = get(self.app.voice_clients, guild=ctx.guild)
        channel = ctx.author.voice.channel
        try:
            if voice and voice.is_connected():
                await voice.move_to(channel)
            else:
                await ctx.guild.change_voice_state(channel=channel)
                voice = await channel.connect()
        except:
            await ctx.send(":no_entry: 연결 오류가 발생했습니다.")
        else:
            await ctx.send(channel.name + "에 연결합니다.")

    @commands.check_any(commands.has_role("DJ"), commands.is_owner(), commands.has_permissions(administrator=True))
    @commands.command(
        name="퇴장", aliases=["연결해제", "연결끊기", "disconnect", "dc", "leave"],
        help="음성 채널을 나갑니다.", usage="*"
    )
    async def leave_ch(self, ctx):
        await ctx.voice_client.disconnect()
        await ctx.send("연결을 끊습니다.")
        self.clear_mp3()

    @commands.command(
        name="잠수", aliases=["afk"],
        help="잠수방으로 이동합니다.", usage="*"
    )
    async def submerge(self, ctx):
        afkchannel = ctx.guild.get_channel(760198518987685949)
        await ctx.message.author.move_to(afkchannel)
        await ctx.send(ctx.message.author.name + " 님을 잠수방으로 옮겼습니다.")

    @commands.check_any(commands.has_role("DJ"), commands.is_owner(), commands.has_permissions(administrator=True))
    @commands.command(
        name="tts", aliases=["TTS"],
        help="입력받은 문자열을 tts 음성으로 출력합니다.", usage="* str()"
    )
    async def tts_voice(self, ctx, *, msg):
        for file in os.listdir("./"):
            if file.startswith("tts_ko"):
                os.remove(file)
        tts = gTTS(text=msg, lang='ko', slow=False)
        tts.save('tts_ko.mp3')
        ctx.voice_client.play(discord.FFmpegPCMAudio('tts_ko.mp3'),
                              after=lambda e: print(f'Player error: {e}') if e else None)

    @commands.check_any(commands.has_role("DJ"), commands.is_owner(), commands.has_permissions(administrator=True))
    @commands.command(
        name="재생", aliases=["play", "p"],
        help="유튜브 url을 통해 음악을 재생합니다."
             "\nurl 뒤에 -s를 붙이면 스트리밍으로 재생합니다.", usage="* str(*url*) (-s)", pass_context=True
    )
    async def play_song(self, ctx, url: str, stream=None):
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

    @commands.check_any(commands.has_role("DJ"), commands.is_owner(), commands.has_permissions(administrator=True))
    @commands.command(
        name="검색", aliases=["search"],
        help="유튜브 검색을 통해 목록을 가져옵니다."
             "\n채팅으로 1~5의 숫자를 치면 해당 번호의 링크를 재생합니다.", usage="* str()"
    )
    async def yt_search(self, ctx, *, args):
        msg = await ctx.send("데이터 수집 중... :mag:")

        url = "https://www.youtube.com/results?search_query=" + args

        chrome_options = webdriver.ChromeOptions()
        chrome_options.binary_location = os.environ.get("GOOGLE_CHROME_BIN")
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--no-sandbox")
        browser = webdriver.Chrome(executable_path=os.environ.get("CHROMEDRIVER_PATH"),
                                   chrome_options=chrome_options)
        browser.get(url)

        search_list = {}
        embed = discord.Embed(title=f"\"{args}\"의 검색 결과 :mag:",
                              description="1~5를 입력해 선택하거나, x를 입력해 취소하세요.")
        for n in range(0, 5):
            get_title = browser.find_elements(By.XPATH, '//a[@id="video-title"]')[n].get_attribute('title')
            get_href = browser.find_elements(By.XPATH, '//a[@id="video-title"]')[n].get_attribute('href')
            get_info = browser.find_elements(By.XPATH, '//a[@id="video-title"]')[n].get_attribute('aria-label')
            get_info = get_info[len(get_title):]
            search_list[n+1] = get_href
            embed.add_field(name=f"> {str(n+1)}. " + get_title, value=get_info, inline=False)
        await msg.edit(content=None, embed=embed)

        answer_list = ["X", "x", "1", "2", "3", "4", "5"]

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

    @commands.check_any(commands.has_role("DJ"), commands.is_owner(), commands.has_permissions(administrator=True))
    @commands.command(
        name="정지", aliases=["stop", "s"],
        help="음악 재생을 정지합니다.", usage="*"
    )
    async def stop_song(self, ctx):
        voice = get(self.app.voice_clients, guild=ctx.guild)
        if voice and voice.is_connected():
            voice.stop()

    @play_song.before_invoke
    async def ensure_voice(self, ctx):
        if ctx.voice_client is None:
            await self.join_ch(ctx)


def setup(app):
    app.add_cog(Voice(app))