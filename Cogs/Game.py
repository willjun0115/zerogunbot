import discord
import random
import asyncio
from discord.utils import get
from discord.ext import commands
import openpyxl


class Game(commands.Cog, name="게임(Game)"):

    def __init__(self, app):
        self.app = app

    @commands.command(name="도박", help="지정한 확률로 당첨되는 게임을 실행합니다.", usage="%도박 ~", pass_context=int())
    async def gamble(self, ctx, args):
        args = int(args)
        if args > 50:
            await ctx.send("당첨 확률은 50이하로만 설정할 수 있습니다.")
        elif args <= 0:
            await ctx.send("당첨 확률은 0이하로 설정할 수 없습니다.")
        elif args % 5 != 0:
            await ctx.send("당첨 확률은 5의 배수여야 합니다.")
        else:
            await ctx.send(str(args) + "% 확률의 도박을 돌립니다... - " + str(1) + ":coin:")
            await asyncio.sleep(2)
            win = random.random() * 100
            if win >= args:
                await ctx.send(ctx.author.name + " Lose")
            else:
                await ctx.send(ctx.author.name + " Win! 배율 x" + str(100 / args))

    @commands.command(name="가위바위보", help="봇과 가위바위보를 합니다.\n이기면 토큰 하나를 얻고, 지면 토큰 하나를 잃습니다.", usage="%가위바위보")
    async def rock_scissors_paper(self, ctx):
        log_channel = ctx.guild.get_channel(874970985307201546)
        find_id = False
        async for message in log_channel.history(limit=100):
            if message.content.startswith(str(ctx.author.id)) is True:
                coin = int(message.content[19:message.content.index('$')])
                find_id = True
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
                    if str(reaction) == '✊':
                        bot_react = random.randint(0, 2)
                        if bot_react == 0:
                            await ctx.send(':fist:')
                            await ctx.send('비겼네요.')
                            coin += 0
                        elif bot_react == 1:
                            await ctx.send(':v:')
                            await ctx.send('제가 졌네요.')
                            coin += 1
                        elif bot_react == 2:
                            await ctx.send(':hand_splayed:')
                            await ctx.send('제가 이겼네요!')
                            coin -= 1
                    elif str(reaction) == '✌️':
                        bot_react = random.randint(0, 2)
                        if bot_react == 0:
                            await ctx.send(':fist:')
                            await ctx.send('제가 이겼네요!')
                            coin -= 1
                        elif bot_react == 1:
                            await ctx.send(':v:')
                            await ctx.send('비겼네요.')
                            coin += 0
                        elif bot_react == 2:
                            await ctx.send(':hand_splayed:')
                            await ctx.send('제가 졌네요.')
                            coin += 1
                    elif str(reaction) == '🖐️':
                        bot_react = random.randint(0, 2)
                        if bot_react == 0:
                            await ctx.send(':fist:')
                            await ctx.send('제가 졌네요.')
                            coin += 1
                        elif bot_react == 1:
                            await ctx.send(':v:')
                            await ctx.send('제가 이겼네요!')
                            coin -= 1
                        elif bot_react == 2:
                            await ctx.send(':hand_splayed:')
                            await ctx.send('비겼네요.')
                            coin += 0
                    await message.edit(content=message.content[:19] + str(coin) + message.content[message.content.index('$'):])
                break
        if find_id is False:
            await ctx.send('토큰 로그에 없는 ID 입니다.')

    @commands.command(name="가챠", help="확률적으로 권한이 승급합니다.\n강등될 수도 있습니다.", usage="%가챠")
    async def gacha(self, ctx):
        my_channel = ctx.guild.get_channel(811849095031029762)
        if ctx.channel == my_channel:
            if ctx.author.top_role.position >= get(ctx.guild.roles, name="언랭").position:
                msg = await ctx.send(":warning: 주의: 권한을 잃을 수 있습니다.\n시작하려면 :white_check_mark: 을 눌러주세요.")
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
                        rand = random.random()
                        embed = discord.Embed(title="<:video_game:  가챠 결과>", description=ctx.author.name + " 님의 결과")
                        win = 0.0
                        lose = 0.0
                        toprole = ctx.author.top_role
                        if toprole == get(ctx.guild.roles, name="창씨개명"):
                            win = 0.0
                            lose = 0.0
                        elif toprole == get(ctx.guild.roles, name="음성 통제"):
                            win = 0.025
                            lose = 0.15
                        elif toprole == get(ctx.guild.roles, name="언론 통제"):
                            win = 0.05
                            lose = 0.1
                        elif toprole == get(ctx.guild.roles, name="이모티콘 관리"):
                            win = 0.075
                            lose = 0.075
                        elif toprole == get(ctx.guild.roles, name="DJ"):
                            win = 0.1
                            lose = 0.05
                        elif toprole == get(ctx.guild.roles, name="언랭"):
                            win = 0.2
                            lose = 0.0
                        if rand <= win:
                            await ctx.author.add_roles([ctx.gulid.roles[ctx.guild.roles.index(toprole) + 1]])
                            embed.add_field(name="승급", value="+", inline=True)
                        elif rand >= 1.0 - lose:
                            await ctx.author.remove_roles([toprole])
                            embed.add_field(name="강등", value="-", inline=True)
                        else:
                            embed.add_field(name="유지", value="=", inline=True)
                        await ctx.send(embed=embed)
                    else:
                        await ctx.send(":negative_squared_cross_mark: 가챠를 취소했습니다.")
            else:
                await ctx.send(":no_entry: 권한이 없습니다.")
        else:
            await ctx.send(":no_entry: 이 채널에서는 사용할 수 없는 명령어입니다.")

    @commands.command(
        name="가챠확률", aliases=["가챠정보"],
        help="명령어 '가챠'의 확률 정보를 공개합니다.", usage="%가챠확률, %가챠정보"
    )
    async def gacha_info(self, ctx):
        embed = discord.Embed(title="<가챠 확률 정보>", description="승급 확률 % (강등 확률 %)")
        embed.add_field(name="> 이용제한", value="10%", inline=False)
        embed.add_field(name="> 음성 통제", value="2.5% (15%)", inline=False)
        embed.add_field(name="> 언론 통제", value="5% (10%)", inline=False)
        embed.add_field(name="> 이모티콘 관리", value="7.5% (7.5%)", inline=False)
        embed.add_field(name="> DJ", value="10% (5%)", inline=False)
        embed.add_field(name="> 언랭", value="20%", inline=False)
        await ctx.send(embed=embed)

    @commands.command(
        name="리폿", aliases=["신고", "report"],
        help="부적절한 사용자를 신고합니다.\n확률적으로 강등되며, 이용제한에 걸립니다."
             "\n대상의 권한이 높을수록 신고가 접수될 확률이 높습니다.", usage="%리폿 @, %신고 @, %report @"
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
                                inline=True)
            elif lv == get(ctx.guild.roles, name="창씨개명").position:
                win = 5
            elif lv == get(ctx.guild.roles, name="음성 통제").position:
                win = 4
            elif lv == get(ctx.guild.roles, name="언론 통제").position:
                win = 3
            elif lv == get(ctx.guild.roles, name="이모티콘 관리").position:
                win = 2
            elif lv == get(ctx.guild.roles, name="DJ").position:
                win = 1
            elif lv == get(ctx.guild.roles, name="언랭").position:
                win = 0
            if rand <= win * 0.01:
                await member.remove_roles([member.top_role])
                embed.add_field(name="신고 접수", value="감사합니다. 신고가 접수되었습니다.\n" + member.name + " 님이 강등됩니다.",
                                inline=True)
            else:
                embed.add_field(name="신고 미접수", value="죄송합니다. 신고가 접수되지 않았습니다.", inline=True)
            await ctx.send(embed=embed)

    @commands.command(name="토큰", help="자신의 토큰 수를 확인합니다.\n토큰 로그에 기록되지 않았다면, 새로 ID를 등록합니다.", usage="%토큰")
    async def checktoken(self, ctx):
        log_channel = ctx.guild.get_channel(874970985307201546)
        find_id = False
        async for message in log_channel.history(limit=100):
            if message.content.startswith(str(ctx.author.id)) is True:
                coin = int(message.content[19:message.content.index('$')])
                find_id = True
                await ctx.send(str(coin)+' :coin:')
                break
        if find_id is False:
            await log_channel.send(str(ctx.author.id)+';0$0!')
            await ctx.send('토큰 로그에 ' + ctx.author.name + ' 님의 ID를 기록했습니다.')

    @commands.has_permissions(administrator=True)
    @commands.command(name="토큰설정", help="해당 멤버의 토큰을 설정합니다. (관리자 권한)", usage="%토큰설정 @ ~")
    async def edittoken(self, ctx, member: discord.Member, num):
        log_channel = ctx.guild.get_channel(874970985307201546)
        find_id = False
        async for message in log_channel.history(limit=100):
            if message.content.startswith(str(member.id)) is True:
                find_id = True
                await message.edit(content=message.content[:19] + str(num) + message.content[message.content.index('$'):])
                await ctx.send('토큰 로그를 업데이트했습니다.')
                break
        if find_id is False:
            await ctx.send('토큰 로그에 없는 ID 입니다.')

    @commands.has_permissions(administrator=True)
    @commands.command(name="토큰증감", help="해당 멤버의 토큰을 증가 및 감소시킵니다. (관리자 권한)", usage="%토큰증감 @ ~")
    async def givetoken(self, ctx, member: discord.Member, num):
        log_channel = ctx.guild.get_channel(874970985307201546)
        find_id = False
        async for message in log_channel.history(limit=100):
            if message.content.startswith(str(member.id)) is True:
                find_id = True
                coin = int(message.content[19:message.content.index('$')])
                await message.edit(
                    content=message.content[:19] + str(coin + num) + message.content[message.content.index('$'):])
                await ctx.send('토큰 로그를 업데이트했습니다.')
                break
        if find_id is False:
            await ctx.send('토큰 로그에 없는 ID 입니다.')

    @commands.has_permissions(administrator=True)
    @commands.command(name="토큰편집", help="해당 멤버의 토큰 로그를 편집합니다. (관리자 권한)", usage="%토큰편집 @ ~")
    async def edittokenlog(self, ctx, member: discord.Member, *, args):
        log_channel = ctx.guild.get_channel(874970985307201546)
        find_id = False
        async for message in log_channel.history(limit=100):
            if message.content.startswith(str(member.id)) is True:
                find_id = True
                await message.edit(
                    content=message.content[:19] + str(args))
                await ctx.send('토큰 로그를 업데이트했습니다.')
                break
        if find_id is False:
            await ctx.send('토큰 로그에 없는 ID 입니다.')

    @commands.command(name="인디언포커", help="인디언 포커를 신청합니다."
                                         "\n시작하면 각자에게 개인 메세지로 상대의 패를 알려준 후,"
                                         "\n토큰 베팅을 시작합니다. 자신의 패는 알 수 없으며,"
                                         "\n숫자가 높은 쪽이 이깁니다.", usage="%인디언포커 @")
    async def indianpoker(self, ctx, member: discord.Member):
        log_channel = ctx.guild.get_channel(874970985307201546)
        find_id = 0
        author_log = None
        member_log = None
        author_coin = 0
        member_coin = 0
        async for message in log_channel.history(limit=100):
            if message.content.startswith(str(ctx.author.id)) is True:
                author_log = message
                author_coin = int(message.content[19:message.content.index('$')])
                find_id += 1
            elif message.content.startswith(str(member.id)) is True:
                member_log = message
                member_coin = int(message.content[19:message.content.index('$')])
                find_id += 1
        if find_id < 2:
            await ctx.send('토큰 로그에 없는 ID 입니다.')
        else:
            msg = await ctx.send(
                ctx.author.name + " 님이 " + member.name + " 님에게 인디언 포커를 신청합니다.\n수락하려면 :white_check_mark: 을 눌러주세요.")
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
                    author_card = random.choice(deck)
                    deck.remove(author_card)
                    member_card = random.choice(deck)
                    deck.remove(member_card)
                    author_dm = await ctx.author.create_dm()
                    member_dm = await member.create_dm()
                    await author_dm.send(member_card)
                    await member_dm.send(author_card)
                    coin = 1
                    author_call = False
                    member_call = False
                    msg_ = await ctx.send(ctx.author.name + " 님과 " + member.name + " 님의 인디언 포커 베팅을 시작합니다."
                                                                                  "\n 베팅 토큰: " + str(coin))
                    reaction_list = ['⏏️', '✅', '💀']
                    while True:
                        for r in reaction_list:
                            await msg_.add_reaction(r)

                        def check(reaction, user):
                            return str(reaction) in reaction_list and reaction.message.id == msg_.id \
                                   and user in [ctx.author, member]

                        try:
                            reaction, user = await self.app.wait_for("reaction_add", check=check, timeout=60.0)
                        except asyncio.TimeoutError:
                            await msg_.edit(content="시간 초과!", delete_after=2)
                        else:
                            if str(reaction) == '⏏️':
                                author_call = False
                                member_call = False
                                coin += 1
                            elif str(reaction) == '✅':
                                if user == ctx.author:
                                    author_call = True
                                    await ctx.send(ctx.author.name + " 콜")
                                else:
                                    member_call = True
                                    await ctx.send(member.name + " 콜")
                            else:
                                if user == ctx.author:
                                    await author_log.edit(content=author_log.content[:19] + str(author_coin - 1) +
                                                          author_log.content[author_log.content.index('$'):])
                                    await member_log.edit(content=member_log.content[:19] + str(member_coin + 1) +
                                                          member_log.content[member_log.content.index('$'):])
                                    await ctx.send(ctx.author.name + " 다이")
                                    await msg_.delete()
                                else:
                                    await author_log.edit(content=author_log.content[:19] + str(author_coin + 1) +
                                                          author_log.content[author_log.content.index('$'):])
                                    await member_log.edit(content=member_log.content[:19] + str(member_coin - 1) +
                                                          member_log.content[member_log.content.index('$'):])
                                    await ctx.send(member.name + " 다이")
                                    await msg_.delete()
                                break
                            if author_call is True:
                                if member_call is True:
                                    await ctx.send("콜 성사")
                                    await msg_.delete()
                                    break
                            await msg_.clear_reactions()
                            await msg_.edit(content=ctx.author.name + " 님과 " + member.name + " 님의 인디언 포커 베팅을 시작합니다."
                                                                                            "\n 베팅 토큰: " + str(
                                coin))
                    if author_card[author_card.rfind(':') + 1:] == 'A':
                        author_num = 1
                    else:
                        author_num = int(author_card[author_card.rfind(':') + 1:])
                    if member_card[member_card.rfind(':') + 1:] == 'A':
                        member_num = 1
                    else:
                        member_num = int(member_card[member_card.rfind(':') + 1:])
                    await ctx.send(
                        ctx.author.name + ' ' + str(author_num) + ' : ' + member.name + ' ' + str(member_num))
                    if author_call is True:
                        if member_call is True:
                            if author_num > member_num:
                                await author_log.edit(content=author_log.content[:19] + str(author_coin + coin) +
                                                      author_log.content[author_log.content.index('$'):])
                                await member_log.edit(content=member_log.content[:19] + str(member_coin - coin) +
                                                      member_log.content[member_log.content.index('$'):])
                                await ctx.send(ctx.author.name + ' 승!')
                            elif author_num < member_num:
                                await author_log.edit(content=author_log.content[:19] + str(author_coin - coin) +
                                                      author_log.content[author_log.content.index('$'):])
                                await member_log.edit(content=member_log.content[:19] + str(member_coin + coin) +
                                                      member_log.content[member_log.content.index('$'):])
                                await ctx.send(member.name + ' 승!')
                            else:
                                await ctx.send("무승부")

    @commands.command(name="블랙잭", help="블랙잭을 신청합니다."
                                       "\nA는 1 or 11, J,Q,K는 10으로 계산하며,"
                                       "\n패의 합이 21에 가장 가까운 사람이 승리합니다."
                                       "\n21를 초과하면 0점으로 처리됩니다."
                                       "\n시작하면 참가자마다 두 장의 카드를 받습니다."
                                       "\n카드를 더 받을 지, 그대로 정할 지 모두 선택이 끝나면,"
                                       "\n승자를 정합니다.", usage="%블랙잭")
    async def blackjack(self, ctx):
        log_channel = ctx.guild.get_channel(874970985307201546)
        find_id = False
        async for message in log_channel.history(limit=100):
            if message.content.startswith(str(ctx.author.id)) is True:
                find_id = True
        if find_id is False:
            await ctx.send('토큰 로그에 없는 ID 입니다.')
        else:
            members = []
            start = False
            msg = await ctx.send(
                ctx.author.name + " 님이 블랙잭을 신청합니다.\n참가하려면 :white_check_mark: 을 눌러주세요.")
            reaction_list = ['✅', '❎']
            while True:
                for r in reaction_list:
                    await msg.add_reaction(r)

                def check(reaction, user):
                    return str(reaction) in reaction_list and reaction.message.id == msg.id and user.bot is False

                try:
                    reaction, user = await self.app.wait_for("reaction_add", check=check, timeout=10.0)
                except asyncio.TimeoutError:
                    await msg.edit(content="시간 초과!", delete_after=2)
                else:
                    if str(reaction) == '✅':
                        if user == ctx.author:
                            members.append(ctx.author)
                            start = True
                            break
                        if user not in members:
                            find_id = False
                            async for message in log_channel.history(limit=100):
                                if message.content.startswith(str(user.id)) is True:
                                    find_id = True
                                    members.append(user)
                            if find_id is False:
                                await ctx.send('토큰 로그에 없는 ID 입니다.')
                    else:
                        if user == ctx.author:
                            await ctx.send("호스트가 블랙잭을 취소했습니다.")
                            break
                        if user in members:
                            members.remove(user)
                    names = [x.name for x in members]
                    await msg.clear_reactions()
                    await msg.edit(content=ctx.author.name + " 님이 블랙잭을 신청합니다.\n참가하려면 :white_check_mark: 을 눌러주세요."
                                                             "\n참가자 " + str(names))
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
                    embed = discord.Embed(title="<블랙잭>", description=players[0].name + " 님 카드를 더 받을 지, 멈출 지 선택해주세요.")
                    for member in members:
                        if member in finish_members:
                            embed.add_field(name="> " + member.name, value=board[member], inline=True)
                        else:
                            embed.add_field(name=member.name, value=board[member], inline=True)
                    msg_ = await ctx.send(embed=embed)
                    reaction_list = ['✅', '❎']
                    num = 0
                    while len(finish_members) != len(members):
                        players = []
                        for x in members:
                            if x in finish_members:
                                pass
                            else:
                                players.append(x)
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
                            await msg_.edit(content="시간 초과!", delete_after=2)
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
                            players = []
                            for x in members:
                                if x in finish_members:
                                    pass
                                else:
                                    players.append(x)
                            if num >= len(players):
                                num = 0
                            if len(players) > 0:
                                embed = discord.Embed(title="<블랙잭>",
                                                      description=players[num].name + " 님 카드를 더 받을 지, 멈출 지 선택해주세요.")
                            else:
                                embed = discord.Embed(title="<블랙잭>", description="모든 플레이어가 선택을 종료했습니다.")
                            for member in members:
                                if member in finish_members:
                                    embed.add_field(name="> " + member.name, value=board[member], inline=True)
                                else:
                                    embed.add_field(name=member.name, value=board[member], inline=True)
                            await msg_.clear_reactions()
                            await msg_.edit(embed=embed)
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
                    finish_members.reverse()
                    winner = finish_members[0]
                    for member in finish_members:
                        if board[member] >= board[winner]:
                            winner = member
                    embed = discord.Embed(title="<블랙잭 결과>", description=winner.name + ' 우승!')
                    for member in members:
                        if board[member] == 22:
                            embed.add_field(name=member.name, value='21(blackjack)', inline=True)
                        else:
                            embed.add_field(name=member.name, value=str(board[member]), inline=True)
                    await ctx.send(embed=embed)

    @commands.command(name="시드포커", help="시드 포커를 신청합니다."
                                        "\n덱에는 1~15까지의 숫자가 있으며,"
                                        "\n시작하면 참가자마다 한 장의 카드를 받습니다."
                                        "\n순서대로 카드를 받을 지, 시드를 추가할 지 선택합니다."
                                        "\n카드를 받으면 기존 카드와 받은 카드 중 하나를 버립니다."
                                        "\n시드를 추가하면 시드에 새 카드를 추가합니다."
                                        "\n덱에 있는 카드를 모두 쓰고 나면, 패가 가장 낮은 멤버에게"
                                        "\n순서대로 시드 카드를 줍니다."
                                        "\n가지고 있는 카드의 합이 가장 높은 사람이 승리합니다.", usage="%시드포커")
    async def seedpoker(self, ctx):
        log_channel = ctx.guild.get_channel(874970985307201546)
        find_id = False
        async for message in log_channel.history(limit=100):
            if message.content.startswith(str(ctx.author.id)) is True:
                find_id = True
        if find_id is False:
            await ctx.send('토큰 로그에 없는 ID 입니다.')
        else:
            members = []
            start = False
            msg = await ctx.send(
                ctx.author.name + " 님이 시드 포커를 신청합니다.\n참가하려면 :white_check_mark: 을 눌러주세요.")
            reaction_list = ['✅', '❎']
            while True:
                for r in reaction_list:
                    await msg.add_reaction(r)

                def check(reaction, user):
                    return str(reaction) in reaction_list and reaction.message.id == msg.id and user.bot is False

                try:
                    reaction, user = await self.app.wait_for("reaction_add", check=check, timeout=10.0)
                except asyncio.TimeoutError:
                    await msg.edit(content="시간 초과!", delete_after=2)
                else:
                    if str(reaction) == '✅':
                        if user == ctx.author:
                            members.append(ctx.author)
                            start = True
                            break
                        if user not in members:
                            find_id = False
                            async for message in log_channel.history(limit=100):
                                if message.content.startswith(str(user.id)) is True:
                                    find_id = True
                                    members.append(user)
                            if find_id is False:
                                await ctx.send('토큰 로그에 없는 ID 입니다.')
                    else:
                        if user == ctx.author:
                            await ctx.send("호스트가 시드 포커를 취소했습니다.")
                            break
                        if user in members:
                            members.remove(user)
                    names = [x.name for x in members]
                    await msg.clear_reactions()
                    await msg.edit(content=ctx.author.name + " 님이 시드 포커를 신청합니다.\n참가하려면 :white_check_mark: 을 눌러주세요."
                                                             "\n참가자 " + str(names))
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
                                          description=members[0].name + " 님 카드를 받을 지, 시드를 추가할 지 선택해주세요.")
                    embed.add_field(name='> 덱', value=str(len(deck)), inline=True)
                    embed.add_field(name='> 시드', value=str(seed), inline=True)
                    embed.add_field(name='> 버린 카드', value=str(waste), inline=True)
                    msg_ = await ctx.send(embed=embed)
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
                            await msg_.edit(content="시간 초과!", delete_after=2)
                        else:
                            if str(reaction) == '✅':
                                c = random.choice(deck)
                                deck.remove(c)
                                user_dm = await user.create_dm()
                                await user_dm.send(str(c))
                                ask = await ctx.send(
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
                                    await ask.edit(content="시간 초과!", delete_after=2)
                                else:
                                    if str(reaction) == '✅':
                                        waste.append(board[user])
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
                                                  description=members[num].name + " 님 카드를 받을 지, 시드를 추가할 지 선택해주세요.")
                            embed.add_field(name='> 덱', value=str(len(deck)), inline=True)
                            embed.add_field(name='> 시드', value=str(seed), inline=True)
                            embed.add_field(name='> 버린 카드', value=str(waste), inline=True)
                            await msg_.clear_reactions()
                            await msg_.edit(embed=embed)
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
                    winner = ctx.author
                    for member in members:
                        if board[member] > board[winner]:
                            winner = member
                    embed = discord.Embed(title='<시드 포커 결과>', description=winner.name + " 님 우승!")
                    for member in members:
                        embed.add_field(name=member.name, value=str(board[member]), inline=True)
                    await ctx.send(embed=embed)

    @commands.command(name="섯다", help="섯다를 신청합니다."
                                      "\n시작하면 참가자마다 두 장의 패를 받습니다."
                                      "\n모두 패를 받으면, 순서대로 베팅을 시작합니다."
                                      "⏏️: 하프, ‼️: 따당, ✅: 콜(체크), 💀: 다이"
                                      "\n모두 베팅을 마치고 나면, 패를 공개해 승자를 정합니다."
                                      "\n가지고 있는 패의 족보가 높은 사람이 승리합니다.", usage="%섯다")
    async def seotda(self, ctx):
        log_channel = ctx.guild.get_channel(874970985307201546)
        find_id = False
        async for message in log_channel.history(limit=100):
            if message.content.startswith(str(ctx.author.id)) is True:
                find_id = True
        if find_id is False:
            await ctx.send('토큰 로그에 없는 ID 입니다.')
        else:
            members = []
            start = False
            msg = await ctx.send(
                ctx.author.name + " 님이 섯다를 신청합니다.\n참가하려면 :white_check_mark: 을 눌러주세요.")
            reaction_list = ['✅', '❎']
            while True:
                for r in reaction_list:
                    await msg.add_reaction(r)

                def check(reaction, user):
                    return str(reaction) in reaction_list and reaction.message.id == msg.id and user.bot is False

                try:
                    reaction, user = await self.app.wait_for("reaction_add", check=check, timeout=10.0)
                except asyncio.TimeoutError:
                    await msg.edit(content="시간 초과!", delete_after=2)
                else:
                    if str(reaction) == '✅':
                        if user == ctx.author:
                            members.append(ctx.author)
                            start = True
                            break
                        if user not in members:
                            find_id = False
                            async for message in log_channel.history(limit=100):
                                if message.content.startswith(str(user.id)) is True:
                                    find_id = True
                                    members.append(user)
                            if find_id is False:
                                await ctx.send('토큰 로그에 없는 ID 입니다.')
                    else:
                        if user == ctx.author:
                            await ctx.send("호스트가 섯다를 취소했습니다.")
                            break
                        if user in members:
                            members.remove(user)
                    names = [x.name for x in members]
                    await msg.clear_reactions()
                    await msg.edit(content=ctx.author.name + " 님이 섯다를 신청합니다.\n참가하려면 :white_check_mark: 을 눌러주세요."
                                                             "\n참가자 " + str(names))
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
                    board = {}
                    specials = ['멍텅구리구사', '구사', '땡잡이', '암행어사']
                    middles = ['세륙', '장사', '장삥', '구삥', '독사', '알리']
                    ends = []
                    for i in range(0, 10):
                        ends.append(str(i)+'끗')
                    pairs = []
                    for i in range(1, 10):
                        pairs.append(str(i) + '땡')
                    pairs.append('장땡')
                    leveltable = specials + ends + middles + pairs + ['13광땡', '18광땡', '38광땡']
                    for member in members:
                        a = random.choice(deck)
                        deck.remove(a)
                        board[member] = a
                    for member in members:
                        b = random.choice(deck)
                        deck.remove(b)
                        board[member] = board[member] + ' ' + b
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
                    coin = len(members)
                    call = 0
                    die_members = []
                    call_members = []
                    winner = ctx.author
                    embed = discord.Embed(title="<섯다>",
                                          description=members[0].name + " 님 베팅해주세요.")
                    embed.add_field(name='> 판돈', value=str(coin) + ' :coin:', inline=True)
                    embed.add_field(name='> 콜 비용', value=str(call) + ' :coin:', inline=True)
                    msg_ = await ctx.send(embed=embed)
                    reaction_list = ['⏏️', '‼️', '✅', '💀']
                    num = 0
                    while len(call_members) != len(members):
                        players = []
                        for x in members:
                            if x in die_members:
                                pass
                            else:
                                players.append(x)
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
                            await msg_.edit(content="시간 초과!", delete_after=2)
                        else:
                            if str(reaction) == '⏏️':
                                call = coin//2
                                coin += call
                                call_members = []
                            elif str(reaction) == '‼️':
                                call = call * 2
                                coin += call
                                call_members = []
                            elif str(reaction) == '✅':
                                call_members.append(user)
                                coin += call
                            else:
                                die_members.append(user)
                                await ctx.send(user.name + ' 다이')
                                num -= 1
                            num += 1
                            players = []
                            for x in members:
                                if x in die_members:
                                    pass
                                else:
                                    players.append(x)
                            if num >= len(players):
                                num = 0
                            if len(players) == 1:
                                winner = players[0]
                                break
                            embed = discord.Embed(title="<섯다>",
                                                  description=players[num].name + " 님 베팅해주세요.")
                            embed.add_field(name='> 판돈', value=str(coin) + ' :coin:', inline=True)
                            embed.add_field(name='> 콜 비용', value=str(call) + ' :coin:', inline=True)
                            await msg_.clear_reactions()
                            await msg_.edit(embed=embed)
                    for member in call_members:
                        m_hand = board[member].split()
                        w_hand = board[winner].split()
                        if leveltable.index(m_hand[2]) > leveltable.index(w_hand[2]):
                            winner = member
                    w_hand = board[winner].split()
                    if w_hand[2] in ['13광땡', '18광땡']:
                        for member in call_members:
                            m_hand = board[member].split()
                            if m_hand[2] == '암행어사':
                                winner = member
                    elif w_hand[2] in pairs:
                        for member in call_members:
                            m_hand = board[member].split()
                            if m_hand[2] == '땡잡이':
                                winner = member
                    embed = discord.Embed(title="<섯다 결과>", description=winner.name + ' 우승!')
                    for member in members:
                        hand = board[member].split()
                        embed.add_field(name=member.name, value=hand[0] + ' , ' + hand[1]
                                        + ' (' + hand[2] + ')', inline=True)
                    await ctx.send(embed=embed)


def setup(app):
    app.add_cog(Game(app))