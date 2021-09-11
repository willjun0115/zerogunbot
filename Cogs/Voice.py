import discord
import random
import asyncio
from discord.utils import get
from discord.ext import commands
from discord import FFmpegPCMAudio
import openpyxl
import os
import youtube_dl
import opuslib


class Voice(commands.Cog, name="음성(Voice)"):

    def __init__(self, app):
        self.app = app

    @commands.command(
        name="연결", aliases=["connect", "join"],
        help="음성 채널에 연결합니다.", usage="%*"
    )
    async def join(self, ctx):
        if get(ctx.guild.roles, name='DJ') in ctx.message.author.roles:
            channel = ctx.message.author.voice.channel
            voice = get(self.app.voice_clients, guild=ctx.guild)
            if voice and voice.is_connected():
                await voice.move_to(channel)
            else:
                voice = await channel.connect()
                await ctx.send(str(channel.name) + ' 채널에 연결합니다.')
        else:
            await ctx.send(" :no_entry: 이 명령을 실행하실 권한이 없습니다.")

    @commands.command(
        name="퇴장", aliases=["연결해제", "연결끊기", "disconnect", "dc", "leave"],
        help="음성 채널을 나갑니다.", usage="%*"
    )
    async def leave(self, ctx):
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
        help="유튜브 url을 통해 음악을 재생합니다.", usage="%* str(url)", pass_context=True
    )
    async def play(self, ctx, url: str):
        if get(ctx.guild.roles, name='DJ') in ctx.message.author.roles:
            voice = get(self.app.voice_clients, guild=ctx.guild)
            if voice and voice.is_connected():
                try:
                    if os.path.isfile("0.mp3"):
                        os.remove("0.mp3")
                except PermissionError:
                    await ctx.send("현재 음악이 재생 중입니다. 끝날때까지 기다리시거나, 음악을 중지해주세요.")
                else:
                    msg = await ctx.send("재생 준비 중...")
                    ydl_opt = {
                        'format': 'bestaudio/best',
                        'noplaylist': True,
                        'postprocessors': [{
                            'key': 'FFmpegExtractAudio',
                            'preferredcodec': 'mp3',
                            'preferredquality': '192'
                        }]
                    }
                    with youtube_dl.YoutubeDL(ydl_opt) as ydl:
                        ydl.download([url])
                    for file in os.listdir('./'):
                        if file.endswith(".mp3"):
                            os.rename(file, "0.mp3")
                    await msg.edit(content="재생 시작")
                    source = FFmpegPCMAudio(source="0.mp3")
                    voice.play(source, after=lambda e: voice.stop())
        else:
            await ctx.send(" :no_entry: 이 명령을 실행하실 권한이 없습니다.")

    @commands.command(
        name="정지", aliases=["stop", "s"],
        help="음악 재생을 정지합니다.", usage="%*"
    )
    async def stop(self, ctx):
        if get(ctx.guild.roles, name='DJ') in ctx.message.author.roles:
            voice = get(self.app.voice_clients, guild=ctx.guild)
            if voice and voice.is_connected():
                voice.stop()
        else:
            await ctx.send(" :no_entry: 이 명령을 실행하실 권한이 없습니다.")

    @commands.command(
        name="queueclear", aliases=["qc"],
        help="재생 목록을 비웁니다.", usage="%*"
    )
    async def queue(self, ctx):
        if get(ctx.guild.roles, name='DJ') in ctx.message.author.roles:
            for file in os.listdir('./'):
                if file.endswith(".mp3"):
                    os.remove(file)
        else:
            await ctx.send(" :no_entry: 이 명령을 실행하실 권한이 없습니다.")


def setup(app):
    app.add_cog(Voice(app))