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


@app.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(":no_entry_sign: 값이 없습니다.")
    elif isinstance(error, commands.BadArgument):
        await ctx.send(":x: 값이 잘못되었습니다.")
    elif isinstance(error, commands.MissingPermissions):
        await ctx.send(":no_entry: 이 명령을 실행하실 권한이 없습니다.")
    elif isinstance(error, commands.MissingRole):
        await ctx.send(":no_entry: 이 명령을 실행하실 권한이 없습니다.")
    elif isinstance(error, commands.CommandOnCooldown):
        await ctx.send(f" :stopwatch: 쿨타임 중인 명령어입니다. (남은 쿨타임: {int(error.retry_after)}초)")
    elif isinstance(error, commands.ChannelNotFound):
        await ctx.send(":no_entry: 이 채널에서 실행할 수 없는 명령어입니다.")


app.run(token)