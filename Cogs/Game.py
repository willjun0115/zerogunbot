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

    @commands.command(name="토큰", help="자신의 토큰 수를 확인합니다.\n토큰 시스템에 등록되지 않았다면, 새로 ID를 등록합니다.", usage="%토큰")
    async def zerotoken(self, ctx):
        log_channel = ctx.guild.get_channel(874970985307201546)
        log = log_channel.history(limit=1)
        if str(ctx.author.name) in str(log.content):
            await ctx.send(str(log.content))
        else:
            new_log = str(log.content) + str(ctx.author.name)
            await log_channel.send(new_log)


def setup(app):
    app.add_cog(Game(app))