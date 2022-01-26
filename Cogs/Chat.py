import discord
import asyncio
import random
from discord.ext import commands
from discord.utils import get


class Chat(commands.Cog, name="채팅", description="채팅 및 채팅 채널 조작에 관련된 카테고리입니다."):

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

    @commands.check_any(commands.has_role("언론 통제"), commands.has_permissions(administrator=True), commands.is_owner())
    @commands.command(
        name="말하기", aliases=["say"],
        help="입력값을 채팅에 전송합니다.", usage="* str()", pass_context=True
    )
    async def _say(self, ctx, *, args):
        await ctx.message.delete()
        await ctx.send(args)

    @commands.check_any(commands.has_role("언론 통제"), commands.has_permissions(administrator=True), commands.is_owner())
    @commands.command(
        name="타이머챗", aliases=["timerchat", "tc"],
        help="잠시 후 사라지는 채팅을 전송합니다.", usage="* str()", pass_context=True
    )
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

    @commands.cooldown(1, 60., commands.BucketType.member)
    @commands.check_any(commands.has_role("언론 통제"), commands.has_permissions(administrator=True), commands.is_owner())
    @commands.command(
        name="청소", aliases=["일괄삭제", "clear", "purge"],
        help="숫자만큼 채팅 기록을 읽어 메세지를 지웁니다."
             "\n특정 사용자의 채팅만을 지울 수도 있습니다. (쿨타임: 60초)", usage="* int((0, 999]) (@*member*)", pass_context=True
    )
    async def clean(self, ctx, num=1, member: discord.Member = None):
        await ctx.message.delete()
        if int(num) > 999:
            await ctx.send(" :no_entry: 읽을 수 있는 채팅 기록은 최대 999개 입니다.")
        elif get(ctx.guild.roles, name="언론 통제") in ctx.channel.changed_roles:
            await ctx.send(" :no_entry: 이 채널에서 사용할 수 없는 명령어입니다.")
        else:
            if member is None:
                deleted = await ctx.channel.purge(limit=int(num))
            else:
                member = [member]

                def check(m):
                    return m.author in member and m.channel == ctx.channel

                deleted = await ctx.channel.purge(limit=int(num), check=check)
            await ctx.send(f":white_check_mark: {len(deleted)}개의 채팅을 삭제했습니다.")

    @commands.command(
        name='패드립', aliases=["mb"],
        help="저희 봇에 그런 기능은 없습니다?", usage="*", hidden=True
    )
    async def fdr(self, ctx):
        msg = await ctx.send("느금마")
        await asyncio.sleep(1)
        await msg.edit(content='저는 그런 말 못해요 ㅠㅠ')


def setup(app):
    app.add_cog(Chat(app))
