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
        help="짧은 인사를 건넵니다.", usage="*"
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
        help="입력값을 채팅에 전송합니다.", usage="* str()", pass_context=True
    )
    async def _say(self, ctx, *, args):
        if get(ctx.guild.roles, name='언론 통제') in ctx.message.author.roles:
            await ctx.message.delete()
            await ctx.send(args)
        else:
            await ctx.send(" :no_entry: 이 명령을 실행하실 권한이 없습니다.")

    @commands.command(
        name="tts", aliases=["TTS"],
        help="입력값을 채팅에 tts 메세지로 전송합니다.", usage="* str()", pass_context=True
    )
    async def _say_tts(self, ctx, *, args):
        if get(ctx.guild.roles, name='언론 통제') in ctx.message.author.roles:
            await ctx.message.delete()
            await ctx.send(args, tts=True)
        else:
            await ctx.send(" :no_entry: 이 명령을 실행하실 권한이 없습니다.")

    @commands.command(
        name="타이머챗", aliases=["timerchat", "tc"],
        help="잠시 후 사라지는 채팅을 전송합니다.", usage="* str()", pass_context=True
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
        name="청소", aliases=["clear", "purge"],
        help="숫자만큼 채팅을 지웁니다.", usage="* int(*(0, 100]*)", pass_context=True
    )
    async def clean(self, ctx, num):
        if get(ctx.guild.roles, name='언론 통제') in ctx.message.author.roles:
            await ctx.message.delete()
            await ctx.channel.purge(limit=int(num))
        else:
            await ctx.send(" :no_entry: 이 명령을 실행하실 권한이 없습니다.")

    @commands.command(
        name="일괄삭제", aliases=["지우기", "deleteall"],
        help="옵션에 있는 단어가 포함된 채팅을 지웁니다."
             "\n다소 시간이 걸릴 수 있습니다."
             "\n옵션은 \"단어1 단어2 단어3 ...\"와 같이 큰따옴표 안에 입력하며,"
             " 반드시 단어는 띄어쓰기로 구분합니다."
             "\n단어를 모두 포함하는 채팅을 삭제할 경우 and,"
             "\n단어를 하나라도 포함하는 채팅을 삭제할 경우 or을 입력합니다.",
        usage="* str(*options*) str(and *or* or) (@*member*)", pass_context=True
    )
    async def list_delete(self, ctx, words, opt, member: discord.Member = None):
        if get(ctx.guild.roles, name='언론 통제') in ctx.message.author.roles:
            await ctx.message.delete()
            counter = 0
            word_list = words.split()
            msg = await ctx.send("채팅 목록을 읽고 있습니다...")
            async for message in ctx.channel.history(limit=999):
                deletion = False
                if opt == 'or':
                    for word in word_list:
                        if word in message.content:
                            deletion = True
                elif opt == 'and':
                    found_count = len([x for x in word_list if x in message.content])
                    if len(word_list) == found_count:
                        deletion = True
                if deletion is True:
                    if member is None:
                        await message.delete()
                        counter += 1
                    else:
                        if message.author == member:
                            await message.delete()
                            counter += 1
            await msg.edit(content=f":white_check_mark: {counter}개의 채팅을 삭제했습니다.")
        else:
            await ctx.send(" :no_entry: 이 명령을 실행하실 권한이 없습니다.")

    @commands.command(
        name='패드립', aliases=["mb"],
        help="저희 봇에 그런 기능은 없습니다?", usage="*"
    )
    async def fdr(self, ctx):
        msg = await ctx.send("느금마")
        await asyncio.sleep(1)
        await msg.edit(content='저는 그런 말 못해요 ㅠㅠ')

    @commands.command(
        name='암호화', aliases=["encrypt", "enc"],
        help='입력받은 문자열을 암호화해 출력합니다.', usage='* int(*[0, 999]*) str()', pass_context=True
    )
    async def chat_encode(self, ctx, num, *, args):
        await ctx.message.delete()
        code = ""
        num = int(num)
        if 0 <= num < 1000:
            for c in args:
                x = ord(c)
                x = x * 2 + num * 3
                cc = chr(x)
                code = code + cc
            await ctx.send(str(code))
        else:
            await ctx.send(":warning: 코드번호는 0~999의 정수만 가능합니다.")

    @commands.command(
        name='복호화', aliases=["decrypt", "dec"],
        help='0군봇이 암호화한 암호를 입력받아 복호화해 출력합니다.', usage='* int(*[0, 999]*) str(*code*)', pass_context=True
    )
    async def chat_decode(self, ctx, num, *, code):
        await ctx.message.delete()
        args = ""
        num = int(num)
        if 0 <= num < 1000:
            for c in code:
                x = ord(c)
                x = (x - num * 3) // 2
                cc = chr(x)
                args = args + cc
            await ctx.send(str(args))
        else:
            await ctx.send(":warning: 코드번호는 0~999의 정수만 가능합니다.")


def setup(app):
    app.add_cog(Chat(app))