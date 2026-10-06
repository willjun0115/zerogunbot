import discord
from discord.ext import commands
import aiohttp
import asyncio
import os
import re
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


class Steam(commands.Cog, name="스팀", description="Steam 프로필 및 게임 정보 조회 카테고리입니다."):
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
        # https://steamcommunity.com/profiles/76561198000000000
        match_profile = re.search(r"steamcommunity\.com/profiles/(\d{17})", query)
        if match_profile:
            return match_profile.group(1)

        # https://steamcommunity.com/id/custom_name/
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

    @commands.cooldown(1, 3.0, commands.BucketType.user)
    @commands.command(
        name="스팀", aliases=["steam", "스팀프로필", "스팀유저"],
        help="Steam 유저의 프로필 및 플레이 정보를 조회합니다.\n"
             "사용법: %스팀 [SteamID64 / 커스텀ID / 프로필URL]\n"
             "예시: `%스팀 gabelogannewell` 또는 `%스팀 76561197960287930`",
        usage="* str(*SteamID/URL*)"
    )
    async def steam_profile(self, ctx, *, query: Optional[str] = None):
        if not query:
            embed = discord.Embed(
                title="🔍 Steam 프로필 조회 사용법",
                description="조회할 Steam 계정의 고유 ID, 커스텀 ID 또는 프로필 링크를 입력해 주세요.\n\n"
                            "**사용 예시:**\n"
                            "• `%스팀 gabelogannewell` (커스텀 ID)\n"
                            "• `%스팀 76561197960287930` (SteamID64)\n"
                            "• `%스팀 https://steamcommunity.com/id/gabelogannewell` (프로필 링크)",
                color=0x171A21
            )
            embed.set_footer(text="Steam Web API • 0군봇")
            await ctx.send(embed=embed)
            return

        api_key = self.get_api_key()
        if not api_key:
            await ctx.send(":no_entry: `.env` 파일에 `STEAM_API_KEY`가 설정되어 있지 않습니다.")
            return

        loading_msg = await ctx.send("🔍 Steam 프로필 정보를 불러오는 중입니다... :hourglass_flowing_sand:")
        timeout = aiohttp.ClientTimeout(total=10)

        async with aiohttp.ClientSession(timeout=timeout) as session:
            # 1. SteamID64 확인
            steam_id = await self.resolve_steam_id(session, api_key, query)
            if not steam_id:
                await loading_msg.edit(content=f":x: **'{query}'**에 해당하는 Steam 유저를 찾을 수 없습니다. 아이디 또는 URL을 확인해 주세요.")
                return

            # 2. 유저 요약 정보 (GetPlayerSummaries)
            summary_url = "https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/"
            bans_url = "https://api.steampowered.com/ISteamUser/GetPlayerBans/v1/"
            owned_games_url = "https://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/"
            recent_games_url = "https://api.steampowered.com/IPlayerService/GetRecentlyPlayedGames/v0001/"

            summary_data = None
            bans_data = None
            owned_games_data = None
            recent_games_data = None

            try:
                # 동시 요청 처리
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

                # 보유 게임 및 최근 플레이 게임 조회 (공개 프로필인 경우만 정상 반환)
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


async def setup(app):
    await app.add_cog(Steam(app))
