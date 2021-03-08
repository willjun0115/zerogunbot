import asyncio
import discord
from discord.ext import commands
from discord.utils import get
import os

prefix = '%'
app = commands.Bot(command_prefix=prefix)

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
    await app.process_commands(message)
    if message.author.bot:
        return None


@commands.has_permissions(administrator=True)
@app.command(name="load")
async def load_commands(ctx, extension):
    app.load_extension(f"Cogs.{extension}")
    await ctx.send(f":white_check_mark: {extension}을(를) 로드했습니다.")


@commands.has_permissions(administrator=True)
@app.command(name="unload")
async def unload_commands(ctx, extension):
    app.unload_extension(f"Cogs.{extension}")
    await ctx.send(f":white_check_mark: {extension}을(를) 언로드했습니다.")


@commands.has_permissions(administrator=True)
@app.command(name="reload")
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

@app.command(name='prefix', help="접두사를 변경합니다."
                                        "\n('매니저' 필요)", usage="%prefix ~", pass_context=True)
async def set_prefix(ctx, args):
    if get(ctx.guild.roles, name='매니저') in ctx.author.roles:
        app.prefix = str(args)
        await ctx.send("접두사를 " + str(args) + "로 변경했습니다.")
    else:
        await ctx.send(" :no_entry: 이 명령을 실행하실 권한이 없습니다.")


app.remove_command("help")
app.run(token)