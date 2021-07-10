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
                    await ctx.send(str(args) + "% 확률의 도박을 돌립니다... - :coin: " + str(100))
                    await asyncio.sleep(2)
                    win = random.random() * 100
                    if win >= args:
                        await ctx.send(ctx.author.name + " Lose")
                    else:
                        await ctx.send(ctx.author.name + " Win! 배율 x" + str(100 / args))

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

    @commands.command(name="가챠", help="확률적으로 권한을 보상으로 얻습니다.\n권한을 잃을 수도 있습니다.", usage="%가챠")
    async def gacha(self, ctx):
        my_channel = ctx.guild.get_channel(811849095031029762)
        if ctx.channel == my_channel:
            if get(ctx.guild.roles, name="0군 정품 인증 마크") in ctx.message.author.roles:
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
                        embed = discord.Embed(title="<:video_game:  가챠 결과>", description=ctx.author.name + " 님의 결과")
                        namectrl = random.random() * 100
                        voicectrl = random.random() * 100
                        chatctrl = random.random() * 100
                        emoji = random.random() * 100
                        dj = random.random() * 100
                        if namectrl <= 1:
                            await ctx.message.author.add_roles(get(ctx.guild.roles, name="창씨개명"))
                            embed.add_field(name='창씨개명', value='+', inline=True)
                        elif namectrl >= 85:
                            await ctx.message.author.remove_roles(get(ctx.guild.roles, name="창씨개명"))
                            embed.add_field(name='창씨개명', value='-', inline=True)
                        else:
                            embed.add_field(name='창씨개명', value='=', inline=True)
                        if voicectrl <= 2:
                            await ctx.message.author.add_roles(get(ctx.guild.roles, name="음성 통제"))
                            embed.add_field(name='음성 통제', value='+', inline=True)
                        elif voicectrl >= 90:
                            await ctx.message.author.remove_roles(get(ctx.guild.roles, name="음성 통제"))
                            embed.add_field(name='음성 통제', value='-', inline=True)
                        else:
                            embed.add_field(name='음성 통제', value='=', inline=True)
                        if chatctrl <= 3:
                            await ctx.message.author.add_roles(get(ctx.guild.roles, name="언론 통제"))
                            embed.add_field(name='언론 통제', value='+', inline=True)
                        elif chatctrl >= 92.5:
                            await ctx.message.author.remove_roles(get(ctx.guild.roles, name="언론 통제"))
                            embed.add_field(name='언론 통제', value='-', inline=True)
                        else:
                            embed.add_field(name='언론 통제', value='=', inline=True)
                        if emoji <= 10:
                            await ctx.message.author.add_roles(get(ctx.guild.roles, name="이모티콘 관리"))
                            embed.add_field(name='이모티콘 관리', value='+', inline=True)
                        elif emoji >= 95:
                            await ctx.message.author.remove_roles(get(ctx.guild.roles, name="이모티콘 관리"))
                            embed.add_field(name='이모티콘 관리', value='-', inline=True)
                        else:
                            embed.add_field(name='이모티콘 관리', value='=', inline=True)
                        if dj <= 15:
                            await ctx.message.author.add_roles(get(ctx.guild.roles, name="DJ"))
                            embed.add_field(name='DJ', value='+', inline=True)
                        elif dj >= 97.5:
                            await ctx.message.author.remove_roles(get(ctx.guild.roles, name="DJ"))
                            embed.add_field(name='DJ', value='-', inline=True)
                        else:
                            embed.add_field(name='DJ', value='=', inline=True)
                        await ctx.send(embed=embed)
                    else:
                        await ctx.send(":negative_squared_cross_mark: 가챠를 취소했습니다.")
            else:
                await ctx.send(":no_entry: 권한이 없습니다.")
        else:
            await ctx.send(":no_entry: 이 채널에서는 사용할 수 없는 명령어입니다.")

    @commands.command(name="가챠확률", help="명령어 '가챠'의 확률 정보를 공개합니다.", usage="%가챠확률")
    async def gacha_p(self, ctx):
        embed = discord.Embed(title="<가챠 확률 정보>", description="개발자가 업데이트를 안했을 수도 있습니다 ㅎㅎ")
        embed.add_field(name="> 창씨개명", value="1% (15%)", inline=False)
        embed.add_field(name="> 음성 통제", value="2% (10%)", inline=False)
        embed.add_field(name="> 언론 통제", value="3% (7.5%)", inline=False)
        embed.add_field(name="> 이모티콘 관리", value="10% (5%)", inline=False)
        embed.add_field(name="> DJ", value="15% (2.5%)", inline=False)
        await ctx.send(embed=embed)


def setup(app):
    app.add_cog(Game(app))