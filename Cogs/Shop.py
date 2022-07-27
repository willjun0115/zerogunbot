import discord
import random
import asyncio
from discord.utils import get
from discord.ext import commands
import operator
from datetime import datetime


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

    @commands.cooldown(1, 60., commands.BucketType.channel)
    @commands.command(
        name="토큰순위", aliases=["순위", "rank"],
        help="현재 토큰 보유 순위를 조회합니다. (쿨타임 1분)\n"
             "YYYY_MM 포맷으로 시즌별 토큰 순위를 조회할 수 있습니다.\n"
             "all로 검색 시 역대 토큰 1위 목록을 조회할 수 있습니다.", usage="* (*season*)"
    )
    async def token_rank(self, ctx, season=None):
        global_guild = self.app.get_guild(self.app.global_guild_id)
        if season == "all":
            msg = await ctx.send("DB를 조회 중입니다... :mag:")
            winner_list = []
            for db in global_guild.text_channels:
                if db.name.startswith("20"):
                    members = {}
                    messages = await db.history(limit=100).flatten()
                    for message in messages:
                        if message.content.startswith('$') is True:
                            member = await ctx.guild.fetch_member(int(message.content[1:19]))
                            members[member] = int(message.content[20:])
                    members = sorted(members.items(), key=operator.itemgetter(1), reverse=True)
                    winner = members[0]
                    winner_list.append((db.name, winner[0], winner[1]))
            embed = discord.Embed(title="<역대 1위 목록>", description="역대 토큰 1위 목록")
            for w in winner_list:
                embed.add_field(name=f"시즌 {w[0]}", value=f"{w[1].display_name} :crown: : {w[2]} :coin:", inline=True)
            await msg.edit(content=None, embed=embed)
        else:
            if season is None:
                season = "db"
                text = "현재 토큰 순위"
            else:
                text = season + " 시즌 토큰 순위"
            db_channel = get(global_guild.text_channels, name=season)
            msg = await ctx.send("DB를 조회 중입니다... :mag:")
            members = {}
            messages = await db_channel.history(limit=100).flatten()
            for message in messages:
                if message.content.startswith('$') is True:
                    member = await ctx.guild.fetch_member(int(message.content[1:19]))
                    members[member] = int(message.content[20:])
            members = sorted(members.items(), key=operator.itemgetter(1), reverse=True)
            embed = discord.Embed(title="<토큰 랭킹>", description=text)
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
            embed.add_field(name=f":first_place:. " + winner[0].display_name + " :crown:", value=names, inline=True)
            embed.add_field(name=f"{str(winner[1])} :coin:", value=coins, inline=True)
            await msg.edit(content=None, embed=embed)

    @commands.command(
        name="상점", aliases=["shop", "tokenshop", "coinshop"],
        help="상품 목록을 나열합니다.", usage="*", enabled=False
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
        help="상점의 상품 목록에서 역할이나 아이템을 구매합니다.", usage="* str(*role or item*)", enabled=False
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


def setup(app):
    app.add_cog(Shop(app))
