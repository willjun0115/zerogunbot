import random
import discord
from discord.ext import commands
from discord.utils import get
import os
import datetime
from dotenv import load_dotenv

prefix = '%'
intents = discord.Intents.all()
load_dotenv()

import typing
from Database import Database
from Utils import InsufficientTokensError, UserNotRegisteredError

class ZeroGunBot(commands.Bot):
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
app.db = Database()
app.global_guild_id = 943244634602213396
app.prefix = prefix

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


app.encrypt = encrypt
app.decrypt = decrypt
app.find_id = find_id
app.find_data = find_data
app.update_data = update_data
app.collect_data = collect_data
app.setup_database = setup_database


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
