import asyncio
import discord
from discord.ext import commands
from discord.utils import get
import os
import ctypes
import ctypes.util

prefix = '%'
app = commands.Bot(command_prefix=commands.when_mentioned_or(prefix), help_command=None, strip_after_prefix=True)
app.prefix = prefix
app.id = 811077328099606531
app.gacha_ch = 811849095031029762
app.log_ch = 874970985307201546
app.role_lst = [
    ("임시차단", 0.1, 4000),
    ("창씨개명", 0.5, 2000),
    ("강제 이동", 1.0, 1000),
    ("침묵", 1.5, 750),
    ("언론 통제", 3.0, 500),
    ("DJ", 5.0, 250),
    ("이모티콘 관리", 7.5, 100),
]
app.shop = {
    "닉변": 200,
    "행운": 50,
    "수은": 30,
    "유료복권": 10,
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


@commands.has_permissions(administrator=True)
@app.command(name="로드", aliases=["load"])
async def load_commands(ctx, extension):
    app.load_extension(f"Cogs.{extension}")
    await ctx.send(f":white_check_mark: {extension}을(를) 로드했습니다.")


@commands.has_permissions(administrator=True)
@app.command(name="언로드", aliases=["unload"])
async def unload_commands(ctx, extension):
    app.unload_extension(f"Cogs.{extension}")
    await ctx.send(f":white_check_mark: {extension}을(를) 언로드했습니다.")


@commands.has_permissions(administrator=True)
@app.command(name="리로드", aliases=["reload"])
async def reload_commands(ctx, extension=None):
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


@commands.is_owner()
@app.group(name="admin", aliases=["%"])
async def admin_command(ctx):
    return


@admin_command.group(name="status", aliases=["stat"])
async def admin_status(ctx):
    appinfo = await app.application_info()
    embed = discord.Embed(
        title="Status",
        description=
        f"prefix : {app.prefix}\n"
        f"app_name : {appinfo.name}\n"
        f"client_name : {str(app.user)}\n"
        f"client_id : {app.user.id}\n"
        f"guilds_number : {len(app.guilds)}\n"
        f"users_number : {len(app.users)}\n"
        f"created_at : {app.user.created_at}\n"
        f"owner_name : {str(appinfo.owner)}\n"
        f"owner_id : {appinfo.owner.id}"
    )
    await ctx.send(embed=embed)


@admin_status.group(name="detail")
async def admin_status_detail(ctx):
    appinfo = await app.application_info()
    embed = discord.Embed(
        title="Detail",
        description=
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
async def admin_fetch_guild(ctx, id):
    id = int(id)
    embed = discord.Embed(title="Fetch", description=f"fetch guild by id : {id}")
    try:
        guild = await app.fetch_guild(id)
    except discord.NotFound:
        embed.add_field(name="NotFound", value="No guild was found.")
    except discord.Forbidden:
        embed.add_field(name="Forbidden", value="Cannot fetch the guild.")
    else:
        embed.add_field(
            name="name : " + guild.name,
            value=f"created at {guild.created_at}\n"
                  f"region : {guild.region}\n"
                  f"owner : {str(guild.owner)}\n"
                  f"members_number : {len(guild.members)}",
            inline=False
        )
        embed.add_field(
            name="members",
            value="\n".join([str(m) for m in guild.members]),
            inline=False
        )
        embed.add_field(
            name="channels", value="\n".join([c.name for c in guild.channels if c not in guild.voice_channels]),
            inline=False
        )
        embed.add_field(
            name=":sound: voice channels",
            value="\n".join([c.name for c in guild.voice_channels]),
            inline=False
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


@admin_command.group(name="command", aliases=["cmd", "help"])
async def admin_help(ctx):
    description = ""
    for cmd in admin_command.commands:
        description += f"({cmd.full_parent_name}) {cmd.name}\n"
        if cmd.commands is not None:
            for sub_cmd in cmd.commands:
                description += f"({cmd.full_parent_name}) {sub_cmd.name}\n"
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
        await ctx.send(f" :stopwatch: 쿨타임 중인 명령어입니다. (남은 쿨타임: {int(error.retry_after)}초)")


app.run(token)
