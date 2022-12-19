import discord
import random
import asyncio
from discord.utils import get
from discord.ext import commands, tasks
import operator
from collections import OrderedDict
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta


class GachaAbility:
    def __init__(self, name: str, icon: str, chance: float, description: str = "*No description*",
                 chance_revision: dict = None, pre_effects: list = None, post_effects: list = None):
        self.name = name
        self.icon = icon
        self.chance = chance
        self.description = description
        self.chance_revision = chance_revision
        self.rand_revision = 0.0
        for value in chance_revision.values():
            self.rand_revision += value
        self.pre_effects = pre_effects
        self.post_effects = post_effects

    def __str__(self):
        return self.icon + ' ' + self.name

    def __eq__(self, other):
        return other.name == self.name


class GachaItem:
    def __init__(self, icon: str, chance: float, events: list):
        self.icon = icon
        self.chance = chance
        self.events = events

    def __str__(self):
        return self.icon

    def check_event(self, prev: list, ability: GachaAbility = None):
        event_lst = []
        for event in self.events:
            if event.check_cond(prev, ability) is True:
                event_lst.append(event)
        return event_lst


class GachaEvent:
    def __init__(self, cond: list, event_methods: list, cond_range: int = 0,
                 exceptions: dict = None, description: str = "*No description*"):
        if len(cond) < 1:
            self.cond = ["Any"]
        else:
            self.cond = cond
        if cond_range < len(self.cond):
            self.cond_range = len(self.cond)
        else:
            self.cond_range = cond_range
        self.event_methods = event_methods
        self.description = description
        self.exceptions = exceptions

    def check_cond(self, prev: list, ability: GachaAbility = None):
        if ability.name in self.exceptions.get('ability'):
            return False
        if "Identical" in self.cond:
            check = [prev[0]] * self.cond_range
        else:
            check = self.cond.copy()
        for i in range(0, self.cond_range):
            if prev[i] in check:
                check.remove(prev[i])
            elif "Any" in check:
                check.remove("Any")
        return len(check) == 0


class Game(commands.Cog, name="게임", description="오락 및 도박과 관련된 카테고리입니다.\n토큰을 수급할 수 있습니다."):

    def __init__(self, app):
        self.app = app
        self.cannot_find_id = 'DB에서 ID를 찾지 못했습니다.\n\'%토큰\' 명령어를 통해 ID를 등록할 수 있습니다.'
        self.items = [
            GachaItem(":coin:", 50., [
                GachaEvent(
                    [":coin:"], [lambda ctx: self.event_get_coin(ctx, random.randint(20, 100))],
                    description="20~100개의 토큰을 얻습니다."
                ),
                GachaEvent(
                    [":coin:", ":coin:"], [lambda ctx: self.event_get_coin(ctx, random.randint(80, 120))],
                    description="80~120개의 토큰을 얻습니다."
                ),
                GachaEvent(
                    [":coin:", ":coin:", ":coin:"], [lambda ctx: self.event_get_coin(ctx, random.randint(160, 240))],
                    description="160~240개의 토큰을 얻습니다."
                )
            ]),
            GachaItem(":four_leaf_clover:", 10., [
                GachaEvent(
                    [":four_leaf_clover:"], [lambda ctx: self.event_luck(ctx, 1)], cond_range=3,
                    description="행운을 1중첩 얻습니다."
                )
            ]),
            GachaItem(":bomb:", 7.5, []),
            GachaItem(":firecracker:", 2.5, []),
            GachaItem(":fire:", 20., [
                GachaEvent(
                    [":four_leaf_clover:"], [lambda ctx: self.event_luck(ctx, -random.randint(1, 5))],
                    exceptions={'ability': ["firefighter"]},
                    description="행운을 1~5중첩 잃습니다. 중첩이 5 이하면 행운 효과를 모두 잃습니다."
                ),
                GachaEvent(
                    [":bomb:"], [lambda ctx: self.event_get_coin(ctx, -random.randint(120, 160)),
                                 lambda ctx: self.event_remove_item(ctx, ":bomb:", 3, 1)], cond_range=3,
                    exceptions={'ability': ["firefighter"]},
                    description="폭탄을 터트리고 120~160개의 토큰을 잃습니다."
                ),
                GachaEvent(
                    [":firecracker:"], [lambda ctx: self.event_get_coin(ctx, -random.randint(200, 300)),
                                 lambda ctx: self.event_remove_item(ctx, ":firecracker:", 3, 1)], cond_range=3,
                    exceptions={'ability': ["firefighter"]},
                    description="다이너마이트를 터트리고 200~300개의 토큰을 잃습니다."
                )
            ]),
            GachaItem(":cheese:", 10., []),
        ]
        self.special_items = [
            GachaItem(":slot_machine:", 15., [
                GachaEvent(
                    ["Identical"], [lambda ctx: self.event_get_coin(ctx, 777)], cond_range=3,
                    description="토큰을 777개 얻습니다."
                )
            ]),
            GachaItem(":mouse:", 25., [
                GachaEvent(
                    [":cheese:"], [lambda ctx: self.event_get_coin(ctx, random.randint(50, 100)),
                                   lambda ctx: self.event_remove_item(ctx, ":cheese:", 3, 1)],
                    cond_range=3,
                    description="치즈를 하나 먹고 50~100개의 토큰을 얻습니다."
                ),
                GachaEvent(
                    [":mouse_trap:"], [lambda ctx: self.event_get_coin(ctx, -random.randint(100, 150))],
                    cond_range=3,
                    description="쥐덫에 걸려 100~150개의 토큰을 잃습니다."
                )
            ]),
            GachaItem(":mouse_trap:", 15., [
                GachaEvent(
                    [":cheese:"], [lambda ctx: self.event_mousetrap(ctx, 3)], cond_range=3,
                    description="범위 안의 치즈를 모두 쥐덫으로 바꿉니다. 쥐덫에 걸리면 토큰을 잃습니다."
                )
            ]),
            GachaItem(":gift:", 25., [
                GachaEvent(
                    [":four_leaf_clover:"], [lambda ctx: self.event_gift(ctx)], cond_range=3,
                    description="50~50+(행운 중첩 수)개의 토큰을 얻습니다."
                )
            ]),
            GachaItem(":magnet:", 5., [
                GachaEvent(
                    [":coin:"], [lambda ctx: self.event_magnet(ctx, 10)], cond_range=10,
                    description="범위 안의 :coin:을 모두 끌어당기고 토큰을 (범위 안의 :coin:의 개수)*20개 얻습니다."
                )
            ]),
            GachaItem(":skull:", 5., [
                GachaEvent(
                    [], [lambda ctx: self.event_bankrupt(ctx)],
                    description="토큰을 모두 잃습니다."
                )
            ]),
            GachaItem(":fire_extinguisher:", 10., [
                GachaEvent(
                    [":fire:"], [lambda ctx: self.event_fire_extinguisher(ctx, 10)], cond_range=10,
                    description="범위 안의 불을 모두 제거하고 (제거한 불의 개수)*50의 토큰을 얻습니다."
                )
            ]),
        ]
        self.abilities = [
            GachaAbility("heart_afire", ":heart_on_fire:", 1.,
                         chance_revision={":fire:": 10},
                         description="불의 등장 확률이 증가합니다. 불이 나오면 토큰을 얻습니다."),
            GachaAbility("fastclock", ":hourglass:", 1.,
                         post_effects=[lambda ctx: self.event_reset_cooldown(ctx)],
                         description="일정 확률로 가챠의 쿨타임을 초기화합니다."),
            GachaAbility("firefighter", ":firefighter:", 1.,
                         chance_revision={":fire_extinguisher:": 10},
                         description="불로 인한 부정적인 효과를 받지 않으며, 소화기의 등장 확률이 증가합니다."),
        ]

    async def event_none(self, ctx):
        return None

    async def event_mousetrap(self, ctx, max_range: int = 1):
        gacha_channel = get(ctx.guild.text_channels, name="가챠")
        msgs = [message async for message in gacha_channel.history(limit=max_range)]
        cnt = 0
        for msg in msgs:
            if msg.content == ":cheese:":
                await msg.edit(content=":mouse_trap:")
                cnt += 1
        return f"{cnt}개의 치즈에 덫을 설치했습니다."

    async def event_fire_extinguisher(self, ctx, max_range: int = 5):
        gacha_channel = get(ctx.guild.text_channels, name="가챠")
        msgs = [message async for message in gacha_channel.history(limit=max_range)]
        cnt = 0
        for msg in msgs:
            if msg.content == ":fire:":
                await msg.delete()
                cnt += 1
        coin = await self.event_get_coin(ctx, cnt * 50)
        return f"{cnt}개의 불을 끄고 토큰을 얻었습니다!\n{coin}"

    async def event_magnet(self, ctx, max_range: int = 5):
        gacha_channel = get(ctx.guild.text_channels, name="가챠")
        msgs = [message async for message in gacha_channel.history(limit=max_range)]
        cnt = 0
        for msg in msgs:
            if msg.content == ":coin:":
                await msg.delete()
                await gacha_channel.send(":coin:")
                cnt += 1
        coin = await self.event_get_coin(ctx, cnt * 20)
        return f"{cnt}개의 :coin:을 끌어당겼습니다!\n{coin}"

    async def event_get_coin(self, ctx, n: int = 0):
        db = await self.app.find_id('$', ctx.author.id)
        coin = int(db.content[20:])
        await db.edit(content=db.content[:20] + str(coin + n))
        if n >= 0:
            return '+' + str(n) + " :coin:"
        else:
            return str(n) + " :coin:"

    async def event_luck(self, ctx, n: int = 0):
        global_guild = self.app.get_guild(self.app.global_guild_id)
        db_channel = get(global_guild.text_channels, name="db")
        db = await self.app.find_id('$', ctx.author.id)
        luck_log = await self.app.find_id('%', ctx.author.id)
        if luck_log is None:
            if n > 0:
                await db_channel.send('%' + str(ctx.author.id) + ';' + str(n))
                return "행운 효과를 얻었습니다!"
            else:
                return None
        else:
            luck = int(luck_log.content[20:])
            if n >= 0:
                await luck_log.edit(content=luck_log.content[:20] + str(luck + n))
                return f'+{n} :four_leaf_clover:'
            elif luck <= 5:
                await luck_log.delete()
                return f"행운 효과를 잃었습니다."
            else:
                await luck_log.edit(content=luck_log.content[:20] + str(luck + n))
                return f'{n} :four_leaf_clover:'

    async def event_gift(self, ctx):
        luck_log = await self.app.find_id('%', ctx.author.id)
        if luck_log is None:
            return None
        else:
            luck = int(luck_log.content[20:])
            gift = random.randint(50, 50 + luck)
            result = await self.event_get_coin(ctx, gift)
            return result

    async def event_remove_item(self, ctx, icon: str, max_range: int = 1, cnt: int = 1):
        gacha_channel = get(ctx.guild.text_channels, name="가챠")
        msgs = [message async for message in gacha_channel.history(limit=max_range)]
        for msg in msgs:
            if msg.content == icon:
                await msg.delete()
                break
        return f"{cnt}개의 {icon}을 제거했습니다."

    async def event_remove_all_items(self, ctx, icon: str, max_range: int = 1):
        gacha_channel = get(ctx.guild.text_channels, name="가챠")
        msgs = [message async for message in gacha_channel.history(limit=max_range)]
        cnt = 0
        for msg in msgs:
            if msg.content == icon:
                await msg.delete()
                cnt += 1
        return f"{cnt}개의 {icon}을 제거했습니다."

    async def event_bankrupt(self, ctx):
        db = await self.app.find_id('$', ctx.author.id)
        if int(db.content[20:]) > 0:
            await db.edit(content=db.content[:20]+'0')
        return "모든 토큰을 잃었습니다."

    async def event_reset_cooldown(self, ctx):
        rand = random.random() * 100
        if rand <= 20:
            await ctx.command.reset_cooldown(ctx)
            return "쿨타임 초기화 되었습니다."

    async def prize_token_change(self, ctx):
        db = await self.app.find_id('$', ctx.author.id)
        global_guild = self.app.get_guild(self.app.global_guild_id)
        db_channel = get(global_guild.text_channels, name="db")
        messages = await db_channel.history(limit=100).flatten()
        member_db = random.choice(
            [
                m for m in messages
                if m.content.startswith('$') and int(m.content[1:19]) not in [self.app.user.id, ctx.author.id]
            ]
        )
        member = await ctx.guild.fetch_member(int(member_db.content[1:19]))
        coin = db.content[20:]
        member_coin = member_db.content[20:]
        await db.edit(content=db.content[:20]+member_coin)
        await member_db.edit(content=member_db.content[:20]+coin)
        return member.mention + f" 님과 토큰이 뒤바뀌었습니다!\n{coin} <-> {member_coin} :coin:"

    async def prize_scales(self, ctx):
        db = await self.app.find_id('$', ctx.author.id)
        global_guild = self.app.get_guild(self.app.global_guild_id)
        db_channel = get(global_guild.text_channels, name="db")
        messages = await db_channel.history(limit=100).flatten()
        member_db = random.choice(
            [
                m for m in messages
                if m.content.startswith('$') and int(m.content[1:19]) not in [self.app.user.id, ctx.author.id]
            ]
        )
        member = await ctx.guild.fetch_member(int(member_db.content[1:19]))
        coin = int(db.content[20:])
        member_coin = int(member_db.content[20:])
        allocated_coin = (coin + member_coin) // 2
        await db.edit(content=db.content[:20] + str(allocated_coin))
        await member_db.edit(content=member_db.content[:20] + str(allocated_coin))
        return member.mention + " 님과 " + str(allocated_coin) + " :coin: 만큼 토큰을 분배받았습니다."

    async def prize_rise(self, ctx):
        bot_db = await self.app.find_id('$', self.app.user.id)
        prize = int(bot_db.content[20:])
        delta = random.randint(10, 30)
        await bot_db.edit(content=bot_db.content[:20] + str(prize + delta))
        return '복권 상금 +' + str(delta) + " :coin:"

    async def prize_reduce(self, ctx):
        bot_db = await self.app.find_id('$', self.app.user.id)
        prize = int(bot_db.content[20:])
        delta = random.randint(30, 50)
        await bot_db.edit(content=bot_db.content[:20] + str(prize - delta))
        return '복권 상금 -' + str(delta) + " :coin:"

    async def prize_pill(self, ctx):
        db = await self.app.find_id('$', ctx.author.id)
        coin = int(db.content[20:])
        prize = random.choice([2, 0.5])
        await db.edit(content=db.content[:20]+str(int(coin * prize)))
        return str(coin) + ' x ' + str(prize) + " :coin:"

    async def prize_cyclone(self, ctx):
        global_guild = self.app.get_guild(self.app.global_guild_id)
        db_channel = get(global_guild.text_channels, name="db")
        messages = await db_channel.history(limit=100).flatten()
        members_db = [
            m for m in messages
            if m.content.startswith('$') and int(m.content[1:19]) not in [self.app.user.id]
        ]
        increment = 0
        for member_db in members_db:
            lose = int(member_db.content[20:]) // 5
            if lose < 0:
                lose = 0
            increment += lose
            await member_db.edit(content=member_db.content[:20]+str(int(member_db.content[20:])-lose))
        bot_db = await self.app.find_id('$', self.app.user.id)
        await bot_db.edit(content=bot_db.content[:20] + str(int(bot_db.content[20:]) + increment))
        return f"0군봇이 모든 유저의 토큰의 20%를 빨아들였습니다!\n복권 상금 +{increment} :coin:"

    async def gather_members(self, ctx, game_name="게임"):
        members = []
        author_coin = await self.app.find_id('$', ctx.author.id)
        start = False
        if author_coin is None:
            await ctx.send(self.cannot_find_id)
        else:
            msg = await ctx.send(
                ctx.author.name + f" 님이 {game_name}을(를) 신청합니다."
                                  "\n참가하려면 :white_check_mark: 을 눌러주세요."
            )
            reaction_list = ['✅', '❎']
            while True:
                for r in reaction_list:
                    await msg.add_reaction(r)

                def check(reaction, user):
                    return str(reaction) in reaction_list and reaction.message.id == msg.id and user.bot is False

                try:
                    reaction, user = await self.app.wait_for("reaction_add", check=check, timeout=20.0)
                except asyncio.TimeoutError:
                    await msg.edit(content="시간 초과!", delete_after=2)
                else:
                    if str(reaction) == '✅':
                        if user == ctx.author:
                            members.append(user)
                            start = True
                            break
                        elif user not in members:
                            member_coin = await self.app.find_id('$', user.id)
                            if member_coin is None:
                                await ctx.send(self.cannot_find_id)
                            else:
                                members.append(user)
                    else:
                        if user == ctx.author:
                            await ctx.send(f"호스트가 {game_name}을(를) 취소했습니다.")
                            break
                        if user in members:
                            members.remove(user)
                    await msg.clear_reactions()
                    await msg.edit(
                        content=ctx.author.name + f" 님이 {game_name}을(를) 신청합니다."
                                                  "\n참가하려면 :white_check_mark: 을 눌러주세요."
                                                  "\n참가자 : " + ' '.join([x.nick for x in members])
                    )
        return start, members

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
            if ctx.author in ctx.guild.premium_subscribers:
                await db_channel.send('$' + str(ctx.author.id) + ';100')
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
        name="도박", aliases=["베팅", "gamble", "bet"],
        help="베팅한 토큰이 -1.0x ~ 1.0x 의 랜덤한 배율로 반환됩니다.", usage="* int((0, *token/2*])", pass_context=True
    )
    async def gamble(self, ctx, bet):
        log = await self.app.find_id('$', ctx.author.id)
        if log is None:
            await ctx.send(self.cannot_find_id)
        else:
            bet = int(bet)
            coin = int(log.content[20:])
            if ctx.channel == get(ctx.guild.text_channels, name="가챠"):
                if coin < bet:
                    await ctx.send("토큰이 부족합니다.")
                elif bet > coin//2:
                    await ctx.send("베팅은 보유 토큰의 절반까지만 할 수 있습니다.")
                elif bet <= 0:
                    await ctx.send("최소 토큰 1개 이상 베팅해야 합니다.")
                else:
                    embed = discord.Embed(title="<:video_game:  베팅 결과>", description=ctx.author.display_name + " 님의 결과")
                    multi = (random.random() - 0.5) * 1
                    prize = round(bet*multi)
                    await log.edit(content=log.content[:20] + str(coin + prize))
                    embed.add_field(name="> 베팅", value=str(bet) + " :coin:")
                    embed.add_field(name="> 배율", value=str("{:0.3f}".format(multi))+"x")
                    embed.add_field(name="> 배당", value=str(prize) + " :coin:")
                    await ctx.send(embed=embed)
            else:
                await ctx.send(":no_entry: 이 채널에서는 실행할 수 없는 명령어입니다.")

    @commands.cooldown(1, 60., commands.BucketType.user)
    @commands.bot_has_permissions(administrator=True)
    @commands.command(
        name="가챠", aliases=["ㄱㅊ", "gacha"],
        help="확률적으로 역할을 얻습니다.\n자세한 정보는 '%가챠정보'을 참고해주세요.", usage="* (str(*option*))"
    )
    async def gacha(self, ctx, option=None):
        db = await self.app.find_id('$', ctx.author.id)
        gacha_channel = get(ctx.guild.text_channels, name="가챠")
        if db is None:
            await ctx.send(self.cannot_find_id)
        else:
            if option is None:
                msg = await ctx.send("일반 가챠를 돌리시려면 :white_check_mark:, 특수 가챠를 돌리시려면 :black_joker:,"
                                     "취소하시려면 :negative_squared_cross_mark:를 눌러주세요.")
                reaction_list = ['✅', '🃏', '❎']
                for r in reaction_list:
                    await msg.add_reaction(r)

                def check(reaction, user):
                    return str(reaction) in reaction_list and reaction.message.id == msg.id and user == ctx.author

                try:
                    reaction, user = await self.app.wait_for("reaction_add", check=check, timeout=5.0)
                except asyncio.TimeoutError:
                    await msg.edit(content="시간 초과!", delete_after=2)
                else:
                    await msg.delete()
                    if str(reaction) in ['✅', '🃏']:
                        if str(reaction) == '🃏':
                            option = 's'
                        else:
                            option = 'n'
                    else:
                        await ctx.send("취소했습니다.")
                        return None
            if option in ['special', 'SPECIAL', '-s']:
                option = 's'
                item_lst = self.special_items
            elif option in ['normal', 'NORMAL', '-n']:
                option = 'n'
                item_lst = self.items
            else:
                return None
            ability = None
            ability_name = await self.app.find_id('*', ctx.author.id)
            for a in self.abilities:
                if a.name == ability_name:
                    ability = a
            item = None
            prev = [message.content async for message in gacha_channel.history(limit=10)]
            embed = discord.Embed(title="<:video_game: 가챠>",
                                  description=ctx.author.display_name + " 님의 결과")
            if ability and ability.pre_effects:
                for effect in ability.pre_effects:
                    await effect(ctx)
            if ability:
                rand = random.random() * (100 + ability.rand_revision)
            else:
                rand = random.random() * 100
            for i in item_lst:
                chance = i.chance
                if i.icon in ability.chance_revision.keys():
                    chance += ability.chance_revision.get(i.icon)
                if rand <= chance:
                    item = i
                    break
                else:
                    rand -= chance
            if option == 's':
                await ctx.send(item.icon)
            elif option == 'n':
                await gacha_channel.send(item.icon)
            event_lst = item.check_event(prev, ability)
            if len(event_lst) > 0:
                for event in event_lst:
                    for method in event.event_methods:
                        effect = await method(ctx)
                        embed.add_field(name="이벤트", value=effect, inline=False)
                await ctx.send(embed=embed)
            if ability and ability.post_effects:
                for effect in ability.post_effects:
                    await effect(ctx)

    @commands.command(
        name="가챠정보", aliases=["gachainfo"],
        help="'가챠'의 정보를 공개합니다.\n'%가챠정보 특수'를 통해 특수 가챠의 정보를 확인할 수 있습니다."
             "\n'%가챠정보 *item*을 통해 아이템의 이벤트 목록을 확인할 수 있습니다.", usage="* (str()) (str(adjusted))", pass_context=True
    )
    async def gacha_info(self, ctx, args: str = None, option: str = None):
        ability = None
        ability_name = await self.app.find_id('*', ctx.author.id)
        for a in self.abilities:
            if a.name == ability_name:
                ability = a
        if args is None:
            embed = discord.Embed(
                title="<가챠 정보>",
                description="일반 가챠의 아이템 목록입니다.\n"
                            "일반 가챠로 등장한 아이템은 가챠 채널에 추가됩니다."
            )
            whole_rand = 100
            if option == 'adjusted' and ability:
                whole_rand += ability.rand_revision
            rest = whole_rand
            for item in self.items:
                chance = item.chance
                if option == 'adjusted' and ability:
                    if ability and item.icon in ability.chance_revision.keys():
                        chance += ability.chance_revision.get(item.icon)
                embed.add_field(name=item.icon, value="{:0.2f}%".format((chance/whole_rand)*100), inline=True)
                rest -= chance
            embed.add_field(name="> Rest", value='{:0.2f}%'.format((rest/whole_rand)*100), inline=False)
            await ctx.send(embed=embed)
        elif args in ["special", "특수", "특수가챠"]:
            embed = discord.Embed(
                title="<가챠 정보>",
                description="특수 가챠의 아이템 목록입니다.\n"
                            "특수 가챠는 기본적으로 가챠 채널에 아이템을 추가하지 않으며, 기대 이익이 큰 만큼 높은 리스크를 동반합니다."
            )
            whole_rand = 100
            if option == 'adjusted' and ability:
                whole_rand += ability.rand_revision
            rest = whole_rand
            for item in self.special_items:
                chance = item.chance
                if option == 'adjusted' and ability:
                    if ability and item.icon in ability.chance_revision.keys():
                        chance += ability.chance_revision.get(item.icon)
                embed.add_field(name=item.icon, value="{:0.2f}%".format((chance / whole_rand) * 100), inline=True)
                rest -= chance
            embed.add_field(name="> Rest", value='{:0.2f}%'.format((rest / whole_rand) * 100), inline=False)
            await ctx.send(embed=embed)
        else:
            not_found = True
            for item in self.items + self.special_items:
                if args in [item.icon, item.icon[1:-1]]:
                    embed = discord.Embed(
                        title="<가챠 정보>",
                        description=f"{item.icon}의 이벤트 목록입니다."
                    )
                    for event in item.events:
                        embed.add_field(
                            name=f"> {' '.join(event.cond)} in {event.cond_range}",
                            value=event.description, inline=False
                        )
                    await ctx.send(embed=embed)
                    not_found = False
                    break
            if not_found:
                await ctx.send("항목을 찾을 수 없습니다.")

    @commands.command(
        name="복권", aliases=["ㅂㄱ", "lottery"],
        help="가챠에서 꽝이 나오면 복권 상금이 오릅니다."
             "\n'복권' 명령어를 통해 당첨 시 상금을 얻습니다."
             "\n(기본 당첨 확률은 1%)", usage="*"
    )
    async def lottery(self, ctx):
        log = await self.app.find_id('$', ctx.author.id)
        if log is None:
            await ctx.send(self.cannot_find_id)
        else:
            bot_log = await self.app.find_id('$', self.app.user.id)
            luck_log = await self.app.find_id('%', ctx.author.id)
            luck = 0
            prob = 1
            if luck_log is not None:
                luck = int(luck_log.content[20:])
            if ctx.author in ctx.guild.premium_subscribers:
                prob = 1.5
            coin = int(log.content[20:])
            prize = int(bot_log.content[20:])
            if ctx.channel == get(ctx.guild.text_channels, name="가챠"):
                rand = random.random() * 100
                if rand <= prob + (luck ** 0.5) * 0.1:
                    await bot_log.edit(content=bot_log.content[:20] + str(10))
                    await log.edit(content=log.content[:20] + str(coin + prize))
                    await ctx.send(f"{ctx.author.display_name} 님이 복권에 당첨되셨습니다! 축하드립니다!\n상금: {prize} :coin:")
                    if luck_log is not None:
                        await luck_log.delete()
                        await ctx.send("행운이 초기화되었습니다.")
                else:
                    await ctx.send("꽝 입니다. 다음에 도전하세요.")
            else:
                await ctx.send(f"현재 당첨 상금: {prize} :coin:")

    @commands.cooldown(1, 30., commands.BucketType.member)
    @commands.command(
        name="가위바위보", aliases=["rsp"],
        help="봇과 가위바위보를 합니다.\n이기면 토큰 하나를 얻고, 지면 토큰 하나를 잃습니다.",
        usage="*"
    )
    async def rock_scissors_paper(self, ctx):
        log = await self.app.find_id('$', ctx.author.id)
        if log is not None:
            coin = int(log.content[20:])
            msg = await ctx.send("아래 반응 중 하나를 골라보세요.")
            reaction_list = ['✊', '✌️', '🖐️']
            for r in reaction_list:
                await msg.add_reaction(r)

            def check(reaction, user):
                return str(reaction) in reaction_list and reaction.message.id == msg.id and user == ctx.author

            try:
                reaction, user = await self.app.wait_for("reaction_add", check=check, timeout=5.0)
            except asyncio.TimeoutError:
                await msg.edit(content="시간 초과!", delete_after=2)
            else:
                hand = [':fist:', ':v:', ':hand_splayed:']
                bot_react = random.choice(hand)
                user_react = None
                await ctx.send(bot_react)
                if str(reaction) == '✊':
                    user_react = ':fist:'
                elif str(reaction) == '✌️':
                    user_react = ':v:'
                elif str(reaction) == '🖐️':
                    user_react = ':hand_splayed:'
                i = hand.index(user_react) + 1
                if i > 2:
                    i = 0
                if bot_react == user_react:
                    await ctx.send('비겼네요.')
                elif bot_react == hand[i]:
                    await ctx.send(ctx.author.display_name + ' 님 승리!')
                    coin += 1
                else:
                    await ctx.send(ctx.author.display_name + ' 님 패배')
                    coin -= 1
                await log.edit(content=log.content[:20] + str(coin))
        else:
            await ctx.send(self.cannot_find_id)

    @commands.cooldown(1, 30., commands.BucketType.member)
    @commands.command(
        name="홀짝", aliases=["짝홀", "odd-even"],
        help="봇이 무작위로 한자리 정수를 정합니다."
             "\n봇이 정한 숫자의 홀짝을 맞히면 승리합니다."
             "\n승리하면 봇이 정한 숫자만큼 토큰을 얻고, 패배하면 잃습니다."
             "\n만약 0을 맞추면 15 ~ 30코인을 얻습니다.",
        usage="*"
    )
    async def odd_or_even(self, ctx):
        log = await self.app.find_id('$', ctx.author.id)
        if log is not None:
            coin = int(log.content[20:])
            num = random.randint(0, 9)
            if num == 0:
                result = 'zero'
            elif num % 2 == 0:
                result = 'even'
            else:
                result = 'odd'
            msg = await ctx.send("홀짝을 맞춰보세요!")
            odd_aliases = ['홀', '홀수', 'odd']
            even_aliases = ['짝', '짝수', 'even']
            zero_aliases = ['0', '영', 'zero']

            def check(m):
                return m.content in odd_aliases + even_aliases + zero_aliases and m.author == ctx.author and m.channel == ctx.channel

            try:
                message = await self.app.wait_for("message", check=check, timeout=60.0)
            except asyncio.TimeoutError:
                await msg.edit(content="시간 초과!", delete_after=2)
            else:
                await msg.edit(content=str(num))
                if message.content in odd_aliases:
                    choice = 'odd'
                elif message.content in even_aliases:
                    choice = 'even'
                else:
                    choice = 'zero'
                if result == choice:
                    await ctx.send(ctx.author.display_name + " 님 승!")
                    if num == 0:
                        prize = random.randint(15, 30)
                        await log.edit(content=log.content[:20] + str(coin + prize))
                    else:
                        await log.edit(content=log.content[:20] + str(coin + num))
                else:
                    await ctx.send(ctx.author.display_name + " 님 패!")
                    await log.edit(content=log.content[:20] + str(coin - num))
        else:
            await ctx.send(self.cannot_find_id)

    @commands.cooldown(1, 60., commands.BucketType.guild)
    @commands.command(
        name="인디언포커", aliases=["IndianPoker"],
        help="인디언 포커를 신청합니다."
             "\n시작하면 각자에게 개인 메세지로 상대의 패를 알려준 후, 토큰 베팅을 시작합니다."
             "\n레이즈하면 판 돈을 두 배로 올리며, 플레이어 양쪽이 콜하면 결과를 공개합니다."
             "\n자신의 패는 알 수 없으며 숫자가 높은 쪽이 이깁니다.", usage="* @*member*"
    )
    async def indian_poker(self, ctx, member: discord.Member):
        party = (member, ctx.author)
        limit = 0
        author_log = await self.app.find_id('$', ctx.author.id)
        member_log = await self.app.find_id('$', member.id)
        if author_log is None:
            await ctx.send(f'로그에서 {ctx.author.name} 님의 ID를 찾지 못했습니다.')
        else:
            limit += int(author_log.content[20:])
        if member_log is None:
            await ctx.send(f'로그에서 {member.name} 님의 ID를 찾지 못했습니다.')
        else:
            limit += int(member_log.content[20:])
        limit = limit // 2
        if author_log is not None:
            if member_log is not None:
                msg = await ctx.send(
                    ctx.author.display_name + " 님이 " + member.display_name + " 님에게 인디언 포커를 신청합니다."
                    "\n수락하려면 :white_check_mark: 을 눌러주세요."
                )
                reaction_list = ['✅', '❎']
                for r in reaction_list:
                    await msg.add_reaction(r)

                def check(reaction, user):
                    return str(reaction) in reaction_list and reaction.message.id == msg.id and user == member

                try:
                    reaction, user = await self.app.wait_for("reaction_add", check=check, timeout=10.0)
                except asyncio.TimeoutError:
                    await msg.edit(content="시간 초과!", delete_after=2)
                else:
                    if str(reaction) == '✅':
                        await msg.delete()
                        deck = []
                        for i in [':spades:', ':clubs:', ':hearts:', ':diamonds:']:
                            for j in ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10']:
                                deck.append(i + j)
                        coin = 1
                        board = {}
                        called_party = []
                        for m in party:
                            card = random.choice(deck)
                            board[m] = card
                            deck.remove(card)
                        a_dm = await ctx.author.create_dm()
                        await a_dm.send(board.get(member))
                        m_dm = await member.create_dm()
                        await m_dm.send(board.get(ctx.author))
                        reaction_list = ['⏏️', '✅', '💀']
                        num = 0
                        msg_ = await ctx.send("On ready...")
                        while len(called_party) < 2:
                            embed = discord.Embed(title="<인디언 포커>", description=f"{str(coin)} :coin:")
                            embed.add_field(name="> :white_check_mark:", value=str([x.display_name for x in called_party]),
                                            inline=True)
                            await msg_.edit(content=party[num].mention + " 님 차례입니다.", embed=embed)
                            for r in reaction_list:
                                await msg_.add_reaction(r)

                            def check(reaction, user):
                                return str(reaction) in reaction_list and reaction.message.id == msg_.id \
                                       and user == party[num]

                            try:
                                reaction, user = await self.app.wait_for("reaction_add", check=check, timeout=30.0)
                            except asyncio.TimeoutError:
                                await ctx.send(party[num].display_name + " 님이 시간을 초과하여 자동으로 다이 처리됩니다.")
                                if party[num] == ctx.author:
                                    await author_log.edit(
                                        content=author_log.content[:20] + str(int(author_log.content[20:]) - coin)
                                    )
                                    await member_log.edit(
                                        content=member_log.content[:20] + str(int(member_log.content[20:]) + coin)
                                    )
                                else:
                                    await author_log.edit(
                                        content=author_log.content[:20] + str(int(author_log.content[20:]) + coin)
                                    )
                                    await member_log.edit(
                                        content=member_log.content[:20] + str(int(member_log.content[20:]) - coin)
                                    )
                                await ctx.send(party[num].display_name + " 다이")
                                await msg_.delete()
                                break
                            else:
                                if str(reaction) == '⏏️':
                                    if coin*2 > limit:
                                        await ctx.send("판돈은 두 플레이어의 토큰의 합의 절반을 초과할 수 없습니다.")
                                    else:
                                        called_party = []
                                        coin *= 2
                                        num += 1
                                elif str(reaction) == '✅':
                                    called_party.append(user)
                                    num += 1
                                else:
                                    if user == ctx.author:
                                        await author_log.edit(
                                            content=author_log.content[:20] + str(int(author_log.content[20:]) - coin)
                                        )
                                        await member_log.edit(
                                            content=member_log.content[:20] + str(int(member_log.content[20:]) + coin)
                                        )
                                    else:
                                        await author_log.edit(
                                            content=author_log.content[:20] + str(int(author_log.content[20:]) + coin)
                                        )
                                        await member_log.edit(
                                            content=member_log.content[:20] + str(int(member_log.content[20:]) - coin)
                                        )
                                    await ctx.send(user.display_name + " 다이")
                                    await msg_.delete()
                                    break
                            if num >= 2:
                                num = 0
                            if len(called_party) == 2:
                                await ctx.send("콜 성사")
                                await msg_.delete()
                                break
                            await msg_.clear_reactions()
                        await ctx.send(f'{ctx.author.nick} {str(board[ctx.author])} : {member.nick} {str(board[member])}')
                        for m in party:
                            card = board.get(m)
                            if card[card.rfind(':') + 1:] == 'A':
                                board[m] = 1
                            else:
                                board[m] = int(card[card.rfind(':') + 1:])
                        if len(called_party) == 2:
                            if board[ctx.author] == board[member]:
                                await ctx.send("무승부")
                            elif board[ctx.author] > board[member]:
                                await author_log.edit(
                                    content=author_log.content[:20] + str(int(author_log.content[20:]) + coin)
                                )
                                await member_log.edit(
                                    content=member_log.content[:20] + str(int(member_log.content[20:]) - coin)
                                )
                                await ctx.send(ctx.author.nick + " 승!")
                            elif board[ctx.author] < board[member]:
                                await author_log.edit(
                                    content=author_log.content[:20] + str(int(author_log.content[20:]) - coin)
                                )
                                await member_log.edit(
                                    content=member_log.content[:20] + str(int(member_log.content[20:]) + coin)
                                )
                                await ctx.send(member.nick + " 승!")
                    else:
                        await ctx.send("신청을 거절했습니다.")

    @commands.cooldown(1, 60., commands.BucketType.guild)
    @commands.command(
        name="블랙잭", aliases=["Blackjack"],
        help="블랙잭을 신청합니다."
             "\nA는 1 or 11으로, J,Q,K는 10으로 계산하며,"
             "\n패의 합이 21에 가장 가까운 사람이 승리합니다."
             "\n21를 초과하면 0점으로 처리됩니다."
             "\n시작하면 참가자마다 두 장의 카드를 받습니다."
             "\n카드를 더 받을 지, 그대로 정할 지 모두 선택이 끝나면,"
             "\n승자를 정합니다.", usage="* (int(default=1))"
    )
    async def blackjack(self, ctx, coin=1):
        start, members = await self.gather_members(ctx, "블랙잭")
        coin = int(coin)
        if coin < 1:
            await ctx.send("상금 배율은 1 이상이어야 합니다.")
            start = False
        elif coin > 100:
            await ctx.send("상금 배율은 100 이하여야 합니다.")
            start = False
        if start is True:
            if len(members) < 2:
                await ctx.send("블랙잭은 혼자할 수 없습니다.")
            elif len(members) > 8:
                await ctx.send("블랙잭은 최대 8인까지 가능합니다.")
            else:
                deck = []
                for i in [':spades:', ':clubs:', ':hearts:', ':diamonds:']:
                    for j in ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K']:
                        deck.append(i + j)
                board = {}
                finish_members = []
                for member in members:
                    a = random.choice(deck)
                    deck.remove(a)
                    b = random.choice(deck)
                    deck.remove(b)
                    board[member] = a + ' ' + b
                    member_sum = 0
                    ace = False
                    for i in board.get(member).split():
                        if i[i.rfind(':') + 1:] == 'A':
                            ace = True
                            member_sum += 1
                        elif i[i.rfind(':') + 1:] in ['J', 'Q', 'K']:
                            member_sum += 10
                        else:
                            member_sum += int(i[i.rfind(':') + 1:])
                    if ace is True:
                        if member_sum <= 11:
                            member_sum += 10
                    if member_sum >= 21:
                        finish_members.append(member)
                players = []
                for x in members:
                    if x in finish_members:
                        pass
                    else:
                        players.append(x)
                reaction_list = ['✅', '❎']
                num = 0
                msg_ = await ctx.send("On ready...")
                while len(finish_members) != len(members):
                    players = [x for x in members if x not in finish_members]
                    if num >= len(players):
                        num = 0
                    embed = discord.Embed(title="<블랙잭>", description=f"{str(len(members)*coin)} :coin:")
                    for member in members:
                        if member in finish_members:
                            embed.add_field(name="> " + member.name, value=board[member], inline=True)
                        else:
                            embed.add_field(name=member.name, value=board[member], inline=True)
                    await msg_.edit(content=players[num].mention + " 님 카드를 더 받을 지, 멈출 지 선택해주세요.", embed=embed)
                    for r in reaction_list:
                        await msg_.add_reaction(r)

                    def check(reaction, user):
                        return str(reaction) in reaction_list and reaction.message.id == msg_.id \
                               and user == players[num]

                    try:
                        reaction, user = await self.app.wait_for("reaction_add", check=check, timeout=60.0)
                    except asyncio.TimeoutError:
                        await ctx.send(players[num].name + " 님이 시간을 초과하여 자동으로 홀드 처리됩니다.")
                        finish_members.append(players[num])
                        num -= 1
                    else:
                        if str(reaction) == '✅':
                            c = random.choice(deck)
                            deck.remove(c)
                            board[user] = board[user] + ' ' + c
                            member_sum = 0
                            ace = False
                            for i in board[user].split():
                                if i[i.rfind(':') + 1:] == 'A':
                                    ace = True
                                    member_sum += 1
                                elif i[i.rfind(':') + 1:] in ['J', 'Q', 'K']:
                                    member_sum += 10
                                else:
                                    member_sum += int(i[i.rfind(':') + 1:])
                            if ace is True:
                                if member_sum <= 11:
                                    member_sum += 10
                            if member_sum >= 21:
                                finish_members.append(user)
                                num -= 1
                        else:
                            finish_members.append(user)
                            num -= 1
                    num += 1
                    players = [x for x in members if x not in finish_members]
                    if num >= len(players):
                        num = 0
                    await msg_.clear_reactions()
                embed = discord.Embed(title="<블랙잭>", description=f"{str(len(members)*coin)} :coin:")
                for member in members:
                    if member in finish_members:
                        embed.add_field(name="> " + member.name, value=board[member], inline=True)
                    else:
                        embed.add_field(name=member.name, value=board[member], inline=True)
                await msg_.edit(content="모든 플레이어가 선택을 종료했습니다.", embed=embed)
                for member in finish_members:
                    member_sum = 0
                    ace = False
                    bj = False
                    for i in board[member].split():
                        if i[i.rfind(':') + 1:] == 'A':
                            ace = True
                            if len(board[member].split()) == 2:
                                bj = True
                            member_sum += 1
                        elif i[i.rfind(':') + 1:] in ['J', 'Q', 'K']:
                            member_sum += 10
                        else:
                            member_sum += int(i[i.rfind(':') + 1:])
                    if ace is True:
                        if member_sum <= 11:
                            member_sum += 10
                    if member_sum == 21:
                        if bj is True:
                            board[member] = 22
                        else:
                            board[member] = 21
                    elif member_sum < 21:
                        board[member] = int(member_sum)
                    else:
                        board[member] = 0
                winners = [finish_members[0]]
                for member in finish_members:
                    if member not in winners:
                        if board[member] == board[winners[0]]:
                            winners.append(member)
                        elif board[member] > board[winners[0]]:
                            winners = [member]
                for member in finish_members:
                    if member in winners:
                        prize = int((len(finish_members) - 1) // len(winners)) * int(coin)
                    else:
                        prize = -1 * int(coin)
                    member_log = await self.app.find_id('$', member.id)
                    member_coin = int(member_log.content[20:])
                    await member_log.edit(content=member_log.content[:20] + str(member_coin + prize))
                embed = discord.Embed(
                    title="<블랙잭 결과>",
                    description=', '.join([x.name for x in winners]) +
                                f' 님 우승! (상금: {((len(finish_members)-1) // len(winners))*coin} :coin:)'
                )
                for member in members:
                    if board[member] == 22:
                        embed.add_field(name=member.name, value='21(Blackjack)', inline=True)
                    else:
                        embed.add_field(name=member.name, value=str(board[member]), inline=True)
                await ctx.send(embed=embed)

    @commands.cooldown(1, 60., commands.BucketType.guild)
    @commands.command(
        name="섯다", aliases=["ㅅㄷ"],
        help="섯다를 신청합니다."
             "\n시작하면 참가자마다 두 장의 패를 받습니다."
             "\n모두 패를 받으면, 순서대로 베팅을 시작합니다."
             "\n⏏️: 하프, ‼️: 따당, ✅: 콜(체크), 💀: 다이"
             "\n모두 베팅을 마치고 나면, 패를 공개해 승자를 정합니다."
             "\n가지고 있는 패의 족보가 높은 사람이 승리합니다."
             "\n족보: 38광땡, 광땡, 땡, 알리, 독사, "
             "구삥, 장삥, 장사, 세륙, 끗, 구사, 땡잡이, 암행어사", usage="* (int(default=1))"
    )
    async def seotda(self, ctx, seed=1):
        seed = int(seed)
        start, members = await self.gather_members(ctx, "섯다")
        if seed > 10:
            await ctx.send("삥값은 10을 넘을 수 없습니다.")
            start = False
        elif seed < 1:
            await ctx.send("삥값은 최소 1 이상이어야 합니다.")
            start = False
        if start is True:
            if len(members) < 2:
                await ctx.send("섯다는 혼자할 수 없습니다.")
            elif len(members) > 5:
                await ctx.send("섯다는 최대 5인까지 가능합니다.")
            else:
                deck = ['1광', '2열끗', '3광', '4열끗', '5열끗', '6열끗', '7열끗', '8광', '9열끗', '장열끗']
                for i in range(1, 10):
                    deck.append(str(i))
                deck.append('장')
                middles = ['세륙', '장사', '장삥', '구삥', '독사', '알리']
                ends = []
                for i in range(0, 10):
                    ends.append(str(i) + '끗')
                pairs = []
                for i in range(1, 10):
                    pairs.append(str(i) + '땡')
                pairs.append('장땡')
                level_table = ['땡잡이', '암행어사', '멍텅구리구사', '구사'] + ends + middles + pairs + ['13광땡', '18광땡', '38광땡']
                coin = len(members) * seed
                pay = {}
                for member in members:
                    pay[member] = seed
                regame = True
                while regame:
                    regame = False
                    board = {}
                    die_members = []
                    call_members = []
                    for member in members:
                        a = random.choice(deck)
                        deck.remove(a)
                        b = random.choice(deck)
                        deck.remove(b)
                        board[member] = a + ' ' + b
                    for member in members:
                        hand = board.get(member).split()
                        hand1 = hand[0]
                        hand2 = hand[1]
                        n = 0
                        if hand1[0] == '장':
                            n += 10
                        else:
                            n += int(hand1[0])
                        if hand2[0] == '장':
                            n += 10
                        else:
                            n += int(hand2[0])
                        while n > 9:
                            n -= 10
                        n = str(n) + '끗'
                        if hand1[0] == hand2[0]:
                            n = hand1[0] + '땡'
                        if hand1[0] == '9' or hand1[0] == '4':
                            if int(hand1[0]) + int(hand2[0]) == 13:
                                n = '구사'
                        if hand1[0] == '1' or hand2[0] == '1':
                            if int(hand1[0]) + int(hand2[0]) == 3:
                                n = '알리'
                            elif int(hand1[0]) + int(hand2[0]) == 5:
                                n = '독사'
                            elif int(hand1[0]) + int(hand2[0]) == 10:
                                n = '구삥'
                            elif hand1[0] == '장' or hand2[0] == '장':
                                n = '장삥'
                        if hand1[0] == '4' or hand2[0] == '4':
                            if hand1[0] == '장' or hand2[0] == '장':
                                n = '장사'
                            elif int(hand1[0]) + int(hand2[0]) == 10:
                                n = '세륙'
                        if '8광' in hand:
                            if '3광' in hand:
                                n = '38광땡'
                            elif '1광' in hand:
                                n = '18광땡'
                        elif '1광' in hand:
                            if '3광' in hand:
                                n = '13광땡'
                        elif '7열끗' in hand:
                            if '3광' in hand:
                                n = '땡잡이'
                            elif '4열끗' in hand:
                                n = '암행어사'
                        elif '9열끗' in hand:
                            if '4열끗' in hand:
                                n = '멍텅구리구사'
                        board[member] = board.get(member) + ' ' + n
                    for member in members:
                        hand = board.get(member).split()
                        member_dm = await member.create_dm()
                        await member_dm.send(hand[0] + ' , ' + hand[1])
                    call = 0
                    winner = ctx.author
                    embed = discord.Embed(title="<섯다>",
                                          description=f'{str(coin)} :coin: (콜 비용: {str(call)})')
                    for member in members:
                        embed.add_field(name='> ' + member.name,
                                        value=str(pay[member]) + ' :coin:', inline=True)
                    msg_ = await ctx.send(content=members[0].mention + " 님 베팅해주세요.", embed=embed)
                    reaction_list = ['⏏️', '‼️', '✅', '💀']
                    num = 0
                    while len(call_members) != len(members):
                        players = [x for x in members if x not in die_members]
                        if num >= len(players):
                            num = 0
                        for r in reaction_list:
                            await msg_.add_reaction(r)

                        def check(reaction, user):
                            return str(reaction) in reaction_list and reaction.message.id == msg_.id \
                                   and user == players[num]

                        try:
                            reaction, user = await self.app.wait_for("reaction_add", check=check, timeout=60.0)
                        except asyncio.TimeoutError:
                            die_members.append(players[num])
                            await ctx.send(players[num].name + " 님이 시간을 초과하여 자동으로 다이 처리합니다.")
                            num -= 1
                        else:
                            if str(reaction) == '⏏️':
                                call = coin // 2
                                coin += call
                                call_members = [user]
                                pay[user] += call
                            elif str(reaction) == '‼️':
                                call = call * 2
                                coin += call
                                call_members = [user]
                                pay[user] += call
                            elif str(reaction) == '✅':
                                call_members.append(user)
                                coin += call
                                pay[user] += call
                            else:
                                die_members.append(user)
                                await ctx.send(user.name + ' 다이')
                                num -= 1
                        num += 1
                        players = [x for x in members if x not in die_members]
                        if num >= len(players):
                            num = 0
                        if len(players) == 1:
                            winner = players[0]
                            break
                        embed = discord.Embed(title="<섯다>",
                                              description=f'{str(coin)} :coin: (콜 비용: {str(call)})')
                        for member in members:
                            embed.add_field(name='> ' + member.name,
                                            value=str(pay[member]) + ' :coin:', inline=True)
                        await msg_.clear_reactions()
                        await msg_.edit(content=players[num].mention + " 님 베팅해주세요.", embed=embed)
                    for member in call_members:
                        m_hand = board.get(member).split()
                        w_hand = board.get(winner).split()
                        if level_table.index(m_hand[2]) > level_table.index(w_hand[2]):
                            winner = member
                    w_hand = board[winner].split()
                    if w_hand[2] in ['13광땡', '18광땡']:
                        for member in call_members:
                            m_hand = board.get(member).split()
                            if m_hand[2] == '암행어사':
                                winner = member
                    elif w_hand[2] in pairs[:9]:
                        for member in call_members:
                            m_hand = board.get(member).split()
                            if m_hand[2] == '땡잡이':
                                winner = member
                    elif level_table.index(w_hand[2]) < 30:
                        for member in call_members:
                            m_hand = board.get(member).split()
                            if m_hand[2] == '멍텅구리구사':
                                regame = True
                    elif level_table.index(w_hand[2]) < 20:
                        for member in call_members:
                            m_hand = board.get(member).split()
                            if m_hand[2] == '구사':
                                regame = True
                    if regame:
                        for member in die_members:
                            member_log = await self.app.find_id('$', member.id)
                            member_coin = int(member_log.content[20:])
                            await member_log.edit(content=member_log.content[:20] + str(member_coin - pay[member]))
                        embed = discord.Embed(title="<섯다 결과>", description='재경기')
                        for member in members:
                            hand = board.get(member).split()
                            embed.add_field(name=member.name, value=hand[0] + ' , ' + hand[1]
                                                                    + ' (' + hand[2] + ')', inline=True)
                        await ctx.send(embed=embed)
                        members = call_members
                    else:
                        for member in members:
                            if member == winner:
                                pay[member] -= coin
                            member_log = await self.app.find_id('$', member.id)
                            member_coin = int(member_log.content[20:])
                            await member_log.edit(content=member_log.content[:20] + str(member_coin - pay[member]))
                        embed = discord.Embed(title="<섯다 결과>", description=winner.name + ' 우승!')
                        for member in members:
                            hand = board.get(member).split()
                            embed.add_field(name=member.name, value=hand[0] + ' , ' + hand[1]
                                            + ' (' + hand[2] + ')', inline=True)
                        await ctx.send(embed=embed)


def setup(app):
    app.add_cog(Game(app))
