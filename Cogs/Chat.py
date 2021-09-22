import discord
import asyncio
import random
from discord.ext import commands
from discord.utils import get


class Chat(commands.Cog, name="채팅", description="채팅과 관련된 카테고리입니다."):

    def __init__(self, app):
        self.app = app

    @commands.command(
        name="안녕", aliases=["인사", "ㅎㅇ", "hello", "hi"],
        help="짧은 인사를 건넵니다.", usage="%*"
    )
    async def hello(self, ctx):
        what_message = random.randint(1, 3)
        if what_message == 1:
            await ctx.channel.send('안녕하세요? ' + ctx.author.name + '님, 오늘도 좋은하루 보내세요!')
        elif what_message == 2:
            await ctx.channel.send('안녕하세요? ' + ctx.author.name + '님, 오늘 하루 힘내세요!')
        else:
            await ctx.channel.send(ctx.author.name + '님, 안녕하세요!')

    @commands.command(
        name="말하기", aliases=["say"],
        help="입력값을 채팅에 전송합니다.", usage="%* str()", pass_context=True
    )
    async def _say(self, ctx, *, args):
        if get(ctx.guild.roles, name='언론 통제') in ctx.message.author.roles:
            await ctx.message.delete()
            await ctx.send(args)
        else:
            await ctx.send(" :no_entry: 이 명령을 실행하실 권한이 없습니다.")

    @commands.command(
        name="tts", aliases=["TTS"],
        help="입력값을 채팅에 tts 메세지로 전송합니다.", usage="%* str()", pass_context=True
    )
    async def _say_tts(self, ctx, *, args):
        if get(ctx.guild.roles, name='언론 통제') in ctx.message.author.roles:
            await ctx.message.delete()
            await ctx.send(args, tts=True)
        else:
            await ctx.send(" :no_entry: 이 명령을 실행하실 권한이 없습니다.")

    @commands.command(
        name="타이머챗", aliases=["timerchat", "tc"],
        help="잠시 후 사라지는 채팅을 전송합니다.", usage="%* str()", pass_context=True
    )
    async def _say_timer(self, ctx, *, args):
        if get(ctx.guild.roles, name='언론 통제') in ctx.message.author.roles:
            await ctx.message.delete()
            msg = await ctx.send(":clock12: " + args)
            await asyncio.sleep(1)
            await msg.edit(content=":clock3: " + args)
            await asyncio.sleep(1)
            await msg.edit(content=":clock6: " + args)
            await asyncio.sleep(1)
            await msg.edit(content=":clock9: " + args)
            await asyncio.sleep(1)
            await msg.edit(content=":clock12: " + args)
            await asyncio.sleep(1)
            await msg.edit(content=':boom: ', delete_after=1)
        else:
            await ctx.send(" :no_entry: 이 명령을 실행하실 권한이 없습니다.")

    @commands.command(
        name="청소", aliases=["지우기", "clear", "purge"],
        help="숫자만큼 채팅을 지웁니다.", usage="%* int()", pass_context=True
    )
    async def clean(self, ctx, num):
        if get(ctx.guild.roles, name='언론 통제') in ctx.message.author.roles:
            await ctx.message.delete()
            await ctx.channel.purge(limit=int(num))
        else:
            await ctx.send(" :no_entry: 이 명령을 실행하실 권한이 없습니다.")

    @commands.command(
        name='패드립', aliases=["mb"],
        help="저희 봇에 그런 기능은 없습니다?", usage="%*"
    )
    async def fdr(self, ctx):
        msg = await ctx.send("느금마")
        await asyncio.sleep(1)
        await msg.edit(content='저는 그런 말 못해요 ㅠㅠ')


def setup(app):
    app.add_cog(Chat(app))