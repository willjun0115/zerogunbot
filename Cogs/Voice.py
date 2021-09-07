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
        help="음성 채널에 연결합니다.", usage="%연결, %connect, %join"
    )
    async def join(self, ctx):
        channel = ctx.message.author.voice.channel
        voice = get(self.app.voice_clients, guild=ctx.guild)
        if voice and voice.is_connected():
            await voice.move_to(channel)
        else:
            voice = await channel.connect()
            await ctx.send(str(channel.name) + ' 채널에 연결합니다.')

    @commands.command(
        name="퇴장", aliases=["연결해제", "연결끊기", "disconnect", "leave"],
        help="음성 채널을 나갑니다.", usage="%퇴장, %연결해제, %연결끊기, %disconnect, %leave"
    )
    async def leave(self, ctx):
        await ctx.guild.voice_client.disconnect()
        await ctx.send("연결을 끊습니다.")

    @commands.command(
        name="잠수", aliases=["afk"],
        help="잠수방으로 이동합니다.", usage="%잠수, %afk"
    )
    async def submerge(self, ctx):
        afkchannel = ctx.guild.get_channel(760198518987685949)
        await ctx.message.author.move_to(afkchannel)
        await ctx.send(ctx.message.author.name + " 님을 잠수방으로 옮겼습니다.")

    @commands.command(
        name="재생", aliases=["play"],
        help="유튜브 url을 통해 음악을 재생합니다.", usage="%재생 ~, %play ~", pass_context=True
    )
    async def play(self, ctx, url: str):
        voice = get(self.app.voice_clients, guild=ctx.guild)
        if voice and voice.is_connected():
            try:
                if os.path.isfile("song.mp3"):
                    os.remove("song.mp3")
            except PermissionError:
                await ctx.send("현재 음악이 재생 중입니다. 끝날때까지 기다리시거나, 음악을 중지해주세요.")
            else:
                msg = await ctx.send("재생 준비 중...")
                ydl_opt = {
                    'format': 'bestaudio/best',
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
                        os.rename(file, "song.mp3")
                await msg.edit(content="재생 시작")
                source = FFmpegPCMAudio(source="song.mp3")
                voice.play(source)

    @commands.command(
        name="정지", aliases=["stop"],
        help="음악 재생을 정지합니다.", usage="%정지, %stop"
    )
    async def stop(self, ctx):
        voice = get(self.app.voice_clients, guild=ctx.guild)
        if voice and voice.is_connected():
            voice.stop()

    @commands.command(
        name="재생목록", aliases=["queue"],
        help="재생 목록을 비웁니다.", usage="%재생목록, %queue"
    )
    async def queue(self, ctx):
        for file in os.listdir('./'):
            if file.endswith(".mp3"):
                os.remove(file)


def setup(app):
    app.add_cog(Voice(app))