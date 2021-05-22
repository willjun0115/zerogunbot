import discord
import random
import asyncio
from discord.utils import get
from discord.ext import commands
import openpyxl


class Game(commands.Cog, name="게임(Game)"):

    def __init__(self, app):
        self.app = app

    @commands.command(name="도박", help="지정한 확률로 당첨되는 게임을 실행합니다.", usage="%도박 (확률%)", pass_context=int())
    async def gamble(self, ctx, args):
        args = int(args)
        if args > 50:
            await ctx.send("당첨 확률은 50이하로만 설정할 수 있습니다.")
        elif args <= 0:
            await ctx.send("당첨 확률은 0이하로 설정할 수 없습니다.")
        elif args % 5 != 0:
            await ctx.send("당첨 확률은 5의 배수여야 합니다.")
        else:
            await ctx.send(str(args) + "% 확률의 도박을 돌립니다...")
            await asyncio.sleep(2)
            win = random.random() * 100
            if win >= args:
                await ctx.send(ctx.author.name + " Lose 배율 x" + str(100/args))
            else:
                await ctx.send(ctx.author.name + " Win! 배율 x" + str(100/args))

    @commands.command(name="가위바위보", help="봇과 가위바위보를 합니다.", usage="%가위바위보")
    async def rock_scissors_paper(self, ctx):
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
                elif bot_react == 1:
                    await ctx.send(':v:')
                    await ctx.send('제가 졌네요.')
                elif bot_react == 2:
                    await ctx.send(':hand_splayed:')
                    await ctx.send('제가 이겼네요!')
            elif str(reaction) == '✌️':
                bot_react = random.randint(0, 2)
                if bot_react == 0:
                    await ctx.send(':fist:')
                    await ctx.send('제가 이겼네요!')
                elif bot_react == 1:
                    await ctx.send(':v:')
                    await ctx.send('비겼네요.')
                elif bot_react == 2:
                    await ctx.send(':hand_splayed:')
                    await ctx.send('제가 졌네요.')
            elif str(reaction) == '🖐️':
                bot_react = random.randint(0, 2)
                if bot_react == 0:
                    await ctx.send(':fist:')
                    await ctx.send('제가 졌네요.')
                elif bot_react == 1:
                    await ctx.send(':v:')
                    await ctx.send('제가 이겼네요!')
                elif bot_react == 2:
                    await ctx.send(':hand_splayed:')
                    await ctx.send('비겼네요.')

    @commands.command(name="가챠", help="확률적으로 권한을 보상으로 얻습니다.\n권한을 잃을 수도 있습니다."
                                      "\n10~100개의 코인을 얻습니다.", usage="%가챠")
    async def gacha(self, ctx):
        my_channel = ctx.guild.get_channel(811849095031029762)
        if ctx.channel == my_channel:
            msg = await ctx.send(":warning: 주의: 권한을 잃을 수 있습니다.\n:skull_crossbones: 을 누르면 확률이 올라가는 대신,"
                                 "\n10% 확률로 '도박중독'에 걸립니다.\n일반 가챠는 :video_game: 을 눌러주세요.")
            reaction_list = ['🎮', '☠️', '❎']
            for r in reaction_list:
                await msg.add_reaction(r)

            def check(reaction, user):
                return str(reaction) in reaction_list and reaction.message.id == msg.id and user == ctx.author

            try:
                reaction, user = await self.app.wait_for("reaction_add", check=check, timeout=10.0)
            except asyncio.TimeoutError:
                await msg.edit(content="시간 초과!", delete_after=2)
            else:
                if str(reaction) == '🎮':
                    embed = discord.Embed(title="<:video_game:  가챠 결과>", description=ctx.author.name + " 님의 결과")
                    win_garen = random.random() * 100
                    win_deaf = random.random() * 100
                    win_grab = random.random() * 100
                    win_chatctrl = random.random() * 100
                    win_namectrl = random.random() * 100
                    win_emoji = random.random() * 100
                    win_dj = random.random() * 100
                    win_michael = random.random() * 100
                    win_fdr = random.random() * 100
                    if win_namectrl <= 0.5:
                        await ctx.message.author.add_roles(get(ctx.guild.roles, name="창씨개명"))
                        embed.add_field(name='창씨개명', value='+', inline=True)
                    elif win_namectrl >= 88:
                        await ctx.message.author.remove_roles(get(ctx.guild.roles, name="창씨개명"))
                        embed.add_field(name='창씨개명', value='-', inline=True)
                    else:
                        embed.add_field(name='창씨개명', value='=', inline=True)
                    if win_grab <= 1:
                        await ctx.message.author.add_roles(get(ctx.guild.roles, name="강제이동"))
                        embed.add_field(name='강제이동', value='+', inline=True)
                    elif win_grab >= 90:
                        await ctx.message.author.remove_roles(get(ctx.guild.roles, name="강제이동"))
                        embed.add_field(name='강제이동', value='-', inline=True)
                    else:
                        embed.add_field(name='강제이동', value='=', inline=True)
                    if win_garen <= 1.5:
                        await ctx.message.author.add_roles(get(ctx.guild.roles, name="가렌Q"))
                        embed.add_field(name='가렌Q', value='+', inline=True)
                    elif win_garen >= 90:
                        await ctx.message.author.remove_roles(get(ctx.guild.roles, name="가렌Q"))
                        embed.add_field(name='가렌Q', value='-', inline=True)
                    else:
                        embed.add_field(name='가렌Q', value='=', inline=True)
                    if win_deaf <= 1.5:
                        await ctx.message.author.add_roles(get(ctx.guild.roles, name="귀마개"))
                        embed.add_field(name='귀마개', value='+', inline=True)
                    elif win_deaf >= 90:
                        await ctx.message.author.remove_roles(get(ctx.guild.roles, name="귀마개"))
                        embed.add_field(name='귀마개', value='-', inline=True)
                    else:
                        embed.add_field(name='귀마개', value='=', inline=True)
                    if win_michael <= 1.5:
                        await ctx.message.author.add_roles(get(ctx.guild.roles, name="미카엘"))
                        embed.add_field(name='미카엘', value='+', inline=True)
                    elif win_michael >= 92:
                        await ctx.message.author.remove_roles(get(ctx.guild.roles, name="미카엘"))
                        embed.add_field(name='미카엘', value='-', inline=True)
                    else:
                        embed.add_field(name='미카엘', value='=', inline=True)
                    if win_chatctrl <= 3:
                        await ctx.message.author.add_roles(get(ctx.guild.roles, name="언론통제"))
                        embed.add_field(name='언론통제', value='+', inline=True)
                    elif win_chatctrl >= 92:
                        await ctx.message.author.remove_roles(get(ctx.guild.roles, name="언론통제"))
                        embed.add_field(name='언론통제', value='-', inline=True)
                    else:
                        embed.add_field(name='언론통제', value='=', inline=True)
                    if win_fdr <= 5:
                        await ctx.message.author.add_roles(get(ctx.guild.roles, name="유미학살자"))
                        embed.add_field(name='유미학살자', value='+', inline=True)
                    elif win_fdr >= 92:
                        await ctx.message.author.remove_roles(get(ctx.guild.roles, name="유미학살자"))
                        embed.add_field(name='유미학살자', value='-', inline=True)
                    else:
                        embed.add_field(name='유미학살자', value='=', inline=True)
                    if win_emoji <= 94:
                        await ctx.message.author.add_roles(get(ctx.guild.roles, name="이모티콘 관리"))
                        embed.add_field(name='이모티콘 관리', value='+', inline=True)
                    elif win_emoji >= 90:
                        await ctx.message.author.remove_roles(get(ctx.guild.roles, name="이모티콘 관리"))
                        embed.add_field(name='이모티콘 관리', value='-', inline=True)
                    else:
                        embed.add_field(name='이모티콘 관리', value='=', inline=True)
                    if win_dj <= 15:
                        await ctx.message.author.add_roles(get(ctx.guild.roles, name="DJ"))
                        embed.add_field(name='DJ', value='+', inline=True)
                    elif win_dj >= 96:
                        await ctx.message.author.remove_roles(get(ctx.guild.roles, name="DJ"))
                        embed.add_field(name='DJ', value='-', inline=True)
                    else:
                        embed.add_field(name='DJ', value='=', inline=True)
                    await ctx.send(embed=embed)
                    id = str(ctx.message.author.id)
                    coin = random.randint(10, 50)
                    if get(ctx.guild.roles, name='가챠 확장팩') in ctx.message.author.roles:
                        coin = coin * 2
                    openxl = openpyxl.load_workbook("coin.xlsx")
                    wb = openxl.active
                    for i in range(1, 100):
                        if wb["B" + str(i)].value == id:
                            wb["C" + str(i)].value = wb["C" + str(i)].value + int(coin)
                            await ctx.channel.send(f"코인 획득! + :coin: {coin}")
                            break
                    openxl.save("coin.xlsx")
                elif str(reaction) == '☠️':
                    embed = discord.Embed(title="<:skull_crossbones:  가챠 결과>", description=ctx.author.name + " 님의 결과")
                    lose_gacha = random.random() * 100
                    if lose_gacha <= 10:
                        await ctx.send(":no_entry: " + ctx.author.name + "님이 가챠에 실패해 가챠가 금지되었습니다.")
                        await ctx.message.author.add_roles(get(ctx.guild.roles, name="도박중독"))
                    else:
                        win_namectrl = random.random() * 100
                        win_michael = random.random() * 100
                        win_garen = random.random() * 100
                        win_deaf = random.random() * 100
                        win_grab = random.random() * 100
                        win_chatctrl = random.random() * 100
                        win_fdr = random.random() * 100
                        win_emoji = random.random() * 100
                        win_dj = random.random() * 100
                        if get(ctx.guild.roles, name='가챠 확장팩') in ctx.message.author.roles:
                            win_immune_holic = random.random() * 100
                            win_steal = random.random() * 100
                            win_manager = random.random() * 100
                            if win_manager <= 0.1:
                                await ctx.message.author.add_roles(get(ctx.guild.roles, name="매니저"))
                                embed.add_field(name='매니저', value='+', inline=True)
                            elif win_manager >= 95:
                                await ctx.message.author.remove_roles(get(ctx.guild.roles, name="스틸"))
                                embed.add_field(name='매니저', value='-', inline=True)
                            else:
                                embed.add_field(name='매니저', value='=', inline=True)
                            if win_steal <= 0.25:
                                await ctx.message.author.add_roles(get(ctx.guild.roles, name="스틸"))
                                embed.add_field(name='스틸', value='+', inline=True)
                            elif win_steal >= 95:
                                await ctx.message.author.remove_roles(get(ctx.guild.roles, name="스틸"))
                                embed.add_field(name='스틸', value='-', inline=True)
                            else:
                                embed.add_field(name='스틸', value='=', inline=True)
                            if win_immune_holic <= 0.5:
                                await ctx.message.author.add_roles(get(ctx.guild.roles, name="도박중독 치료"))
                                embed.add_field(name='도박중독 치료', value='+', inline=True)
                            elif win_immune_holic >= 90:
                                await ctx.message.author.remove_roles(get(ctx.guild.roles, name="도박중독 치료"))
                                embed.add_field(name='도박중독 치료', value='-', inline=True)
                            else:
                                embed.add_field(name='도박중독 치료', value='=', inline=True)
                        if win_namectrl <= 1:
                            await ctx.message.author.add_roles(get(ctx.guild.roles, name="창씨개명"))
                            embed.add_field(name='창씨개명', value='+', inline=True)
                        elif win_namectrl >= 82:
                            await ctx.message.author.remove_roles(get(ctx.guild.roles, name="창씨개명"))
                            embed.add_field(name='창씨개명', value='-', inline=True)
                        else:
                            embed.add_field(name='창씨개명', value='=', inline=True)
                        if win_grab <= 2:
                            await ctx.message.author.add_roles(get(ctx.guild.roles, name="강제이동"))
                            embed.add_field(name='강제이동', value='+', inline=True)
                        elif win_grab >= 84:
                            await ctx.message.author.remove_roles(get(ctx.guild.roles, name="강제이동"))
                            embed.add_field(name='강제이동', value='-', inline=True)
                        else:
                            embed.add_field(name='강제이동', value='=', inline=True)
                        if win_garen <= 3:
                            await ctx.message.author.add_roles(get(ctx.guild.roles, name="가렌Q"))
                            embed.add_field(name='가렌Q', value='+', inline=True)
                        elif win_garen >= 86:
                            await ctx.message.author.remove_roles(get(ctx.guild.roles, name="가렌Q"))
                            embed.add_field(name='가렌Q', value='-', inline=True)
                        else:
                            embed.add_field(name='가렌Q', value='=', inline=True)
                        if win_deaf <= 3:
                            await ctx.message.author.add_roles(get(ctx.guild.roles, name="귀마개"))
                            embed.add_field(name='귀마개', value='+', inline=True)
                        elif win_deaf >= 86:
                            await ctx.message.author.remove_roles(get(ctx.guild.roles, name="귀마개"))
                            embed.add_field(name='귀마개', value='-', inline=True)
                        else:
                            embed.add_field(name='귀마개', value='=', inline=True)
                        if win_michael <= 1.5:
                            await ctx.message.author.add_roles(get(ctx.guild.roles, name="미카엘"))
                            embed.add_field(name='미카엘', value='+', inline=True)
                        elif win_michael >= 88:
                            await ctx.message.author.remove_roles(get(ctx.guild.roles, name="미카엘"))
                            embed.add_field(name='미카엘', value='-', inline=True)
                        else:
                            embed.add_field(name='미카엘', value='=', inline=True)
                        if win_chatctrl <= 5:
                            await ctx.message.author.add_roles(get(ctx.guild.roles, name="언론통제"))
                            embed.add_field(name='언론통제', value='+', inline=True)
                        elif win_chatctrl >= 88:
                            await ctx.message.author.remove_roles(get(ctx.guild.roles, name="언론통제"))
                            embed.add_field(name='언론통제', value='-', inline=True)
                        else:
                            embed.add_field(name='언론통제', value='=', inline=True)
                        if win_fdr <= 8:
                            await ctx.message.author.add_roles(get(ctx.guild.roles, name="유미학살자"))
                            embed.add_field(name='유미학살자', value='+', inline=True)
                        elif win_fdr >= 88:
                            await ctx.message.author.remove_roles(get(ctx.guild.roles, name="유미학살자"))
                            embed.add_field(name='유미학살자', value='-', inline=True)
                        else:
                            embed.add_field(name='유미학살자', value='=', inline=True)
                        if win_emoji <= 15:
                            await ctx.message.author.add_roles(get(ctx.guild.roles, name="이모티콘 관리"))
                            embed.add_field(name='이모티콘 관리', value='+', inline=True)
                        elif win_emoji >= 88:
                            await ctx.message.author.remove_roles(get(ctx.guild.roles, name="이모티콘 관리"))
                            embed.add_field(name='이모티콘 관리', value='-', inline=True)
                        else:
                            embed.add_field(name='이모티콘 관리', value='=', inline=True)
                        if win_dj <= 25:
                            await ctx.message.author.add_roles(get(ctx.guild.roles, name="DJ"))
                            embed.add_field(name='DJ', value='+', inline=True)
                        elif win_dj >= 90:
                            await ctx.message.author.remove_roles(get(ctx.guild.roles, name="DJ"))
                            embed.add_field(name='DJ', value='-', inline=True)
                        else:
                            embed.add_field(name='DJ', value='=', inline=True)
                        await ctx.send(embed=embed)
                        id = str(ctx.message.author.id)
                        coin = random.randint(10, 100)
                        if get(ctx.guild.roles, name='가챠 확장팩') in ctx.message.author.roles:
                            coin = coin * 2
                        openxl = openpyxl.load_workbook("coin.xlsx")
                        wb = openxl.active
                        for i in range(1, 100):
                            if wb["B" + str(i)].value == id:
                                wb["C" + str(i)].value = wb["C" + str(i)].value + int(coin)
                                await ctx.channel.send(f"코인 획득! + :coin: {coin}")
                                break
                        openxl.save("coin.xlsx")
                else:
                    await ctx.send(":negative_squared_cross_mark: 가챠를 취소했습니다.")
        else:
            await ctx.send(":no_entry: 이 채널에서는 사용할 수 없는 명령어입니다.")

    @commands.command(name="가챠확률", help="명령어 '가챠'의 확률 정보를 공개합니다.", usage="%가챠확률")
    async def gacha_p(self, ctx):
        embed = discord.Embed(title="<가챠 확률 정보>", description="개발자가 업데이트를 안했을 수도 있습니다 ㅎㅎ"
                                                              "\n(:video_game: 확률 / :skull_crossbones: 확률)")
        if get(ctx.guild.roles, name='가챠 확장팩') in ctx.message.author.roles:
            embed.add_field(name="> 매니저", value="0.1% (5%)", inline=False)
            embed.add_field(name="> 스틸", value="0.25% (5%)", inline=False)
            embed.add_field(name="> 도박중독 치료", value="0.5% (10%)", inline=False)
        embed.add_field(name="> 창씨개명", value="0.5% / 1% (12% / 18%)", inline=False)
        embed.add_field(name="> 강제이동", value="1% / 2% (10% / 16%)", inline=False)
        embed.add_field(name="> 가렌Q", value="1.5% / 3% (10% / 14%)", inline=False)
        embed.add_field(name="> 귀마개", value="1.5% / 3% (10% / 14%)", inline=False)
        embed.add_field(name="> 미카엘", value="1.5% / 3% (8% / 12%)", inline=False)
        embed.add_field(name="> 언론통제", value="3% / 5% (8% / 12%)", inline=False)
        embed.add_field(name="> 유미학살자", value="5% / 8% (8% / 12%)", inline=False)
        embed.add_field(name="> 이모티콘 관리", value="10% / 15% (6% / 12%)", inline=False)
        embed.add_field(name="> DJ", value="15% / 25% (4% / 10%)", inline=False)
        await ctx.send(embed=embed)

    @commands.command(name="탈출", help="코인을 내고 '가챠'로 금지된 가챠 권한을 회복합니다.", usage="%탈출")
    async def escape_jail(self, ctx):
        my_channel = ctx.guild.get_channel(811937429689991169)
        if ctx.channel == my_channel:
            member = ctx.message.author
            if get(ctx.guild.roles, name='도박중독 치료') in member.roles:
                await ctx.send(ctx.author.name + " 님의 가챠 권한이 회복되었습니다.")
                await ctx.message.author.remove_roles(get(ctx.guild.roles, name="도박중독"))
            else:
                id = str(ctx.author.id)
                openxl = openpyxl.load_workbook("coin.xlsx")
                wb = openxl.active
                for i in range(1, 100):
                    if wb["B" + str(i)].value == id:
                        price = wb["C" + str(i)].value // 10
                        if wb["C" + str(i)].value >= price:
                            coin = wb["C" + str(i)].value
                            wb["C" + str(i)].value = coin - price
                            await ctx.message.author.remove_roles(get(ctx.guild.roles, name="도박중독"))
                            await ctx.channel.send(ctx.author.name + " 님의 가챠 권한이 회복되었습니다. - :coin:" + str(price))
                            break
                        else:
                            await ctx.channel.send(f"코인이 부족합니다. (보석금: :coin: {price})")
                openxl.save("coin.xlsx")

    @commands.command(name='도전', help="(역할 레벨 총합이 15 이상이어야만 사용 가능)\n상위 권한에 도전합니다."
                                      "\n실패 시 가장 높은 권한을 하나 잃습니다."
                                      "\n100~200개의 코인을 얻습니다.", usage="%도전")
    async def challenge(self, ctx):
        my_channel = ctx.guild.get_channel(811849095031029762)
        if ctx.channel == my_channel:
            member = ctx.message.author
            role_p = 0
            try:
                for role in member.roles:
                    if 2 < role.position <= 15:
                        role_p += role.position - 2
            except:
                pass
            if role_p >= 15:
                msg = await ctx.send(":warning: 주의: 가장 높은 권한 하나를 잃을 수 있습니다."
                                     "\n상위 권한에 도전합니다.\n계속하시려면 :white_check_mark: 을 눌러주세요.")
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
                        win_chan = random.random() * 100
                        if win_chan <= 0.5:
                            await member.add_roles(get(ctx.guild.roles, name='매니저'))
                            await ctx.send("'매니저' 권한을 얻었습니다!")
                        if 0.5 < win_chan <= 2:
                            await member.add_roles(get(ctx.guild.roles, name='스틸'))
                            await ctx.send("'스틸' 권한을 얻었습니다!")
                        elif 2 < win_chan <= 5:
                            await member.add_roles(get(ctx.guild.roles, name='가챠 확장팩'))
                            await ctx.send("'가챠 확장팩' 권한을 얻었습니다!")
                        elif 5 < win_chan <= 10:
                            await member.add_roles(get(ctx.guild.roles, name='도박중독 치료'))
                            await ctx.send("'도박중독 치료' 권한을 얻었습니다!")
                        elif win_chan > 50:
                            await ctx.send(":skull_crossbones: 최고 권한을 잃었습니다.")
                            lst = member.roles
                            await member.remove_roles(lst[-1])
                        else:
                            await ctx.send("도전에 실패했습니다.")
                        id = str(ctx.message.author.id)
                        coin = random.randint(200, 300)
                        if get(ctx.guild.roles, name='가챠 확장팩') in member.roles:
                            coin = coin * 2
                        openxl = openpyxl.load_workbook("coin.xlsx")
                        wb = openxl.active
                        for i in range(1, 100):
                            if wb["B" + str(i)].value == id:
                                wb["C" + str(i)].value = wb["C" + str(i)].value + int(coin)
                                await ctx.channel.send(f"코인 획득! + :coin: {coin}")
                                break
                        openxl.save("coin.xlsx")
                    else:
                        await ctx.send(":negative_squared_cross_mark: 가챠를 취소했습니다.")
            else:
                await ctx.send(" :no_entry: 이 명령을 실행하실 권한이 없습니다.")

    @commands.command(name="도전확률", help="명령어 '도전'의 확률 정보를 공개합니다.", usage="%도전확률")
    async def challenge_p(self, ctx):
        embed = discord.Embed(title="<도전 확률 정보>",
                              description="개발자가 업데이트를 안했을 수도 있습니다 ㅎㅎ")
        embed.add_field(name="> :skull_crossbones: 권한 상실", value="50%", inline=False)
        embed.add_field(name="> 매니저", value="0.5%", inline=False)
        embed.add_field(name="> 스틸", value="1.5%", inline=False)
        embed.add_field(name="> 가챠 확장팩", value="3%", inline=False)
        embed.add_field(name="> 도박중독 치료", value="5%", inline=False)
        await ctx.send(embed=embed)


def setup(app):
    app.add_cog(Game(app))