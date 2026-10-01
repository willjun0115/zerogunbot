import discord
from discord.ext import commands
from discord.utils import get
import asyncio
import io
import datetime
import re
import operator
import os
import subprocess
import shutil
import platform
import time
try:
    import psutil
except ImportError:
    psutil = None


class Tool(commands.Cog, name="도구", description="다양한 기능의 명령어 카테고리입니다."):

    def __init__(self, app):
        self.app = app
        self.chat_decryption.help = f'{self.app.name}이 암호화한 암호를 입력받아 복호화해 출력합니다.'


    @commands.command(
        name="도움말", aliases=["help", "?"],
        help="도움말을 불러옵니다.\n'%사용법'에서 명령어 사용법 참조.", usage="* (str(*command*))"
    )
    async def help_command(self, ctx, func=None):
        if func is None:
            embed = discord.Embed(
                title="도움말",
                description=f"접두사는 {self.app.prefix} 입니다.\n"
                            "%*명령어*로 더 자세한 정보를 확인하세요."
            )
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
        help="DB를 편집합니다. (관리자 권한)", usage="* str(*selector*) @*member* int()",
        hidden=True
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

    @commands.command(
        name='암호화', aliases=["encrypt", "enc"],
        help='입력받은 문자열을 암호화해 출력합니다.', usage='* int([0, 999]) str()', enabled=False
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
        help='봇이 암호화한 암호를 입력받아 복호화해 출력합니다.', usage='* int([0, 999]) str(*code*)', enabled=False
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

    @commands.command(
        name="등록", aliases=["register", "가입"],
        help="정보 수집에 동의하고 DB에 사용자 정보를 등록합니다.",
        usage="*"
    )
    async def register(self, ctx):
        await prompt_user_registration(self.app, ctx)

    @commands.command(
        name="등록해제", aliases=["unregister", "탈퇴", "삭제"],
        help="DB에서 사용자 기록을 영구적으로 삭제합니다. (삭제 시 복구 불가)",
        usage="*"
    )
    async def unregister(self, ctx):
        prefix = getattr(self.app, 'prefix', '%')
        registered = await self.app.db.is_registered(ctx.author.id)
        if not registered:
            embed = discord.Embed(
                title="ℹ️ 미등록 사용자",
                description=f"{ctx.author.mention} 님은 현재 DB에 등록되어 있지 않습니다.\n"
                            f"등록을 원하시면 `{prefix}등록` 명령어를 이용해주세요.",
                color=0xe67e22
            )
            await ctx.send(embed=embed)
            return

        embed = discord.Embed(
            title="⚠️ 데이터 삭제 및 등록 해제 안내",
            description=f"{ctx.author.mention} 님, 정말로 등록을 해제하시겠습니까?\n\n"
                        f"🚨 **주의사항 (되돌릴 수 없음)**\n"
                        f"• **DB에서 삭제하면 정보를 다시는 되돌릴 수 없습니다.**\n"
                        f"• 보유 중인 **토큰(:coin:)** 등 모든 데이터가 영구적으로 삭제됩니다.\n"
                        f"• 삭제 후 재등록하더라도 이전 데이터는 복구되지 않으며 초기 상태(0 코인)로 시작됩니다.\n\n"
                        f"정말로 삭제를 진행하시려면 아래의 ✅, 취소하시려면 ❌ 아이콘을 눌러주세요.",
            color=0xe74c3c
        )
        msg = await ctx.send(embed=embed)
        await msg.add_reaction("✅")
        await msg.add_reaction("❌")

        def check(reaction, user):
            return user.id == ctx.author.id and str(reaction.emoji) in ["✅", "❌"] and reaction.message.id == msg.id

        try:
            reaction, user = await self.app.wait_for("reaction_add", check=check, timeout=30.0)
        except asyncio.TimeoutError:
            try:
                await msg.clear_reactions()
            except Exception:
                pass
            cancel_embed = discord.Embed(
                title="⏰ 시간 초과",
                description="시간이 초과되어 등록 해제가 취소되었습니다. 사용자 데이터는 안전하게 유지됩니다.",
                color=0x95a5a6
            )
            await msg.edit(embed=cancel_embed)
        else:
            try:
                await msg.clear_reactions()
            except Exception:
                pass

            if str(reaction.emoji) == "✅":
                deleted = await self.app.db.delete_user(ctx.author.id)
                if deleted:
                    done_embed = discord.Embed(
                        title="🗑️ 등록 해제 완료",
                        description=f"{ctx.author.mention} 님의 모든 사용자 정보가 DB에서 영구적으로 삭제되었습니다.\n"
                                    f"**DB에서 삭제된 정보는 되돌릴 수 없습니다.**\n\n"
                                    f"언제든지 다시 이용을 원하시면 `{prefix}등록` 명령어를 통해 새로 등록하실 수 있습니다.",
                        color=0x95a5a6
                    )
                    await msg.edit(embed=done_embed)
                else:
                    await msg.edit(content="이미 삭제되었거나 처리 중 오류가 발생했습니다.")
            else:
                cancel_embed = discord.Embed(
                    title="🛑 등록 해제 취소",
                    description="등록 해제를 취소했습니다. 사용자 데이터가 그대로 보존됩니다.",
                    color=0x3498db
                )
                await msg.edit(embed=cancel_embed)

    @commands.command(
        name="토큰", aliases=["코인", "token", "coin", "$"],
        help="자신의 토큰 수를 확인합니다.\nDB에 등록되지 않은 경우 %등록 명령어를 호출해 등록을 진행합니다.",
        usage="*"
    )
    async def check_token(self, ctx):
        find, data = await self.app.find_data("db", ctx.author.id)
        if find is not None:
            coin = data.get('$')
            await ctx.send(str(coin) + ' :coin:')
        else:
            await prompt_user_registration(self.app, ctx)

    @commands.cooldown(1, 60., commands.BucketType.channel)
    @commands.command(
        name="토큰순위", aliases=["순위", "rank"],
        help="현재 토큰 보유 순위를 조회합니다. (쿨타임 1분)", usage="*"
    )
    async def token_rank(self, ctx):
        global_guild = self.app.get_guild(self.app.global_guild_id)
        text = "현재 토큰 순위 (유저명/토큰/점유율)"
        msg = await ctx.send("DB를 조회 중입니다... :mag:")
        members = {}
        data_dict = await self.app.collect_data()
        for member_id in data_dict.keys():
            data = data_dict.get(member_id)
            try:
                member = await ctx.guild.fetch_member(member_id)
            except Exception:
                members[member_id] = data.get('$')
            else:
                members[member] = data.get('$')
        if len(members) == 0:
            embed = discord.Embed(title="<토큰 랭킹>", description=text)
            embed.add_field(name="해당 시즌에 참여한 유저가 없어요", value="ㅜ.ㅜ", inline=True)
            await msg.edit(content=None, embed=embed)
            return

        coin_mass = sum(members.values())
        members = sorted(members.items(), key=operator.itemgetter(1), reverse=True)
        embed = discord.Embed(title="<토큰 랭킹>", description=text)
        winner = members[0]
        names = ""
        coins = ""
        shares = ""
        n = 1
        if len(members) <= 1:
            names = "-"
            coins = "-"
            shares = "-"
        else:
            for md in members[1:]:
                n += 1
                if n == 2:
                    names += f":second_place: {md[0]}\n"
                elif n == 3:
                    names += f":third_place: {md[0]}\n"
                else:
                    names += f"{n}. {md[0]}\n"
                coins += f"{md[1]}\n"
                shares += f"({100 * md[1] / coin_mass:0.2f}%)\n"
        embed.add_field(name=f":first_place: " + str(winner[0]) + " :crown:", value=names, inline=True)
        embed.add_field(name=f"{winner[1]} :coin:", value=coins, inline=True)
        embed.add_field(name=f"({100 * winner[1] / coin_mass:0.2f}%)", value=shares, inline=True)
        await msg.edit(content=None, embed=embed)

    @commands.command(
        name="행운", aliases=["luck"],
        help="자신의 행운 중첩량을 확인합니다.",
        usage="*"
    )
    async def luck(self, ctx):
        find, data = await self.app.find_data("db", ctx.author.id)
        luck = data.get('%')
        if find is None:
            await ctx.send(f"DB에 등록되지 않은 사용자입니다.\n'{self.app.prefix}등록' 명령어를 통해 정보 수집 동의 후 등록을 진행해주세요.")
            return
        elif luck is None:
            luck = 0
        await ctx.send(str(luck) + ' :four_leaf_clover:')

    @commands.check_any(commands.has_permissions(administrator=True), commands.is_owner())
    @commands.cooldown(1, 10.0, commands.BucketType.channel)
    @commands.command(
        name="서버상태", aliases=["서버정보", "status", "serverinfo", "시스템상태", "호스트상태"],
        help="봇 호스트 서버의 리소스 및 시스템 상태를 확인합니다. (쿨타임: 10초)",
        usage="*"
    )
    async def server_status(self, ctx):
        msg = await ctx.send("🔍 서버 리소스 상태를 측정하는 중입니다...")

        def make_bar(percent: float, length: int = 10) -> str:
            filled = round(length * (max(0.0, min(100.0, percent)) / 100))
            return "█" * filled + "░" * (length - filled)

        # 1. CPU 정보
        cpu_count = os.cpu_count() or 1
        cpu_percent = 0.0
        if psutil:
            try:
                cpu_percent = psutil.cpu_percent(interval=0.5)
            except Exception:
                cpu_percent = 0.0

        # CPU 온도 측정
        cpu_temp = None
        if os.path.exists("/sys/class/thermal/thermal_zone0/temp"):
            try:
                with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
                    cpu_temp = float(f.read().strip()) / 1000.0
            except Exception:
                pass
        if cpu_temp is None and psutil and hasattr(psutil, "sensors_temperatures"):
            try:
                temps = psutil.sensors_temperatures()
                if temps:
                    for name, entries in temps.items():
                        if entries:
                            cpu_temp = entries[0].current
                            break
            except Exception:
                pass
        if cpu_temp is None:
            try:
                res = subprocess.run(
                    ["vcgencmd", "measure_temp"],
                    capture_output=True,
                    text=True,
                    timeout=1
                ).stdout
                if "temp=" in res:
                    cpu_temp = float(res.replace("temp=", "").replace("'C", "").strip())
            except Exception:
                pass

        temp_text = "측정 불가"
        if cpu_temp is not None:
            temp_icon = "🟢" if cpu_temp < 55 else ("🟡" if cpu_temp < 70 else "🔴")
            temp_text = f"{temp_icon} **{cpu_temp:.1f}°C**"

        # 로드 애버리지
        load_avg_str = ""
        if hasattr(os, "getloadavg"):
            try:
                l1, l5, l15 = os.getloadavg()
                load_avg_str = f"\n• 로드 애버리지: `{l1:.2f}`, `{l5:.2f}`, `{l15:.2f}`"
            except Exception:
                pass

        cpu_field_value = (
            f"`{make_bar(cpu_percent)}` **{cpu_percent:.1f}%** ({cpu_count} 코어)\n"
            f"• CPU 온도: {temp_text}{load_avg_str}"
        )

        # 2. RAM (메모리) 정보
        mem_total_gb = 0.0
        mem_used_gb = 0.0
        mem_percent = 0.0
        bot_mem_mb = 0.0

        if psutil:
            try:
                vm = psutil.virtual_memory()
                mem_total_gb = vm.total / (1024 ** 3)
                mem_used_gb = vm.used / (1024 ** 3)
                mem_percent = vm.percent

                proc = psutil.Process()
                bot_mem_mb = proc.memory_info().rss / (1024 ** 2)
            except Exception:
                pass
        elif os.path.exists("/proc/meminfo"):
            try:
                meminfo = {}
                with open("/proc/meminfo", "r") as f:
                    for line in f:
                        parts = line.split(":")
                        if len(parts) == 2:
                            meminfo[parts[0].strip()] = int(parts[1].strip().split()[0])
                t_kb = meminfo.get("MemTotal", 0)
                a_kb = meminfo.get("MemAvailable", meminfo.get("MemFree", 0))
                u_kb = t_kb - a_kb
                mem_total_gb = t_kb / (1024 ** 2)
                mem_used_gb = u_kb / (1024 ** 2)
                mem_percent = (u_kb / t_kb * 100) if t_kb else 0.0
            except Exception:
                pass

        bot_mem_text = f"\n• 봇 점유 메모리: `{bot_mem_mb:.1f} MB`" if bot_mem_mb > 0 else ""
        mem_field_value = (
            f"`{make_bar(mem_percent)}` **{mem_percent:.1f}%**\n"
            f"• 사용량: `{mem_used_gb:.2f} GB` / `{mem_total_gb:.2f} GB`{bot_mem_text}"
        )

        # 3. 스토리지 (디스크)
        disk_path = "/" if os.name != "nt" else "."
        try:
            d_total, d_used, d_free = shutil.disk_usage(disk_path)
            d_total_gb = d_total / (1024 ** 3)
            d_used_gb = d_used / (1024 ** 3)
            d_free_gb = d_free / (1024 ** 3)
            d_percent = (d_used / d_total * 100) if d_total else 0.0
            disk_field_value = (
                f"`{make_bar(d_percent)}` **{d_percent:.1f}%**\n"
                f"• 사용량: `{d_used_gb:.1f} GB` / `{d_total_gb:.1f} GB` (`{d_free_gb:.1f} GB` 여유)"
            )
        except Exception:
            disk_field_value = "디스크 정보를 조회할 수 없습니다."

        # 4. 가동 시간 (Uptime) & 지연시간
        def format_delta(seconds: float) -> str:
            seconds = int(seconds)
            days, rem = divmod(seconds, 86400)
            hours, rem = divmod(rem, 3600)
            mins, secs = divmod(rem, 60)
            parts = []
            if days > 0:
                parts.append(f"{days}일")
            if hours > 0:
                parts.append(f"{hours}시간")
            if mins > 0:
                parts.append(f"{mins}분")
            if not parts or secs > 0:
                parts.append(f"{secs}초")
            return " ".join(parts)

        # 봇 가동 시간
        start_time = getattr(self.app, "start_time", None)
        if start_time:
            bot_uptime_sec = (datetime.datetime.now() - start_time).total_seconds()
            bot_uptime_str = format_delta(bot_uptime_sec)
        else:
            bot_uptime_str = "측정 불가"

        # 시스템 업타임
        sys_uptime_str = None
        if psutil:
            try:
                sys_uptime_str = format_delta(time.time() - psutil.boot_time())
            except Exception:
                pass
        if sys_uptime_str is None and os.path.exists("/proc/uptime"):
            try:
                with open("/proc/uptime", "r") as f:
                    up_sec = float(f.read().split()[0])
                    sys_uptime_str = format_delta(up_sec)
            except Exception:
                pass
        if sys_uptime_str is None:
            sys_uptime_str = "측정 불가"

        ping_ms = round(self.app.latency * 1000)
        ping_icon = "🟢" if ping_ms < 100 else ("🟡" if ping_ms < 200 else "🔴")

        status_field_value = (
            f"• 봇 가동 시간: `{bot_uptime_str}`\n"
            f"• 시스템 업타임: `{sys_uptime_str}`\n"
            f"• 응답 속도 (Ping): {ping_icon} `{ping_ms} ms`"
        )

        # 상태별 임베드 컬러
        if (cpu_temp and cpu_temp >= 75) or cpu_percent >= 90 or mem_percent >= 90:
            embed_color = 0xe74c3c  # 빨강
        elif (cpu_temp and cpu_temp >= 65) or cpu_percent >= 75 or mem_percent >= 75:
            embed_color = 0xf39c12  # 주황
        else:
            embed_color = 0x2ecc71  # 초록

        embed = discord.Embed(
            title=f"🖥️ {self.app.name} 호스트 서버 상태",
            description="호스트 서버(라즈베리파이)의 실시간 하드웨어 및 시스템 리소스 현황입니다.",
            color=embed_color
        )
        embed.add_field(name="🔥 CPU", value=cpu_field_value, inline=False)
        embed.add_field(name="🧠 RAM (메모리)", value=mem_field_value, inline=False)
        embed.add_field(name="💾 스토리지 (디스크)", value=disk_field_value, inline=False)
        embed.add_field(name="⏱️ 가동 시간 & 네트워크", value=status_field_value, inline=False)

        os_str = f"{platform.system()} {platform.release()} ({platform.machine()})"
        py_ver = platform.python_version()
        embed.set_footer(text=f"OS: {os_str} | Python {py_ver}")

        await msg.edit(content=None, embed=embed)


async def prompt_user_registration(app, ctx) -> bool:
    """
    사용자에게 정보 수집에 대한 내용을 고지하고 체크 이모티콘 클릭 시 DB에 등록합니다.
    이미 등록된 경우 %등록해제를 통해 DB에서 삭제할 수 있음을 안내합니다.
    Cogs.Game 등 다른 모듈에서 import하여 사용 가능합니다.
    """
    prefix = getattr(app, 'prefix', '%')
    bot_name = getattr(app, 'name', "0군봇")
    registered = await app.db.is_registered(ctx.author.id)
    if registered:
        embed = discord.Embed(
            title="ℹ️ 이미 등록된 사용자입니다",
            description=f"{ctx.author.mention} 님은 이미 DB에 등록되어 있습니다.\n\n"
                        f"💡 **등록 해제(탈퇴) 안내**\n"
                        f"등록 해제를 원하실 경우 `{prefix}등록해제` 명령어를 통해 언제든지 DB에서 정보를 삭제할 수 있습니다.\n"
                        f"*(주의: 삭제 시 모든 보유 토큰 및 게임 데이터는 영구 삭제되며 복구할 수 없습니다.)*",
            color=0x3498db
        )
        await ctx.send(embed=embed)
        return True

    embed = discord.Embed(
        title=f"📋 {bot_name} 서비스 이용 및 정보 수집 안내",
        description=f"{ctx.author.mention} 님, {bot_name}의 토큰 및 게임 기능을 이용하시려면 아래의 정보 수집 및 이용 동의가 필요합니다.",
        color=0x2ecc71
    )
    embed.add_field(
        name="1. 수집 항목",
        value="• 디스코드 고유 사용자 ID (Discord User ID)",
        inline=False
    )
    embed.add_field(
        name="2. 수집 및 이용 목적",
        value="• 가상 화폐(:coin:) 관리\n• 게임 데이터(행운 수치, 출석 보상 등) 기록 및 랭킹 제공",
        inline=False
    )
    embed.add_field(
        name="3. 보유 및 이용 기간",
        value=f"• 이용자의 `{prefix}등록해제` 요청 시 또는 봇 서비스 종료 시까지 보관 (해제 시 즉시 영구 파기)",
        inline=False
    )
    embed.add_field(
        name="4. 동의 거부 권리 및 안내",
        value="• 정보 수집에 동의하지 않으실 수 있으나, 미동의 시 토큰 및 게임 등 일부 기능 이용이 제한됩니다.\n"
              f"• 등록 후 언제든지 `{prefix}등록해제` 명령어로 저장된 모든 정보를 삭제할 수 있습니다. (삭제 시 복구 불가)",
        inline=False
    )
    embed.set_footer(text="동의하고 등록하시려면 아래의 체크(✅) 이모티콘을 눌러주세요. (제한시간: 60초)")

    msg = await ctx.send(embed=embed)
    await msg.add_reaction("✅")

    def check(reaction, user):
        return user.id == ctx.author.id and str(reaction.emoji) == "✅" and reaction.message.id == msg.id

    try:
        reaction, user = await app.wait_for("reaction_add", check=check, timeout=60.0)
    except asyncio.TimeoutError:
        try:
            await msg.clear_reactions()
        except Exception:
            pass
        timeout_embed = discord.Embed(
            title="⏰ 등록 시간 초과",
            description=f"시간이 초과되어 등록이 취소되었습니다. 다시 시도하시려면 `{prefix}등록`을 입력해주세요.",
            color=0xe74c3c
        )
        await msg.edit(embed=timeout_embed)
        return False
    else:
        # 서버 부스터 여부 확인
        is_booster = False
        if ctx.guild and hasattr(ctx.guild, 'premium_subscribers'):
            if ctx.author in ctx.guild.premium_subscribers:
                is_booster = True

        init_coins = 1000 if is_booster else 0
        init_luck = 10 if is_booster else 0

        await app.db.register_user(ctx.author.id, coins=init_coins, luck=init_luck)

        try:
            await msg.clear_reactions()
        except Exception:
            pass

        booster_text = f"\n✨ **서버 부스터 혜택**: 시작 보너스 🪙 1,000 코인 / 🍀 행운 10 지급 완료!\n" if is_booster else ""
        success_embed = discord.Embed(
            title="🎉 등록 완료",
            description=f"{ctx.author.mention} 님의 정보가 DB에 정상적으로 등록되었습니다!\n"
                        f"이제 {bot_name}의 토큰 및 게임 기능을 마음껏 이용하실 수 있습니다.{booster_text}\n"
                        f"💡 등록을 해제하고 정보를 삭제하려면 언제든지 `{prefix}등록해제` 명령어를 입력하세요.",
            color=0x2ecc71
        )
        await msg.edit(embed=success_embed)
        return True


async def setup(app):
    await app.add_cog(Tool(app))
