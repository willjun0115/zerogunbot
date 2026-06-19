import discord
import random
import asyncio
from discord.utils import get
from discord.ext import commands
import operator


class GachaAbility:
    def __init__(self, name: str, icon: str, chance: float, added_slots = 0, chance_revision: dict | None = None,
                 special_events: list | None = None, description: str = "*No description*"):
        self.name = name
        self.icon = icon
        self.chance = chance
        self.description = description
        self.added_slots = added_slots
        self.chance_revision = chance_revision
        self.special_events = special_events

    def __str__(self):
        return self.icon + ' ' + self.name

    def __eq__(self, other):
        return other.name == self.name


class GachaItem:
    def __init__(self, icon: str, chance: float):
        self.icon = icon
        self.chance = chance

    def __str__(self):
        return self.icon


class GachaEvent:
    def __init__(self, cond: list, event_methods: list,
                 tags: list | None = None, description: str = "*No description*"):
        self.cond = cond
        self.event_methods = event_methods
        self.tags = tags
        self.description = description

    def check_cond(self, item_lst: list):
        cond = self.cond
        for i in cond:
            if i in item_lst or i == 'Any':
                cond.remove(i)
        return len(cond) == 0


class Game(commands.Cog, name="게임", description="오락 및 도박과 관련된 카테고리입니다.\n토큰을 수급할 수 있습니다."):

    def __init__(self, app):
        self.app = app
        self.cannot_find_id = 'DB에서 ID를 찾지 못했습니다.\n\'%토큰\' 명령어를 통해 ID를 등록할 수 있습니다.'
        self.items = [
            GachaItem(":coin:", 50.),
            GachaItem(":four_leaf_clover:", 15.),
            GachaItem(":bomb:", 4.),
            GachaItem(":fire:", 20.),
            GachaItem(":cheese:", 10.),
            GachaItem(":gift:", 1.),
        ]
        self.all_icons = [i.icon for i in self.items]
        self.events = [
            GachaEvent(
                [":coin:"], [lambda ctx, data: self.event_get_coin(data, 10)],
                description="토큰을 10 :coin: 얻습니다."
            ),
            GachaEvent(
                [":coin:", ":coin:", ":coin:"], [lambda ctx, data: self.event_get_coin(data, 100)],
                description="토큰을 100 :coin: 얻습니다."
            )
        ]
        self.abilities = [
            GachaAbility("heart_afire", ":heart_on_fire:", 0.,
                         chance_revision={":fire:": 20.},
                         special_events=[
                             lambda ctx, data, item: self.event_get_coin(data, random.randint(0, 400))
                             if item.icon == ":fire:" else self.event_none()
                         ],
                         description=":fire:의 등장 확률이 증가합니다."
                                     "\n:fire:가 나오면 0~400 토큰을 얻습니다."),
            GachaAbility("fast_clock", ":hourglass:", 5.,
                         special_events=[
                             lambda ctx, data, item: self.event_reset_cooldown(ctx)
                             if random.random() <= 0.25 else self.event_none()
                         ],
                         description="25%의 확률로 가챠의 쿨타임을 초기화합니다."),
            GachaAbility("firefighter", ":firefighter:", 0.,
                         chance_revision={":fire_extinguisher:": 30.},
                         special_events=[
                             lambda event: [] if ":fire:" == event.parent else [event]
                         ],
                         description=":fire:로 인한 부정적인 효과를 받지 않습니다.\n"
                                     "특수 가챠에서 :fire_extinguisher:의 등장 확률이 발생합니다."),
            GachaAbility("cat", ":cat:", 0.,
                         special_events=[
                             lambda event: [] if ":mouse:" == event.parent else [event],
                             lambda ctx, data, item: self.event_get_coin(data, 100)
                             if item.icon == ":mouse:" else self.event_none()
                         ],
                         description=":mouse: 등장 시 100 토큰을 얻습니다.\n"
                                     ":mouse:로 인한 효과를 받지 않습니다."),
            GachaAbility("genie", ":genie:", 0.,
                         chance_revision={":four_leaf_clover:": 20.},
                         description=":four_leaf_clover: 등장 확률이 증가합니다.\n"
                                     "가챠를 할 때마다 행운에 비례한 토큰을 얻습니다."),
            GachaAbility("the_rich", ":money_mouth:", 0.,
                         chance_revision={":coin:": 20.},
                         special_events=[
                             lambda event: [] if "get_coin" in event.tags else [event],
                             lambda ctx, data, item: self.event_rich(data)
                             if item.icon == ":coin:" else self.event_none()
                         ],
                         description=":coin: 등장 확률이 증가합니다.\n"
                                     "가챠 이벤트로 토큰을 얻지 못하는 대신, :coin:이 나오면 보유 토큰에 비례해 토큰을 얻습니다."),
            GachaAbility("mage", ":mage:", 0.,
                         chance_revision={":magic_wand:": 30.},
                         description="특수 가챠에서 :magic_wand:의 등장 확률이 발생합니다."),
            GachaAbility("ghost", ":ghost:", 0.,
                         chance_revision={":skull:": 10.},
                         special_events=[
                             lambda event: [] if event.parent == ":skull:" else [event],
                             lambda ctx, data, item: self.event_get_coin(data, 444)
                             if item.icon == ":skull:" else self.event_none()
                         ],
                         description=":skull: 등장 확률이 증가하며, :skull:이 나오면 이벤트를 무시하고 444 토큰을 얻습니다."),
            GachaAbility("dice", ":game_die:", 0.,
                         special_events=[
                         ],
                         description=""),
            GachaAbility("magic_mirror", ":mirror:", 0.,
                         special_events=[
                             lambda event: [event, event]
                         ],
                         description="모든 이벤트가 두 번 발생합니다."),
            GachaAbility("santa", ":santa:", 0.,
                         chance_revision={":gift:": 10.},
                         special_events=[
                             lambda ctx, data, icon_lst: self.event_get_coin(data, 120)
                             if ":gift:" in icon_lst else self.event_none()
                         ],
                         description=":gift: 등장 확률이 증가하며, :gift:가 나오면 추가로 120 토큰을 얻습니다."),
            GachaAbility("peace_bringer", ":dove:", 5.,
                         chance_revision={":bomb:": -5., ":firecracker:": -1.5, ":skull:": -1.},
                         description="폭탄류 등장 확률이 감소하며, :skull: 등장 확률이 사라집니다."),
            GachaAbility("mouse_trap", ":mouse_trap:", 2.5,
                         chance_revision={":mouse_trap:": 20.},
                         description="특수 가챠에서 :mouse_trap: 등장 확률이 발생합니다.\n"
                                     ":mouse_trap:이 나오면 치즈에 쥐덫을 설치합니다."),
            GachaAbility("smoker", ":smoking:", 5.,
                         chance_revision={":smoking:": 20., ":skull:": 10.},
                         description="특수 가챠에서 :smoking: 등장 확률이 발생합니다.\n"
                                     ":skull: 등장 확률이 증가합니다."),
        ]

    def get_whole_revision(self, chance_revision: dict):
        whole_revision = 0.0
        for key, value in chance_revision.items():
            whole_revision += value
        return whole_revision

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
                        content=f"{ctx.author.name} 님이 {game_name}을(를) 신청합니다."
                                "\n참가하려면 :white_check_mark: 을 눌러주세요."
                                "\n참가자 : " + ' '.join([x.nick for x in members])
                    )
        return start, members

    # event methods
    async def event_none(self):
        return None

    async def event_get_coin(self, data: dict, n: int = 0):
        data['$'] += n
        if n >= 0:
            return '+' + str(n) + " :coin:"
        else:
            return str(n) + " :coin:"

    async def event_luck(self, data: dict, n: int = 0):
        if data.get('%'):
            data['%'] += n
        else:
            data['%'] = n
        if n >= 0:
            return f'+{n} :four_leaf_clover:'
        else:
            return f'{n} :four_leaf_clover:'

    async def event_change_items(self, ctx, from_icon: str, to_icon: str, max_range: int = 1):
        gacha_channel = get(ctx.guild.text_channels, name="가챠")
        if gacha_channel is None:
            return "가챠 채널을 찾을 수 없습니다."
        msgs = [message async for message in gacha_channel.history(limit=max_range)]
        cnt = 0
        for msg in msgs:
            if msg.content == from_icon:
                await msg.edit(content=to_icon)
                cnt += 1
        return f"{cnt}개의 {from_icon}을 {to_icon}으로 변경했습니다."

    async def event_bankrupt(self, data: dict):
        if int(data.get('$') or 0) > 0:
            data['$'] = 0
            return "보유 토큰을 모두 잃었습니다."
        else:
            return None

    async def event_reset_cooldown(self, ctx):
        ctx.command.reset_cooldown(ctx)
        return "쿨타임 초기화 되었습니다."

    async def event_rich(self, data: dict):
        coin = int(data.get('$') or 0)
        n = round(coin**0.5) + random.randint(0, coin//10)
        result = await self.event_get_coin(data, n)
        return result

    # deprecated methods
    async def prize_token_change(self, ctx):
        db = await self.app.find_id('$', ctx.author.id)
        global_guild = self.app.get_guild(self.app.global_guild_id)
        if global_guild is None:
            return "글로벌 서버를 찾을 수 없습니다."
        db_channel = get(global_guild.text_channels, name="db")
        if db_channel is None:
            return "db 채널을 찾을 수 없습니다."
        messages = [msg async for msg in db_channel.history(limit=100)]
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
        if global_guild is None:
            return "글로벌 서버를 찾을 수 없습니다."
        db_channel = get(global_guild.text_channels, name="db")
        if db_channel is None:
            return "db 채널을 찾을 수 없습니다."
        messages = [msg async for msg in db_channel.history(limit=100)]
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

    async def prize_pill(self, ctx):
        db = await self.app.find_id('$', ctx.author.id)
        coin = int(db.content[20:])
        prize = random.choice([2, 0.5])
        await db.edit(content=db.content[:20]+str(int(coin * prize)))
        return str(coin) + ' x ' + str(prize) + " :coin:"

    @commands.command(
        name="토큰", aliases=["코인", "token", "coin", "$"],
        help="자신의 토큰 수를 확인합니다.\n토큰 DB에 기록되지 않았다면, 새로 ID를 등록합니다.",
        usage="*"
    )
    async def check_token(self, ctx):
        find, data = await self.app.find_data("db", ctx.author.id)
        if find is not None:
            coin = data.get('$')
            await ctx.send(str(coin) + ' :coin:')
        else:
            if ctx.author in ctx.guild.premium_subscribers:
                data = {'$': 1000, '%': 10}
            else:
                data = {'$': 0, '%': 0}
            await self.app.update_data(ctx.author.id, data, find)
            await ctx.send('DB에 ' + ctx.author.mention + ' 님의 ID를 기록했습니다.')

    @commands.cooldown(1, 60., commands.BucketType.channel)
    @commands.command(
        name="토큰순위", aliases=["순위", "rank"],
        help="현재 토큰 보유 순위를 조회합니다. (쿨타임 1분)\n"
             "YYYY_MM 포맷으로 시즌별 토큰 순위를 조회할 수 있습니다.\n"
             "all로 검색 시 역대 토큰 1위 목록을 조회할 수 있습니다.", usage="* (*season*)"
    )
    async def token_rank(self, ctx):
        global_guild = self.app.get_guild(self.app.global_guild_id)
        season = "db"
        text = "현재 토큰 순위 (유저명/토큰/점유율)"
        msg = await ctx.send("DB를 조회 중입니다... :mag:")
        members = {}
        data_dict = await self.app.collect_data(season)
        for member_id in data_dict.keys():
            data = data_dict.get(member_id)
            try:
                member = await ctx.guild.fetch_member(member_id)
            except:
                members[member_id] = data.get('$')
            else:
                members[member] = data.get('$')
        if len(members) == 0:
            embed = discord.Embed(title="<토큰 랭킹>", description=text)
            embed.add_field(name="해당 시즌에 참여한 유저가 없어요", value="ㅜ.ㅜ", inline=True)
            await msg.edit(content=None, embed=embed)
        coin_mass = sum(members.values())
        members = sorted(members.items(), key=operator.itemgetter(1), reverse=True)
        embed = discord.Embed(title="<토큰 랭킹>", description=text)
        winner = members[0]
        names = ""
        coins = ""
        shares = ""
        n = 1
        if len(members) <= 1:
            names = "-"
            coins = "-"
            shares = "-"
        else:
            for md in members[1:]:
                n += 1
                if n == 2:
                    names += f":second_place: {md[0]}\n"
                elif n == 3:
                    names += f":third_place: {md[0]}\n"
                else:
                    names += f"{n}. {md[0]}\n"
                coins += f"{md[1]}\n"
                shares += f"({100 * md[1] / coin_mass:0.2f}%)\n"
        embed.add_field(name=f":first_place: " + str(winner[0]) + " :crown:", value=names, inline=True)
        embed.add_field(name=f"{winner[1]} :coin:", value=coins, inline=True)
        embed.add_field(name=f"({100 * winner[1] / coin_mass:0.2f}%)", value=shares, inline=True)
        await msg.edit(content=None, embed=embed)

    @commands.command(
        name="행운", aliases=["luck"],
        help="자신의 행운 중첩량을 확인합니다.",
        usage="*"
    )
    async def luck(self, ctx):
        find, data = await self.app.find_data("db", ctx.author.id)
        luck = data.get('%')
        if find is None:
            await ctx.send(self.cannot_find_id)
            return
        elif luck is None:
            luck = 0
        await ctx.send(str(luck) + ' :four_leaf_clover:')

    @commands.command(
        name="특성", aliases=["ability"],
        help="자신의 특성을 확인합니다.\n특성은 한 가지만 보유 가능합니다.",
        usage="*"
    )
    async def check_ability(self, ctx):
        find, data = await self.app.find_data("db", ctx.author.id)
        ability_name = data.get('*')
        ability = None
        for a in self.abilities:
            if a.name == ability_name:
                ability = a
        if ability is not None:
            embed = discord.Embed(
                title="<특성>",
                description=f"{ctx.author.display_name} 님의 특성 정보"
            )
            embed.add_field(name=f"> {str(ability)}", value=ability.description, inline=False)
            if ability.chance_revision:
                embed.add_field(
                    name="> 확률 보정",
                    value='\n'.join([f"{key} : {ability.chance_revision.get(key):0.2f}" for key in ability.chance_revision.keys()]),
                    inline=False
                )
            await ctx.send(embed=embed)
        else:
            await ctx.send("특성이 없습니다.")

    @commands.cooldown(1, 30., commands.BucketType.user)
    @commands.command(
        name="도박", aliases=["베팅", "gamble", "bet"],
        help="베팅한 토큰이 -1.0x ~ 1.0x 의 랜덤한 배율로 반환됩니다.", usage="* int((0, *token*])"
    )
    async def gamble(self, ctx, bet):
        find, data = await self.app.find_data("db", ctx.author.id)
        if find is None:
            await ctx.send(self.cannot_find_id)
        else:
            bet = int(bet)
            coin = data.get('$')
            if coin < bet:
                await ctx.send("토큰이 부족합니다.")
            elif bet <= 0:
                await ctx.send("최소 토큰 1개 이상 베팅해야 합니다.")
            else:
                embed = discord.Embed(title="<:video_game:  베팅 결과>", description=ctx.author.display_name + " 님의 결과")
                mag = random.random() - 0.5
                prize = round(bet*mag)
                data['$'] += prize
                await self.app.update_data(ctx.author.id, data, find)
                embed.add_field(name="> 베팅", value=f"{bet} :coin:")
                embed.add_field(name="> 배율", value=f"{mag:0.3f}x")
                embed.add_field(name="> 손익", value=f"{prize} :coin:")
                await ctx.send(embed=embed)

    @commands.cooldown(1, 10., commands.BucketType.user)
    @commands.bot_has_permissions(administrator=True)
    @commands.command(
        name="가챠", aliases=["ㄱㅊ", "gacha"],
        help="가챠를 돌려 무작위 보상을 얻습니다.\n자세한 정보는 '%가챠정보'을 참고해주세요.", usage="* (str(*option*))"
    )
    async def gacha(self, ctx, option=None):
        find, data = await self.app.find_data("db", ctx.author.id)
        if find is None:
            await ctx.send(self.cannot_find_id)
        else:
            if option is None:
                msg = await ctx.send(ctx.author.mention +
                                     " 일반 가챠를 돌리시려면 :white_check_mark:,"
                                     "특성 가챠를 돌리시려면 :black_joker: (100 :coin: 소모), "
                                     "취소하시려면 :negative_squared_cross_mark:를 눌러주세요.")
                reaction_list = ['✅', '🃏', '❎']
                for r in reaction_list:
                    await msg.add_reaction(r)

                def check(reaction, user):
                    return str(reaction) in reaction_list and reaction.message.id == msg.id and user == ctx.author

                try:
                    reaction, user = await self.app.wait_for("reaction_add", check=check, timeout=10.0)
                except asyncio.TimeoutError:
                    await msg.edit(content="시간 초과!", delete_after=2)
                else:
                    await msg.delete()
                    if str(reaction) == '✅':
                        option = 'n'
                    elif str(reaction) == '🃏':
                        option = 'a'
                    else:
                        await ctx.send("취소했습니다.")
                        return None
            if option in ['normal', 'NORMAL', '-n', 'n']:
                option = 'n'
            elif option in ['ability', 'ABILITY', '-a', 'a']:
                coin = data.get('$')
                if coin < 100:
                    await ctx.send("토큰이 부족합니다.")
                    return None
                else:
                    data['$'] -= 100
                    option = 'a'
            else:
                return None
            revision = 0
            ability = None
            ability_name = data.get('*')
            if ability_name:
                for a in self.abilities:
                    if a.name == ability_name:
                        ability = a
            if option == 'a':
                item = None
                rand = random.random() * 100
                for i in self.abilities:
                    if rand <= i.chance:
                        item = i
                        break
                    else:
                        rand -= i.chance
                if item:
                    data['*'] = item.name
                    await self.app.update_data(ctx.author.id, data, find)
                    await ctx.send(f"{str(item)}을(를) 얻었습니다!")
                    return
                else:
                    await self.app.update_data(ctx.author.id, data, find)
                    await ctx.send("아무것도 얻지 못했습니다.")
                    return
            else:
                item_lst = []
                event_lst = []
                slot = 3
                if ability and ability.added_slots:
                    slot += ability.added_slots
                embed = discord.Embed(title="<:video_game: 가챠>",
                                      description=ctx.author.display_name + " 님의 결과")

                if ability and ability.chance_revision:
                    revision = self.get_whole_revision(ability.chance_revision)

                while slot > len(item_lst):
                    rand = random.random() * (100 + revision)
                    for i in self.items:
                        chance = i.chance
                        if ability and ability.chance_revision and i.icon in ability.chance_revision.keys():
                            chance += ability.chance_revision[i.icon]
                        if rand <= chance:
                            item_lst.append(i)
                            break
                        else:
                            rand -= chance

                icon_lst = []
                for i in item_lst:
                    icon_lst.append(i.icon)
                await ctx.send(''.join(icon_lst))

                for event in self.events:
                    if event.check_cond(icon_lst):
                        event_lst.extend(event.event_methods)

                if ability and ability.special_events:
                    event_lst.extend(ability.special_events)

                if len(event_lst) > 0:
                    for event in event_lst:
                        effect = await event(ctx, data)
                        embed.add_field(name="이벤트", value=effect, inline=False)
                    await ctx.send(embed=embed)

                await self.app.update_data(ctx.author.id, data, find)
                return

    @commands.command(
        name="가챠정보", aliases=["확률", "gachainfo"],
        help="'가챠'의 정보를 공개합니다.\n'%가챠정보 특수'를 통해 특수 가챠의 정보를 확인할 수 있습니다."
             "\n'%가챠정보 특성'을 통해 특성 가챠의 정보를 확인할 수 있습니다."
             "\n'%가챠정보 *item*'을 통해 아이템의 이벤트 목록을 확인할 수 있습니다.", usage="* (str()) (str(adjusted))"
    )
    async def gacha_info(self, ctx, args: str | None = None, option: str | None = None):
        ability_name: str | None = None
        if option in ["특성적용", "-a"]:
            option = 'adjusted'
        elif option and (option.startswith("특성적용:") or option.startswith("-a:")):
            ability_name = option[option.index(':') + 1:]
            option = 'adjusted'
        ability = None
        if option == 'adjusted':
            if ability_name is None:
                find, data = await self.app.find_data("db", ctx.author.id)
                ability_name = data.get('*')
            for a in self.abilities:
                if a.name == ability_name:
                    ability = a
        if args is None or args in ["normal", "일반", "일반가챠"]:
            embed = discord.Embed(
                title="<가챠 정보>",
                description="일반 가챠의 아이템 목록입니다.\n"
                            "일반 가챠로 등장한 아이템은 가챠 채널에 추가됩니다.\n"
                            "등장한 아이템에 따라 특정 조건을 만족 시 이벤트가 발생합니다.\n"
                            "이벤트 조건 및 내용은 '%가챠정보 *item*'을 통해 확인할 수 있습니다."
            )
            whole_rand = 100.0
            if option == 'adjusted' and ability and ability.chance_revision:
                revision = self.get_whole_revision(ability.chance_revision)
                whole_rand += revision
            rest = whole_rand
            for item in self.items:
                chance = item.chance
                if option == 'adjusted' and ability:
                    if ability.chance_revision and item.icon in ability.chance_revision.keys():
                        chance += ability.chance_revision[item.icon]
                if chance > 0:
                    embed.add_field(name=item.icon, value="{:0.2f}%".format((chance / whole_rand) * 100), inline=True)
                rest -= chance
            embed.add_field(name="> Rest", value='{:0.2f}%'.format((rest/whole_rand)*100), inline=False)
            await ctx.send(embed=embed)
        elif args in ["ability", "abilities", "특성", "특성가챠"]:
            embed = discord.Embed(
                title="<가챠 정보>",
                description="특성 가챠의 특성 목록입니다.\n"
                            "특성 가챠는 100 토큰을 소모하며, 특성을 얻지 못할 확률이 존재합니다.\n"
                            "특성은 한 가지만 보유할 수 있습니다."
            )
            rest = 100.0
            for item in self.abilities:
                embed.add_field(name=str(item), value="{:0.2f}%".format(item.chance), inline=True)
                rest -= item.chance
            embed.add_field(name="> Rest", value='{:0.2f}%'.format(rest), inline=False)
            await ctx.send(embed=embed)
        else:
            not_found = True
            for item in self.items:
                if args in [item.icon, item.icon[1:-1]]:
                    embed = discord.Embed(
                        title="<가챠 정보>",
                        description=f"{item.icon}의 이벤트 목록입니다."
                    )
                    await ctx.send(embed=embed)
                    not_found = False
                    break
            if not_found:
                for item in self.abilities:
                    if args in [item.icon, item.icon[1:-1], item.name]:
                        embed = discord.Embed(
                            title="<가챠 정보>",
                            description=f"{str(item)}의 특성 정보입니다."
                        )
                        embed.add_field(name=f"> {str(item)}", value=item.description, inline=False)
                        if item.chance_revision:
                            embed.add_field(
                                name="> 확률 보정",
                                value='\n'.join([f"{key} : {item.chance_revision.get(key):0.2f}" for key in
                                                 item.chance_revision.keys()]),
                                inline=False
                            )
                        await ctx.send(embed=embed)
                        not_found = False
                        break
            if not_found:
                await ctx.send("항목을 찾을 수 없습니다.")

    @commands.cooldown(1, 30., commands.BucketType.user)
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
                else:
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

    @commands.cooldown(1, 30., commands.BucketType.user)
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
                        await ctx.send(f'{ctx.author.display_name} {str(board[ctx.author])} : {member.display_name} {str(board[member])}')
                        for m in party:
                            card = board[m]
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
                                await ctx.send(f"{ctx.author.display_name} 승!")
                            elif board[ctx.author] < board[member]:
                                await author_log.edit(
                                    content=author_log.content[:20] + str(int(author_log.content[20:]) - coin)
                                )
                                await member_log.edit(
                                    content=member_log.content[:20] + str(int(member_log.content[20:]) + coin)
                                )
                                await ctx.send(f"{member.display_name} 승!")
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
                    for i in board[member].split():
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
                        board[member] = member_sum
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
                        prize = (len(finish_members) - 1) // len(winners) * coin
                    else:
                        prize = -1 * coin
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
                        hand = board[member].split()
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
                        board[member] = board[member] + ' ' + n
                    for member in members:
                        hand = board[member].split()
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
                        m_hand = board[member].split()
                        w_hand = board[winner].split()
                        if level_table.index(m_hand[2]) > level_table.index(w_hand[2]):
                            winner = member
                    w_hand = board[winner].split()
                    if w_hand[2] in ['13광땡', '18광땡']:
                        for member in call_members:
                            m_hand = board[member].split()
                            if m_hand[2] == '암행어사':
                                winner = member
                    elif w_hand[2] in pairs[:9]:
                        for member in call_members:
                            m_hand = board[member].split()
                            if m_hand[2] == '땡잡이':
                                winner = member
                    elif level_table.index(w_hand[2]) < 30:
                        for member in call_members:
                            m_hand = board[member].split()
                            if m_hand[2] == '멍텅구리구사':
                                regame = True
                    elif level_table.index(w_hand[2]) < 20:
                        for member in call_members:
                            m_hand = board[member].split()
                            if m_hand[2] == '구사':
                                regame = True
                    if regame:
                        for member in die_members:
                            member_log = await self.app.find_id('$', member.id)
                            member_coin = int(member_log.content[20:])
                            await member_log.edit(content=member_log.content[:20] + str(member_coin - pay[member]))
                        embed = discord.Embed(title="<섯다 결과>", description='재경기')
                        for member in members:
                            hand = board[member].split()
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
                            hand = board[member].split()
                            embed.add_field(name=member.name, value=hand[0] + ' , ' + hand[1]
                                            + ' (' + hand[2] + ')', inline=True)
                        await ctx.send(embed=embed)


async def setup(app):
    await app.add_cog(Game(app))
