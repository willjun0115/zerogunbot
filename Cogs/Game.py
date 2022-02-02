import discord
import random
import asyncio
from discord.utils import get
from discord.ext import commands
import operator


class Game(commands.Cog, name="게임", description="오락 및 도박과 관련된 카테고리입니다.\n토큰을 수급할 수 있습니다."):

    def __init__(self, app):
        self.app = app
        self.cannot_find_id = 'DB에서 ID를 찾지 못했습니다.\n\'%토큰\' 명령어를 통해 ID를 등록할 수 있습니다.'
        self.roulette_lst = [
            (":gem:", 1.25, self.prize_gem, "상당한 토큰을 얻습니다."),
            (":coin:", 8, self.prize_coin, "토큰을 조금 얻습니다."),
            (":four_leaf_clover:", 4, self.prize_luck, "행운 효과를 받습니다."),
            (":gift:", 3.5, self.prize_gift, "행운 효과를 모두 소모해 토큰을 얻습니다. 행운 중첩 수에 비례해 획득량이 증가합니다."),
            (":smiling_imp:", 6, self.prize_imp, "토큰을 잃습니다."),
            (":skull:", 0.1, self.prize_skull, "토큰을 모두 잃습니다."),
            (":game_die:", 20, self.prize_dice, "역할을 하나 얻습니다. 높은 역할일수록 확률이 낮아집니다."),
            (":bomb:", 4, self.prize_bomb, "역할을 무작위로 하나 잃습니다."),
            (":cloud_lightning:", 1.5, self.prize_lightning, "최고 역할을 잃습니다. 행운을 보유중이라면 행운을 대신 잃습니다."),
            (":chart_with_upwards_trend:", 5, self.prize_rise, "복권 상금이 상승합니다."),
            (":chart_with_downwards_trend:", 5, self.prize_reduce, "복권 상금이 감소합니다."),
            (":cyclone:", 0.1, self.prize_cyclone, "토큰을 보유한 모든 멤버의 토큰 20%가 복권 상금으로 들어갑니다."),
            (":pick:", 1.25, self.prize_theft, "무작위 멤버 한 명의 역할을 무작위로 하나 빼앗습니다."),
            (":magnet:", 1.25, self.prize_magnet, "무작위 멤버 한 명의 토큰을 10% 빼앗습니다."),
            (":pill:", 0.5, self.prize_pill, "보유 토큰이 절반이 되거나, 두 배가 됩니다."),
            (":arrows_counterclockwise:", 0.25, self.prize_token_change, "무작위 멤버 한 명과 토큰이 뒤바뀝니다."),
            (":busts_in_silhouette:", 0.25, self.prize_role_change, "무작위 멤버 한 명과 역할이 뒤바뀝니다."),
            (":scales:", 0.5, self.prize_scales, "무작위 멤버 한 명과 토큰을 합쳐 동등하게 나눠 가집니다."),
            (":japanese_ogre:", 1.5, self.prize_oni, "가장 높은 역할을 가진 멤버의 최고 역할을 없앱니다."),
            (":black_joker:", 0.05, self.prize_joker, "미보유중인 역할을 모두 얻고 보유중인 역할은 모두 잃습니다."),
            (":dove:", 0.05, self.prize_dove, "모든 멤버의 역할을 제거합니다."),
        ]

    async def prize_gem(self, ctx, db):
        coin = int(db.content[20:])
        prize = random.randint(160, 240)
        await db.edit(content=db.content[:20]+str(coin + prize))
        return '+' + str(prize) + " :coin:"

    async def prize_coin(self, ctx, db):
        coin = int(db.content[20:])
        prize = random.randint(10, 30)
        await db.edit(content=db.content[:20]+str(coin + prize))
        return '+' + str(prize) + " :coin:"

    async def prize_luck(self, ctx, db):
        db_channel = get(ctx.guild.text_channels, name="db")
        luck_log = await self.app.find_id(ctx, '%', ctx.author.id)
        if luck_log is None:
            await db_channel.send('%' + str(ctx.author.id) + ';1')
            return "행운 효과를 얻었습니다!"
        else:
            luck = int(luck_log.content[20:])
            await luck_log.edit(content=luck_log.content[:20] + str(luck + 1))
            return f'+1 :four_leaf_clover:'

    async def prize_gift(self, ctx, db):
        luck_log = await self.app.find_id(ctx, '%', ctx.author.id)
        if luck_log is None:
            return "행운 효과가 받고 있지 않습니다."
        else:
            luck = int(luck_log.content[20:])
            gift = random.randint(luck*5, luck*10)
            await db.edit(content=db.content[:20] + str(int(db.content[20:]) + gift))
            await luck_log.delete()
            return str(gift) + " :coin: 을 얻었습니다!"

    async def prize_imp(self, ctx, db):
        coin = int(db.content[20:])
        prize = - random.randint(15, 75)
        await db.edit(content=db.content[:20] + str(coin + prize))
        return str(prize) + " :coin:"

    async def prize_bomb(self, ctx, db):
        if len(ctx.author.roles[2:]) == 0:
            return "보유중인 역할이 없습니다."
        else:
            role = random.choice(ctx.author.roles[2:])
            await ctx.author.remove_roles(role)
            return role.name + "을(를) 잃었습니다."

    async def prize_lightning(self, ctx, db):
        if len(ctx.author.roles[2:]) == 0:
            return "보유중인 역할이 없습니다."
        else:
            luck_log = await self.app.find_id(ctx, '%', ctx.author.id)
            if luck_log is None:
                role = ctx.author.top_role
                await ctx.author.remove_roles(role)
                return role.name + "을(를) 잃었습니다."
            else:
                await luck_log.delete()
                return "행운 효과를 잃었습니다."

    async def prize_skull(self, ctx, db):
        if int(db.content[20:]) > 0:
            await db.edit(content=db.content[:20]+'0')
        return "모든 토큰을 잃었습니다."

    async def prize_joker(self, ctx, db):
        role_set = [get(ctx.guild.roles, name="0군 인증서")]
        for role in ctx.guild.roles:
            if get(ctx.guild.roles, name="0군 인증서").position < role.position < get(ctx.guild.roles, name="관리자").position:
                if role not in ctx.author.roles:
                    role_set.append(role)
        await ctx.author.edit(roles=role_set)
        return ', '.join([r.name for r in role_set]) + "(으)로 역할이 바뀌었습니다!"

    async def prize_token_change(self, ctx, db):
        db_channel = get(ctx.guild.text_channels, name="db")
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
        await member_db.edit(content=db.content[:20]+coin)
        return member.mention + f" 님과 토큰이 뒤바뀌었습니다!\n{coin} <-> {member_coin} :coin:"

    async def prize_role_change(self, ctx, db):
        db_channel = get(ctx.guild.text_channels, name="db")
        messages = await db_channel.history(limit=100).flatten()
        member_db = random.choice(
            [
                m for m in messages
                if m.content.startswith('$') and int(m.content[1:19]) not in [self.app.user.id, ctx.author.id]
            ]
        )
        member = await ctx.guild.fetch_member(int(member_db.content[1:19]))
        await ctx.author.edit(roles=member.roles)
        await member.edit(roles=ctx.author.roles)
        return member.mention + " 님과 역할이 뒤바뀌었습니다!"

    async def prize_scales(self, ctx, db):
        db_channel = get(ctx.guild.text_channels, name="db")
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

    async def prize_theft(self, ctx, db):
        db_channel = get(ctx.guild.text_channels, name="db")
        messages = await db_channel.history(limit=100).flatten()
        member_db = random.choice(
            [
                m for m in messages
                if m.content.startswith('$') and int(m.content[1:19]) not in [self.app.user.id, ctx.author.id]
            ]
        )
        member = await ctx.guild.fetch_member(int(member_db.content[1:19]))
        role = random.choice(member.roles[2:])
        await ctx.author.add_roles(role)
        await member.remove_roles(role)
        return member.mention + " 님의 역할 중 " + role.name + "을(를) 빼앗았습니다!"

    async def prize_magnet(self, ctx, db):
        db_channel = get(ctx.guild.text_channels, name="db")
        messages = await db_channel.history(limit=100).flatten()
        member_db = random.choice(
            [
                m for m in messages
                if m.content.startswith('$') and int(m.content[1:19]) not in [self.app.user.id, ctx.author.id]
            ]
        )
        member = await ctx.guild.fetch_member(int(member_db.content[1:19]))
        coin = round(int(member_db.content[20:]) * 0.1)
        await db.edit(content=db.content[:20] + str(int(db.content[20:])+coin))
        await member_db.edit(content=member_db.content[:20] + str(int(member_db.content[20:])-coin))
        return member.mention + " 님의 토큰을 " + str(coin) + " :coin: 빼앗았습니다!"

    async def prize_rise(self, ctx, db):
        bot_db = await self.app.find_id(ctx, '$', self.app.user.id)
        prize = int(bot_db.content[20:])
        delta = random.random() * 0.25 + 0.1
        await bot_db.edit(content=bot_db.content[:20] + str(prize + round(prize*delta)))
        return '+' + str(round(prize*delta)) + " :coin: (+{:0.1f}%)".format(100*delta)

    async def prize_reduce(self, ctx, db):
        bot_db = await self.app.find_id(ctx, '$', self.app.user.id)
        prize = int(bot_db.content[20:])
        delta = random.random() * 0.1 + 0.05
        await bot_db.edit(content=bot_db.content[:20] + str(prize - round(prize*delta)))
        return '-' + str(round(prize*delta)) + " :coin: (-{:0.1f}%)".format(100*delta)

    async def prize_pill(self, ctx, db):
        coin = int(db.content[20:])
        prize = random.choice([2, 0.5])
        await db.edit(content=db.content[:20]+str(int(coin * prize)))
        return str(coin) + ' x ' + str(prize) + " :coin:"

    async def prize_cyclone(self, ctx, db):
        db_channel = get(ctx.guild.text_channels, name="db")
        messages = await db_channel.history(limit=100).flatten()
        members_db = [
            m for m in messages
            if m.content.startswith('$') and int(m.content[1:19]) not in [self.app.user.id]
        ]
        increment = 0
        for member_db in members_db:
            lose = int(member_db.content[:20]) // 5
            if lose < 0:
                lose = 0
            increment += lose
            await member_db.edit(content=member_db.content[:20]+str(int(member_db.content[:20])-lose))
        bot_db = await self.app.find_id(ctx, '$', self.app.user.id)
        await bot_db.edit(content=bot_db.content[:20] + str(int(bot_db.content[20:]) + increment))
        return f"0군봇이 모든 유저의 토큰의 20%를 빨아들였습니다!\n복권 상금 +{increment} :coin:"

    async def prize_dice(self, ctx, db):
        coin = int(db.content[20:])
        prize = None
        rand = random.random()
        for role in self.app.role_lst:
            if rand <= role[1] / 2 ** len(self.app.role_lst) - 1:
                prize = role[0]
                if get(ctx.guild.roles, name=prize) in ctx.author.roles:
                    prize += f" (+ {str(role[2] // 10)} :coin:)"
                    await db.edit(content=db.content[:20] + str(coin + role[2] // 10))
                else:
                    await ctx.author.add_roles(get(ctx.guild.roles, name=prize))
                break
            else:
                rand -= role[1]
        if prize is None:
            prize = "꽝"
        return prize + " 획득!"

    async def prize_oni(self, ctx, db):
        role = None
        kings = []
        for role_data in self.app.role_lst:
            role = get(ctx.guild.roles, name=role_data[0])
            kings = role.members
            if len(kings) > 0:
                for king in kings:
                    await king.remove_roles(role)
                break
        return f"{', '.join([king.mention for king in kings])} 님이 {role.name}을(를) 잃었습니다!"

    async def prize_dove(self, ctx, db):
        db_channel = get(ctx.guild.text_channels, name="db")
        messages = await db_channel.history(limit=100).flatten()
        members_db = [
            m for m in messages
            if m.content.startswith('$') and int(m.content[1:19]) not in [self.app.user.id]
        ]
        for member_db in members_db:
            member = await ctx.guild.fetch_member(int(member_db.content[1:19]))
            await member.edit(roles=[get(ctx.guild.roles, name="0군 인증서")])
        return "모든 유저의 역할이 사라졌습니다!"

    async def gather_members(self, ctx, game_name="게임"):
        members = []
        author_coin = await self.app.find_id(ctx, '$', ctx.author.id)
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
                            member_coin = await self.app.find_id(ctx, '$', user.id)
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
        name="도박", aliases=["베팅", "gamble", "bet"],
        help="베팅한 토큰이 -1.0x ~ 1.0x 의 랜덤한 배율로 반환됩니다."
             "\n베팅은 보유 토큰의 절반까지 가능합니다.", usage="* int((0, *token/2*])", pass_context=True
    )
    async def gamble(self, ctx, bet):
        log = await self.app.find_id(ctx, '$', ctx.author.id)
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

    @commands.bot_has_permissions(administrator=True)
    @commands.command(
        name="가챠", aliases=["ㄱㅊ", "gacha"],
        help="확률적으로 역할을 얻습니다.\n자세한 정보는 '%가챠정보'을 참고해주세요.", usage="*"
    )
    async def gacha(self, ctx):
        db = await self.app.find_id(ctx, '$', ctx.author.id)
        if db is None:
            await ctx.send(self.cannot_find_id)
        else:
            if ctx.channel == get(ctx.guild.text_channels, name="가챠"):
                msg = await ctx.send(
                    ":warning: 주의: 권한이나 토큰을 잃을 수 있습니다."
                    "\n가챠를 돌리려면 :white_check_mark: 을 누르세요."
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
                    await msg.delete()
                    if str(reaction) == '✅':
                        embed = discord.Embed(title="<:video_game: 가챠>",
                                              description=ctx.author.display_name + " 님의 결과")
                        rand = random.random() * 100
                        result = None
                        effect = None
                        for prize in self.roulette_lst:
                            if rand <= prize[1]:
                                result = prize[3]
                                await ctx.send(prize[0])
                                effect = await prize[2](ctx, db)
                                break
                            else:
                                rand -= prize[1]
                        if result is None:
                            embed.add_field(name="꽝", value="아무일도 일어나지 않았습니다.")
                        else:
                            embed.add_field(name=result, value=effect)
                        await ctx.send(embed=embed)
                    else:
                        await ctx.send(":negative_squared_cross_mark: 룰렛을 취소했습니다.")

    @commands.group(
        name="가챠정보", aliases=["gachainfo"],
        help="가챠의 보상목록 및 정보를 공개합니다.", usage="*", pass_context=True
    )
    async def gacha_info(self, ctx):
        embed = discord.Embed(title="<가챠 정보>", description="가챠 보상 목록")
        rest = 100
        for prize in self.roulette_lst:
            embed.add_field(name="> " + prize[0], value=str(prize[1]) + '%\n' + str(prize[3]), inline=True)
            rest -= prize[1]
        embed.add_field(name="> 꽝", value='{:0.2f}%'.format(rest), inline=True)
        await ctx.send(embed=embed)

    @gacha_info.command(
        name="세부정보", aliases=["detail"],
        help="명령어 '가챠'의 확률 정보를 공개합니다.", usage="*"
    )
    async def gacha_info_detail(self, ctx):
        embed = discord.Embed(title="<가챠 세부 정보>", description="확률(%) (중복 시 얻는 코인)")
        for role in self.app.role_lst:
            embed.add_field(
                name="> " + role[0],
                value=f'{(role[1] / 2 ** len(self.app.role_lst) - 1):0.2f}% ({str(role[2] // 10)} :coin:)',
                inline=False
            )
        await ctx.send(embed=embed)

    @commands.command(
        name="복권", aliases=["ㅂㄱ", "lottery"],
        help="가챠에서 꽝이 나오면 복권 상금이 오릅니다."
             "\n'복권' 명령어를 통해 당첨 시 상금을 얻습니다."
             "\n(당첨 확률은 1.25%)", usage="*"
    )
    async def lottery(self, ctx):
        log = await self.app.find_id(ctx, '$', ctx.author.id)
        if log is None:
            await ctx.send(self.cannot_find_id)
        else:
            bot_log = await self.app.find_id(ctx, '$', self.app.user.id)
            luck_log = await self.app.find_id(ctx, '%', ctx.author.id)
            luck = 0
            if luck_log is not None:
                luck = int(luck_log.content[20:])
            coin = int(log.content[20:])
            prize = int(bot_log.content[20:])
            if ctx.channel == get(ctx.guild.text_channels, name="가챠"):
                rand = random.random() * 100
                if rand <= 1 + (luck ** 0.5) * 0.1:
                    await bot_log.edit(content=bot_log.content[:20] + str(10))
                    await log.edit(content=log.content[:20] + str(coin + prize))
                    await ctx.send(f"{ctx.author.display_name} 님이 복권에 당첨되셨습니다! 축하드립니다!\n상금: {prize} :coin:")
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
        log = await self.app.find_id(ctx, '$', ctx.author.id)
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
        log = await self.app.find_id(ctx, '$', ctx.author.id)
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
        author_log = await self.app.find_id(ctx, '$', ctx.author.id)
        member_log = await self.app.find_id(ctx, '$', member.id)
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
        elif coin > 10:
            await ctx.send("상금 배율은 10 이하여야 합니다.")
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
                    member_log = await self.app.find_id(ctx, '$', member.id)
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
                            member_log = await self.app.find_id(ctx, '$', member.id)
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
                            member_log = await self.app.find_id(ctx, '$', member.id)
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
