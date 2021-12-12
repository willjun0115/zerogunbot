import discord
from discord.ext import commands
from discord.utils import get
import asyncio
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import os
import youtube_dl
from discord import FFmpegPCMAudio


class Tool(commands.Cog, name="도구", description="정보 조회 및 편집에 관한 카테고리입니다."):

    def __init__(self, app):
        self.app = app
        self.ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '320'
            }],
        }

    async def find_log(self, ctx, selector, id):
        log_channel = ctx.guild.get_channel(self.app.log_ch)
        find = None
        async for message in log_channel.history(limit=100):
            if message.content.startswith(selector + str(id)) is True:
                find = message
                break
        return find

    @commands.command(
        name="도움말", aliases=["help", "?"],
        help="도움말을 불러옵니다.\n'%사용법'에서 명령어 사용법 참조.", usage="* (str(*command or category*))"
    )
    async def help_command(self, ctx, func=None):
        if func is None:
            embed = discord.Embed(title="도움말", description=f"접두사는 {self.app.prefix} 입니다.")
            cog_list = {"도구": "Tool", "채팅": "Chat", "음성": "Voice", "게임": "Game", "상점": "Shop"}
            for x in cog_list.keys():
                cog_data = self.app.get_cog(x)
                command_list = cog_data.get_commands()
                embed.add_field(
                    name=f"> {x}({cog_list[x]})",
                    value="\n".join([c.name for c in command_list if c.hidden is False]),
                    inline=True
                )
            await ctx.send(embed=embed)
        else:
            command_notfound = True
            for _title, cog in self.app.cogs.items():
                if func == cog.qualified_name:
                    embed = discord.Embed(title=f"카테고리 : {cog.qualified_name}", description=cog.description)
                    await ctx.send(embed=embed)
                    command_notfound = False
                    break
                else:
                    for title in cog.get_commands():
                        if func in ([title.name] + title.aliases):
                            cmd = self.app.get_command(title.name)
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
        name="사용법", aliases=["usage"],
        help="명령 선언에 대한 기본적인 법칙을 설명합니다.", usage="*"
    )
    async def usage_help(self, ctx):
        embed = discord.Embed(
            title="사용법",
            description="봇의 기본 명령어 구조는 '접두사 + 명령어' 입니다."
                        "\n명령어에 따라 필요한 인자를 명령어 뒤에 띄어쓰기 후 붙입니다."
        )
        embed.add_field(
            name="> 접두사 (prefix)",
            value="기본값(default): %"
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

    @commands.has_permissions(administrator=True)
    @commands.command(
        name="로그편집", aliases=["editlog", "edit"],
        help="해당 멤버의 로그를 편집합니다. (관리자 권한)", usage="* str(*selector*) @*member* int()"
    )
    async def edit_log(self, ctx, selector, member: discord.Member, val):
        log_channel = ctx.guild.get_channel(self.app.log_ch)
        if len(selector) == 1:
            log = await self.find_log(ctx, selector, member.id)
            if log is not None:
                await log.edit(content=log.content[:20] + str(val))
                await ctx.send('로그를 업데이트했습니다.')
            else:
                await log_channel.send(selector + str(member.id) + ';0')
                await ctx.send('로그에 ' + member.name + ' 님의 ID를 기록했습니다.')
        else:
            await ctx.send("식별자는 1글자여야 합니다.")

    @commands.command(
        name='암호화', aliases=["encrypt", "enc"],
        help='입력받은 문자열을 암호화해 출력합니다.', usage='* int([0, 999]) str()', pass_context=True
    )
    async def chat_encode(self, ctx, num, *, args):
        await ctx.message.delete()
        code = ""
        num = int(num)
        if 0 <= num < 1000:
            for c in args:
                x = ord(c)
                x = x * 2 + num * 3
                cc = chr(x)
                code = code + cc
            await ctx.send(str(code))
        else:
            await ctx.send(":warning: 코드번호는 0~999의 정수만 가능합니다.")

    @commands.command(
        name='복호화', aliases=["decrypt", "dec"],
        help='0군봇이 암호화한 암호를 입력받아 복호화해 출력합니다.', usage='* int([0, 999]) str(*code*)', pass_context=True
    )
    async def chat_decode(self, ctx, num, *, code):
        await ctx.message.delete()
        args = ""
        num = int(num)
        if 0 <= num < 1000:
            for c in code:
                x = ord(c)
                x = (x - num * 3) // 2
                cc = chr(x)
                args = args + cc
            await ctx.send(str(args))
        else:
            await ctx.send(":warning: 코드번호는 0~999의 정수만 가능합니다.")

    @commands.command(
        name="음원추출", aliases=["extract_mp3"],
        help="유튜브 링크를 통해 음원을 추출합니다.", usage="* str(*url*)", hidden=True
    )
    async def extract_yt(self, ctx, url):
        if url.startswith("https://www.youtube.com/"):
            msg = await ctx.send("음원을 추출 중 입니다...")
            with youtube_dl.YoutubeDL(self.ydl_opts) as ydl:
                ydl.download([url])
            await msg.edit(content="다운 완료! 배포 중...")
            for file in os.listdir("./"):
                if file.endswith(".mp3"):
                    await msg.delete()
                    await ctx.send(content=None, file=file)
                    os.remove(file)
                    break


def setup(app):
    app.add_cog(Tool(app))