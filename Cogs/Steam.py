import discord
from discord.ext import commands
import aiohttp
import asyncio
import os
import re
import html
from datetime import datetime
from typing import Optional, Dict, Any, List

# Steam 온라인 상태 매핑
STATUS_MAP = {
    0: ("⚫ 오프라인", 0x8A8A8A),
    1: ("🟢 온라인", 0x57CBDE),
    2: ("🔴 다른 용무 중", 0xD9534F),
    3: ("🟡 자리 비움", 0xF0AD4E),
    4: ("💤 수면 중", 0x9E9E9E),
    5: ("🤝 거래 원함", 0x5BC0DE),
    6: ("🎮 게임 원함", 0x5CB85C),
}


def get_country_flag(country_code: str) -> str:
    """2자리 국가 코드를 국기 이모지로 변환합니다."""
    if not country_code or len(country_code) != 2:
        return ""
    try:
        flag = "".join(chr(ord(c.upper()) + 127397) for c in country_code)
        return f"{flag} {country_code.upper()}"
    except Exception:
        return country_code.upper()


def format_playtime(minutes: int) -> str:
    """분을 'X시간 Y분' 형식으로 변환합니다."""
    if not minutes:
        return "0분"
    hours = minutes // 60
    rem_minutes = minutes % 60
    if hours > 0 and rem_minutes > 0:
        return f"{hours:,}시간 {rem_minutes}분"
    elif hours > 0:
        return f"{hours:,}시간"
    else:
        return f"{rem_minutes}분"


def clean_html(raw_html: str) -> str:
    """HTML 태그 및 HTML 엔티티를 제거하여 순수 텍스트로 정리합니다."""
    if not raw_html:
        return ""
    text = re.sub(r"<[^>]+>", "", raw_html)
    return html.unescape(text).strip()


class Steam(commands.Cog, name="스팀", description="Steam 프로필, 게임 정보 및 할인 조회 카테고리입니다."):
    def __init__(self, app):
        self.app = app

    def get_api_key(self) -> Optional[str]:
        return os.environ.get("STEAM_API_KEY")

    async def resolve_steam_id(self, session: aiohttp.ClientSession, api_key: str, query: str) -> Optional[str]:
        """
        다양한 형태의 입력(SteamID64, 프로필 URL, 커스텀 URL 식별자)에서 SteamID64를 추출/변환합니다.
        """
        query = query.strip()

        # 1. URL 형태인 경우 파싱
        match_profile = re.search(r"steamcommunity\.com/profiles/(\d{17})", query)
        if match_profile:
            return match_profile.group(1)

        match_id = re.search(r"steamcommunity\.com/id/([a-zA-Z0-9_\-]+)", query)
        if match_id:
            query = match_id.group(1)

        # 2. 17자리 숫자인 경우 바로 SteamID64로 간주
        if re.fullmatch(r"\d{17}", query):
            return query

        # 3. 커스텀 식별자(Vanity URL) -> ResolveVanityURL API 호출
        url = "https://api.steampowered.com/ISteamUser/ResolveVanityURL/v0001/"
        params = {"key": api_key, "vanityurl": query}
        try:
            async with session.get(url, params=params) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    response = data.get("response", {})
                    if response.get("success") == 1:
                        return response.get("steamid")
        except Exception as e:
            print(f"[Steam Cog] Vanity URL 변환 오류: {e}")

        return None

    # ==========================================
    # 메인 그룹 명령어: %스팀
    # ==========================================
    @commands.group(
        name="스팀", aliases=["steam"],
        invoke_without_command=True,
        help="Steam 관련 정보(유저, 게임, 할인)를 조회합니다.\n"
             "사용법: %스팀 [유저|게임|할인] [검색어]",
        usage="* [유저|게임|할인] [검색어]"
    )
    async def steam_group(self, ctx, *, extra: Optional[str] = None):
        """하위 명령어가 지정되지 않았거나 잘못 입력되었을 때 안내 임베드를 전송합니다."""
        embed = discord.Embed(
            title="🎮 Steam 명령어 안내",
            description="Steam 정보를 조회할 수 있는 명령어 목록입니다.\n"
                        "아래의 하위 명령어 중 하나를 선택해 사용해 보세요.",
            color=0x1B2838
        )
        embed.add_field(
            name="👤 %스팀 유저 [ID / URL]",
            value="Steam 유저 프로필, 상태, 제재 현황, 최근 플레이 게임을 조회합니다.\n"
                  "└ 예: `%스팀 유저 gabelogannewell`",
            inline=False
        )
        embed.add_field(
            name="🎲 %스팀 게임 [게임명 / AppID]",
            value="Steam 게임의 상세 정보(가격, 장르, 출시일, 현재 접속자 수)를 조회합니다.\n"
                  "└ 예: `%스팀 게임 팰월드` 또는 `%스팀 게임 730`",
            inline=False
        )
        embed.add_field(
            name="🏷️ %스팀 할인 [게임명(선택)]",
            value="현재 Steam 상점의 인기 특가 목록을 보거나 특정 게임의 할인을 조회합니다.\n"
                  "└ 예: `%스팀 할인` 또는 `%스팀 할인 사이버펑크`",
            inline=False
        )
        embed.set_footer(text="Steam Web & Storefront API • 0군봇")
        await ctx.send(embed=embed)

    # ==========================================
    # 자식 명령어 1: %스팀 유저
    # ==========================================
    @commands.cooldown(1, 3.0, commands.BucketType.user)
    @steam_group.command(
        name="유저", aliases=["user", "프로필", "profile"],
        help="Steam 유저의 프로필 및 플레이 정보를 조회합니다.\n"
             "사용법: %스팀 유저 [SteamID64 / 커스텀ID / 프로필URL]\n"
             "예시: `%스팀 유저 gabelogannewell` 또는 `%스팀 유저 76561197960287930`",
        usage="* str(*SteamID/URL*)"
    )
    async def steam_user(self, ctx, *, query: Optional[str] = None):
        if not query:
            embed = discord.Embed(
                title="🔍 Steam 유저 조회 사용법",
                description="조회할 Steam 계정의 고유 ID, 커스텀 ID 또는 프로필 링크를 입력해 주세요.\n\n"
                            "**사용 예시:**\n"
                            "• `%스팀 유저 gabelogannewell` (커스텀 ID)\n"
                            "• `%스팀 유저 76561197960287930` (SteamID64)\n"
                            "• `%스팀 유저 https://steamcommunity.com/id/gabelogannewell` (프로필 링크)",
                color=0x171A21
            )
            embed.set_footer(text="Steam Web API • 0군봇")
            await ctx.send(embed=embed)
            return

        api_key = self.get_api_key()
        if not api_key:
            await ctx.send(":no_entry: `.env` 파일에 `STEAM_API_KEY`가 설정되어 있지 않습니다.")
            return

        loading_msg = await ctx.send("🔍 Steam 유저 프로필 정보를 불러오는 중입니다... :hourglass_flowing_sand:")
        timeout = aiohttp.ClientTimeout(total=10)

        async with aiohttp.ClientSession(timeout=timeout) as session:
            # 1. SteamID64 확인
            steam_id = await self.resolve_steam_id(session, api_key, query)
            if not steam_id:
                await loading_msg.edit(content=f":x: **'{query}'**에 해당하는 Steam 유저를 찾을 수 없습니다. 아이디 또는 URL을 확인해 주세요.")
                return

            # 2. 유저 정보 요청
            summary_url = "https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/"
            bans_url = "https://api.steampowered.com/ISteamUser/GetPlayerBans/v1/"
            owned_games_url = "https://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/"
            recent_games_url = "https://api.steampowered.com/IPlayerService/GetRecentlyPlayedGames/v0001/"

            summary_data = None
            bans_data = None
            owned_games_data = None
            recent_games_data = None

            try:
                async with session.get(summary_url, params={"key": api_key, "steamids": steam_id}) as resp:
                    if resp.status == 200:
                        res = await resp.json()
                        players = res.get("response", {}).get("players", [])
                        if players:
                            summary_data = players[0]

                if not summary_data:
                    await loading_msg.edit(content=":x: 유저 프로필 정보를 가져오지 못했습니다.")
                    return

                # 제재 내역 요청
                async with session.get(bans_url, params={"key": api_key, "steamids": steam_id}) as resp:
                    if resp.status == 200:
                        res = await resp.json()
                        players_bans = res.get("players", [])
                        if players_bans:
                            bans_data = players_bans[0]

                # 보유 게임 및 최근 플레이 게임 조회 (공개 프로필인 경우)
                is_public = (summary_data.get("communityvisibilitystate") == 3)
                if is_public:
                    async with session.get(owned_games_url, params={"key": api_key, "steamid": steam_id, "include_appinfo": 0}) as resp:
                        if resp.status == 200:
                            res = await resp.json()
                            owned_games_data = res.get("response", {})

                    async with session.get(recent_games_url, params={"key": api_key, "steamid": steam_id, "count": 3}) as resp:
                        if resp.status == 200:
                            res = await resp.json()
                            recent_games_data = res.get("response", {})

            except asyncio.TimeoutError:
                await loading_msg.edit(content=":warning: Steam 서버 응답 시간이 초과되었습니다. 잠시 후 다시 시도해 주세요.")
                return
            except Exception as e:
                await loading_msg.edit(content=f":x: 데이터를 불러오는 중 오류가 발생했습니다: `{e}`")
                return

            # 데이터 파싱 및 임베드 생성
            persona_name = summary_data.get("personaname", "알 수 없음")
            profile_url = summary_data.get("profileurl", f"https://steamcommunity.com/profiles/{steam_id}")
            avatar_url = summary_data.get("avatarfull", "")
            persona_state = summary_data.get("personastate", 0)
            game_extra_info = summary_data.get("gameextrainfo")  # 현재 플레이 중인 게임

            status_text, embed_color = STATUS_MAP.get(persona_state, ("알 수 없음", 0x171A21))
            if game_extra_info:
                status_text = f"🎮 **{game_extra_info}** 플레이 중"
                embed_color = 0x90BA3C  # 게임 플레이 중일 때 연두색 하이라이트

            embed = discord.Embed(
                title=f"{persona_name} 님의 Steam 프로필",
                url=profile_url,
                color=embed_color
            )
            if avatar_url:
                embed.set_thumbnail(url=avatar_url)

            # 상태 및 기본 정보
            info_lines = [f"• **상태**: {status_text}"]
            country_code = summary_data.get("loccountrycode")
            if country_code:
                flag = get_country_flag(country_code)
                info_lines.append(f"• **국가**: {flag}")

            time_created = summary_data.get("timecreated")
            if time_created:
                created_dt = datetime.fromtimestamp(time_created)
                info_lines.append(f"• **계정 생성**: {created_dt.strftime('%Y년 %m월 %d일')}")

            embed.add_field(name="📌 기본 정보", value="\n".join(info_lines), inline=False)

            # 제재/밴 상태
            ban_lines = []
            if bans_data:
                vac_banned = bans_data.get("VACBanned", False)
                community_banned = bans_data.get("CommunityBanned", False)
                vac_bans_count = bans_data.get("NumberOfVACBans", 0)
                game_bans_count = bans_data.get("NumberOfGameBans", 0)

                if vac_banned or community_banned or game_bans_count > 0:
                    if vac_banned:
                        ban_lines.append(f"⚠️ **VAC 밴**: {vac_bans_count}건")
                    if game_bans_count > 0:
                        ban_lines.append(f"⚠️ **게임 밴**: {game_bans_count}건")
                    if community_banned:
                        ban_lines.append("⚠️ **커뮤니티 밴**: 제재 중")
                else:
                    ban_lines.append("✅ 제재 이력 없음 (정상)")
            else:
                ban_lines.append("확인 불가")

            embed.add_field(name="🛡️ 제재 현황", value="\n".join(ban_lines), inline=True)

            # 보유 게임 수
            if is_public and owned_games_data:
                game_count = owned_games_data.get("game_count", 0)
                embed.add_field(name="📦 보유 게임", value=f"{game_count:,}개", inline=True)
            elif not is_public:
                embed.add_field(name="🔒 프로필 공개 상태", value="비공개 프로필", inline=True)

            # 최근 플레이 게임 (공개 프로필인 경우)
            if is_public and recent_games_data:
                recent_games = recent_games_data.get("games", [])
                if recent_games:
                    recent_lines = []
                    for g in recent_games[:3]:
                        g_name = g.get("name", "알 수 없음")
                        p_2weeks = format_playtime(g.get("playtime_2weeks", 0))
                        p_total = format_playtime(g.get("playtime_forever", 0))
                        recent_lines.append(f"• **{g_name}**\n  └ 최근 2주: `{p_2weeks}` | 총: `{p_total}`")
                    embed.add_field(name="⏱️ 최근 플레이 게임 (최근 2주)", value="\n".join(recent_lines), inline=False)
                else:
                    embed.add_field(name="⏱️ 최근 플레이 게임", value="최근 2주간 플레이 기록이 없습니다.", inline=False)

            embed.set_footer(text=f"SteamID64: {steam_id} • Steam Web API")
            await loading_msg.edit(content=None, embed=embed)

    # ==========================================
    # 자식 명령어 2: %스팀 게임
    # ==========================================
    @commands.cooldown(1, 3.0, commands.BucketType.user)
    @steam_group.command(
        name="게임", aliases=["game", "정보", "info"],
        help="Steam 상점의 게임 상세 정보 및 가격을 조회합니다.\n"
             "사용법: %스팀 게임 [게임명 / AppID]\n"
             "예시: `%스팀 게임 팰월드` 또는 `%스팀 게임 730`",
        usage="* str(*게임명/AppID*)"
    )
    async def steam_game(self, ctx, *, query: Optional[str] = None):
        if not query:
            embed = discord.Embed(
                title="🔍 Steam 게임 검색 사용법",
                description="검색할 게임 이름 또는 AppID를 입력해 주세요.\n\n"
                            "**사용 예시:**\n"
                            "• `%스팀 게임 사이버펑크 2077`\n"
                            "• `%스팀 게임 Palworld`\n"
                            "• `%스팀 게임 1091500` (AppID)",
                color=0x1B2838
            )
            embed.set_footer(text="Steam Storefront API • 0군봇")
            await ctx.send(embed=embed)
            return

        loading_msg = await ctx.send(f"🔍 **'{query}'** 게임 정보를 검색하는 중입니다... :hourglass_flowing_sand:")
        timeout = aiohttp.ClientTimeout(total=10)

        async with aiohttp.ClientSession(timeout=timeout) as session:
            target_appid: Optional[int] = None

            # 1. 숫자로만 이루어진 경우 AppID로 바로 처리
            cleaned = query.strip()
            if cleaned.isdigit():
                target_appid = int(cleaned)
            else:
                # 상점 검색 API 호출
                search_url = "https://store.steampowered.com/api/storesearch/"
                params = {"term": cleaned, "l": "korean", "cc": "kr"}
                try:
                    async with session.get(search_url, params=params) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            items = data.get("items", [])
                            if items:
                                target_appid = items[0].get("id")
                except Exception as e:
                    print(f"[Steam Cog] 게임 검색 오류: {e}")

            if not target_appid:
                await loading_msg.edit(content=f":x: **'{query}'**에 대한 Steam 검색 결과를 찾을 수 없습니다.")
                return

            # 2. 게임 상세 정보(appdetails) 및 동접자 수 요청
            app_url = "https://store.steampowered.com/api/appdetails"
            app_params = {"appids": target_appid, "cc": "kr", "l": "korean"}
            players_url = "https://api.steampowered.com/ISteamUserStats/GetNumberOfCurrentPlayers/v1/"
            players_params = {"appid": target_appid}

            app_data = None
            player_count = None

            try:
                async with session.get(app_url, params=app_params) as resp:
                    if resp.status == 200:
                        detail_json = await resp.json()
                        app_res = detail_json.get(str(target_appid), {})
                        if app_res.get("success"):
                            app_data = app_res.get("data", {})

                # 동시 접속자 수 요청
                async with session.get(players_url, params=players_params) as resp:
                    if resp.status == 200:
                        p_json = await resp.json()
                        player_count = p_json.get("response", {}).get("player_count")
            except asyncio.TimeoutError:
                await loading_msg.edit(content=":warning: Steam 서버 응답 시간이 초과되었습니다.")
                return
            except Exception as e:
                await loading_msg.edit(content=f":x: 게임 정보를 불러오는 중 오류가 발생했습니다: `{e}`")
                return

            if not app_data:
                await loading_msg.edit(content=f":x: AppID `{target_appid}`의 상세 정보를 가져올 수 없습니다. (지역 제한 또는 비공개 항목)")
                return

            # 데이터 파싱
            game_name = app_data.get("name", "알 수 없음")
            store_url = f"https://store.steampowered.com/app/{target_appid}"
            header_img = app_data.get("header_image", "")
            short_desc = clean_html(app_data.get("short_description", ""))
            if len(short_desc) > 180:
                short_desc = short_desc[:177] + "..."

            # 가격 정보 파싱
            is_free = app_data.get("is_free", False)
            price_overview = app_data.get("price_overview")
            if is_free:
                price_text = "🆓 **무료 플레이**"
            elif price_overview:
                discount_percent = price_overview.get("discount_percent", 0)
                final_formatted = price_overview.get("final_formatted", "")
                initial_formatted = price_overview.get("initial_formatted", "")

                if discount_percent > 0:
                    price_text = f"🔥 ~~{initial_formatted}~~ ➔ **{final_formatted}** (`-{discount_percent}%` 할인 중!)"
                else:
                    price_text = f"🏷️ **{final_formatted}**"
            else:
                price_text = "가격 미정 또는 무료"

            # 출시일
            release_info = app_data.get("release_date", {})
            release_date = release_info.get("date", "미정")
            if release_info.get("coming_soon"):
                release_date = f"⏳ 출시 예정 ({release_date})"

            # 장르
            genres = [g.get("description", "") for g in app_data.get("genres", [])]
            genre_text = ", ".join(genres) if genres else "정보 없음"

            # 개발사 / 배급사
            developers = ", ".join(app_data.get("developers", [])) or "정보 없음"

            # 메타크리틱 점수
            metacritic = app_data.get("metacritic", {})
            metascore = metacritic.get("score")

            embed = discord.Embed(
                title=f"🎮 {game_name}",
                url=store_url,
                description=short_desc if short_desc else None,
                color=0x66C0F4
            )
            if header_img:
                embed.set_image(url=header_img)

            embed.add_field(name="💰 가격", value=price_text, inline=False)

            if player_count is not None:
                embed.add_field(name="👥 현재 접속자 수", value=f"**{player_count:,}명** 플레이 중", inline=True)

            if metascore:
                embed.add_field(name="🏆 메타스코어", value=f"**{metascore}점** / 100", inline=True)

            embed.add_field(name="📅 출시일", value=release_date, inline=True)
            embed.add_field(name="🏷️ 장르", value=genre_text, inline=True)
            embed.add_field(name="🏢 개발사", value=developers, inline=True)

            embed.set_footer(text=f"AppID: {target_appid} • Steam Store")
            await loading_msg.edit(content=None, embed=embed)

    # ==========================================
    # 자식 명령어 3: %스팀 할인
    # ==========================================
    @commands.cooldown(1, 3.0, commands.BucketType.user)
    @steam_group.command(
        name="할인", aliases=["sale", "세일", "특가"],
        help="Steam 상점의 주요 특별 할인 목록을 확인하거나 특정 게임의 할인 여부를 조회합니다.\n"
             "사용법: %스팀 할인 [게임명(선택)]\n"
             "예시: `%스팀 할인` 또는 `%스팀 할인 몬스터헌터`",
        usage="* opt(*게임명*)"
    )
    async def steam_sale(self, ctx, *, query: Optional[str] = None):
        loading_msg = await ctx.send("🔍 Steam 할인 정보를 불러오는 중입니다... :hourglass_flowing_sand:")
        timeout = aiohttp.ClientTimeout(total=10)

        async with aiohttp.ClientSession(timeout=timeout) as session:
            # 1. 특정 게임 검색어가 전달된 경우: 해당 게임 할인 여부 확인
            if query:
                cleaned = query.strip()
                search_url = "https://store.steampowered.com/api/storesearch/"
                params = {"term": cleaned, "l": "korean", "cc": "kr"}
                target_appid = None

                try:
                    if cleaned.isdigit():
                        target_appid = int(cleaned)
                    else:
                        async with session.get(search_url, params=params) as resp:
                            if resp.status == 200:
                                data = await resp.json()
                                items = data.get("items", [])
                                if items:
                                    target_appid = items[0].get("id")

                    if not target_appid:
                        await loading_msg.edit(content=f":x: **'{query}'** 게임을 찾을 수 없습니다.")
                        return

                    # appdetails 조회
                    app_url = "https://store.steampowered.com/api/appdetails"
                    async with session.get(app_url, params={"appids": target_appid, "cc": "kr", "l": "korean"}) as resp:
                        if resp.status == 200:
                            detail_json = await resp.json()
                            app_data = detail_json.get(str(target_appid), {}).get("data", {})
                        else:
                            app_data = {}

                except Exception as e:
                    await loading_msg.edit(content=f":x: 할인 정보를 가져오는 중 오류가 발생했습니다: `{e}`")
                    return

                if not app_data:
                    await loading_msg.edit(content=f":x: AppID `{target_appid}` 정보를 불러오지 못했습니다.")
                    return

                game_name = app_data.get("name", query)
                store_url = f"https://store.steampowered.com/app/{target_appid}"
                header_img = app_data.get("header_image", "")
                price_overview = app_data.get("price_overview")
                is_free = app_data.get("is_free", False)

                embed = discord.Embed(
                    title=f"🏷️ {game_name} 할인 정보",
                    url=store_url,
                    color=0xE040FB if (price_overview and price_overview.get("discount_percent", 0) > 0) else 0x1B2838
                )
                if header_img:
                    embed.set_thumbnail(url=header_img)

                if is_free:
                    embed.description = "🆓 **무료 플레이** 게임입니다."
                elif price_overview:
                    discount_percent = price_overview.get("discount_percent", 0)
                    initial_formatted = price_overview.get("initial_formatted", "")
                    final_formatted = price_overview.get("final_formatted", "")

                    if discount_percent > 0:
                        embed.description = (
                            f"🎉 **현재 `{discount_percent}%` 할인 진행 중!**\n\n"
                            f"• 원래 가격: ~~{initial_formatted}~~\n"
                            f"• 할인가: **{final_formatted}**\n\n"
                            f"[👉 Steam 상점 페이지 바로가기]({store_url})"
                        )
                    else:
                        embed.description = (
                            f"현재 할인 진행 중이 아닙니다.\n\n"
                            f"• 정가: **{final_formatted}**\n\n"
                            f"[👉 Steam 상점 페이지 바로가기]({store_url})"
                        )
                else:
                    embed.description = "가격 정보를 확인할 수 없습니다 (미출시 또는 데모 등)."

                embed.set_footer(text=f"AppID: {target_appid} • Steam Store")
                await loading_msg.edit(content=None, embed=embed)
                return

            # 2. 검색어가 없는 경우: 스팀 메인 특별 할인(Specials) 목록 조회
            featured_url = "https://store.steampowered.com/api/featuredcategories/?cc=kr&l=korean"
            try:
                async with session.get(featured_url) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        specials = data.get("specials", {}).get("items", [])
                    else:
                        specials = []
            except Exception as e:
                await loading_msg.edit(content=f":x: 할인 목록을 불러오는 중 오류가 발생했습니다: `{e}`")
                return

            if not specials:
                await loading_msg.edit(content=":x: 현재 Steam 특별 할인 목록을 불러올 수 없습니다.")
                return

            embed = discord.Embed(
                title="🔥 Steam 상점 오늘의 인기 특가 / 특별 할인",
                url="https://store.steampowered.com/specials",
                description="현재 Steam 상점에서 주목받고 있는 주요 할인 게임 목록입니다.\n"
                            "특정 게임의 할인을 확인하려면 `%스팀 할인 [게임명]`을 입력해 보세요!\n",
                color=0xD32F2F
            )

            # 상위 최대 7개 할인 항목 정리
            lines = []
            first_img = None
            for idx, item in enumerate(specials[:7], start=1):
                item_name = item.get("name", "알 수 없음")
                item_id = item.get("id")
                discount_pct = item.get("discount_percent", 0)
                orig_price = item.get("original_price", 0) // 100
                final_price = item.get("final_price", 0) // 100
                app_link = f"https://store.steampowered.com/app/{item_id}"

                if idx == 1 and item.get("header_image"):
                    first_img = item.get("header_image")

                lines.append(
                    f"`{idx}.` [**{item_name}**]({app_link}) (`-{discount_pct}%`)\n"
                    f"　└ ~~₩{orig_price:,}~~ ➔ **₩{final_price:,}**"
                )

            embed.add_field(name="🏆 인기 특별 할인 TOP 7", value="\n\n".join(lines), inline=False)
            if first_img:
                embed.set_thumbnail(url=first_img)

            embed.set_footer(text="Steam Featured Specials • 0군봇")
            await loading_msg.edit(content=None, embed=embed)


async def setup(app):
    await app.add_cog(Steam(app))
