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
@app.group(
    name="admin"
)
async def admin_command(ctx):
    return


@admin_command.group(
    name="command", aliases=["cmd"]
)
async def admin_help(ctx):
    description = ""
    for cmd in admin_command.commands:
        if len(cmd.aliases) > 0:
            description += f"{cmd.name}({cmd.aliases[0]})\n"
        else:
            description += f"{cmd.name}\n"
    embed = discord.Embed(
        title="Commands",
        description=description
    )
    await ctx.send(embed=embed)


@admin_command.group(
    name="status", aliases=["stat"]
)
async def bot_status(ctx):
    appinfo = await app.application_info()
    embed = discord.Embed(
        title="Status",
        description=
        f"prefix : {app.prefix}\n"
        f"app_name : {appinfo.name}\n"
        f"client_name : {app.user.name}#{app.user.discriminator}\n"
        f"client_id : {app.user.id}\n"
        f"guilds_number : {len(app.guilds)}\n"
        f"users_number : {len(app.users)}\n"
        f"created_at : {app.user.created_at}\n"
        f"locale : {app.user.locale}\n"
        f"owner_name : {appinfo.owner.name}\n"
        f"owner_id : {appinfo.owner.id}"
    )
    await ctx.send(embed=embed)


@admin_command.group(
    name="fetch", aliases=["find"], pass_context=True
)
async def bot_fetch(ctx, id, fetch_type=None):
    result_type = None
    embed = discord.Embed(
        title="Fetch",
        description=f"fetch result by id : {id} (type: {fetch_type})")
    if result_type is None or fetch_type == "guild":
        try:
            fetch_result = app.get_guild(id)
            result_type = "guild"
            embed.add_field(name=result_type, value=f"name : {fetch_result.name}")
        except discord.NotFound:
            result_type = None
        except discord.Forbidden:
            result_type = "Forbidden"
    if result_type is None or fetch_type == "channel":
        try:
            fetch_result = app.get_channel(id)
            result_type = "channel"
            embed.add_field(name=result_type, value=f"name : {fetch_result.name}")
        except discord.NotFound:
            result_type = None
        except discord.Forbidden:
            result_type = "Forbidden"
    if result_type is None or fetch_type == "user":
        try:
            fetch_result = app.get_user(id)
            result_type = "user"
            embed.add_field(name=result_type, value=f"name : {fetch_result.name}#{fetch_result.discriminator}")
        except discord.NotFound:
            result_type = None
        except discord.Forbidden:
            result_type = "Forbidden"
    if result_type is None or fetch_type == "emoji":
        try:
            fetch_result = app.get_channel(id)
            result_type = "emoji"
            embed.add_field(name=result_type, value=f"name : {fetch_result.name}")
        except discord.NotFound:
            result_type = None
        except discord.Forbidden:
            result_type = "Forbidden"
    if result_type is None or fetch_type == "message":
        try:
            fetch_result = await ctx.fetch_message(id)
            result_type = "message"
            embed.add_field(name=result_type, value=f"content : {fetch_result.content}\n"
                                                    f"created_at : {fetch_result.created_at}")
        except discord.NotFound:
            result_type = None
        except discord.Forbidden:
            result_type = "Forbidden"
    if result_type is None:
        await ctx.send("No object was found")
    elif result_type == "Forbidden":
        await ctx.send("Denied to access")
    else:
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
