import asyncio
import discord
from discord.ext import commands
from discord.utils import get
import os
import ctypes
import ctypes.util

prefix = '%'
app = commands.Bot(command_prefix=prefix, help_command=None)
app.prefix = prefix
app.gacha_ch = 811849095031029762
app.log_ch = 874970985307201546
app.role_lst = [
    ("창씨개명", 0.1, 5000),
    ("강제 이동", 0.5, 2500),
    ("침묵", 1.0, 1500),
    ("언론 통제", 1.5, 1000),
    ("DJ", 3.0, 750),
    ("이모티콘 관리", 5.0, 500),
]
app.shop = {
    "닉변": 1000,
    "행운": 100
}

token = "ODExMDc3MzI4MDk5NjA2NTMx.YCs8oA.3Upak_WkaF8pSPTsUR0F_BOJ8Xc"

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
        await ctx.send(" :no_entry: 이 명령을 실행하실 권한이 없습니다.")


app.run(token)