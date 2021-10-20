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
        name="청소", aliases=["일괄삭제", "clear", "purge"],
        help="숫자만큼 채팅 기록을 읽어 메세지를 지웁니다."
             "\n특정 사용자의 채팅만을 지울 수도 있습니다.", usage="* int() (@*member*)", pass_context=True
    )
    async def clean(self, ctx, num=1, member: discord.Member = None):
        if get(ctx.guild.roles, name='언론 통제') in ctx.message.author.roles:
            await ctx.message.delete()
            if member is None:
                member = ctx.guild.members
            else:
                member = [member]

            def check(m):
                return m.author in member and m.channel == ctx.channel

            deleted = await ctx.channel.purge(limit=int(num), check=check)
            await ctx.send(f":white_check_mark: {len(deleted)}개의 채팅을 삭제했습니다.")
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
        help='입력받은 문자열을 암호화해 출력합니다.', usage='* int([0, 1000)) str()', pass_context=True
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
        help='0군봇이 암호화한 암호를 입력받아 복호화해 출력합니다.', usage='* int([0, 1000)) str(*code*)', pass_context=True
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