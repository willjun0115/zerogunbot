import discord
import random
import asyncio
from discord.utils import get
from discord.ext import commands
import operator


class Shop(commands.Cog, name="상점", description="게임에서 얻은 토큰의 이용에 관련된 카테고리입니다."):

    def __init__(self, app):
        self.app = app

    async def has_enough_token(self, ctx, price: int):
        db = await self.app.find_id('$', ctx.author.id)
        if db is None:
            await ctx.send("DB에서 ID를 찾지 못했습니다.\n'%토큰' 명령어를 통해 ID를 등록할 수 있습니다.")
            return False, None
        else:
            coin = int(db.content[20:])
            if coin >= price:
                return True, db
            else:
                await ctx.send('토큰이 부족합니다.')
                return False, db

    @commands.command(
        name="토큰", aliases=["코인", "token", "coin", "$"],
        help="자신의 토큰 수를 확인합니다.\n토큰 DB에 기록되지 않았다면, 새로 ID를 등록합니다.",
        usage="*"
    )
    async def check_token(self, ctx):
        global_guild = self.app.get_guild(self.app.global_guild_id)
        db_channel = get(global_guild.text_channels, name="db")
        data = await self.app.find_id('$', ctx.author.id)
        if data is not None:
            coin = int(data.content[20:])
            await ctx.send(str(coin) + ' :coin:')
        else:
            await db_channel.send('$' + str(ctx.author.id) + ';0')
            await ctx.send('DB에 ' + ctx.author.mention + ' 님의 ID를 기록했습니다.')

    @commands.cooldown(1, 300., commands.BucketType.channel)
    @commands.command(
        name="토큰순위", aliases=["순위표", "랭크표", "rank"],
        help="서버 내 토큰 보유 순위를 조회합니다. (쿨타임 5분)", usage="* (@*member*)"
    )
    async def token_rank(self, ctx, num=10):
        num = int(num)
        global_guild = self.app.get_guild(self.app.global_guild_id)
        db_channel = get(global_guild.text_channels, name="db")
        msg = await ctx.send("DB를 조회 중입니다... :mag:")
        members = {}
        messages = await db_channel.history(limit=100).flatten()
        for message in messages:
            if message.content.startswith('$') is True:
                member = await ctx.guild.fetch_member(int(message.content[1:19]))
                members[member] = int(message.content[20:])
        members = sorted(members.items(), key=operator.itemgetter(1), reverse=True)
        embed = discord.Embed(title="<토큰 랭킹>", description=ctx.guild.name + " 서버의 토큰 순위")
        winner = members[0]
        names = ""
        coins = ""
        n = 1
        for md in members[1:]:
            n += 1
            if n == 2:
                names += f":second_place:. {md[0].display_name}\n"
            elif n == 3:
                names += f":third_place:. {md[0].display_name}\n"
            else:
                names += f"{n}. {md[0].display_name}\n"
            coins += str(md[1]) + "\n"
            if n >= num:
                break
        embed.add_field(name=f":first_place:. " + winner[0].display_name + " :crown:", value=names, inline=True)
        embed.add_field(name=f"{str(winner[1])} :coin:", value=coins, inline=True)
        await msg.edit(content=None, embed=embed)

    @commands.command(
        name="상점", aliases=["shop", "tokenshop", "coinshop"],
        help="상품 목록을 나열합니다.", usage="*"
    )
    async def token_shop(self, ctx):
        embed = discord.Embed(title="<가챠 확률 정보>", description="'%구매 ~'를 통해 상품 구매")
        for role in self.app.role_lst:
            embed.add_field(name="> " + role[0], value=f'{role[1]} :coin:', inline=True)
        for item in self.app.shop.keys():
            embed.add_field(name="> " + item, value=f'{self.app.shop.get(item)} :coin:', inline=True)
        await ctx.send(embed=embed)

    @commands.command(
        name="구매", aliases=["buy"],
        help="상점의 상품 목록에서 역할이나 아이템을 구매합니다.", usage="* str(*role or item*)"
    )
    async def buy_item(self, ctx, *, args):
        item_found = False
        for role in self.app.role_lst:
            if args == role[0]:
                is_enough, db = await self.has_enough_token(ctx, role[1])
                if is_enough:
                    await ctx.author.add_roles(get(ctx.guild.roles, name=role[0]))
                    await db.edit(content=db.content[:20]+str(int(db.content[20:])-role[1]))
                    await ctx.send("구매 완료!")
                item_found = True
                break
        if item_found is False:
            if args.startswith("행운"):
                if len(args[3:]) > 0:
                    num = int(args[3:])
                else:
                    num = 1
                await self.enhance_luck(ctx, num=num)
            elif args == "닉변":
                await ctx.send("%닉변 (변경하고자 하는 별명) 으로 이용해주세요.")
            elif args == "수은":
                await self.mercury(ctx)
            else:
                await ctx.send("상품을 찾지 못했습니다.")

    async def enhance_luck(self, ctx, num=1):
        num = int(num)
        if num < 0:
            await ctx.send("0개 이상부터 구매할 수 있습니다.")
        else:
            global_guild = self.app.get_guild(self.app.global_guild_id)
            db_channel = get(global_guild.text_channels, name="db")
            luck_log = await self.app.find_id('%', ctx.author.id)
            price = self.app.shop.get("행운") * num
            is_enough, db = await self.has_enough_token(ctx, price)
            if is_enough:
                await db.edit(content=db.content[:20] + str(int(db.content[20:]) - price))
                if luck_log is not None:
                    luck = int(luck_log.content[20:])
                    await luck_log.edit(content=luck_log.content[:20]+str(luck + num))
                    await ctx.send(f'+{num} :four_leaf_clover:')
                else:
                    await db_channel.send('%' + str(ctx.author.id) + ';' + str(num))
                    await ctx.send(ctx.author.display_name + f" 님이 행운 버프를 받습니다. -{price} :coin:")

    @commands.command(
        name="행운", aliases=["luck"],
        help="자신의 행운 중첩량을 확인합니다."
             "\n행운은 가챠에서 일부 효과를 방어 또는 강화합니다."
             "\n행운은 중첩 가능하며, 중첩에 비례해 복권 당첨 확률이 증가합니다."
             "\n(+ 행운^0.5 * 0.1%)",
        usage="*"
    )
    async def luck(self, ctx):
        luck_log = await self.app.find_id('%', ctx.author.id)
        if luck_log is not None:
            luck = int(luck_log.content[20:])
            await ctx.send(f'{luck} :four_leaf_clover: (복권 확률 +{(luck ** 0.5) * 0.1:0.2f}%)')
        else:
            await ctx.send("행운 효과가 없습니다.")

    @commands.command(
        name="닉변", aliases=["nick"],
        help="닉네임을 변경합니다."
             "\n아무것도 입력하지 않으면 기본 닉네임으로 변경됩니다.", usage="* (str())"
    )
    async def nick_change(self, ctx, *, nickname=None):
        price = self.app.shop.get("닉변")
        is_enough, db = await self.has_enough_token(ctx, price)
        if is_enough:
            if get(ctx.guild.roles, name="창씨개명") in ctx.message.author.roles:
                await ctx.send("창씨개명을 보유 중입니다.")
            else:
                coin = int(db.content[20:])
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
                        await db.edit(content=db.content[:20] + str(coin - price))
                        await ctx.send(ctx.author.name + " 님의 닉네임을 " + nickname + "(으)로 변경했습니다.")
                    else:
                        await ctx.send("닉네임 변경을 취소했습니다.")

    @commands.command(
        name="수은", aliases=["Hg"],
        help="자신의 마이크, 헤드셋 음소거를 해제합니다.", usage="*"
    )
    async def mercury(self, ctx):
        price = self.app.shop.get("수은")
        is_enough, db = await self.has_enough_token(ctx, price)
        if is_enough:
            if ctx.author.voice.deaf or ctx.author.voice.mute:
                await ctx.author.edit(deafen=False, mute=False)
                await db.edit(content=db.content[:20] + str(int(db.content[20:]) - price))
            else:
                await ctx.send("마이크 및 헤드셋이 음소거 상태가 아닙니다.")


def setup(app):
    app.add_cog(Shop(app))
