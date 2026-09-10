import discord
from discord.ext import commands
from discord.utils import get
import asyncio


class Tool(commands.Cog, name="도구", description="다양한 기능의 명령어 카테고리입니다."):

    def __init__(self, app):
        self.app = app


    @commands.command(
        name="도움말", aliases=["help", "?"],
        help="도움말을 불러옵니다.\n'%사용법'에서 명령어 사용법 참조.", usage="* (str(*command*))"
    )
    async def help_command(self, ctx, func=None):
        if func is None:
            embed = discord.Embed(title="도움말", description=f"접두사는 {self.app.prefix} 입니다.")
            cog_list = {"도구": "Tool", "채팅": "Chat", "음성": "Voice", "게임": "Game"}
            for x in cog_list.keys():
                cog_data = self.app.get_cog(x)
                if cog_data is None:
                    continue
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
        if len(selector) != 1:
            await ctx.send("식별자는 1글자여야 합니다.")
            return

        is_delta = val[0] in ['+', '-']
        op = val[0] if is_delta else None
        num_str = val[1:] if is_delta else val

        if selector in ['$', '%']:
            try:
                parsed_num = int(num_str)
            except ValueError:
                await ctx.send("숫자 형식이 올바르지 않습니다.")
                return
            parsed_val = parsed_num
        else:
            parsed_val = val

        find, user_data = await self.app.db.find_data('db', member.id)
        if find is None:
            initial_val = parsed_val if not is_delta else (parsed_val if op == '+' else -parsed_val)
            await self.app.db.update_data(member.id, {selector: initial_val})
            await ctx.send('DB에 ' + member.mention + ' 님의 ID를 기록했습니다.')
        else:
            if is_delta:
                curr_val = int(user_data.get(selector, 0))
                user_data[selector] = curr_val + parsed_val if op == '+' else curr_val - parsed_val
            else:
                user_data[selector] = parsed_val
            await self.app.db.update_data(member.id, user_data)
            await ctx.send('DB를 업데이트했습니다.')

    @commands.command(
        name='암호화', aliases=["encrypt", "enc"],
        help='입력받은 문자열을 암호화해 출력합니다.', usage='* int([0, 999]) str()'
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
        help='0군봇이 암호화한 암호를 입력받아 복호화해 출력합니다.', usage='* int([0, 999]) str(*code*)'
    )
    async def chat_decryption(self, ctx, num, *, code):
        await ctx.message.delete()
        num = int(num)
        if 0 <= num < 1000:
            args = await self.app.decrypt(num, code)
            await ctx.send(args)
        else:
            await ctx.send(":warning: 코드번호는 0~999의 정수만 가능합니다.")

    @commands.cooldown(1, 60., commands.BucketType.member)
    @commands.command(
        name='0군인증', aliases=["인증", "0id"],
        help='0군 인증서를 발급합니다. (쿨타임: 60초)', usage='*'
    )
    async def zero_identification(self, ctx):
        password = '0000'
        msg = await ctx.send("암호를 입력해주세요.")

        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel

        try:
            message = await self.app.wait_for("message", check=check, timeout=30.0)
        except asyncio.TimeoutError:
            await msg.edit(content="시간 초과!", delete_after=2)
        else:
            if message.content == password:
                await ctx.author.add_roles(ctx.guild.get_role(782684349899472916))
            else:
                await ctx.send('잘못된 암호입니다.')


async def setup(app):
    await app.add_cog(Tool(app))
