import discord
import asyncio
import random
from discord.ext import commands
from discord.utils import get


class Chat(commands.Cog, name="채팅(Chat)"):

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

    @commands.command(
        name='엄마삭제', aliases=["md"],
        help="입력값의 엄마를 삭제합니다.", usage="%* str()", pass_context=True
    )
    async def delete_mom_(self, ctx, *, args):
        msg = await ctx.send("\"" + args + "\"님의 엄마 삭제 중...  0% :clock12: ")
        await asyncio.sleep(1)
        await msg.edit(content="\"" + args + "\"님의 엄마 삭제 중...  25% :clock3: ")
        await asyncio.sleep(1)
        await msg.edit(content="\"" + args + "\"님의 엄마 삭제 중...  50% :clock6: ")
        await asyncio.sleep(1)
        await msg.edit(content="\"" + args + "\"님의 엄마 삭제 중...  75% :clock9: ")
        await asyncio.sleep(1)
        await msg.edit(content="\"" + args + "\"님의 엄마 삭제 중...  99% :clock11: ")
        await asyncio.sleep(2)
        await msg.edit(content=":white_check_mark: \"" + args + "\"님의 엄마이(가) 삭제되었습니다.")

    @commands.command(
        name="엄마검색", aliases=["ms"],
        help="입력값의 엄마를 검색합니다.", usage="%* str()", pass_context=True
    )
    async def search_mom_(self, ctx, *, args):
        msg = await ctx.send(":mag_right: \"" + args + "\"님의 엄마 검색 중.")
        await asyncio.sleep(1)
        await msg.edit(content=":mag_right: \"" + args + "\"님의 엄마 검색 중..")
        await asyncio.sleep(1)
        await msg.edit(content=":mag_right: \"" + args + "\"님의 엄마 검색 중...")
        await asyncio.sleep(1)
        mom_exist = random.randint(0, 3)
        if mom_exist == 0:
            await msg.edit(content=":warning: \"" + args + "\"님의 엄마을(를) 찾을 수 없습니다.")
        elif mom_exist == 1:
            await msg.edit(content=":white_check_mark: \"" + args + "\"님의 엄마가 확인되었습니다. \n(검색결과 수: 1)")
        elif mom_exist == 2:
            await msg.edit(content=":white_check_mark: \"" + args + "\"님의 엄마가 확인되었습니다. \n(검색결과 수: 2)")
        else:
            await msg.edit(content=":white_check_mark: \"" + args + "\"님의 엄마가 확인되었습니다. \n(검색결과 수: 99+)")


def setup(app):
    app.add_cog(Chat(app))