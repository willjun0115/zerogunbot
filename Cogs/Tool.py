import discord
from discord.ext import commands
from discord.utils import get
import openpyxl


class Tool(commands.Cog, name="도구(Tool)"):

    def __init__(self, app):
        self.app = app

    @commands.command(name="도움말", help="도움말을 불러옵니다.", usage="%도움말, %도움말 ~")
    async def help_command(self, ctx, func=None):
        if func is None:
            embed = discord.Embed(title="도움말", description="접두사는 % 입니다.")
            cog_list = ["도구(Tool)", "채팅(Chat)", "게임(Game)", "음성(Voice)"]
            embed.add_field(name="> 시스템(System)", value="load\nunload\nreload", inline=True)
            for x in cog_list:
                cog_data = self.app.get_cog(x)
                command_list = cog_data.get_commands()
                embed.add_field(name="> " + x, value="\n".join([c.name for c in command_list]), inline=True)
            await ctx.send(embed=embed)
        else:
            command_notfound = True
            for _title, cog in self.app.cogs.items():
                if not command_notfound:
                    break

                else:
                    for title in cog.get_commands():
                        if title.name == func:
                            cmd = self.app.get_command(title.name)
                            embed = discord.Embed(title=f"명령어 : {cmd}", description=cmd.help)
                            embed.add_field(name="사용법", value=cmd.usage)
                            await ctx.send(embed=embed)
                            command_notfound = False
                            break
                        else:
                            command_notfound = True
                            if func == 'load':
                                embed = discord.Embed(title=f"명령어 : load", description='명령어 카테고리를 불러옵니다.')
                                embed.add_field(name="사용법", value='%load ~')
                                await ctx.send(embed=embed)
                                command_notfound = False
                                break
                            if func == 'unload':
                                embed = discord.Embed(title=f"명령어 : unload", description='불러온 명령어 카테고리를 제거합니다.')
                                embed.add_field(name="사용법", value='%unload ~')
                                await ctx.send(embed=embed)
                                command_notfound = False
                                break
                            if func == 'reload':
                                embed = discord.Embed(title=f"명령어 : reload", description='명령어 카테고리를 다시 불러옵니다.')
                                embed.add_field(name="사용법", value='%reload, %reload ~')
                                await ctx.send(embed=embed)
                                command_notfound = False
                                break
            if command_notfound is True:
                await ctx.send('명령어를 찾을 수 없습니다.')

    @commands.command(name='인코드', help='입력받은 문자열을 인코딩해 출력합니다.',
                      usage='%인코드 ~', pass_context=True)
    async def chat_encode(self, ctx, *, args):
        await ctx.message.delete()
        code = ""
        for c in args:
            x = ord(c)
            x = x * 2 + 11
            cc = chr(x)
            code = code + cc
        await ctx.send(str(code))

    @commands.command(name='디코드', help='0군봇이 인코딩한 코드를 입력받아 디코드해 출력합니다.',
                      usage='%디코드 ~', pass_context=True)
    async def chat_decode(self, ctx, *, code):
        await ctx.message.delete()
        args = ""
        for c in code:
            x = ord(c)
            x = (x - 11) // 2
            cc = chr(x)
            args = args + cc
        await ctx.send(str(args))

    @commands.command(name='프라이빗인코드', help='입력받은 문자열을 자신만 디코드할 수 있는 코드로 인코딩해 출력합니다.',
                      usage='%프라이빗인코드 ~', pass_context=True)
    async def private_encode(self, ctx, *, args):
        await ctx.message.delete()
        id = str(ctx.author.id)
        id_1 = int(id[0:3])
        id_2 = int(id[3:6])
        id_3 = int(id[6:9])
        id_4 = int(id[9:12])
        id_5 = int(id[12:15])
        id_6 = int(id[15:18])
        idcode = chr(id_1) + chr(id_2) + chr(id_3) + chr(id_4) + chr(id_5) + chr(id_6)
        code = ""
        for c in args:
            x = ord(c)
            x = x * 2 - 31
            cc = chr(x)
            code = code + cc
        code = idcode + ";" + code
        await ctx.send(str(code))

    @commands.command(name='프라이빗디코드', help='0군봇이 인코딩한 프라이빗코드를 입력받아 디코드해 출력합니다.',
                      usage='%프라이빗디코드 ~', pass_context=True)
    async def private_decode(self, ctx, *, code):
        await ctx.message.delete()
        id = str(ctx.author.id)
        id_1 = int(id[0:3])
        id_2 = int(id[3:6])
        id_3 = int(id[6:9])
        id_4 = int(id[9:12])
        id_5 = int(id[12:15])
        id_6 = int(id[15:18])
        idcode = chr(id_1) + chr(id_2) + chr(id_3) + chr(id_4) + chr(id_5) + chr(id_6)
        if idcode == code[:6]:
            code = code[7:]
            args = ""
            for c in code:
                x = ord(c)
                x = (x + 31) // 2
                cc = chr(x)
                args = args + cc
            await ctx.send(str(args))
        else:
            await ctx.send(":no_entry_sign: 코드 작성자의 아이디가 일치하지 않습니다.")


def setup(app):
    app.add_cog(Tool(app))