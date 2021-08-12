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
                coin = int(message.content[19:])
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
                    await message.edit(content=message.content[:19]+str(coin))
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
                        lv = ctx.author.top_role.position
                        if lv == get(ctx.guild.roles, name="이용제한").position:
                            if rand <= 0.1:
                                await ctx.author.remove_roles(get(ctx.guild.roles, name="이용제한"))
                                embed.add_field(name="해제", value="+", inline=True)
                            else:
                                embed.add_field(name="유지", value="=", inline=True)
                        elif lv >= get(ctx.guild.roles, name="창씨개명").position:
                            embed.add_field(name="-", value="이미 최고 등급입니다.", inline=True)
                        elif lv == get(ctx.guild.roles, name="음성 통제").position:
                            if rand <= 0.025:
                                await ctx.author.add_roles(get(ctx.guild.roles, name="창씨개명"))
                                embed.add_field(name="승급", value="+", inline=True)
                            elif rand >= 0.85:
                                await ctx.author.remove_roles(get(ctx.guild.roles, name="음성 통제"))
                                embed.add_field(name="강등", value="-", inline=True)
                            else:
                                embed.add_field(name="유지", value="=", inline=True)
                        elif lv == get(ctx.guild.roles, name="언론 통제").position:
                            if rand <= 0.05:
                                await ctx.author.add_roles(get(ctx.guild.roles, name="음성 통제"))
                                embed.add_field(name="승급", value="+", inline=True)
                            elif rand >= 0.9:
                                await ctx.author.remove_roles(get(ctx.guild.roles, name="언론 통제"))
                                embed.add_field(name="강등", value="-", inline=True)
                            else:
                                embed.add_field(name="유지", value="=", inline=True)
                        elif lv == get(ctx.guild.roles, name="이모티콘 관리").position:
                            if rand <= 0.075:
                                await ctx.author.add_roles(get(ctx.guild.roles, name="언론 통제"))
                                embed.add_field(name="승급", value="+", inline=True)
                            elif rand >= 0.925:
                                await ctx.author.remove_roles(get(ctx.guild.roles, name="이모티콘 관리"))
                                embed.add_field(name="강등", value="-", inline=True)
                            else:
                                embed.add_field(name="유지", value="=", inline=True)
                        elif lv == get(ctx.guild.roles, name="DJ").position:
                            if rand <= 0.1:
                                await ctx.author.add_roles(get(ctx.guild.roles, name="이모티콘 관리"))
                                embed.add_field(name="승급", value="+", inline=True)
                            elif rand >= 0.95:
                                await ctx.author.remove_roles(get(ctx.guild.roles, name="DJ"))
                                embed.add_field(name="강등", value="-", inline=True)
                            else:
                                embed.add_field(name="유지", value="=", inline=True)
                        elif lv == get(ctx.guild.roles, name="언랭").position:
                            if rand <= 0.2:
                                await ctx.author.add_roles(get(ctx.guild.roles, name="DJ"))
                                embed.add_field(name="승급", value="+", inline=True)
                            else:
                                embed.add_field(name="유지", value="=", inline=True)
                        await ctx.send(embed=embed)
                    else:
                        await ctx.send(":negative_squared_cross_mark: 가챠를 취소했습니다.")
            else:
                await ctx.send(":no_entry: 권한이 없습니다.")
        else:
            await ctx.send(":no_entry: 이 채널에서는 사용할 수 없는 명령어입니다.")

    @commands.command(name="가챠확률", help="명령어 '가챠'의 확률 정보를 공개합니다.", usage="%가챠확률")
    async def gacha_p(self, ctx):
        embed = discord.Embed(title="<가챠 확률 정보>", description="승급 확률 % (강등 확률 %)")
        embed.add_field(name="> 이용제한", value="10%", inline=False)
        embed.add_field(name="> 음성 통제", value="2.5% (15%)", inline=False)
        embed.add_field(name="> 언론 통제", value="5% (10%)", inline=False)
        embed.add_field(name="> 이모티콘 관리", value="7.5% (7.5%)", inline=False)
        embed.add_field(name="> DJ", value="10% (5%)", inline=False)
        embed.add_field(name="> 언랭", value="20%", inline=False)
        await ctx.send(embed=embed)

    @commands.command(name="리폿", help="부적절한 사용자를 신고합니다.\n확률적으로 강등되며, 이용제한에 걸립니다."
                                      "\n대상의 권한이 높을수록 신고가 접수될 확률이 높습니다.", usage="%리폿 @")
    async def report(self, ctx, member: discord.Member):
        my_channel = ctx.guild.get_channel(872938926019575879)
        if ctx.channel == my_channel:
            await ctx.message.delete()
            rand = random.random()
            embed = discord.Embed(title="<리폿 결과>", description="대상: " + member.name + " 님")
            lv = member.top_role.position
            if lv == get(ctx.guild.roles, name="관리자").position:
                embed.add_field(name="신고 미접수", value="관리자는 신고할 수 없습니다.", inline=True)
            elif lv == get(ctx.guild.roles, name="이용제한").position:
                embed.add_field(name="신고 미접수", value="이미 이용제한 중인 사용자입니다.", inline=True)
            elif lv == get(ctx.guild.roles, name="창씨개명").position:
                if rand <= 0.05:
                    await member.remove_roles(member.top_role)
                    await member.add_roles(get(ctx.guild.roles, name="이용제한"))
                    embed.add_field(name="신고 접수", value="감사합니다. 신고가 접수되었습니다.\n" + member.name + "님이 이용제한에 걸립니다.",
                                    inline=True)
                else:
                    embed.add_field(name="신고 미접수", value="죄송합니다. 신고가 접수되지 않았습니다.", inline=True)
            elif lv == get(ctx.guild.roles, name="음성 통제").position:
                if rand <= 0.04:
                    await member.remove_roles(member.top_role)
                    await member.add_roles(get(ctx.guild.roles, name="이용제한"))
                    embed.add_field(name="신고 접수", value="감사합니다. 신고가 접수되었습니다.\n" + member.name + "님이 이용제한에 걸립니다.",
                                    inline=True)
                else:
                    embed.add_field(name="신고 미접수", value="죄송합니다. 신고가 접수되지 않았습니다.", inline=True)
            elif lv == get(ctx.guild.roles, name="언론 통제").position:
                if rand <= 0.03:
                    await member.remove_roles(member.top_role)
                    await member.add_roles(get(ctx.guild.roles, name="이용제한"))
                    embed.add_field(name="신고 접수", value="감사합니다. 신고가 접수되었습니다.\n" + member.name + "님이 이용제한에 걸립니다.",
                                    inline=True)
                else:
                    embed.add_field(name="신고 미접수", value="죄송합니다. 신고가 접수되지 않았습니다.", inline=True)
            elif lv == get(ctx.guild.roles, name="이모티콘 관리").position:
                if rand <= 0.02:
                    await member.remove_roles(member.top_role)
                    await member.add_roles(get(ctx.guild.roles, name="이용제한"))
                    embed.add_field(name="신고 접수", value="감사합니다. 신고가 접수되었습니다.\n" + member.name + "님이 이용제한에 걸립니다.",
                                    inline=True)
                else:
                    embed.add_field(name="신고 미접수", value="죄송합니다. 신고가 접수되지 않았습니다.", inline=True)
            elif lv == get(ctx.guild.roles, name="DJ").position:
                if rand <= 0.01:
                    await member.remove_roles(member.top_role)
                    await member.add_roles(get(ctx.guild.roles, name="이용제한"))
                    embed.add_field(name="신고 접수", value="감사합니다. 신고가 접수되었습니다.\n" + member.name + "님이 이용제한에 걸립니다.",
                                    inline=True)
                else:
                    embed.add_field(name="신고 미접수", value="죄송합니다. 신고가 접수되지 않았습니다.", inline=True)
            elif lv == get(ctx.guild.roles, name="언랭").position:
                if rand <= 0:
                    await member.add_roles(get(ctx.guild.roles, name="이용제한"))
                    embed.add_field(name="신고 접수", value="감사합니다. 신고가 접수되었습니다.\n" + member.name + "님이 이용제한에 걸립니다.",
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
                coin = int(message.content[19:])
                find_id = True
                await ctx.send(str(coin)+' :coin:')
                break
        if find_id is False:
            await log_channel.send(str(ctx.author.id)+';0')
            await ctx.send('토큰 로그에 ' + ctx.author.name + ' 님의 ID를 기록했습니다.')

    @commands.has_permissions(administrator=True)
    @commands.command(name="토큰설정", help="해당 멤버의 토큰 로그를 편집합니다. (관리자 권한)", usage="%토큰로그 @ ~")
    async def edittoken(self, ctx, member: discord.Member, num):
        log_channel = ctx.guild.get_channel(874970985307201546)
        find_id = False
        async for message in log_channel.history(limit=100):
            if message.content.startswith(str(member.id)) is True:
                find_id = True
                await message.edit(content=message.content[:19] + str(num))
                await ctx.send('토큰 로그를 업데이트했습니다.')
                break
        if find_id is False:
            await ctx.send('토큰 로그에 없는 ID 입니다.')

    @commands.command(name="인디언포커", help="인디언 포커를 신청합니다."
                                         "\n시작하면 각자에게 개인 메세지로 상대의 패를 알려준 후,"
                                         "\n토큰 베팅을 시작합니다. 자신의 패는 알 수 없으며,"
                                         "\n숫자가 높은 쪽이 이깁니다.\n또한, 10을 들고 '폴드'하면 페널티로 토큰을 추가로 잃습니다.", usage="%인디언포커 @")
    async def indianpoker(self, ctx, member: discord.Member):
        log_channel = ctx.guild.get_channel(874970985307201546)
        find_id = False
        author_log = None
        member_log = None
        author_coin = 0
        member_coin = 0
        async for message in log_channel.history(limit=100):
            if message.content.startswith(str(ctx.author.id)) is True:
                author_log = message
                author_coin = int(message.content[19:])
                async for message_ in log_channel.history(limit=100):
                    if message.content.startswith(str(member.id)) is True:
                        member_log = message_
                        member_coin = int(message_.content[19:])
                        find_id = True
                        break
        if find_id is False:
            await ctx.send('토큰 로그에 없는 ID 입니다.')
        msg = await ctx.send(
            ctx.author.name + " 님이 " + member.name + " 님에게 인디언 포커를 신청합니다.\n수락하려면 :white_check_mark: 을 눌러주세요.")
        reaction_list = ['✅', '❎']
        for r in reaction_list:
            await msg.add_reaction(r)

        def check(reaction, user):
            return str(reaction) in reaction_list and reaction.message.id == msg.id and user == member

        try:
            reaction, user = await self.app.wait_for("reaction_add", check=check, timeout=5.0)
        except asyncio.TimeoutError:
            await msg.edit(content="시간 초과!", delete_after=2)
        else:
            if str(reaction) == '✅':
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
                coin = 2
                author_call = False
                member_call = False
                msg = await ctx.send(ctx.author.name + " 님과 " + member.name + " 님의 인디언 포커 베팅을 시작합니다."
                                                                              "\n 베팅 토큰: " + str(coin))
                reaction_list = ['🔱', '✅', '💀']
                while True:
                    for r in reaction_list:
                        await msg.add_reaction(r)

                    def check(reaction, user):
                        return str(reaction) in reaction_list and reaction.message.id == msg.id \
                               and user in [ctx.author, member]

                    try:
                        reaction, user = await self.app.wait_for("reaction_add", check=check, timeout=60.0)
                    except asyncio.TimeoutError:
                        await msg.edit(content="시간 초과!", delete_after=2)
                    else:
                        if str(reaction) == '🔱':
                            if user == ctx.author:
                                author_call = False
                            else:
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
                                await author_log.edit(content=author_log.content[:19] + str(author_coin - 1))
                                await member_log.edit(content=member_log.content[:19] + str(member_coin + 1))
                                await ctx.send(ctx.author.name + " 다이")
                                await msg.delete()
                            else:
                                await author_log.edit(content=author_log.content[:19] + str(author_coin + 1))
                                await member_log.edit(content=member_log.content[:19] + str(member_coin - 1))
                                await ctx.send(member.name + " 다이")
                                await msg.delete()
                            break
                        if author_call is True:
                            if member_call is True:
                                await ctx.send("콜 성사")
                                await msg.delete()
                                break
                        await msg.clear_reactions()
                        await msg.edit(content=ctx.author.name + " 님과 " + member.name + " 님의 인디언 포커 베팅을 시작합니다."
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
                await ctx.send(ctx.author.name + ' ' + str(author_num) + ' : ' + member.name + ' ' + str(member_num))
                if author_call is True:
                    if member_call is True:
                        if author_num > member_num:
                            await author_log.edit(content=author_log.content[:19] + str(author_coin + coin))
                            await member_log.edit(content=member_log.content[:19] + str(member_coin - coin))
                            await ctx.send(ctx.author.name + ' 승!')
                        elif author_num < member_num:
                            await author_log.edit(content=author_log.content[:19] + str(author_coin - coin))
                            await member_log.edit(content=member_log.content[:19] + str(member_coin + coin))
                            await ctx.send(member.name + ' 승!')
                        else:
                            await ctx.send("무승부")


def setup(app):
    app.add_cog(Game(app))