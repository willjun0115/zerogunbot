import discord
from discord.ext import commands
import aiohttp
import asyncio
import os
import urllib.parse
from typing import Optional, Dict, Any, List
import time

TIER_COLORS = {
    "IRON": 0x51484A,
    "BRONZE": 0x8C523A,
    "SILVER": 0x80989D,
    "GOLD": 0xCD8837,
    "PLATINUM": 0x258C86,
    "EMERALD": 0x1A9250,
    "DIAMOND": 0x4B6AB7,
    "MASTER": 0x9D44BE,
    "GRANDMASTER": 0xCD3333,
    "CHALLENGER": 0xF4C042,
}

TIER_NAMES_KR = {
    "IRON": "아이언",
    "BRONZE": "브론즈",
    "SILVER": "실버",
    "GOLD": "골드",
    "PLATINUM": "플래티넘",
    "EMERALD": "에메랄드",
    "DIAMOND": "다이아몬드",
    "MASTER": "마스터",
    "GRANDMASTER": "그랜드마스터",
    "CHALLENGER": "챌린저",
}

QUEUE_NAMES = {
    420: "솔로랭크",
    440: "자유랭크",
    450: "칼바람",
    490: "빠른대전",
    1700: "아레나",
    1900: "URF",
}


class LoL(commands.Cog, name="롤 전적", description="리그 오브 레전드(LoL) 전적 및 통계 검색 카테고리입니다."):
    def __init__(self, app):
        self.app = app
        self.ddragon_version: str = "14.12.1"
        self.champ_name_map: Dict[str, str] = {}
        self.last_ddragon_update: float = 0.0

    def get_api_key(self) -> Optional[str]:
        return os.environ.get("RIOT_API_KEY")

    async def ensure_ddragon(self, session: aiohttp.ClientSession):
        """최신 Data Dragon 버전 및 한국어 챔피언 이름을 캐싱합니다 (1일 1회 갱신)."""
        now = time.time()
        if self.champ_name_map and (now - self.last_ddragon_update) < 86400:
            return

        try:
            v_url = "https://ddragon.leagueoflegends.com/api/versions.json"
            async with session.get(v_url, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                if resp.status == 200:
                    versions = await resp.json()
                    self.ddragon_version = versions[0]

            c_url = f"https://ddragon.leagueoflegends.com/cdn/{self.ddragon_version}/data/ko_KR/champion.json"
            async with session.get(c_url, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                if resp.status == 200:
                    c_data = await resp.json()
                    self.champ_name_map = {k: v.get("name", k) for k, v in c_data.get("data", {}).items()}
                    self.last_ddragon_update = now
        except Exception as e:
            print(f"[LoL Cog] DDragon 캐싱 오류: {e}")

    @commands.cooldown(1, 3.0, commands.BucketType.user)
    @commands.command(
        name="롤", aliases=["lol", "롤전적", "전적"],
        help="소환사의 티어 및 최근 5게임 전적을 조회합니다.\n"
             "사용법: %롤 [소환사명#태그] (태그 생략 시 기본 #KR1)\n"
             "예시: `%롤 Hide on bush#KR1` 또는 `%롤 페이커`",
        usage="* str(*RiotID*)"
    )
    async def lol_stats(self, ctx, *, query: Optional[str] = None):
        if not query:
            embed = discord.Embed(
                title="🔍 롤 전적 검색 사용법",
                description="소환사명과 태그를 함께 입력해 주세요.\n\n"
                            "**사용 예시:**\n"
                            "• `%롤 Hide on bush#KR1`\n"
                            "• `%롤 페이커` (태그 생략 시 `#KR1`로 자동 검색)",
                color=0x1E88E5
            )
            await ctx.send(embed=embed)
            return

        api_key = self.get_api_key()
        if not api_key:
            await ctx.send(":no_entry: `.env` 파일에 `RIOT_API_KEY`가 설정되어 있지 않습니다.")
            return

        # Riot ID 파싱
        cleaned = query.strip()
        if '#' in cleaned:
            parts = cleaned.split('#', 1)
            game_name = parts[0].strip()
            tag_line = parts[1].strip()
        else:
            game_name = cleaned
            tag_line = "KR1"

        if not game_name or not tag_line:
            await ctx.send(":no_entry: 소환사명과 태그를 올바르게 입력해 주세요. (예: `%롤 Hide on bush#KR1`)")
            return

        loading_msg = await ctx.send(f"🔍 **{game_name}#{tag_line}** 님의 전적 데이터를 불러오는 중... :hourglass_flowing_sand:")

        headers = {"X-Riot-Token": api_key}
        timeout = aiohttp.ClientTimeout(total=10)

        async with aiohttp.ClientSession(headers=headers, timeout=timeout) as session:
            await self.ensure_ddragon(session)

            # 1. Account-v1 (PUUID 조회)
            encoded_name = urllib.parse.quote(game_name)
            encoded_tag = urllib.parse.quote(tag_line)
            acc_url = f"https://asia.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{encoded_name}/{encoded_tag}"

            try:
                async with session.get(acc_url) as resp:
                    if resp.status == 404:
                        await loading_msg.edit(content=f":x: 소환사 **{game_name}#{tag_line}**을(를) 찾을 수 없습니다. 이름과 태그를 다시 확인해 주세요.")
                        return
                    elif resp.status in (401, 403):
                        await loading_msg.edit(content=":no_entry: 라이엇 API 키가 만료되었거나 권한이 없습니다. 관리자에게 문의해 주세요.")
                        return
                    elif resp.status == 429:
                        await loading_msg.edit(content=":warning: 라이엇 API 요청 한도를 초과했습니다. 잠시 후 다시 시도해 주세요.")
                        return
                    elif resp.status != 200:
                        await loading_msg.edit(content=f":x: 라이엇 API 오류가 발생했습니다. (HTTP {resp.status})")
                        return
                    acc_data = await resp.json()
            except Exception as e:
                await loading_msg.edit(content=f":x: 데이터를 가져오는 중 오류가 발생했습니다: {e}")
                return

            puuid = acc_data.get("puuid")
            real_name = acc_data.get("gameName", game_name)
            real_tag = acc_data.get("tagLine", tag_line)

            # 2. Summoner-v4 (레벨 및 프로필 아이콘) & League-v4 (랭크 정보) 병렬 조회
            s_url = f"https://kr.api.riotgames.com/lol/summoner/v4/summoners/by-puuid/{puuid}"
            l_url = f"https://kr.api.riotgames.com/lol/league/v4/entries/by-puuid/{puuid}"
            m_ids_url = f"https://asia.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids?start=0&count=5"

            try:
                s_resp, l_resp, m_ids_resp = await asyncio.gather(
                    session.get(s_url),
                    session.get(l_url),
                    session.get(m_ids_url)
                )

                summoner_data = await s_resp.json() if s_resp.status == 200 else {}
                league_data = await l_resp.json() if l_resp.status == 200 else []
                match_ids = await m_ids_resp.json() if m_ids_resp.status == 200 else []
            except Exception as e:
                await loading_msg.edit(content=f":x: 소환사 세부 정보를 조회하는 중 오류가 발생했습니다: {e}")
                return

            profile_icon_id = summoner_data.get("profileIconId", 1)
            summoner_level = summoner_data.get("summonerLevel", 1)

            # 랭크 정보 파싱
            solo_rank_text = "Unranked (배치 전)"
            flex_rank_text = "Unranked (배치 전)"
            embed_color = 0x80989D  # 기본 언랭/실버 계열

            for entry in league_data:
                q_type = entry.get("queueType")
                tier = entry.get("tier", "UNRANKED")
                rank = entry.get("rank", "")
                lp = entry.get("leaguePoints", 0)
                wins = entry.get("wins", 0)
                losses = entry.get("losses", 0)
                total = wins + losses
                winrate = round((wins / total) * 100, 1) if total > 0 else 0.0

                tier_kr = TIER_NAMES_KR.get(tier, tier)
                rank_str = f"**{tier_kr} {rank}** ({lp:,} LP)\n{wins}승 {losses}패 (승률 {winrate}%)"

                if q_type == "RANKED_SOLO_5x5":
                    solo_rank_text = rank_str
                    if tier in TIER_COLORS:
                        embed_color = TIER_COLORS[tier]
                elif q_type == "RANKED_FLEX_SR":
                    flex_rank_text = rank_str

            # 3. 최근 5게임 상세 데이터 병렬 조회
            recent_games_text = "최근 플레이한 매치 기록이 없습니다."
            if match_ids and isinstance(match_ids, list):
                async def fetch_match(mid):
                    try:
                        async with session.get(f"https://asia.api.riotgames.com/lol/match/v5/matches/{mid}") as mr:
                            if mr.status == 200:
                                return await mr.json()
                    except Exception:
                        pass
                    return None

                match_results = await asyncio.gather(*[fetch_match(mid) for mid in match_ids[:5]])
                match_lines = []
                recent_wins = 0
                recent_total = 0
                total_kills = 0
                total_deaths = 0
                total_assists = 0

                for m in match_results:
                    if not m or "info" not in m:
                        continue
                    info = m["info"]
                    queue_id = info.get("queueId", 0)
                    q_name = QUEUE_NAMES.get(queue_id, "일반")
                    duration_sec = info.get("gameDuration", 0)
                    mins, secs = divmod(duration_sec, 60)

                    # 내 참가자 정보 찾기
                    participant = next((x for x in info.get("participants", []) if x.get("puuid") == puuid), None)
                    if not participant:
                        continue

                    recent_total += 1
                    is_win = participant.get("win", False)
                    if is_win:
                        recent_wins += 1

                    champ_id = participant.get("championName", "Unknown")
                    champ_name = self.champ_name_map.get(champ_id, champ_id)
                    kills = participant.get("kills", 0)
                    deaths = participant.get("deaths", 0)
                    assists = participant.get("assists", 0)

                    total_kills += kills
                    total_deaths += deaths
                    total_assists += assists

                    kda_ratio = (kills + assists) / max(1, deaths)
                    kda_str = f"{kills}/{deaths}/{assists} ({kda_ratio:0.2f})"

                    result_badge = "🟢 **승리**" if is_win else "🔴 **패배**"
                    match_lines.append(f"{result_badge} `[{q_name}]` **{champ_name}** | {kda_str} • {mins}분")

                if match_lines:
                    recent_losses = recent_total - recent_wins
                    recent_wr = round((recent_wins / recent_total) * 100, 1) if recent_total > 0 else 0
                    avg_k = total_kills / recent_total if recent_total else 0
                    avg_d = total_deaths / recent_total if recent_total else 0
                    avg_a = total_assists / recent_total if recent_total else 0
                    avg_ratio = (total_kills + total_assists) / max(1, total_deaths)

                    summary_header = f"📊 **최근 {recent_total}전 {recent_wins}승 {recent_losses}패** (승률 **{recent_wr}%**)\n" \
                                     f"🎯 **평균 KDA:** `{avg_k:0.1f} / {avg_d:0.1f} / {avg_a:0.1f}` (`{avg_ratio:0.2f}`)\n\n"
                    recent_games_text = summary_header + "\n".join(match_lines)

            # 4. 최종 Embed 생성
            opgg_url = f"https://www.op.gg/summoners/kr/{encoded_name}-{encoded_tag}"
            icon_url = f"https://ddragon.leagueoflegends.com/cdn/{self.ddragon_version}/img/profileicon/{profile_icon_id}.png"

            embed = discord.Embed(
                title=f"소환사 {real_name} #{real_tag}",
                url=opgg_url,
                description=f"⭐ **레벨:** {summoner_level:,}\n🔗 [OP.GG 전적 보기]({opgg_url})",
                color=embed_color
            )
            embed.set_thumbnail(url=icon_url)
            embed.add_field(name="🏆 솔로랭크", value=solo_rank_text, inline=True)
            embed.add_field(name="👥 자유랭크", value=flex_rank_text, inline=True)
            embed.add_field(name="⚔️ 최근 매치 기록", value=recent_games_text, inline=False)
            embed.set_footer(text="League of Legends • Riot Games API", icon_url="https://static.wikia.nocookie.net/leagueoflegends/images/1/12/League_of_Legends_Icon.png")

            await loading_msg.delete()
            await ctx.send(embed=embed)


async def setup(app):
    await app.add_cog(LoL(app))
