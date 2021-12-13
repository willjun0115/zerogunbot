import discord
import random
import asyncio
from discord.utils import get
from discord.ext import commands
import operator


class Game(commands.Cog, name="게임", description="오락 및 도박과 관련된 카테고리입니다."):

    def __init__(self, app):
        self.app = app
        self.cannot_find_id = '로그에서 ID를 찾지 못했습니다.\n\'%토큰\' 명령어를 통해 ID를 등록할 수 있습니다.'

    async def find_log(self, ctx, selector, id):
        log_channel = ctx.guild.get_channel(self.app.log_ch)
        find = None
        async for message in log_channel.history(limit=100):
            if message.content.startswith(selector + str(id)) is True:
                find = message
                break
        return find

    async def gather_members(self, ctx, game_name="게임"):
        members = []
        author_log = await self.find_log(ctx, '$', ctx.author.id)
        start = False
        if author_log is None:
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
                            member_log = await self.find_log(ctx, '$', user.id)
                            if member_log is None:
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
                                                  "\n참가자 : " + ' '.join([x.name for x in members])
                    )
        return start, members

    async def calc_prize(self, ctx, coin, members, winners):
        for member in members:
            if member in winners:
                prize = int((len(members)-1) // len(winners)) * int(coin)
            else:
                prize = -1 * int(coin)
            member_log = await self.find_log(ctx, '$', member.id)
            member_coin = int(member_log.content[20:])
            await member_log.edit(content=member_log.content[:20] + str(member_coin + prize))

    @commands.command(
        name="도박", aliases=["베팅", "gamble", "bet"],
        help="베팅한 토큰이 -1.0x ~ 1.0x 의 랜덤한 배율로 반환됩니다."
             "\n베팅은 보유 토큰의 절반까지 가능합니다.", usage="* int((0, *token/2*])", pass_context=True
    )
    async def gamble(self, ctx, bet):
        my_channel = ctx.guild.get_channel(self.app.gacha_ch)
        log = await self.find_log(ctx, '$', ctx.author.id)
        if log is None:
            await ctx.send(self.cannot_find_id)
        else:
            bet = int(bet)
            coin = int(log.content[20:])
            if ctx.channel == my_channel:
                if coin < bet:
                    await ctx.send("코인이 부족합니다.")
                elif bet > coin//2:
                    await ctx.send("베팅은 보유 토큰의 절반까지만 할 수 있습니다.")
                elif bet <= 0:
                    await ctx.send("최소 토큰 1개 이상 베팅해야 합니다.")
                else:
                    embed = discord.Embed(title="<:video_game:  베팅 결과>", description=ctx.author.name + " 님의 결과")
                    multi = (random.random() - 0.5) * 1
                    prize = round(bet*multi)
                    await log.edit(content=log.content[:20] + str(coin + prize))
                    embed.add_field(name="> 베팅", value=str(bet) + " :coin:")
                    embed.add_field(name="> 배율", value=str("{:0.3f}".format(multi))+"x")
                    embed.add_field(name="> 배당", value=str(prize) + " :coin:")
                    await ctx.send(embed=embed)
            else:
                await ctx.send(":no_entry: 이 채널에서는 사용할 수 없는 명령어입니다.")

    @commands.command(
        name="가챠", aliases=["ㄱㅊ", "gacha"],
        help="확률적으로 역할을 얻습니다.\n자세한 정보는 '%가챠정보'을 참고해주세요.", usage="*"
    )
    async def gacha(self, ctx):
        my_channel = ctx.guild.get_channel(self.app.gacha_ch)
        log = await self.find_log(ctx, '$', ctx.author.id)
        if log is None:
            await ctx.send(self.cannot_find_id)
        else:
            coin = int(log.content[20:])
            if ctx.channel == my_channel:
                luck = 0
                luck_log = await self.find_log(ctx, '%', ctx.author.id)
                if luck_log is not None:
                    luck = int(luck_log.content[20:])
                msg = await ctx.send(
                    ":warning: 주의: 권한을 잃을 수 있습니다."
                    "\n가챠를 시작하려면 :white_check_mark: 을 누르세요."
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
                        description = ctx.author.name + " 님의 결과"
                        if luck_log is not None:
                            description += "\n(:four_leaf_clover: 행운 버프 적용 중)"
                        embed = discord.Embed(
                            title="<:video_game:  가챠 결과>",
                            description=description
                        )
                        prize = None
                        result = '획득!'
                        rand = random.random() * 100
                        for role in self.app.role_lst:
                            if rand <= role[1] * (1 + luck * 0.1):
                                prize = role[0]
                                if get(ctx.guild.roles, name=prize) in ctx.author.roles:
                                    prize += f" (+ {str(role[2] // 100)} :coin:)"
                                    await log.edit(content=log.content[:20] + str(coin + role[2] // 100))
                                else:
                                    await ctx.author.add_roles(get(ctx.guild.roles, name=prize))
                                break
                            else:
                                rand -= role[1] * (1 + luck * 0.1)
                        if prize is None:
                            roles = ctx.author.roles[2:]
                            lose_p = (len(roles) * 2)
                            if luck_log is not None:
                                await luck_log.edit(content=luck_log.content[:20] + str(luck + 1))
                                lose_p = lose_p / 2
                            if rand <= lose_p:
                                role = random.choice(roles)
                                await ctx.author.remove_roles(role)
                                prize = role.name
                                result = '손실 :x:'
                            else:
                                prize = "꽝"
                                bot_log = await self.find_log(ctx, '$', self.app.id)
                                await bot_log.edit(content=bot_log.content[:20] + str(int(bot_log.content[20:]) + 1))
                            await log.edit(content=log.content[:20] + str(coin))
                        else:
                            if luck_log is not None:
                                await luck_log.delete()
                                await ctx.send(ctx.author.name + " 님의 행운이 초기화 되었습니다.")
                        embed.add_field(name=str(prize), value=result, inline=False)
                        await ctx.send(embed=embed)
                    else:
                        await ctx.send(":negative_squared_cross_mark: 가챠를 취소했습니다.")
            else:
                await ctx.send(":no_entry: 이 채널에서는 사용할 수 없는 명령어입니다.")

    @commands.command(
        name="가챠정보", aliases=["가챠확률", "gachainfo"],
        help="명령어 '가챠'의 확률 정보를 공개합니다.", usage="*"
    )
    async def gacha_info(self, ctx):
        embed = discord.Embed(title="<가챠 확률 정보>", description="확률(%) (중복 시 얻는 코인)")
        for role in self.app.role_lst:
            embed.add_field(name="> " + role[0], value=str(role[1]) + f'% ({str(role[2] // 100)} :coin:)', inline=False)
        embed.add_field(name="> 보유 역할 중 1개 손실", value='(보유 역할 수) * 2%', inline=False)
        embed.add_field(name="> 꽝", value='(Rest)%', inline=False)
        await ctx.send(embed=embed)

    @commands.command(
        name="복권", aliases=["ㅂㄱ", "lottery"],
        help="가챠에서 꽝이 나오면 복권 상금이 오릅니다.\n'복권' 명령어를 통해 당첨 시 상금을 얻습니다.", usage="*"
    )
    async def lottery(self, ctx):
        my_channel = ctx.guild.get_channel(self.app.gacha_ch)
        log = await self.find_log(ctx, '$', ctx.author.id)
        if log is None:
            await ctx.send(self.cannot_find_id)
        else:
            bot_log = await self.find_log(ctx, '$', self.app.id)
            coin = int(log.content[20:])
            prize = int(bot_log.content[20:])
            if ctx.channel == my_channel:
                rand = random.random() * 100
                if rand <= 1:
                    await bot_log.edit(content=bot_log.content[:20] + str(0))
                    await log.edit(content=log.content[:20] + str(coin + prize))
                    await ctx.send(f"{ctx.author.name} 님이 복권에 당첨되셨습니다! 축하드립니다!\n상금: {prize} :coin:")
                else:
                    await ctx.send("꽝 입니다. 다음에 도전하세요")
            else:
                await ctx.send(":no_entry: 이 채널에서는 사용할 수 없는 명령어입니다.")

    @commands.command(
        name="가위바위보", aliases=["가바보", "rsp"],
        help="봇과 가위바위보를 합니다.\n이기면 토큰 하나를 얻고, 지면 토큰 하나를 잃습니다.",
        usage="*"
    )
    async def rock_scissors_paper(self, ctx):
        log = await self.find_log(ctx, '$', ctx.author.id)
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
                    await ctx.send(ctx.author.name + ' 님 승리!')
                    coin += 1
                else:
                    await ctx.send(ctx.author.name + ' 님 패배')
                    coin -= 1
                await log.edit(content=log.content[:20] + str(coin))
        else:
            await ctx.send(self.cannot_find_id)

    @commands.command(
        name="홀짝", aliases=["짝홀", "odd-even"],
        help="봇이 정한 랜덤 정수가 홀수인지 짝수인지 맞추는 게임입니다."
             "\n이기면 숫자만큼 토큰을 얻고, 지면 숫자만큼 잃습니다."
             "\n만약 0을 맞추면 20코인을 얻습니다.",
        usage="*"
    )
    async def odd_or_even(self, ctx):
        log = await self.find_log(ctx, '$', ctx.author.id)
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
                    await ctx.send(ctx.author.name + " 님 승!")
                    if num == 0:
                        await log.edit(content=log.content[:20] + str(coin + 20))
                    else:
                        await log.edit(content=log.content[:20] + str(coin + num))
                else:
                    await ctx.send(ctx.author.name + " 님 패!")
                    await log.edit(content=log.content[:20] + str(coin - num))
        else:
            await ctx.send(self.cannot_find_id)

    @commands.command(
        name="리폿", aliases=["신고", "report"],
        help="부적절한 사용자를 신고합니다.\n낮은 확률로 접수되면 최고 권한을 잃습니다."
             "\n대상의 권한이 높을수록 신고가 접수될 확률이 높습니다."
             "\n신고가 접수되면 보상으로 10 코인을 드립니다.", usage="* @*member*"
    )
    async def report(self, ctx, member: discord.Member):
        my_channel = ctx.guild.get_channel(872938926019575879)
        if ctx.channel == my_channel:
            await ctx.message.delete()
            rand = random.random()
            win = 0
            embed = discord.Embed(title="<리폿 결과>", description="대상: " + member.name + " 님")
            lv = member.top_role.position
            if lv == get(ctx.guild.roles, name="관리자").position:
                win = 0
                embed.add_field(name="관리자는 신고할 수 없습니다.", value=ctx.author.name + " 님, 맞을래요?",
                                inline=False)
            elif get(ctx.guild.roles, name="0군 인증서").position < lv <= get(ctx.guild.roles, name="창씨개명").position:
                win = lv
            elif lv == get(ctx.guild.roles, name="0군 인증서").position:
                win = 0
            if rand <= win * 0.01:
                await member.remove_roles(member.top_role)
                embed.add_field(name="신고 접수", value="감사합니다. 신고가 접수되었습니다.\n" + member.name + " 님이 강등됩니다.",
                                inline=True)
                log = await self.find_log(ctx, '$', ctx.author.id)
                if log is not None:
                    coin = int(log.content[20:])
                    await log.edit(content=log.content[:20] + str(coin+10))
                    await ctx.send("접수 보상 + 10 :coin:")
            else:
                embed.add_field(name="신고 미접수", value="죄송합니다. 신고가 접수되지 않았습니다.", inline=True)
            await ctx.send(embed=embed)

    @commands.command(
        name="인디언포커", aliases=["IndianPoker", "IP", "ip"],
        help="인디언 포커를 신청합니다."
             "\n시작하면 각자에게 개인 메세지로 상대의 패를 알려준 후, 토큰 베팅을 시작합니다."
             "\n레이즈하면 판 돈을 두 배로 올리며, 플레이어 양쪽이 콜하면 결과를 공개합니다."
             "\n자신의 패는 알 수 없으며 숫자가 높은 쪽이 이깁니다.", usage="* @*member*"
    )
    async def indian_poker(self, ctx, member: discord.Member):
        party = (member, ctx.author)
        limit = 0
        author_log = await self.find_log(ctx, '$', ctx.author.id)
        member_log = await self.find_log(ctx, '$', member.id)
        if author_log is None:
            await ctx.send(f'로그에서 {ctx.author.name} 님의 ID를 찾지 못했습니다.')
        else:
            limit += int(author_log.content[20:])
        if member_log is None:
            await ctx.send(f'로그에서 {member.name} 님의 ID를 찾지 못했습니다.')
        else:
            limit += int(member_log.content[20:])
        if author_log is not None:
            if member_log is not None:
                msg = await ctx.send(
                    ctx.author.name + " 님이 " + member.name + " 님에게 인디언 포커를 신청합니다."
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
                            embed.add_field(name="> :white_check_mark:", value=str([x.name for x in called_party]),
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
                                await ctx.send(party[num].name + " 님이 시간을 초과하여 자동으로 다이 처리됩니다.")
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
                                await ctx.send(party[num].name + " 다이")
                                await msg_.delete()
                                break
                            else:
                                if str(reaction) == '⏏️':
                                    if coin*2 > limit:
                                        await ctx.send("판돈은 두 플레이어의 토큰의 합을 초과할 수 없습니다.")
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
                                    await ctx.send(user.name + " 다이")
                                    await msg_.delete()
                                    break
                            if num >= 2:
                                num = 0
                            if len(called_party) == 2:
                                await ctx.send("콜 성사")
                                await msg_.delete()
                                break
                            await msg_.clear_reactions()
                        await ctx.send(f'{ctx.author.name} {str(board[ctx.author])} : {member.name} {str(board[member])}')
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
                                await ctx.send(ctx.author.name + " 승!")
                            elif board[ctx.author] < board[member]:
                                await author_log.edit(
                                    content=author_log.content[:20] + str(int(author_log.content[20:]) - coin)
                                )
                                await member_log.edit(
                                    content=member_log.content[:20] + str(int(member_log.content[20:]) + coin)
                                )
                                await ctx.send(member.name + " 승!")
                    else:
                        await ctx.send("신청을 거절했습니다.")

    @commands.command(
        name="블랙잭", aliases=["Blackjack", "BJ", "bj"],
        help="블랙잭을 신청합니다."
             "\nA는 1 or 11, J,Q,K는 10으로 계산하며,"
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
                await self.calc_prize(ctx, coin, finish_members, winners)
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

    @commands.command(
        name="시드포커", aliases=["SeedPoker", "SP", "sp"],
        help="시드 포커를 신청합니다."
             "\n덱에는 1~15까지의 숫자가 있으며,"
             "\n시작하면 참가자마다 한 장의 카드를 받습니다."
             "\n순서대로 카드를 받을 지, 시드를 추가할 지 선택합니다."
             "\n카드를 받으면 기존 카드와 받은 카드 중 하나를 버립니다."
             "\n시드를 추가하면 시드에 새 카드를 추가합니다."
             "\n덱에 있는 카드를 모두 쓰고 나면, 패가 가장 낮은 멤버에게"
             "\n순서대로 시드 카드를 줍니다."
             "\n가지고 있는 카드의 합이 가장 높은 사람이 승리합니다.", usage="*"
    )
    async def seed_poker(self, ctx):
        start, members = await self.gather_members(ctx, "시드 포커")
        if start is True:
            if len(members) < 3:
                await ctx.send("시드 포커는 3인부터 가능합니다.")
            elif len(members) > 7:
                await ctx.send("시드 포커는 최대 7인까지 가능합니다.")
            else:
                deck = []
                for i in range(1, 16):
                    deck.append(i)
                seed = []
                waste = []
                board = {}
                for member in members:
                    a = random.choice(deck)
                    deck.remove(a)
                    board[member] = a
                    member_dm = await member.create_dm()
                    await member_dm.send(str(a))
                embed = discord.Embed(title="<시드 포커>",
                                      description=f"{str(len(members))} :coin:")
                embed.add_field(name='> 덱', value=str(len(deck)), inline=True)
                embed.add_field(name='> 시드', value=str(seed), inline=True)
                embed.add_field(name='> 버린 카드', value=str(waste), inline=True)
                msg_ = await ctx.send(content=members[0].mention + " 님 카드를 받을 지, 시드에 추가할 지 선택해주세요.", embed=embed)
                reaction_list = ['✅', '❎']
                num = 0
                while len(deck) > 0:
                    for r in reaction_list:
                        await msg_.add_reaction(r)

                    def check(reaction, user):
                        return str(reaction) in reaction_list and reaction.message.id == msg_.id \
                               and user == members[num]

                    try:
                        reaction, user = await self.app.wait_for("reaction_add", check=check, timeout=60.0)
                    except asyncio.TimeoutError:
                        await ctx.send(members[num].name + " 님이 시간을 초과하여 자동으로 시드를 추가합니다.")
                    else:
                        if str(reaction) == '✅':
                            c = random.choice(deck)
                            deck.remove(c)
                            user_dm = await user.create_dm()
                            await user_dm.send(str(c))
                            ask = await user_dm.send(
                                user.name + " 님, 카드를 바꾸시겠습니까?")
                            reaction_list = ['✅', '❎']
                            for r in reaction_list:
                                await ask.add_reaction(r)

                            def check(reaction, user_):
                                return str(
                                    reaction) in reaction_list and reaction.message.id == ask.id and user_ == user

                            try:
                                reaction, user = await self.app.wait_for("reaction_add", check=check, timeout=60.0)
                            except asyncio.TimeoutError:
                                waste.append(c)
                                await ask.delete()
                                await ctx.send(members[num].name + " 님이 시간을 초과하여 자동으로 카드를 버립니다.")
                            else:
                                if str(reaction) == '✅':
                                    waste.append(board.get(user))
                                    board[user] = c
                                else:
                                    waste.append(c)
                                await ask.delete()
                        else:
                            c = random.choice(deck)
                            deck.remove(c)
                            seed.append(c)
                            seed.sort(reverse=True)
                            if len(seed) > 3:
                                waste.append(seed[3])
                                seed = seed[0:3]
                    num += 1
                    if num >= len(members):
                        num = 0
                    embed = discord.Embed(title="<시드 포커>",
                                          description=f"{str(len(members))} :coin:")
                    embed.add_field(name='> 덱', value=str(len(deck)), inline=True)
                    embed.add_field(name='> 시드', value=str(seed), inline=True)
                    embed.add_field(name='> 버린 카드', value=str(waste), inline=True)
                    await msg_.clear_reactions()
                    await msg_.edit(content=members[num].mention + " 님 카드를 더 받을 지, 멈출 지 선택해주세요.", embed=embed)
                v = list(board.values())
                v.sort()
                while len(seed) < 3:
                    seed.append(0)
                for member in members:
                    if board[member] == v[0]:
                        board[member] += seed[0]
                    elif board[member] == v[1]:
                        board[member] += seed[1]
                    elif board[member] == v[2]:
                        board[member] += seed[2]
                winners = [ctx.author]
                for member in members:
                    if board[member] > board[winners[0]]:
                        winners = [member]
                    elif board[member] == board[winners[0]]:
                        winners.append(member)
                await self.calc_prize(ctx, 1, members, winners)
                embed = discord.Embed(
                    title='<시드 포커 결과>',
                    description=', '.join([x.name for x in winners]) +
                                f" 님 우승! (상금: {len(members) // len(winners)} :coin:)"
                )
                for member in members:
                    embed.add_field(name=member.name, value=str(board[member]), inline=True)
                await ctx.send(embed=embed)

    @commands.command(
        name="섯다", aliases=["ㅅㄷ"],
        help="섯다를 신청합니다."
             "\n시작하면 참가자마다 두 장의 패를 받습니다."
             "\n모두 패를 받으면, 순서대로 베팅을 시작합니다."
             "\n⏏️: 하프, ‼️: 따당, ✅: 콜(체크), 💀: 다이"
             "\n모두 베팅을 마치고 나면, 패를 공개해 승자를 정합니다."
             "\n가지고 있는 패의 족보가 높은 사람이 승리합니다.", usage="*"
    )
    async def seotda(self, ctx):
        start, members = await self.gather_members(ctx, "섯다")
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
                level_table = ['멍텅구리구사', '구사', '땡잡이', '암행어사'] + ends + middles + pairs + ['13광땡', '18광땡', '38광땡']
                coin = len(members)
                pay = {}
                for member in members:
                    pay[member] = 1
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
                    elif w_hand[2] in pairs:
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
                            member_log = await self.find_log(ctx, '$', member.id)
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
                            member_log = await self.find_log(ctx, '$', member.id)
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