import discord
import random
import asyncio
from discord.utils import get
from discord.ext import commands
from discord import FFmpegPCMAudio
import openpyxl


class Voice(commands.Cog, name="음성(Voice)"):

    def __init__(self, app):
        self.app = app

    @commands.command(name="연결", help="음성 채널에 연결합니다.", usage="%연결")
    async def join(self, ctx):
        channel = ctx.message.author.voice.channel
        voice = get(self.app.voice_clients, guild=ctx.guild)
        if voice and voice.is_connected():
            await voice.move_to(channel)
        else:
            voice = await channel.connect()
            await ctx.send(str(channel.name) + ' 채널에 연결합니다.')

    @commands.command(
        name="퇴장", aliases=["연결해제", "연결끊기"],
        help="음성 채널을 나갑니다.", usage="%퇴장, %연결해제, %연결끊기"
    )
    async def leave(self, ctx):
        await ctx.guild.voice_client.disconnect()
        await ctx.send("연결을 끊습니다.")

    @commands.command(name="잠수", help="잠수방으로 이동합니다.", usage="%잠수")
    async def submerge(self, ctx):
        afkchannel = ctx.guild.get_channel(760198518987685949)
        await ctx.message.author.move_to(afkchannel)
        await ctx.send(ctx.message.author.name + " 님을 잠수방으로 옮겼습니다.")

    @commands.command(name="에어맨", help="에어맨이 쓰러지지 않습니다.", usage="%에어맨")
    async def airman(self, ctx):
        voice = get(self.app.voice_clients, guild=ctx.guild)
        if voice and voice.is_connected():
            source = FFmpegPCMAudio(executable="ffmpeg/bin/ffmpeg.exe", source="airman.mp3")
            voice.play(source)


def setup(app):
    app.add_cog(Voice(app))