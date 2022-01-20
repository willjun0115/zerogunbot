import discord
import random
import asyncio
from discord.utils import get
from discord.ext import commands
import operator


class Shop(commands.Cog, name="상점", description="게임에서 얻은 토큰의 이용에 관련된 카테고리입니다."):

    def __init__(self, app):
        self.app = app

    async def find_log(self, ctx, selector, id):
        log_channel = ctx.guild.get_channel(self.app.log_ch)
        find = None
        async for message in log_channel.history(limit=100):
            if message.content.startswith(selector + str(id)) is True:
                find = message
                break
        return find

    @commands.command(
        name="토큰", aliases=["코인", "token", "coin", "$"],
        help="자신의 토큰 수를 확인합니다.\n토큰 로그에 기록되지 않았다면, 새로 ID를 등록합니다.",
        usage="*"
    )
    async def check_token(self, ctx):
        log_channel = ctx.guild.get_channel(self.app.log_ch)
        log = await self.find_log(ctx, '$', ctx.author.id)
        if log is not None:
            coin = int(log.content[20:])
            await ctx.send(str(coin) + ' :coin:')
        else:
            await log_channel.send('$' + str(ctx.author.id) + ';0')
            await ctx.send('토큰 로그에 ' + ctx.author.name + ' 님의 ID를 기록했습니다.')

    @commands.cooldown(1, 600., commands.BucketType.channel)
    @commands.command(
        name="토큰순위", aliases=["순위표", "랭크표", "rank"],
        help="서버 내 토큰 보유 순위를 조회합니다. (쿨타임 10분)", usage="* (@*member*)"
    )
    async def token_rank(self, ctx, member: discord.Member = None):
        log_channel = ctx.guild.get_channel(self.app.log_ch)
        msg = await ctx.send("로그를 조회 중입니다... :mag:")
        members = {}
        messages = await log_channel.history(limit=100).flatten()
        for message in messages:
            if message.content.startswith('$') is True:
                mem = await ctx.guild.fetch_member(int(message.content[1:19]))
                member_log = await self.find_log(ctx, '$', mem.id)
                members[mem] = int(member_log.content[20:])
        members = sorted(members.items(), key=operator.itemgetter(1), reverse=True)
        if member is None:
            embed = discord.Embed(title="<토큰 랭킹>", description=ctx.guild.name + " 서버의 토큰 순위")
            winner = members[0]
            names = ""
            coins = ""
            n = 1
            for md in members[1:]:
                n += 1
                names += f"{n}. {md[0].display_name}\n"
                coins += str(md[1]) + "\n"
                if n >= 10:
                    break
            embed.add_field(name=f"1. " + winner[0].display_name + " :crown:", value=names, inline=True)
            embed.add_field(name=f"{str(winner[1])} :coin:", value=coins, inline=True)
            await msg.edit(content=None, embed=embed)
        else:
            embed = discord.Embed(title="<토큰 랭킹>", description=member.display_name + " 님의 토큰 순위")
            log = await self.find_log(ctx, '$', member.id)
            if log is not None:
                coin = int(log.content[20:])
                mem_coin = (member, coin)
                embed.add_field(name=f"{str(members.index(mem_coin))}위", value=f"{str(coin)} :coin:")
                await msg.edit(content=None, embed=embed)
            else:
                await msg.edit(content='로그에서 ID를 찾지 못했습니다.')

    @commands.command(
        name="상점", aliases=["shop", "tokenshop", "coinshop"],
        help="상품 목록을 나열합니다.", usage="*"
    )
    async def token_shop(self, ctx):
        embed = discord.Embed(title="<가챠 확률 정보>", description="'%구매 ~'를 통해 상품 구매")
        for role in self.app.role_lst:
            embed.add_field(name="> " + role[0], value=f'{role[2]} :coin:', inline=True)
        for item in self.app.shop.keys():
            embed.add_field(name="> " + item, value=f'{self.app.shop.get(item)} :coin:', inline=True)
        await ctx.send(embed=embed)

    @commands.command(
        name="구매", aliases=["buy"],
        help="상점의 상품 목록에서 역할이나 아이템을 구매합니다.", usage="* str(*role or item*)"
    )
    async def buy_item(self, ctx, *, args):
        log = await self.find_log(ctx, '$', ctx.author.id)
        if log is None:
            await ctx.send('로그에서 ID를 찾지 못했습니다.')
        else:
            item_found = False
            coin = int(log.content[20:])
            for role in self.app.role_lst:
                if args == role[0]:
                    if coin >= role[2]:
                        await ctx.author.add_roles(get(ctx.guild.roles, name=role[0]))
                        await log.edit(content=log.content[:20]+str(coin-role[2]))
                        await ctx.send("구매 완료!")
                    else:
                        await ctx.send("코인이 부족합니다.")
                    item_found = True
                    break
            if item_found is False:
                if args == "행운":
                    await self.enhance_luck(ctx)
                elif args == "닉변":
                    await ctx.send("%닉변 (변경하고자 하는 별명) 으로 이용해주세요.")
                elif args == "유료복권":
                    await self.lottery_p(ctx)
                elif args == "수은":
                    await self.mercury(ctx)
                else:
                    await ctx.send("상품을 찾지 못했습니다.")

    @commands.command(
        name="행운", aliases=["luck+"],
        help="행운 버프를 얻습니다."
             "\n행운에 비례해 가챠 확률이 증가합니다. (행운 1 당 +0.1%)"
             "\n행운 보유 중엔 손실 확률이 50% 감소합니다."
             "\n역할을 얻으면 행운이 초기화됩니다.",
        usage="*"
    )
    async def enhance_luck(self, ctx):
            luck_log = await self.find_log(ctx, '%', ctx.author.id)
            if luck_log is not None:
                luck = int(luck_log.content[20:])
                await ctx.send(str(luck) + ' :four_leaf_clover:')
            else:
                log_channel = ctx.guild.get_channel(self.app.log_ch)
                log = await self.find_log(ctx, '$', ctx.author.id)
                if log is None:
                    await ctx.send('로그에서 ID를 찾지 못했습니다.')
                else:
                    price = self.app.shop.get("행운")
                    coin = int(log.content[20:])
                    if coin >= price:
                        await log_channel.send('%' + str(ctx.author.id) + ';0')
                        await log.edit(content=log.content[:20]+str(coin-price))
                        await ctx.send(ctx.author.display_name + f" 님이 행운 버프를 받습니다. -{price} :coin:")
                    else:
                        await ctx.send("코인이 부족합니다.")

    @commands.cooldown(5, 30., commands.BucketType.member)
    @commands.command(
        name="유료복권", aliases=["lottery+"],
        help="코인을 소모하며 '복권보다 당첨 확률이 높습니다.\n5회 사용 시 쿨타임 30초가 적용됩니다."
             "\n(당첨 확률은 2.25%)", usage="*"
    )
    async def lottery_p(self, ctx):
        log = await self.find_log(ctx, '$', ctx.author.id)
        price = self.app.shop.get("유료복권")
        if log is None:
            await ctx.send('로그에서 ID를 찾지 못했습니다.\n\'%토큰\' 명령어를 통해 ID를 등록할 수 있습니다.')
        else:
            bot_log = await self.find_log(ctx, '$', self.app.id)
            coin = int(log.content[20:])
            prize = int(bot_log.content[20:])
            if coin < price:
                await ctx.send("코인이 부족합니다.")
            else:
                rand = random.random()
                if rand <= 0.0225:
                    await bot_log.edit(content=bot_log.content[:20] + str(10))
                    await log.edit(content=log.content[:20] + str(coin - price + prize))
                    await ctx.send(f"{ctx.author.display_name} 님이 복권에 당첨되셨습니다! 축하드립니다!\n상금: {prize} :coin:")
                else:
                    await log.edit(content=log.content[:20] + str(coin - price))
                    await ctx.send("꽝 입니다. 다음에 도전하세요.")

    @commands.command(
        name="닉변", aliases=["nick"],
        help="닉네임을 변경합니다."
             "\n아무것도 입력하지 않으면 기본 닉네임으로 변경됩니다.", usage="* (str())"
    )
    async def nick_change(self, ctx, *, nickname=None):
        log = await self.find_log(ctx, '$', ctx.author.id)
        if log is None:
            await ctx.send('로그에서 ID를 찾지 못했습니다.')
        else:
            if get(ctx.guild.roles, name="창씨개명") in ctx.message.author.roles:
                await ctx.send("창씨개명을 보유 중입니다.")
            else:
                price = self.app.shop.get("닉변")
                coin = int(log.content[20:])
                if coin >= price:
                    msg = await ctx.send(
                        ":warning: 주의: 코인을 소모합니다."
                        f"\n정말 닉네임을 {nickname}으로 변경하시겠습니까?"
                    )
                    reaction_list = ['✅', '❎']
                    for r in reaction_list:
                        await msg.add_reaction(r)

                    def check(reaction, user):
                        return str(reaction) in reaction_list and reaction.message.id == msg.id and user == ctx.author

                    try:
                        reaction, user = await self.app.wait_for("reaction_add", check=check, timeout=10.0)
                    except asyncio.TimeoutError:
                        await msg.edit(content="시간 초과!", delete_after=2)
                    else:
                        if str(reaction) == '✅':
                            await ctx.author.edit(nick=nickname)
                            await log.edit(content=log.content[:20] + str(coin - price))
                            await ctx.send(ctx.author.name + " 님의 닉네임을 " + nickname + "(으)로 변경했습니다.")
                        else:
                            await ctx.send("닉네임 변경을 취소했습니다.")
                else:
                    await ctx.send("코인이 부족합니다.")

    @commands.command(
        name="수은", aliases=["Hg"],
        help="자신의 마이크, 헤드셋 음소거를 해제합니다.", usage="*"
    )
    async def mercury(self, ctx):
        log = await self.find_log(ctx, '$', ctx.author.id)
        if log is None:
            await ctx.send('로그에서 ID를 찾지 못했습니다.')
        else:
            price = self.app.shop.get("수은")
            coin = int(log.content[20:])
            if coin >= price:
                if ctx.author.voice.deaf or ctx.author.voice.mute:
                    await ctx.author.edit(deafen=False, mute=False)
                    await log.edit(content=log.content[:20] + str(coin - price))
                else:
                    await ctx.send("마이크 및 헤드셋이 음소거 상태가 아닙니다.")
            else:
                await ctx.send("코인이 부족합니다.")


def setup(app):
    app.add_cog(Shop(app))
