import discord
from discord.ext import commands
from discord.utils import get


class Tool(commands.Cog, name="도구", description="정보 조회 및 편집에 관한 카테고리입니다."):

    def __init__(self, app):
        self.app = app
        self.log_ch_id = 874970985307201546

    async def find_log(self, ctx, selector, id):
        log_channel = ctx.guild.get_channel(self.log_ch_id)
        find = None
        async for message in log_channel.history(limit=100):
            if message.content.startswith(selector + str(id)) is True:
                find = message
                break
        return find

    @commands.command(
        name="도움말", aliases=["help", "?"],
        help="도움말을 불러옵니다.", usage="%*, %* str(command, category)"
    )
    async def help_command(self, ctx, func=None):
        if func is None:
            embed = discord.Embed(title="도움말", description=f"접두사는 {self.app.prefix} 입니다.")
            cog_list = {"도구": "Tool", "채팅": "Chat", "음성": "Voice", "게임": "Game"}
            for x in cog_list.keys():
                cog_data = self.app.get_cog(x)
                command_list = cog_data.get_commands()
                embed.add_field(name=f"> {x}({cog_list[x]})", value="\n".join([c.name for c in command_list]), inline=True)
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
                            embed.add_field(name="대체 명령어", value=', '.join(cmd.aliases))
                            embed.add_field(name="사용법", value=cmd.usage)
                            await ctx.send(embed=embed)
                            command_notfound = False
                            break
                        else:
                            command_notfound = True
                    if command_notfound is False:
                        break
            if command_notfound is True:
                await ctx.send('명령어를 찾을 수 없습니다.')

    @commands.has_permissions(administrator=True)
    @commands.command(
        name="로그편집", aliases=["editlog", "edit"],
        help="해당 멤버의 로그를 편집합니다. (관리자 권한)", usage="%* str(selector) @ int()"
    )
    async def edit_log(self, ctx, selector, member: discord.Member, val):
        log_channel = ctx.guild.get_channel(self.log_ch_id)
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
        name='인코드', aliases=["encode", "enc"],
        help='입력받은 문자열을 인코딩해 출력합니다.', usage='%* str()', pass_context=True
    )
    async def chat_encode(self, ctx, *, args):
        await ctx.message.delete()
        code = ""
        for c in args:
            x = ord(c)
            x = x * 2 + 11
            cc = chr(x)
            code = code + cc
        await ctx.send(str(code))

    @commands.command(
        name='디코드', aliases=["decode", "dec"],
        help='0군봇이 인코딩한 코드를 입력받아 디코드해 출력합니다.', usage='%* str(code)', pass_context=True
    )
    async def chat_decode(self, ctx, *, code):
        await ctx.message.delete()
        args = ""
        for c in code:
            x = ord(c)
            x = (x - 11) // 2
            cc = chr(x)
            args = args + cc
        await ctx.send(str(args))

    @commands.command(
        name='프라이빗인코드', aliases=["privateencode", "privenc"],
        help='입력받은 문자열을 자신만 디코드할 수 있는 코드로 인코딩해 출력합니다.',
        usage='%* str()', pass_context=True
    )
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

    @commands.command(
        name='프라이빗디코드', aliases=["privatedecode", "privdec"],
        help='0군봇이 인코딩한 프라이빗코드를 입력받아 디코드해 출력합니다.',
        usage='%* str(code)', pass_context=True
    )
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