import discord
from discord.ext import commands
from discord.utils import get
import asyncio
import io
import datetime


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
                cmd_names = []
                for c in command_list:
                    if c.hidden is False and c.enabled is True:
                        cost = getattr(c, 'token_cost', 0) or getattr(c.callback, 'token_cost', 0)
                        if cost > 0:
                            cmd_names.append(f"{c.name} [🪙 {cost}]")
                        else:
                            cmd_names.append(c.name)
                embed.add_field(
                    name=f"> {x}({cog_list[x]})",
                    value="\n".join(cmd_names) if cmd_names else "명령어 없음",
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
                            embed.add_field(name="대체명령어", value=', '.join(cmd.aliases) if cmd.aliases else "없음")
                            embed.add_field(name="사용법", value=self.app.prefix + cmd.usage)
                            cost = getattr(cmd, 'token_cost', 0) or getattr(cmd.callback, 'token_cost', 0)
                            if cost > 0:
                                embed.add_field(name="소모 토큰", value=f":coin: {cost}개", inline=False)
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

        find, user_data = await self.app.db.find_data(member.id)
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

    @commands.check_any(commands.has_permissions(administrator=True), commands.is_owner())
    @commands.command(
        name="DB출력", aliases=["db출력", "dumpdb", "exportdb", "DB조회", "db조회"],
        help="DB 내용을 채팅으로 출력하거나 텍스트 파일로 반환합니다. (관리자 권한)\n"
             "사용법:\n"
             "• %DB출력 (기본: 상위 요약 + 전체 텍스트 파일 첨부)\n"
             "• %DB출력 파일 (텍스트 파일만 첨부)\n"
             "• %DB출력 채팅 (채팅창 요약만 출력)\n"
             "• %DB출력 @유저 (특정 유저의 DB 조회)",
        usage="* (@member / str(*mode*))"
    )
    async def dump_db(self, ctx, *args):
        # 1. 특정 유저를 멘션한 경우: 단일 유저 DB 조회
        if ctx.message.mentions:
            target = ctx.message.mentions[0]
            find, user_data = await self.app.db.find_data(target.id)
            if find is None:
                await ctx.send(f":warning: {target.mention} 님의 DB 데이터가 존재하지 않습니다.")
                return

            embed = discord.Embed(
                title=f"👤 {target.display_name} 님의 DB 정보",
                color=0x2ecc71
            )
            embed.set_thumbnail(url=target.display_avatar.url if target.display_avatar else None)
            embed.add_field(name="유저 ID", value=str(target.id), inline=False)
            embed.add_field(name="🪙 토큰 ($)", value=f"{user_data.get('$', 0):,} 개", inline=True)
            embed.add_field(name="🍀 행운 (%)", value=f"{user_data.get('%', 0):,}", inline=True)
            ability = user_data.get('*')
            embed.add_field(name="✨ 능력 (*)", value=str(ability) if ability is not None else "없음", inline=True)
            await ctx.send(embed=embed)
            return

        # 2. 전체 목록 덤프
        file_only = False
        chat_only = False

        for arg in args:
            arg_lower = arg.lower()
            if arg_lower in ['파일', 'file', '-f']:
                file_only = True
            elif arg_lower in ['채팅', 'chat', '-c', '출력']:
                chat_only = True

        records = await self.app.db.dump_data()

        if not records:
            await ctx.send(":warning: 데이터베이스에 저장된 유저 데이터가 없습니다.")
            return

        # 텍스트 파일 포맷팅 생성 (표 형태)
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        lines = [
            "=" * 86,
            f"[ ZeroGunBot Database Export ]",
            f"추출 일시: {now_str} (KST)",
            f"총 레코드: {len(records)}개",
            "=" * 86,
            f"{'유저 ID':<20} | {'닉네임/이름':<20} | {'토큰($)':<12} | {'행운(%)':<8} | {'능력(*)':<10} | {'최근 변경 일시'}",
            "-" * 86
        ]

        for r in records:
            uid = r["user_id"]
            user = self.app.get_user(uid)
            if user:
                name_str = user.name
            else:
                member = ctx.guild.get_member(uid) if ctx.guild else None
                name_str = member.display_name if member else "알 수 없음"

            if len(name_str) > 18:
                name_str = name_str[:15] + "..."

            ability_str = str(r["ability"]) if r["ability"] is not None else "-"
            updated_str = str(r["updated_at"]) if r["updated_at"] else "-"
            coins_str = f"{r['coins']:,}"
            luck_str = f"{r['luck']:,}"

            lines.append(
                f"{uid:<20} | {name_str:<20} | {coins_str:<12} | {luck_str:<8} | {ability_str:<10} | {updated_str}"
            )

        lines.append("=" * 86)
        full_text = "\n".join(lines)

        # 텍스트 파일 버퍼 생성
        file_buffer = io.BytesIO(full_text.encode('utf-8'))
        file_name = f"db_export_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        discord_file = discord.File(fp=file_buffer, filename=file_name)

        # 파일만 전송하는 옵션인 경우
        if file_only:
            await ctx.send(
                content=f"📁 **데이터베이스 내보내기 완료** (총 `{len(records)}`개)",
                file=discord_file
            )
            return

        # 채팅 출력 (임베드 요약)
        embed = discord.Embed(
            title="📊 데이터베이스 조회",
            description=f"총 **{len(records)}**개의 유저 데이터가 조회되었습니다.",
            color=0x3498db
        )

        preview_limit = min(10, len(records))
        preview_text_list = []
        for i, r in enumerate(records[:preview_limit]):
            uid = r["user_id"]
            user = self.app.get_user(uid)
            name_str = user.name if user else f"<@{uid}>"
            coins_str = f"{r['coins']:,}"
            luck_str = f"{r['luck']:,}"
            ability_str = f" / ✨ `{r['ability']}`" if r["ability"] else ""
            preview_text_list.append(
                f"**{i+1}.** {name_str} (`{uid}`): 🪙 **{coins_str}** | 🍀 **{luck_str}**{ability_str}"
            )

        embed.add_field(
            name=f"상위 목록 ({preview_limit}/{len(records)})",
            value="\n".join(preview_text_list),
            inline=False
        )

        if len(records) > preview_limit and chat_only:
            embed.set_footer(text="전체 목록을 파일로 받으려면 '%DB출력 파일'을 입력하세요.")
        else:
            embed.set_footer(text="상세 전체 데이터는 첨부된 텍스트 파일을 확인하세요.")

        if chat_only:
            await ctx.send(embed=embed)
        else:
            await ctx.send(embed=embed, file=discord_file)

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
