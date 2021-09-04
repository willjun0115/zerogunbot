import discord
import random
import asyncio
from discord.utils import get
from discord.ext import commands
import openpyxl


class Voice(commands.Cog, name="음성(Voice)"):

    def __init__(self, app):
        self.app = app

    @commands.command(name="연결", help="음성 채널에 연결합니다.", usage="%연결")
    async def connect(self, ctx):
        channel = ctx.message.author.voice.channel
        await ctx.guild.change_voice_state(channel=channel)
        await ctx.send(str(channel.name) + ' 채널에 연결합니다.')
        await channel.connect()

    @commands.command(name="퇴장", help="음성 채널을 나갑니다.", usage="%퇴장")
    async def disconnect(self, ctx):
        channel = ctx.message.author.voice.channel
        await channel.disconnect()

    @commands.command(name="잠수", help="잠수방으로 이동합니다.", usage="%잠수")
    async def submerge(self, ctx):
        channel = ctx.guild.get_channel(760198518987685949)
        await ctx.message.author.move_to(channel)
        await ctx.send(ctx.message.author.name + " 님을 잠수방으로 옮겼습니다.")

    @commands.command(name="에어맨", help="에어맨이 쓰러지지 않습니다.", usage="%에어맨")
    async def airman(self, ctx):
        channel = ctx.message.author.voice.channel
        await ctx.guild.change_voice_state(channel=channel)
        vc = await channel.connect()
        if not vc.is_playing():
            vc.play(discord.FFmpegPCMAudio('audiosources/에어맨이 쓰러지지 않아.mp3'))


def setup(app):
    app.add_cog(Voice(app))