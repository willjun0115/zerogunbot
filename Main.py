import sys
import random
import discord
from discord.ext import commands
from discord.utils import get
import os
import datetime
import io
import re
from dotenv import load_dotenv

# 라즈베리 파이 systemd 등 백그라운드 환경에서 print() 출력이 버퍼링 없이 journalctl에 즉시 찍히도록 설정
reconfig_out = getattr(sys.stdout, 'reconfigure', None)
if callable(reconfig_out):
    try:
        reconfig_out(line_buffering=True)
    except Exception:
        pass

reconfig_err = getattr(sys.stderr, 'reconfigure', None)
if callable(reconfig_err):
    try:
        reconfig_err(line_buffering=True)
    except Exception:
        pass

prefix = '%'
intents = discord.Intents.all()
load_dotenv()

import typing
from Database import Database
from Utils import InsufficientTokensError, UserNotRegisteredError, NotInVoiceChannelError

class ZeroGunBot(commands.Bot):
    _name: str = "0군봇"
    global_guild_id: int
    prefix: str
    db: Database
    encrypt: typing.Any
    decrypt: typing.Any
    find_id: typing.Any
    find_data: typing.Any
    update_data: typing.Any
    collect_data: typing.Any
    setup_database: typing.Any
    is_registered: typing.Any
    register_user: typing.Any
    delete_user: typing.Any
    start_time: datetime.datetime

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, value: str):
        self._name = value

    IGNORED_COGS = {"BTC.py"}

    async def setup_hook(self):
        await self.db.init_db()
        for filename in os.listdir("Cogs"):
            if filename.endswith(".py") and filename not in self.IGNORED_COGS and not filename.startswith("_"):
                await self.load_extension(f"Cogs.{filename[:-3]}")

app = ZeroGunBot(
    command_prefix=commands.when_mentioned_or(prefix),
    help_command=None,
    strip_after_prefix=True,
    intents=intents
)
app.name = "0군봇"
app.db = Database()
app.global_guild_id = 943244634602213396
app.prefix = prefix
app.start_time = datetime.datetime.now()

rn = random.randint(0, 999)
temp = None


def encrypt(num, args):
    code = ""
    for c in args:
        x = ord(c)
        x = x * 2 + num
        cc = chr(x)
        code = code + cc
    return code

def decrypt(num, code):
    args = ""
    for c in code:
        x = ord(c)
        x = (x - num) // 2
        cc = chr(x)
        args = args + cc
    return args

@app.event
async def on_ready():
    await app.change_presence(status=discord.Status.offline)
    game = discord.Game("시작하는 중...")
    await app.change_presence(status=discord.Status.online, activity=game)
    game = discord.Game(prefix + "도움말")
    await app.change_presence(status=discord.Status.online, activity=game)

@app.event
async def on_message(message):
    if message.author.bot:
        return None
    else:
        await app.process_commands(message)

@app.event
async def on_member_join(member):
    if member.guild.id == 760194959336275988:
        channel = member.guild.get_channel(813664336811786270)
        await channel.send("새 친구가 등장했습니다!")


# Database 관련 함수
async def find_id(selector, id):
    return await app.db.find_id(selector, id)

async def find_data(db_name, user_id=None):
    target = user_id if user_id is not None else db_name
    return await app.db.find_data(target)

async def update_data(user_id, data: dict, message=None):
    return await app.db.update_data(user_id, data, message=message)

async def collect_data(db_name=None):
    return await app.db.collect_data()

async def setup_database(ctx):
    await app.db.init_db()
    return "SQLite 데이터베이스가 정상적으로 초기화되었습니다."

async def is_registered(user_id: int):
    return await app.db.is_registered(user_id)

async def register_user(user_id: int, coins: int = 0, luck: int = 0, ability=None):
    return await app.db.register_user(user_id, coins=coins, luck=luck, ability=ability)

async def delete_user(user_id: int):
    return await app.db.delete_user(user_id)


app.encrypt = encrypt
app.decrypt = decrypt
app.find_id = find_id
app.find_data = find_data
app.update_data = update_data
app.collect_data = collect_data
app.setup_database = setup_database
app.is_registered = is_registered
app.register_user = register_user
app.delete_user = delete_user


# 관리자용 명령어
@commands.is_owner()
@app.group(name="admin", aliases=["%"])
async def admin_command(ctx):
    return


@admin_command.group(name="load", aliases=["l"])
async def load_cogs(ctx, extension):
    await app.load_extension(f"Cogs.{extension}")
    await ctx.send(f":white_check_mark: {extension}을(를) 로드했습니다.")


@admin_command.group(name="unload", aliases=["ul"])
async def unload_cogs(ctx, extension):
    await app.unload_extension(f"Cogs.{extension}")
    await ctx.send(f":white_check_mark: {extension}을(를) 언로드했습니다.")


@admin_command.group(name="reload", aliases=["rl"])
async def reload_cogs(ctx, extension=None):
    if extension is None:
        for file_name in os.listdir("Cogs"):
            if file_name.endswith(".py") and file_name not in app.IGNORED_COGS and not file_name.startswith("_"):
                try:
                    await app.unload_extension(f"Cogs.{file_name[:-3]}")
                except Exception:
                    pass
                await app.load_extension(f"Cogs.{file_name[:-3]}")
        await ctx.send(":white_check_mark: 명령어를 다시 불러왔습니다.")
    else:
        await app.unload_extension(f"Cogs.{extension}")
        await app.load_extension(f"Cogs.{extension}")
        await ctx.send(f":white_check_mark: {extension}을(를) 다시 불러왔습니다.")


@admin_command.group(name="execute", aliases=["exe"])
async def execute_command(ctx, *, strings=None):
    if not strings:
        await ctx.send("Command Not Found.")
        return
    strings_list = strings.split('--')
    cmd = None
    args = []
    kwargs = {}
    for string in strings_list:
        if string.startswith("cmd:"):
            cmd = app.get_command(string[4:].strip())
        elif string.startswith("args:"):
            a = eval(string[5:].strip())
            if type(a) is tuple or type(a) is list:
                args = a
            else:
                args = (a, )
        elif string.startswith("kwargs:"):
            k = eval(string[7:].strip())
            if type(k) is dict:
                kwargs = k
    if cmd:
        try:
            await cmd.__call__(ctx=ctx, *args, **kwargs)
        except:
            await ctx.send("Failed to call command.")
    else:
        await ctx.send("Command Not Found.")


@admin_command.group(name="execlit", aliases=["coro", "await"])
async def execute_literal(ctx, method, *, args):
    method = eval(f'{method}')
    if method is None:
        await ctx.send("MethodNotFound.")
    else:
        args = eval(args)
        if type(args) is tuple or type(args) is list:
            await method.__call__(*args)
        elif type(args) is dict:
            await method.__call__(**args)
        else:
            await method.__call__(args)


@admin_command.group(name="execseq", aliases=["exeseq"])
async def sequential_execute(ctx, *, args):
    args = args.split(';')
    global temp
    for arg in args:
        arg = arg.strip()
        i = arg[0]
        arg = arg[1:]
        if i == '%':
            await execute_command(ctx, strings=arg.strip())
        elif i == '*':
            arg = arg.spilt(maxsplit=1)
            method = arg[0]
            await execute_literal(ctx, method, args=arg[1])
        elif i == '&':
            temp = eval(args)


@admin_command.group(name="value", aliases=["val", "eval"])
async def get_value(ctx, *, args):
    val = eval(args)
    if "token" in args.lower():
        val = "Inaccessible Value"
    if "access" in args.lower():
        val = "Inaccessible Value"
    if "secret" in args.lower():
        val = "Inaccessible Value"
    await ctx.send(str(type(val)) + " " + str(val))


@admin_command.group(name="setvalue", aliases=["setval"])
async def set_value(ctx, *, args):
    global temp
    temp = eval(args)


@admin_command.group(name="delvalue", aliases=["delval"])
async def delete_value(ctx):
    global temp
    temp = None


@admin_command.group(name="status", aliases=["stat"])
async def admin_status(ctx):
    assert app.user is not None
    embed = discord.Embed(
        title="Status",
        description=
        f"prefix : {app.prefix}\n"
        f"client_name : {str(app.user)}\n"
        f"client_id : {app.user.id}\n"
        f"guilds_number : {len(app.guilds)}\n"
        f"users_number : {len(app.users)}\n"
        f"created_at : {app.user.created_at + datetime.timedelta(hours=9)} (UTC+9:00)"
    )
    await ctx.send(embed=embed)


@admin_status.group(name="detail", aliases=["+"])
async def admin_status_detail(ctx):
    assert app.user is not None
    appinfo = await app.application_info()
    embed = discord.Embed(
        title="Detail",
        description=
        f"owner_name : {str(appinfo.owner)}\n"
        f"owner_id : {appinfo.owner.id}\n"
        f"bot_public : {appinfo.bot_public}\n"
        f"bot_require_code_grant : {appinfo.bot_require_code_grant}\n"
        f"locale : {app.user.locale}"
    )
    embed.add_field(name="guilds", value="\n".join([g.name for g in app.guilds]))
    embed.add_field(name="users", value="\n".join([u.name for u in app.users]))
    await ctx.send(embed=embed)


@admin_command.group(name="fetch", aliases=["find", "get", "f"])
async def admin_fetch(ctx):
    return


@admin_fetch.group(name="guild", aliases=["server"])
async def admin_fetch_guild(ctx, id=None):
    if id is None:
        id = ctx.guild.id
    else:
        id = int(id)
    embed = discord.Embed(title="Fetch Guild", description=f"get guild by id : {id}")
    try:
        guild = app.get_guild(id)
        if guild is None:
            guild = await app.fetch_guild(id)
    except (discord.NotFound, discord.HTTPException):
        embed.add_field(name="NotFound", value="No guild was found.")
        await ctx.send(embed=embed)
        return
    except discord.Forbidden:
        embed.add_field(name="Forbidden", value="Cannot fetch the guild.")
        await ctx.send(embed=embed)
        return

    embed.set_thumbnail(url=guild.icon.url if guild.icon else None)
    embed.add_field(
        name="name : " + guild.name,
        value=f"created at {guild.created_at}\n"
              f"owner : {str(guild.owner)}\n"
              f"members_number : {len(guild.members)}",
        inline=False
    )
    await ctx.send(embed=embed)
    embed = discord.Embed(title="Members", description=f"list of members in {guild.name}")
    for member in guild.members:
        embed.add_field(
            name="> " + str(member),
            value=f"id: {member.id}\n"
                    f"joined at {member.joined_at}\n"
                    f"status: {member.raw_status}\n"
                    f"roles: {', '.join([role.name for role in member.roles])}",
            inline=True
        )
    await ctx.send(embed=embed)
    embed = discord.Embed(title="Channels", description=f"list of channels in {guild.name}")
    for category in guild.categories:
        embed.add_field(
            name="> " + category.name,
            value=f"{len(category.channels)} channels\n" +
                  "\n".join([c.mention for c in category.channels]),
            inline=True
        )
    embed.add_field(
        name="no category",
        value=f"{len([c for c in guild.channels if c.category is None and c not in guild.categories])} channels\n" +
              "\n".join([c.mention for c in guild.channels if c.category is None and c not in guild.categories]),
        inline=True
    )
    await ctx.send(embed=embed)
    embed = discord.Embed(title="Roles", description=f"list of roles in {guild.name}")
    for role in guild.roles[1:]:
        embed.add_field(
            name=str(role.position) + ") " + role.name,
            value="\n".join([str(m) for m in role.members]),
            inline=True
        )
    await ctx.send(embed=embed)


@admin_fetch.group(name="user", aliases=["member"])
async def admin_fetch_user(ctx, id):
    id = int(id)
    embed = discord.Embed(title="Fetch", description=f"fetch user by id : {id}")
    try:
        user = app.get_user(id)
        if user is None:
            user = await app.fetch_user(id)
    except (discord.NotFound, discord.HTTPException):
        embed.add_field(name="NotFound", value="No user was found.")
        await ctx.send(embed=embed)
        return
    except discord.Forbidden:
        embed.add_field(name="Forbidden", value="Cannot fetch the user.")
        await ctx.send(embed=embed)
        return

    embed.set_thumbnail(url=user.avatar.url if user.avatar else None)  # type: ignore
    embed.add_field(
        name="name : " + str(user),
        value=f"created at {user.created_at}\n",
        inline=False
    )
    await ctx.send(embed=embed)


@admin_command.group(name="search", aliases=["s"])
async def admin_search(ctx, *, args):
    cannot_find = True
    embed = discord.Embed(title="Search", description=f"search for : {args}")
    try:
        for guild in app.guilds:
            if args == guild.name:
                await admin_fetch_guild(ctx, guild.id)
                cannot_find = False
                break
    except discord.Forbidden:
        embed.add_field(name="Forbidden", value="Cannot fetch the guild.")
        await ctx.send(embed=embed)
    if cannot_find:
        try:
            for user in app.users:
                if args == user.name or args == user.display_name:
                    await admin_fetch_user(ctx, user.id)
                    cannot_find = False
                    break
        except discord.Forbidden:
            embed.add_field(name="Forbidden", value="Cannot fetch the user.")
            await ctx.send(embed=embed)
        if cannot_find:
            embed.add_field(name="NotFound", value="Cannot find any component.")
            await ctx.send(embed=embed)


@admin_command.command(name="dumpdb", aliases=["exportdb"])
async def admin_dump_db(ctx, *args):
    # 1. 특정 유저를 멘션한 경우: 단일 유저 DB 조회
    if ctx.message.mentions:
        target = ctx.message.mentions[0]
        find, user_data = await app.db.find_data(target.id)
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

    query_str = " ".join(args).strip()
    query_lower = query_str.lower()

    # 전체 테이블 목록 확인
    valid_tables = await app.db.get_tables()

    # 2. 테이블 목록 조회 요청인 경우
    if query_lower in ['tables', 'table', '테이블', '테이블목록', 'list']:
        embed = discord.Embed(
            title="🗄️ 데이터베이스 테이블 목록",
            description=f"현재 데이터베이스에 존재하는 테이블 목록입니다 ({len(valid_tables)}개).",
            color=0x3498db
        )
        for t in valid_tables:
            try:
                cols, rows = await app.db.dump_table(t)
                embed.add_field(
                    name=f"📋 {t}",
                    value=f"컬럼: `{', '.join(cols)}`\n레코드 수: `{len(rows):,}개`",
                    inline=False
                )
            except Exception:
                embed.add_field(name=f"📋 {t}", value="조회 불가", inline=False)
        embed.set_footer(text="특정 테이블을 조회하려면 '%admin dumbdb from <테이블명>'을 입력하세요.")
        await ctx.send(embed=embed)
        return

    # 3. 출력 모드 플래그 파싱
    file_only = any(f in query_lower.split() for f in ['파일', 'file', '-f'])
    chat_only = any(f in query_lower.split() for f in ['채팅', 'chat', '-c', '출력'])

    # 4. SQL 스타일 테이블명 추출 (예: from <table_name>, table=<table_name>, 직접 이름 등)
    target_table = None
    m_from = re.search(r'(?:from|table)\s+([a-zA-Z0-9_]+)', query_str, re.IGNORECASE)
    if m_from:
        target_table = m_from.group(1).lower()
    else:
        m_eq = re.search(r'(?:table|t)=([a-zA-Z0-9_]+)', query_str, re.IGNORECASE)
        if m_eq:
            target_table = m_eq.group(1).lower()
        else:
            for arg in args:
                if arg.lower() in valid_tables:
                    target_table = arg.lower()
                    break

    if not target_table:
        target_table = 'user_data'

    if target_table not in valid_tables:
        await ctx.send(
            f":x: `{target_table}` 테이블이 존재하지 않습니다.\n"
            f"사용 가능한 테이블: {', '.join(f'`{t}`' for t in valid_tables)}"
        )
        return

    # 5. LIMIT 파싱 (예: limit 10, limit=10)
    limit = None
    m_limit = re.search(r'(?:limit)\s+(\d+)', query_str, re.IGNORECASE)
    if not m_limit:
        m_limit = re.search(r'(?:limit)=(\d+)', query_str, re.IGNORECASE)
    if m_limit:
        limit = int(m_limit.group(1))

    # 6. 테이블 데이터 조회
    try:
        columns, rows = await app.db.dump_table(target_table, limit=limit)
    except Exception as e:
        await ctx.send(f":x: 테이블 조회 중 오류가 발생했습니다: {e}")
        return

    if not rows:
        await ctx.send(f":warning: `{target_table}` 테이블에 데이터가 없습니다.")
        return

    # 7. 텍스트 파일 포맷팅 생성 (표 형태)
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    col_widths = [max(len(str(col)), 8) for col in columns]
    for row in rows:
        for idx, val in enumerate(row):
            col_widths[idx] = min(max(col_widths[idx], len(str(val if val is not None else "-"))), 40)

    header_line = " | ".join(f"{columns[i]:<{col_widths[i]}}" for i in range(len(columns)))
    sep_line = "-" * len(header_line)

    limit_suffix = f" (LIMIT {limit})" if limit else ""
    lines = [
        "=" * len(header_line),
        f"[ {app.name} Database Export: {target_table} ]",
        f"추출 일시: {now_str} (KST)",
        f"조회 레코드: {len(rows)}개{limit_suffix}",
        "=" * len(header_line),
        header_line,
        sep_line
    ]

    for row in rows:
        row_str = " | ".join(
            f"{str(row[i] if row[i] is not None else '-'):<{col_widths[i]}}"
            for i in range(len(row))
        )
        lines.append(row_str)

    lines.append("=" * len(header_line))
    full_text = "\n".join(lines)

    file_buffer = io.BytesIO(full_text.encode('utf-8'))
    file_name = f"db_{target_table}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    discord_file = discord.File(fp=file_buffer, filename=file_name)

    if file_only:
        await ctx.send(
            content=f"📁 **`{target_table}` 테이블 내보내기 완료** (총 `{len(rows)}`개)",
            file=discord_file
        )
        return

    # 8. 채팅 출력 (임베드 요약)
    embed = discord.Embed(
        title=f"📊 데이터베이스 조회: `{target_table}`",
        description=f"조회된 레코드: **{len(rows)}**개{limit_suffix}",
        color=0x3498db
    )

    preview_limit = min(10, len(rows))
    preview_text_list = []
    for i, row in enumerate(rows[:preview_limit]):
        if target_table == "user_data":
            uid = row[0]
            user = app.get_user(uid)
            if user:
                name_str = user.name
            else:
                member = ctx.guild.get_member(uid) if ctx.guild else None
                name_str = member.display_name if member else f"<@{uid}>"

            coins_str = f"{row[1]:,}" if len(row) > 1 and row[1] is not None else "0"
            luck_str = f"{row[2]:,}" if len(row) > 2 and row[2] is not None else "0"
            ability_str = f" / ✨ `{row[3]}`" if len(row) > 3 and row[3] else ""
            preview_text_list.append(
                f"**{i+1}.** {name_str} (`{uid}`): 🪙 **{coins_str}** | 🍀 **{luck_str}**{ability_str}"
            )
        elif target_table == "daily_rewards":
            uid = row[0]
            rtype = row[1] if len(row) > 1 else "-"
            rdate = row[2] if len(row) > 2 else "-"
            preview_text_list.append(
                f"**{i+1}.** <@{uid}> (`{uid}`) | 유형: `{rtype}` | 수령일: `{rdate}`"
            )
        else:
            row_summary = " | ".join(f"`{columns[j]}`: {row[j]}" for j in range(min(len(columns), 3)))
            preview_text_list.append(f"**{i+1}.** {row_summary}")

    embed.add_field(
        name=f"상위 목록 ({preview_limit}/{len(rows)})",
        value="\n".join(preview_text_list) if preview_text_list else "데이터 없음",
        inline=False
    )

    if len(rows) > preview_limit and chat_only:
        embed.set_footer(text=f"전체 목록을 파일로 받으려면 '%admin dumbdb from {target_table} 파일'을 입력하세요.")
    else:
        embed.set_footer(text="상세 전체 데이터는 첨부된 텍스트 파일을 확인하세요.")

    if chat_only:
        await ctx.send(embed=embed)
    else:
        await ctx.send(embed=embed, file=discord_file)


@admin_command.group(name="help", aliases=["command", "cmd", "?"])
async def admin_help(ctx):
    description = ""
    for cmd in admin_command.commands:
        description += f"{cmd.name}\n"
        if isinstance(cmd, commands.Group):
            for sub_cmd in cmd.commands:
                description += f"+{sub_cmd.name}\n"
    embed = discord.Embed(
        title="Commands",
        description=description
    )
    await ctx.send(embed=embed)


@app.event
async def on_command_error(ctx, error):
    original_error = getattr(error, 'original', error)
    if isinstance(error, InsufficientTokensError) or isinstance(original_error, InsufficientTokensError):
        err = error if isinstance(error, InsufficientTokensError) else original_error
        await ctx.send(f":no_entry: 토큰이 부족합니다. (필요: {err.cost} :coin: / 보유: {err.current} :coin:)")
    elif isinstance(error, UserNotRegisteredError) or isinstance(original_error, UserNotRegisteredError):
        await ctx.send(":no_entry: 등록되지 않은 사용자입니다. `%등록` 명령어로 먼저 등록해주세요.")
    elif isinstance(error, NotInVoiceChannelError) or isinstance(original_error, NotInVoiceChannelError):
        await ctx.send(":no_entry: 먼저 음성 채널에 입장해 주세요.")
    elif isinstance(error, commands.CommandNotFound):
        return
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(":no_entry_sign: 값이 없습니다.")
    elif isinstance(error, commands.BadArgument):
        await ctx.send(":no_entry_sign: 값이 잘못되었습니다.")
    elif isinstance(error, commands.MissingPermissions):
        await ctx.send(":no_entry: 이 명령을 실행하실 권한이 없습니다.")
    elif isinstance(error, commands.NotOwner):
        await ctx.send(":no_entry: 이 명령을 실행하실 권한이 없습니다.")
    elif isinstance(error, commands.MissingRole):
        await ctx.send(f":no_entry: 이 명령을 실행하려면 '{error.missing_role}' 역할이 필요합니다.")
    elif isinstance(error, commands.CheckAnyFailure):
        for e in error.errors:
            if isinstance(e, commands.MissingPermissions):
                await ctx.send(":no_entry: 이 명령을 실행하실 권한이 없습니다.")
                break
            elif isinstance(e, commands.MissingRole):
                await ctx.send(f":no_entry: 이 명령을 실행하려면 '{e.missing_role}' 역할이 필요합니다.")
                break
    elif isinstance(error, commands.BotMissingPermissions) or isinstance(error, commands.BotMissingRole):
        await ctx.send(":no_entry: 봇이 명령을 실행할 권한이 부족합니다.")
    elif isinstance(error, commands.CommandOnCooldown):
        await ctx.send(" :stopwatch: 쿨타임 중인 명령어입니다. (남은 쿨타임: {:0.1f}초)".format(error.retry_after))


if __name__ == '__main__':
    token = os.environ.get("TOKEN")
    assert token is not None, "TOKEN environment variable is not set"
    app.run(token)
