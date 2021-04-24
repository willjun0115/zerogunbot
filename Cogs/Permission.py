import discord
import asyncio
import random
from discord.utils import get
from discord.ext import commands


class Permission(commands.Cog, name="권한(Permission)"):

    def __init__(self, app):
        self.app = app

    @commands.command(name='패드립', help="저희 봇에 그런 기능은 없습니다?\n('유미학살자' 필요)", usage="%패드립")
    async def fdr(self, ctx):
        member = ctx.message.author
        if get(ctx.guild.roles, name='유미학살자') in member.roles:
            msg = await ctx.send("느금마")
            await asyncio.sleep(1)
            await msg.edit(content='저는 그런 말 못해요 ㅠㅠ')
        else:
            await ctx.send(" :no_entry: 이 명령을 실행하실 권한이 없습니다.")

    @commands.command(name='엄마삭제', help="입력값의 엄마를 삭제합니다.\n('유미학살자' 필요)", usage="%엄마삭제 ~", pass_context=True)
    async def delete_mom_(self, ctx, *, args):
        member = ctx.message.author
        if get(ctx.guild.roles, name='유미학살자') in member.roles:
            msg = await ctx.send("\"" + args + "\"님의 엄마 삭제 중...  0% :clock12: ")
            await asyncio.sleep(1)
            await msg.edit(content="\"" + args + "\"님의 엄마 삭제 중...  25% :clock3: ")
            await asyncio.sleep(1)
            await msg.edit(content="\"" + args + "\"님의 엄마 삭제 중...  50% :clock6: ")
            await asyncio.sleep(1)
            await msg.edit(content="\"" + args + "\"님의 엄마 삭제 중...  75% :clock9: ")
            await asyncio.sleep(1)
            await msg.edit(content="\"" + args + "\"님의 엄마 삭제 중...  99% :clock11: ")
            await asyncio.sleep(2)
            await msg.edit(content=":white_check_mark: \"" + args + "\"님의 엄마이(가) 삭제되었습니다.")
        else:
            await ctx.send(" :no_entry: 이 명령을 실행하실 권한이 없습니다.")

    @commands.command(name="엄마검색", help="입력값의 엄마를 검색합니다.\n('유미학살자' 필요)", usage="%엄마검색 ~", pass_context=True)
    async def search_mom_(self, ctx, *, args):
        member = ctx.message.author
        if get(ctx.guild.roles, name='유미학살자') in member.roles:
            msg = await ctx.send(":mag_right: \"" + args + "\"님의 엄마 검색 중.")
            await asyncio.sleep(1)
            await msg.edit(content=":mag_right: \"" + args + "\"님의 엄마 검색 중..")
            await asyncio.sleep(1)
            await msg.edit(content=":mag_right: \"" + args + "\"님의 엄마 검색 중...")
            await asyncio.sleep(1)
            mom_exist = random.randint(0, 3)
            if mom_exist == 0:
                await msg.edit(content=":warning: \"" + args + "\"님의 엄마을(를) 찾을 수 없습니다.")
            elif mom_exist == 1:
                await msg.edit(content=":white_check_mark: \"" + args + "\"님의 엄마가 확인되었습니다. \n(검색결과 수: 1)")
            elif mom_exist == 2:
                await msg.edit(content=":white_check_mark: \"" + args + "\"님의 엄마가 확인되었습니다. \n(검색결과 수: 2)")
            else:
                await msg.edit(content=":white_check_mark: \"" + args + "\"님의 엄마가 확인되었습니다. \n(검색결과 수: 99+)")
        else:
            await ctx.send(" :no_entry: 이 명령을 실행하실 권한이 없습니다.")

    @commands.command(name="스틸", help="자신보다 역할 레벨이 낮은 대상의 '창씨개명' 이하 권한을 가져옵니다.\n('스틸' 필요)", usage="%스틸 @",
                      pass_context=True)
    async def steal(self, ctx, member: discord.Member):
        athr = ctx.message.author
        if get(ctx.guild.roles, name='스틸') in athr.roles:
            if member == ctx.message.author:
                await ctx.channel.send("자신은 스틸할 수 없습니다.")
            else:
                my_role = 0
                oppo_role = 0
                try:
                    for role in member.roles:
                        if 2 < role.position <= 15:
                            oppo_role += role.position - 2
                except:
                    pass
                try:
                    for role in athr.roles:
                        if 2 < role.position <= 15:
                            my_role += role.position - 2
                except:
                    pass
                if oppo_role < my_role:
                    try:
                        for role in athr.roles:
                            if 2 < role.position <= 11:
                                await athr.remove_roles(role)
                    except:
                        pass
                    try:
                        for role in member.roles:
                            if 2 < role.position <= 11:
                                await athr.add_roles(role)
                    except:
                        pass
                    await ctx.send(str(athr.name) + " 님이 " + str(member.name) + " 님의 역할을 스틸했습니다!")
                else:
                    await ctx.channel.send("역할 레벨이 부족합니다.")
        else:
            await ctx.send(" :no_entry: 이 명령을 실행하실 권한이 없습니다.")

    @commands.command(name='인원제한', help="'인원 제한' 음성 채널의 인원 수를 설정합니다."
                                        "\n('매니저' 필요)", usage="%인원제한 ~", pass_context=True)
    async def voice_ch_lim(self, ctx, num):
        if get(ctx.guild.roles, name='매니저') in ctx.author.roles:
            if 0 <= int(num) < 100:
                channel = get(ctx.guild.channels, id=814824977760256001)
                await channel.edit(user_limit=num)
                await ctx.send("채널의 제한 인원 수를 " + str(num) + " 명으로 변경했습니다.")
            else:
                await ctx.send("제한 인원 수는 0~99 사이의 숫자만 가능합니다.")
        else:
            await ctx.send(" :no_entry: 이 명령을 실행하실 권한이 없습니다.")

    @commands.command(name="미카엘", help="대상의 '가렌Q','귀마개' 등의 상태이상을 풀어줍니다."
                                       "\n('미카엘' 필요)", usage="%미카엘, %미카엘 @", pass_context=True)
    async def role_0(self, ctx, member: discord.Member = None):
        if get(ctx.guild.roles, name='미카엘') in ctx.author.roles:
            member = member or ctx.message.author
            if member == ctx.message.author:
                await member.edit(deafen=False)
                await member.edit(mute=False)
                await ctx.channel.send(str(member.name) + " 님이 상태이상을 해제했습니다!")
            else:
                await member.edit(deafen=False)
                await member.edit(mute=False)
                await ctx.channel.send(str(member.name) + " 님의 상태이상이 해제되었습니다!")
        else:
            await ctx.send(" :no_entry: 이 명령을 실행하실 권한이 없습니다.")

    @commands.command(name='히든채팅', help="매니저 채널에서 친 채팅을 #일반에 전송합니다."
                                        "\n('매니저' 필요)", usage="%히든채팅 ~", pass_context=True)
    async def hidden_chat(self, ctx, *, args):
        my_channel = ctx.guild.get_channel(764826097283366932)
        normal_channel = ctx.guild.get_channel(760194959336275991)
        if ctx.channel == my_channel:
            if get(ctx.guild.roles, name='매니저') in ctx.author.roles:
                await normal_channel.send(args)
            else:
                await ctx.send(" :no_entry: 이 명령을 실행하실 권한이 없습니다.")



def setup(app):
    app.add_cog(Permission(app))