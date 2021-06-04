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
            cog_list = ["도구(Tool)", "권한(Permission)", "채팅(Chat)", "게임(Game)", "코인(Coin)"]
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

    @commands.has_permissions(administrator=True)
    @commands.command(name="초기화", help="언급한 대상의 모든 역할과 닉네임을 초기화합니다.\n(관리자 권한)", usage="%초기화, %초기화 @", pass_context=True)
    async def all_reset(self, ctx, member: discord.Member = None):
        member = member or None
        if member is None:
            for member in ctx.channel.members:
                try:
                    for role in member.roles:
                        if 1 < role.position <= 15:
                            await member.remove_roles(role)
                except:
                    pass
                await member.edit(nick=None)
                await ctx.channel.send(str(member) + " 님의 권한과 닉네임을 초기화했습니다.")
        else:
            try:
                for role in member.roles:
                    if 1 < role.position <= 15:
                        await member.remove_roles(role)
            except:
                pass
            await member.edit(nick=None)
            await ctx.channel.send(str(member) + " 님의 권한과 닉네임을 초기화했습니다.")

    @commands.command(name="역할레벨", help="대상의 역할 레벨 총합을 계산합니다.", usage="%역할레벨, %역할레벨 @")
    async def role_lv(self, ctx, member: discord.Member = None):
        member = member or ctx.message.author
        role_p = 0
        try:
            for role in member.roles:
                if 2 < role.position <= 15:
                    role_p += role.position - 2
        except:
            pass
        await ctx.send(str(member) + " 님의 역할 레벨은 " + str(role_p) + " 입니다.")

    @commands.command(name="역할목록", help='역할 목록을 표시합니다.', usage='%역할목록, %역할목록 ~', pass_context=True)
    async def role_lv_list(self, ctx, args: discord.Role = None):
        if args is None:
            embed = discord.Embed(title="<역할 목록>",
                                  description="역할 순위가 높을수록 할당 레벨이 높습니다.")
            for role in ctx.guild.roles:
                if 2 < role.position <= 15:
                    embed.add_field(name="> " + role.name, value="Lv. " + str(role.position - 2), inline=False)
            await ctx.send(embed=embed)
        else:
            openxl = openpyxl.load_workbook("Roles.xlsx")
            wb = openxl.active
            for role in ctx.guild.roles:
                if role == args:
                    embed = discord.Embed(title=role.name,
                                          description="Lv. " + str(role.position - 2), colour=role.colour)
                    embed.add_field(name="> 판매 가격", value=':coin: '+str(wb["B" + str(role.position - 2)].value), inline=False)
                    embed.add_field(name="> 설명", value=str(wb["C" + str(role.position - 2)].value), inline=False)
                    embed.add_field(name="> 관련 명령어", value=str(wb["D" + str(role.position - 2)].value), inline=False)
                    await ctx.send(embed=embed)
                    break
            openxl.save("Roles.xlsx")

    @commands.command(name='인코드', help='유니코드로 인코딩합니다.',
                      usage='%인코드 ~', pass_context=True)
    async def chat_encode(self, ctx, *, args):
        await ctx.message.delete()
        code = ""
        for c in args:
            x = ord(c)
            x = x + 2
            cc = chr(x)
            code = code + cc
        await ctx.send(str(code))

    @commands.command(name='디코드', help='유니코드를 디코딩합니다.',
                      usage='%디코드 ~', pass_context=True)
    async def chat_decode(self, ctx, *, code):
        await ctx.message.delete()
        args = ""
        for c in code:
            x = ord(c)
            x = x - 2
            cc = chr(x)
            args = args + cc
        await ctx.send(str(args))

    @commands.command(name='백업', help='코인 데이터베이스를 백업합니다.',
                      usage='%백업', pass_context=True)
    async def backup_coin(self, ctx):
        await ctx.send(file=discord.File(fp='coin.xlsx', filename='coin.xlsx'))


def setup(app):
    app.add_cog(Tool(app))