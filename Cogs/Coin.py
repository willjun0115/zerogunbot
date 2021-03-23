import discord
import random
import asyncio
from discord.utils import get
from discord.ext import commands
import openpyxl


class Coin(commands.Cog, name="코인(Coin)"):

    def __init__(self, app):
        self.app = app

    @commands.has_permissions(administrator=True)
    @commands.command(name='코인설정', help='대상의 코인을 설정합니다.'
                                        '\n(관리자 권한)', usage='%코인설정 @ ~', pass_context=True)
    async def set_coin(self, ctx, member: discord.Member, num):
        id = str(member.id)
        coin = int(num)
        openxl = openpyxl.load_workbook("coin.xlsx")
        wb = openxl.active
        for i in range(1, 100):
            if wb["B" + str(i)].value == id:
                wb["C" + str(i)].value = int(coin)

                await ctx.channel.send(f"코인 설정: {coin}")
                break
        openxl.save("coin.xlsx")

    @commands.has_permissions(administrator=True)
    @commands.command(name='코인증가', help='대상의 코인을 증가시킵니다.'
                                        '\n(관리자 권한)', usage='%코인증가 @ ~', pass_context=True)
    async def gain_coin(self, ctx, member: discord.Member, num):
        id = str(member.id)
        coin = int(num)
        openxl = openpyxl.load_workbook("coin.xlsx")
        wb = openxl.active
        for i in range(1, 100):
            if wb["B" + str(i)].value == id:
                wb["C" + str(i)].value = wb["C" + str(i)].value + int(coin)

                await ctx.channel.send(f"코인 추가: +{coin}")
                break
        openxl.save("coin.xlsx")

    @commands.has_permissions(administrator=True)
    @commands.command(name='코인감소', help='대상의 코인을 감소시킵니다.'
                                        '\n(관리자 권한)', usage='%코인감소 @ ~', pass_context=True)
    async def lose_coin(self, ctx, member: discord.Member, num):
        id = str(member.id)
        coin = int(num)
        openxl = openpyxl.load_workbook("coin.xlsx")
        wb = openxl.active
        for i in range(1, 100):
            if wb["B" + str(i)].value == id:
                wb["C" + str(i)].value = wb["C" + str(i)].value - int(coin)

                await ctx.channel.send(f"코인 감소: -{coin}")
                break
        openxl.save("coin.xlsx")

    @commands.command(name='코인', help='자신의 코인을 확인합니다.', usage='%코인')
    async def check_coin(self, ctx):
        id = str(ctx.author.id)
        openxl = openpyxl.load_workbook("coin.xlsx")
        wb = openxl.active
        for i in range(1, 100):
            if wb["B" + str(i)].value == id:
                coin = wb["C" + str(i)].value
                await ctx.channel.send(str(ctx.author.name) + f" 님의 코인: {coin}")
                break
        openxl.save("coin.xlsx")

    @commands.command(name='베팅', help='자신의 코인을 베팅합니다.'
                                      '\n1/3 확률로 잃거나, 유지하거나, 2배로 반환됩니다.', usage='%코인 ~')
    async def bet_coin(self, ctx, num):
        my_channel = ctx.guild.get_channel(814888257698398289)
        if ctx.channel == my_channel:
            id = str(ctx.author.id)
            openxl = openpyxl.load_workbook("coin.xlsx")
            wb = openxl.active
            for i in range(1, 100):
                if wb["B" + str(i)].value == id:
                    if 0 < int(num) <= wb["C" + str(i)].value:
                        rand = random.randint(-1, 1)
                        wb["C" + str(i)].value = wb["C" + str(i)].value + int(num) * rand
                        embed = discord.Embed(title="<베팅 결과>",
                                              description=ctx.author.name + " 님의 결과")
                        if rand == -1:
                            embed.add_field(name="> 베팅결과", value="-", inline=True)
                        elif rand == 0:
                            embed.add_field(name="> 베팅결과", value="=", inline=True)
                        elif rand == 1:
                            embed.add_field(name="> 베팅결과", value="+", inline=True)
                        embed.add_field(name="> 현재 코인", value=str(wb["C" + str(i)].value), inline=True)
                        await ctx.send(embed=embed)
                    else:
                        await ctx.send("코인이 부족합니다.")
                    break
            openxl.save("coin.xlsx")
        else:
            await ctx.send(":no_entry: 이 채널에서는 사용할 수 없는 명령어입니다.")

    @commands.command(name='트레이드', help='자신의 코인을 걸고 상대방과 베팅합니다.'
                                      '\n1/2 확률로 이긴 쪽이 코인을 빼앗아옵니다.', usage='%트레이드 @ ~', pass_context=True)
    async def trade_coin(self, ctx, member: discord.Member, num):
        my_channel = ctx.guild.get_channel(814888257698398289)
        if ctx.channel == my_channel:
            id = str(ctx.author.id)
            oppo_id = str(member.id)
            s_coin = 0
            o_coin = 0
            openxl = openpyxl.load_workbook("coin.xlsx")
            wb = openxl.active
            for i in range(1, 100):
                if wb["B" + str(i)].value == id:
                    s_coin += wb["C" + str(i)].value
                elif wb["B" + str(i)].value == oppo_id:
                    o_coin += wb["C" + str(i)].value
            if s_coin >= int(num) and o_coin >= int(num):
                msg = await ctx.send(ctx.author.name + " 님이 " + member.name + " 님에게 "
                                     + str(num) + " 코인을 걸고 트레이드를 신청합니다."
                                                  "\n수락은 :white_check_mark: 을 눌러주세요.")
                reaction_list = ['✅', '❎']
                for r in reaction_list:
                    await msg.add_reaction(r)

                def check(reaction, user):
                    return str(reaction) in reaction_list and \
                           reaction.message.id == msg.id and user == member

                try:
                    reaction, user = await self.app.wait_for("reaction_add", check=check, timeout=10.0)
                except asyncio.TimeoutError:
                    await msg.edit(content="시간 초과!", delete_after=2)
                else:
                    if str(reaction) == '✅':
                        rand = random.randint(0, 1)
                        for i in range(1, 100):
                            if wb["B" + str(i)].value == id:
                                if 0 < int(num) <= wb["C" + str(i)].value:
                                    wb["C" + str(i)].value = wb["C" + str(i)].value + int(num) * (rand * 2 - 1)
                                    embed = discord.Embed(title="<트레이드 결과>",
                                                          description=ctx.author.name + " 님의 결과")
                                    if rand == 0:
                                        embed.add_field(name="> 결과", value="패배", inline=True)
                                    else:
                                        embed.add_field(name="> 결과", value="승리", inline=True)
                                    embed.add_field(name="> 현재 코인", value=str(wb["C" + str(i)].value), inline=True)
                                    await ctx.send(embed=embed)
                                else:
                                    await ctx.send("코인이 부족합니다.")
                                break
                        for i in range(1, 100):
                            if wb["B" + str(i)].value == oppo_id:
                                if 0 < int(num) <= wb["C" + str(i)].value:
                                    wb["C" + str(i)].value = wb["C" + str(i)].value - int(num) * (rand * 2 - 1)
                                    embed = discord.Embed(title="<트레이드 결과>",
                                                          description=member.name + " 님의 결과")
                                    if rand == 0:
                                        embed.add_field(name="> 결과", value="승리", inline=True)
                                    else:
                                        embed.add_field(name="> 결과", value="패배", inline=True)
                                    embed.add_field(name="> 현재 코인", value=str(wb["C" + str(i)].value), inline=True)
                                    await ctx.send(embed=embed)
                                else:
                                    await ctx.send("코인이 부족합니다.")
                                break
                    else:
                        await ctx.send("트레이드 신청을 거절했습니다.", delete_after=2)
            else:
                await ctx.send("자신과 상대의 보유 코인 이하로만 베팅할 수 있습니다.")

            openxl.save("coin.xlsx")
        else:
            await ctx.send(":no_entry: 이 채널에서는 사용할 수 없는 명령어입니다.")

    @commands.command(name='무료충전', help='코인을 100 충전합니다.', usage='%무료충전')
    async def free_coin(self, ctx):
        id = str(ctx.author.id)
        coin = 100
        openxl = openpyxl.load_workbook("coin.xlsx")
        wb = openxl.active
        for i in range(1, 100):
            if wb["B" + str(i)].value == id:
                wb["C" + str(i)].value = int(coin)

                await ctx.channel.send(f"시작 코인 충전: {coin}")
                break
        openxl.save("coin.xlsx")


def setup(app):
    app.add_cog(Coin(app))