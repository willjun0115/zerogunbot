import discord
from discord.ext import commands
from discord.utils import get


class Tool(commands.Cog, name="도구(Tool)"):

    def __init__(self, app):
        self.app = app

    @commands.command(name="도움말", help="도움말을 불러옵니다.", usage="%도움말, %도움말 ~")
    async def help_command(self, ctx, func=None):
        if func is None:
            embed = discord.Embed(title="도움말", description="접두사는 % 입니다.")
            cog_list = ["도구(Tool)", "권한(Permission)", "채팅(Chat)", "게임(Game)", "코인(Coin)", "계정(Accounts)"]
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
                        if 2 < role.position <= 16:
                            await member.remove_roles(role)
                except:
                    pass
                await member.edit(nick=None)
                await ctx.channel.send(str(member) + " 님의 권한과 닉네임을 초기화했습니다.")
        else:
            try:
                for role in member.roles:
                    if 2 < role.position <= 16:
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
                if 3 < role.position <= 16:
                    role_p += role.position - 3
        except:
            pass
        await ctx.send(str(member) + " 님의 역할 레벨은 " + str(role_p) + " 입니다.")

    @commands.command(name="역할순위표", help='역할 순위표를 공개합니다.', usage='%역할순위표')
    async def role_lv_list(self, ctx):
        embed = discord.Embed(title="<역할 순위표>",
                              description="매니저 = 13"
                                          "\n 스틸 = 12"
                                          "\n 가챠 확장팩 = 11"
                                          "\n 도박중독 치료 = 10"
                                          "\n 창씨개명 = 9"
                                          "\n 닉변 = 8"
                                          "\n 강제이동 = 7"
                                          "\n 가렌Q = 6"
                                          "\n 귀마개 = 5"
                                          "\n 언론통제 = 4"
                                          "\n 유미학살자 = 3"
                                          "\n 이모티콘 관리 = 2"
                                          "\n DJ = 1")
        await ctx.send(embed=embed)

    @commands.command(name="접두사", help='접두사를 변경합니다. (default = %)', usage='%접두사')
    async def prefix(self, ctx, args):
        global prefix
        self.prefix = args
        await ctx.send("접두사를 " + prefix + "로 변경하였습니다.")


def setup(app):
    app.add_cog(Tool(app))