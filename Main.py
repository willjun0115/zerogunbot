import asyncio
import discord
from discord.ext import commands
from discord.utils import get
import os
import ctypes
import ctypes.util

prefix = '%'
intents = discord.Intents.all()
app = commands.Bot(
    command_prefix=commands.when_mentioned_or(prefix),
    help_command=None,
    strip_after_prefix=True,
    intents=intents
)
app.global_guild_id = 943244634602213396
app.prefix = prefix
app.role_lst = [
    ("임시차단", 4000),
    ("창씨개명", 2000),
    ("강제 이동", 1000),
    ("침묵", 750),
    ("언론 통제", 500),
    ("DJ", 250),
    ("이모티콘 관리", 100),
]
app.shop = {
    "닉변": 200,
    "행운": 10,
    "수은": 30,
}

token = os.environ.get("TOKEN")

for filename in os.listdir("Cogs"):
    if filename.endswith(".py"):
        app.load_extension(f"Cogs.{filename[:-3]}")


@app.event
async def on_ready():
    await app.change_presence(status=discord.Status.offline)
    game = discord.Game("시작하는 중...")
    await app.change_presence(status=discord.Status.online, activity=game)
    while True:
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
        await channel.send("새 멤버가 등장했습니다!\n0군 인증서를 발급받으려면 '%0군인증'을 진행해주세요.")


async def find_id(ctx, selector, id):
    db_channel = get(ctx.guild.text_channels, name="db")
    find = None
    async for message in db_channel.history(limit=100):
        if message.content.startswith(selector + str(id)) is True:
            find = message
            break
    return find


async def find_global_id(ctx, selector, id):
    global_guild = app.get_guild(app.global_guild_id)
    db_channel = get(global_guild.text_channels, name="gdb")
    find = None
    async for message in db_channel.history(limit=500):
        if message.content.startswith(selector + str(id)) is True:
            find = message
            break
    return find


async def setup_database(ctx):
    db = get(ctx.guild.text_channels, name="db")
    bot_perms = discord.PermissionOverwrite(
        read_messages=True, read_message_history=True, send_messages=True, manage_messages=True
    )
    overwrites = {
        ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False, send_messages=False),
        app.user: bot_perms
    }
    if db is None:
        await ctx.guild.create_text_channel("db", topic="0군봇 데이터베이스 채널입니다. 절대 수정하거나 삭제하지 말아주세요."
                                                        "\n또한, 해당 채널에 봇이 보내는 채팅 이외의 불필요한 메시지 전송은 지양해주세요.",
                                            overwrites=overwrites)
        return "local database channel has been created."
    else:
        if db.overwrites_for(app.user) != bot_perms:
            await db.set_permissions(app.user, overwrite=bot_perms)
            return "database overwrites update."
        else:
            return None

app.find_id = find_id
app.find_global_id = find_global_id
app.setup_database = setup_database


@commands.is_owner()
@app.group(name="admin", aliases=["%"])
async def admin_command(ctx):
    return


@admin_command.group(name="load", aliases=["l"])
async def load_command(ctx, extension):
    app.load_extension(f"Cogs.{extension}")
    await ctx.send(f":white_check_mark: {extension}을(를) 로드했습니다.")


@admin_command.group(name="unload", aliases=["ul"])
async def unload_command(ctx, extension):
    app.unload_extension(f"Cogs.{extension}")
    await ctx.send(f":white_check_mark: {extension}을(를) 언로드했습니다.")


@admin_command.group(name="reload", aliases=["rl"])
async def reload_command(ctx, extension=None):
    if extension is None:
        for file_name in os.listdir("Cogs"):
            if file_name.endswith(".py"):
                app.unload_extension(f"Cogs.{file_name[:-3]}")
                app.load_extension(f"Cogs.{file_name[:-3]}")
                await ctx.send(":white_check_mark: 명령어를 다시 불러왔습니다.")
    else:
        app.unload_extension(f"Cogs.{extension}")
        app.load_extension(f"Cogs.{extension}")
        await ctx.send(f":white_check_mark: {extension}을(를) 다시 불러왔습니다.")


@admin_command.group(name="status", aliases=["stat"])
async def admin_status(ctx):
    embed = discord.Embed(
        title="Status",
        description=
        f"prefix : {app.prefix}\n"
        f"client_name : {str(app.user)}\n"
        f"client_id : {app.user.id}\n"
        f"guilds_number : {len(app.guilds)}\n"
        f"users_number : {len(app.users)}\n"
        f"created_at : {app.user.created_at}"
    )
    await ctx.send(embed=embed)


@admin_status.group(name="detail")
async def admin_status_detail(ctx):
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


@admin_command.group(name="fetch", aliases=["find", "get"], pass_context=True)
async def admin_fetch(ctx):
    return


@admin_fetch.group(name="guild", aliases=["server"], pass_context=True)
async def admin_fetch_guild(ctx, id=None):
    if id is None:
        id = ctx.guild.id
    else:
        id = int(id)
    embed = discord.Embed(title="Fetch Guild", description=f"get guild by id : {id}")
    try:
        guild = app.get_guild(id)
    except discord.NotFound:
        embed.add_field(name="NotFound", value="No guild was found.")
        await ctx.send(embed=embed)
    except discord.Forbidden:
        embed.add_field(name="Forbidden", value="Cannot fetch the guild.")
        await ctx.send(embed=embed)
    else:
        embed.set_thumbnail(url=guild.icon_url)
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
                name=str(member),
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
                name=category.name,
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


@admin_fetch.group(name="user", aliases=["member"], pass_context=True)
async def admin_fetch_user(ctx, id):
    id = int(id)
    embed = discord.Embed(title="Fetch", description=f"fetch user by id : {id}")
    try:
        user = await app.fetch_user(id)
    except discord.NotFound:
        embed.add_field(name="NotFound", value="No user was found.")
    except discord.Forbidden:
        embed.add_field(name="Forbidden", value="Cannot fetch the user.")
    else:
        embed.add_field(
            name="name : " + str(user),
            value=f"created at {user.created_at}\n",
            inline=False
        )
    await ctx.send(embed=embed)


@admin_command.group(name="help", aliases=["command", "cmd", "?"])
async def admin_help(ctx):
    description = ""
    for cmd in admin_command.commands:
        description += f"{cmd.name}\n"
        if cmd.commands is not None:
            for sub_cmd in cmd.commands:
                description += f"> {sub_cmd.name}\n"
    embed = discord.Embed(
        title="Commands",
        description=description
    )
    await ctx.send(embed=embed)


@app.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(":no_entry_sign: 값이 없습니다.")
    elif isinstance(error, commands.BadArgument):
        await ctx.send(":no_entry_sign: 값이 잘못되었습니다.")
    elif isinstance(error, commands.MissingPermissions):
        await ctx.send(":no_entry: 이 명령을 실행하실 권한이 없습니다.")
    elif isinstance(error, commands.NotOwner):
        await ctx.send(":no_entry: 봇의 주인이 아닙니다.")
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


app.run(token)
