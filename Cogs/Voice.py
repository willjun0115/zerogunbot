import discord
import random
import asyncio
from discord.utils import get
from discord.ext import commands
from discord import FFmpegPCMAudio
import os
import youtube_dl
import opuslib
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

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

    async def get_queue(self, ctx):
        queue_channel = ctx.guild.get_channel(887984694866632724)
        queue_list = []
        async for message in queue_channel.history(limit=30, oldest_first=True):
            if message.content.startswith('https://www.youtube.com/') is True:
                queue_list.append(message)
            else:
                await message.delete()
        return queue_list

    async def play_next(self, ctx, voice_client):
        voice_client.stop()
        queue = await self.get_queue(ctx)
        if len(queue) > 0:
            next_song = queue[0].content
            await queue[0].delete()
            await self.play_song(ctx, next_song)

    @commands.command(
        name="연결", aliases=["connect", "join"],
        help="음성 채널에 연결합니다.", usage="%*"
    )
    async def join_ch(self, ctx):
        if get(ctx.guild.roles, name='DJ') in ctx.message.author.roles:
            channel = ctx.message.author.voice.channel
            voice = get(self.app.voice_clients, guild=ctx.guild)
            if voice and voice.is_connected():
                await voice.move_to(channel)
            else:
                await channel.connect()
                await ctx.send(str(channel.name) + ' 채널에 연결합니다.')
        else:
            await ctx.send(" :no_entry: 이 명령을 실행하실 권한이 없습니다.")

    @commands.command(
        name="퇴장", aliases=["연결해제", "연결끊기", "disconnect", "dc", "leave"],
        help="음성 채널을 나갑니다.", usage="%*"
    )
    async def leave_ch(self, ctx):
        if get(ctx.guild.roles, name='DJ') in ctx.message.author.roles:
            await ctx.guild.voice_client.disconnect()
            await ctx.send("연결을 끊습니다.")
        else:
            await ctx.send(" :no_entry: 이 명령을 실행하실 권한이 없습니다.")

    @commands.command(
        name="잠수", aliases=["afk"],
        help="잠수방으로 이동합니다.", usage="%*"
    )
    async def submerge(self, ctx):
        afkchannel = ctx.guild.get_channel(760198518987685949)
        await ctx.message.author.move_to(afkchannel)
        await ctx.send(ctx.message.author.name + " 님을 잠수방으로 옮겼습니다.")

    @commands.command(
        name="재생", aliases=["play", "p"],
        help="유튜브 url을 통해 음악을 재생합니다.", usage="%* str(url) stream=False", pass_context=True
    )
    async def play_song(self, ctx, url: str, stream=False):
        if get(ctx.guild.roles, name='DJ') in ctx.message.author.roles:
            if ctx.voice_client.is_playing():
                ctx.voice_client.stop()
            async with ctx.typing():
                player = await YTDLSource.from_url(url, loop=self.app.loop, stream=stream)
                ctx.voice_client.play(player, after=lambda e: print(f'Player error: {e}') if e else None)
            msg = f'Now playing: {player.title}'
            if stream is True:
                msg = f'Now streaming: {player.title}'
            await ctx.send(msg)
        else:
            await ctx.send(" :no_entry: 이 명령을 실행하실 권한이 없습니다.")

    @commands.command(
        name="검색", aliases=["search"],
        help="유튜브 검색을 통해 목록을 가져옵니다.\n채팅으로 1~5의 숫자를 치면 해당 번호의 링크를 재생합니다.", usage="%* str()"
    )
    async def yt_search(self, ctx, *, args):
        if get(ctx.guild.roles, name='DJ') in ctx.message.author.roles:
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

            embed = discord.Embed(title="YouTube", description=f"\"{args}\"의 검색 결과 :mag:")
            for n in range(0, 5):
                get_title = browser.find_elements_by_xpath('//a[@id="video-title"]')[n].get_attribute('title')
                get_href = browser.find_elements_by_xpath('//a[@id="video-title"]')[n].get_attribute('href')
                embed.add_field(name=f"> {str(n+1)}. " + get_title, value=get_href, inline=False)
            await msg.edit(content=None, embed=embed)

            answer_list = ["1", "2", "3", "4", "5"]

            def check(message, user):
                return message.content in answer_list and user == ctx.author

            try:
                message, user = await self.app.wait_for("message", check=check, timeout=60.0)
            except asyncio.TimeoutError:
                await msg.edit(content="시간 초과!", delete_after=2)
            else:
                await msg.delete()
                select = browser.find_elements_by_xpath('//a[@id="video-title"]')[int(message.content)-1].get_attribute('href')
                await self.play_song(ctx, select, stream=False)
        else:
            await ctx.send(" :no_entry: 이 명령을 실행하실 권한이 없습니다.")

    @commands.command(
        name="정지", aliases=["stop", "s"],
        help="음악 재생을 정지합니다.", usage="%*"
    )
    async def stop_song(self, ctx):
        if get(ctx.guild.roles, name='DJ') in ctx.message.author.roles:
            voice = get(self.app.voice_clients, guild=ctx.guild)
            if voice and voice.is_connected():
                voice.stop()
        else:
            await ctx.send(" :no_entry: 이 명령을 실행하실 권한이 없습니다.")

    @play_song.before_invoke
    async def ensure_voice(self, ctx):
        if ctx.voice_client is None:
            if ctx.author.voice:
                await self.join_ch
            else:
                await ctx.send("음성 채널에 연결되어 있지 않습니다.")
                raise commands.CommandError("Author not connected to a voice channel.")


def setup(app):
    app.add_cog(Voice(app))