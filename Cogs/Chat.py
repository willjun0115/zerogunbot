import discord
import asyncio
import random
from discord.ext import commands
from discord.utils import get
import openpyxl


class Chat(commands.Cog, name="채팅(Chat)"):

    def __init__(self, app):
        self.app = app

    @commands.command(name="안녕", help="짧은 인사를 건넵니다.", usage="%안녕")
    async def hello(self, ctx):
        what_message = random.randint(1, 3)
        if what_message == 1:
            await ctx.channel.send('안녕하세요? ' + ctx.author.name + '님, 오늘도 좋은하루 보내세요!')
        elif what_message == 2:
            await ctx.channel.send('안녕하세요? ' + ctx.author.name + '님, 오늘 하루 힘내세요!')
        else:
            await ctx.channel.send(ctx.author.name + '님, 안녕하세요!')

    @commands.command(name="말하기", help="입력값을 채팅에 전송합니다.", usage="%말하기 ~", pass_context=True)
    async def _say(self, ctx, *, args):
        await ctx.message.delete()
        await ctx.send(args)

    @commands.command(name="tts", help="입력값을 채팅에 tts 메세지로 전송합니다.", usage="%tts ~", pass_context=True)
    async def _say_tts(self, ctx, *, args):
        await ctx.message.delete()
        await ctx.send(args, tts=True)

    @commands.command(name="타이머챗", help="잠시 후 사라지는 채팅을 전송합니다.", usage="%타이머챗 ~", pass_context=True)
    async def _say_timer(self, ctx, *, args):
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

    @commands.command(name="야", help="봇에게 말을 겁니다. 학습한 언어에 대답합니다. \n(A = 단어)",
                      usage="%야 A", pass_context=True)
    async def call_learn(self, ctx, word):
        openxl = openpyxl.load_workbook("learning.xlsx")
        wb = openxl.active
        for i in range(1, 1000):
            if wb["A" + str(i)].value == str(word):
                await ctx.send(str(wb["B" + str(i)].value))
                break


def setup(app):
    app.add_cog(Chat(app))