import discord
import asyncio
import random
from discord.ext import commands
from discord.utils import get
from Utils import token_cost


class Chat(commands.Cog, name="채팅", description="채팅 및 채팅 채널 조작에 관련된 카테고리입니다."):

    def __init__(self, app):
        self.app = app

    @commands.command(
        name="안녕", aliases=["인사", "ㅎㅇ", "hello", "hi"],
        help="짧은 인사를 건네고 일일 보상(10 :coin:)을 받습니다.", usage="*"
    )
    async def hello(self, ctx):
        what_message = random.randint(1, 3)
        if what_message == 1:
            msg = '안녕하세요? ' + ctx.author.name + ' 님, 오늘도 좋은 하루 보내세요!'
        elif what_message == 2:
            msg = '안녕하세요? ' + ctx.author.name + ' 님, 오늘 하루 힘내세요!'
        else:
            msg = ctx.author.name + ' 님, 안녕하세요!'

        reward_given, coins = await self.app.db.claim_daily_reward(ctx.author.id, reward_type="greeting", amount=10)
        if reward_given:
            msg += f"\n:coin: **일일 보상 10토큰**을 획득하셨습니다! (현재 잔액: {coins} :coin:)"
        else:
            msg += f"\n(오늘의 일일 보상은 이미 받으셨습니다. 내일 다시 만나요!)"

        await ctx.channel.send(msg)

    @commands.has_permissions(manage_messages=True)
    @token_cost(5)
    @commands.command(
        name="말하기", aliases=["say", "chat"],
        help="입력값을 채팅에 전송합니다. (소모: 5 :coin:)", usage="* str()"
    )
    async def _say(self, ctx, *, args):
        await ctx.message.delete()
        await ctx.send(args)

    @commands.has_permissions(manage_messages=True)
    @token_cost(5)
    @commands.command(
        name="타이머챗", aliases=["timerchat", "tchat"],
        help="시간이 지나면 사라지는 채팅을 전송합니다. (소모: 5 :coin:)", usage="* int() str()"
    )
    async def _say_timer(self, ctx, sec, *, args):
        await ctx.message.delete()
        msg = await ctx.send(args)
        await asyncio.sleep(int(sec))
        await msg.delete()

    @commands.has_permissions(manage_messages=True)
    @token_cost(10)
    @commands.command(
        name="도배", aliases=["bulkchat", "bchat"],
        help="입력값을 반복 입력해 전송합니다. (소모: 10 :coin:)", usage="* int() str()"
    )
    async def _say_bulk(self, ctx, num, *, args):
        await ctx.message.delete()
        msg = await ctx.send(args * int(num))

    @commands.cooldown(1, 60., commands.BucketType.member)
    @commands.has_permissions(manage_messages=True)
    @token_cost(10)
    @commands.command(
        name="청소", aliases=["일괄삭제", "clear", "purge"],
        help="숫자만큼 채팅 기록을 읽어 메세지를 지웁니다."
             "\n특정 사용자의 채팅만을 지울 수도 있습니다. (쿨타임: 60초 / 소모: 10 :coin:)", usage="* int((0, 999]) (@*member*)"
    )
    async def clean(self, ctx, num: int = 1, member: discord.Member | None = None):
        if num < 1 or num > 999:
            await self.app.db.add_coins(ctx.author.id, 10)
            await ctx.send(" :no_entry: 지울 수 있는 채팅 기록은 1개 이상 999개 이하입니다. (10 :coin: 환불)")
            return
        await ctx.message.delete()
        if member is None:
            deleted = await ctx.channel.purge(limit=num)
        else:
            target_members = [member]

            def check(m):
                return m.author in target_members and m.channel == ctx.channel

            deleted = await ctx.channel.purge(limit=num, check=check)
        await ctx.send(f":white_check_mark: {len(deleted)}개의 채팅을 삭제했습니다.")


async def setup(app):
    await app.add_cog(Chat(app))
