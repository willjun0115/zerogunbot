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
        msg = await ctx.send(":clock12: \t" + args)
        await asyncio.sleep(1)
        await msg.edit(content=":clock3: \t" + args)
        await asyncio.sleep(1)
        await msg.edit(content=":clock6: \t" + args)
        await asyncio.sleep(1)
        await msg.edit(content=":clock9: \t" + args)
        await asyncio.sleep(1)
        await msg.edit(content=":clock12: \t" + args)
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

    @commands.command(name='학습', help='언어를 학습시킵니다.\n(A = 단어, B = 문장)',
                      usage='%학습 A B', pass_context=True)
    async def learn_word(self, ctx, word, *, answer):
        openxl = openpyxl.load_workbook("learning.xlsx")
        wb = openxl.active
        for i in range(1, 1000):
            if wb["A" + str(i)].value == "_":
                wb["A" + str(i)].value = str(word)
                wb["B" + str(i)].value = str(answer)
                await ctx.send("학습 완료!")
                break
            elif wb["A" + str(i)].value == str(word):
                await ctx.channel.send("이미 학습한 언어입니다.")
                break
        openxl.save("learning.xlsx")

    @commands.command(name='망각', help='언어를 망각시킵니다.\n(A = 단어)',
                      usage='%학습 A', pass_context=True)
    async def forget_word(self, ctx, word):
        openxl = openpyxl.load_workbook("learning.xlsx")
        wb = openxl.active
        for i in range(1, 1000):
            if wb["A" + str(i)].value == str(word):
                wb["A" + str(i)].value = '_'
                await ctx.send(str(word) + "을(를) 잊었습니다.")
                break
        openxl.save("learning.xlsx")

    @commands.command(name='재학습', help='언어를 다시 학습시킵니다.\n(A = 단어, B = 문장)',
                      usage='%재학습 A B', pass_context=True)
    async def relearn_word(self, ctx, word, *, answer):
        openxl = openpyxl.load_workbook("learning.xlsx")
        wb = openxl.active
        for i in range(1, 1000):
            if wb["A" + str(i)].value == str(word):
                wb["B" + str(i)].value = answer
                await ctx.channel.send(str(word) + " 단어를 재학습했습니다.")
                break
        openxl.save("learning.xlsx")

    @commands.command(name='언어목록', help='학습한 언어 목록을 공개합니다.',
                      usage='%언어목록')
    async def learn_word_list(self, ctx):
        openxl = openpyxl.load_workbook("learning.xlsx")
        wb = openxl.active
        embed = discord.Embed(title="<언어 목록>",
                              description="0군봇의 학습 언어")
        for i in range(1, 1000):
            if wb["A" + str(i)].value is not None:
                if wb["A" + str(i)].value == "_":
                    pass
                else:
                    embed.add_field(name=wb["A" + str(i)].value,
                                    value=wb["B" + str(i)].value, inline=True)
            elif wb["A" + str(i)].value is None:
                break
        await ctx.send(embed=embed)
        openxl.save("learning.xlsx")

    @commands.has_permissions(administrator=True)
    @commands.command(name='언어초기화', help='언어 목록을 초기화합니다.\n(관리자 권한)',
                      usage='%언어초기화')
    async def reset_word(self, ctx):
        openxl = openpyxl.load_workbook("learning.xlsx")
        wb = openxl.active
        for i in range(1, 1000):
            if wb["A" + str(i)].value is not None:
                if wb["A" + str(i)].value == "_":
                    wb["B" + str(i)].value = None
                    pass
                else:
                    wb["A" + str(i)].value = "_"
                    wb["B" + str(i)].value = None
            elif wb["A" + str(i)].value is None:
                break
        await ctx.send("언어 목록을 초기화했습니다.")
        openxl.save("learning.xlsx")

    @commands.command(name='연결', help='봇을 음성 채널에 연결시킵니다.\n(관리자 권한)',
                      usage='%연결')
    async def connect_voice(self, ctx):
        channel = ctx.author.voice.channel
        await ctx.send(str(channel.name) + "에 연결했습니다.")
        await ctx.author.voice.channel.connect()


def setup(app):
    app.add_cog(Chat(app))