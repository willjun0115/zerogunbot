import discord
from discord.ext import tasks, commands
from discord.utils import get
import asyncio
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import os
import youtube_dl
from discord import FFmpegPCMAudio
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import ast
import operator


class Tool(commands.Cog, name="도구", description="다양한 기능의 명령어 카테고리입니다."):

    def __init__(self, app):
        self.app = app
        #self.check_season_change.start()
        #self.next_season = datetime(2022, 1, 1, 0, 0, 0)

    '''@commands.Cog.listener()
    async def on_ready(self):
        self.check_season_change.start()

    @tasks.loop(minutes=1)
    async def check_season_change(self):
        global_guild = self.app.get_guild(self.app.global_guild_id)
        now = datetime.now()
        present_season_str = now.strftime('%Y.%m.01 00:00:00')
        present_season = datetime.strptime(present_season_str, '%Y.%m.%d %H:%M:%S')
        self.next_season = present_season + relativedelta(months=1) - timedelta(minutes=1)  # %Y.%m+1.01 23:59:00
        if datetime.now() > self.next_season:
            db = get(global_guild.text_channels, name="db")
            await db.edit(name=f"{present_season.strftime('%Y_%m')}")
            new_db = await db.clone(name="db")

    @check_season_change.after_loop
    async def on_check_season_change_cancel(self):
        if self.check_season_change.is_being_cancelled():
            self.check_season_change.restart()

    @commands.command(
        name="시즌", hidden=True
    )
    async def check_season(self, ctx):
        check = self.check_season_change.is_running()
        await ctx.send("season checking task is running: " + str(check))
        now = datetime.now()
        await ctx.send(
            f"present_season: {now.strftime('%Y_%m')}"
            f"\nnow(UTC): {now.strftime('%Y.%m.%d %H:%M:%S')}"
            f"\nnext season starts after {self.next_season - now}")
        if check is False:
            self.check_season_change.start()'''

    @commands.command(
        name="도움말", aliases=["help", "?"],
        help="도움말을 불러옵니다.\n'%사용법'에서 명령어 사용법 참조.", usage="* (str(*command*))"
    )
    async def help_command(self, ctx, func=None):
        if func is None:
            embed = discord.Embed(title="도움말", description=f"접두사는 {self.app.prefix} 입니다.")
            cog_list = {"도구": "Tool", "채팅": "Chat", "음성": "Voice", "게임": "Game", "비트코인": "BTC"}
            for x in cog_list.keys():
                cog_data = self.app.get_cog(x)
                command_list = cog_data.get_commands()
                embed.add_field(
                    name=f"> {x}({cog_list[x]})",
                    value="\n".join([c.name for c in command_list if c.hidden is False and c.enabled is True]),
                    inline=True
                )
            await ctx.send(embed=embed)
        else:
            command_notfound = True
            for title, cog in self.app.cogs.items():
                if func == cog.qualified_name:
                    embed = discord.Embed(title=f"카테고리 : {cog.qualified_name}", description=cog.description)
                    await ctx.send(embed=embed)
                    command_notfound = False
                    break
                else:
                    for cmd in cog.get_commands():
                        if func in ([cmd.name] + cmd.aliases):
                            embed = discord.Embed(title=f"명령어 : {cmd}", description=cmd.help)
                            embed.add_field(name="대체명령어", value=', '.join(cmd.aliases))
                            embed.add_field(name="사용법", value=self.app.prefix + cmd.usage)
                            await ctx.send(embed=embed)
                            command_notfound = False
                            break
                        else:
                            command_notfound = True
                    if command_notfound is False:
                        break
            if command_notfound is True:
                await ctx.send('명령어를 찾을 수 없습니다.')

    @commands.command(
        name="사용법", aliases=["문법", "usage"],
        help="명령 선언에 대한 기본적인 법칙을 설명합니다.", usage="*", hidden=True
    )
    async def usage_help(self, ctx):
        embed = discord.Embed(
            title="사용법",
            description="봇의 기본 명령어 구조는 '접두사 + 명령어' 입니다."
                        "\n명령어에 따라 필요한 인자를 명령어 뒤에 띄어쓰기 후 붙입니다."
        )
        embed.add_field(
            name="> 접두사 (prefix)",
            value="기본값(default): % or @*bot*"
                  "\n명령 선언 시 가장 앞에 입력.",
            inline=False
        )
        embed.add_field(
            name="> 명령어 (command)",
            value="명령어나 대체명령어"
                  "\n도움말에서 확인 가능."
                  "\n(사용법에서는 *로 표기)",
            inline=False
        )
        embed.add_field(
            name="※대체명령어",
            value="명령 선언 시 명령어와 동일하게 취급",
            inline=False
        )
        embed.add_field(
            name="> 인자 (arguments)",
            value="명령어 실행에 필요한 인자"
                  "\n도움말에서 필요한 인자의 형태와 개수 확인 가능."
                  "\n(사용법에서 괄호 안에 있는 인자는 기본값이 있으므로, 선택 포함)",
            inline=False
        )
        embed.add_field(
            name="※인자 형태",
            value="str(*type*): 문자열, int(*range*): 정수, float(*range*): 실수, @*type*: 언급(멘션)",
            inline=False
        )
        await ctx.send(embed=embed)

    @commands.check_any(commands.has_permissions(administrator=True), commands.is_owner())
    @commands.command(
        name="DB편집", aliases=["editdb"],
        help="DB를 편집합니다. (관리자 권한)", usage="* str(*selector*) @*member* int()"
    )
    async def edit_db(self, ctx, selector, member: discord.Member, val):
        global_guild = self.app.get_guild(self.app.global_guild_id)
        db_channel = get(global_guild.text_channels, name="db")
        if len(selector) == 1:
            data = await self.app.find_id(selector, member.id)
            if data is not None:
                if val[0] == '+':
                    val = val[1:]
                    await data.edit(content=data.content[:20] + str(int(data.content[20:]) + int(val)))
                elif val[0] == '-':
                    val = val[1:]
                    await data.edit(content=data.content[:20] + str(int(data.content[20:]) - int(val)))
                else:
                    await data.edit(content=data.content[:20] + str(val))
                await ctx.send('DB를 업데이트했습니다.')
            else:
                await db_channel.send(selector + str(member.id) + ';' + str(val))
                await ctx.send('DB에 ' + member.mention + ' 님의 ID를 기록했습니다.')
        else:
            await ctx.send("식별자는 1글자여야 합니다.")

    @commands.command(
        name='암호화', aliases=["encrypt", "enc"],
        help='입력받은 문자열을 암호화해 출력합니다.', usage='* int([0, 999]) str()', pass_context=True
    )
    async def chat_encryption(self, ctx, num, *, args):
        await ctx.message.delete()
        num = int(num)
        if 0 <= num < 1000:
            code = await self.app.encrypt(num, args)
            await ctx.send(code)
        else:
            await ctx.send(":warning: 코드번호는 0~999의 정수만 가능합니다.")

    @commands.command(
        name='복호화', aliases=["decrypt", "dec"],
        help='0군봇이 암호화한 암호를 입력받아 복호화해 출력합니다.', usage='* int([0, 999]) str(*code*)', pass_context=True
    )
    async def chat_decryption(self, ctx, num, *, code):
        await ctx.message.delete()
        num = int(num)
        if 0 <= num < 1000:
            args = await self.app.decrypt(num, code)
            await ctx.send(args)
        else:
            await ctx.send(":warning: 코드번호는 0~999의 정수만 가능합니다.")


def setup(app):
    app.add_cog(Tool(app))
