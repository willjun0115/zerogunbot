import os
import re
import requests
from typing import Optional, Dict, Any, List, Tuple
from dotenv import load_dotenv

DOTENV_PATH = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(dotenv_path=DOTENV_PATH, override=True)

try:
    import spotipy
    from spotipy.oauth2 import SpotifyClientCredentials
    from spotipy.exceptions import SpotifyException
except ImportError:
    spotipy = None
    SpotifyClientCredentials = None
    SpotifyException = Exception


def clean_music_title(raw: str) -> str:
    """유튜브 제목 등에서 MV, 노이즈 태그 등을 제거하여 순수 음원/아티스트 검색어만 남깁니다."""
    if not raw:
        return ""
    # 1. 괄호 태그 제거: [MV], (Official Audio), [가사] 등
    s = re.sub(r'\[.*?\]|\(.*?\)|\{.*?\}', ' ', raw)
    # 2. 일본어 인용 부호 등 제거 (내용은 유지)
    s = s.replace('「', ' ').replace('」', ' ').replace('『', ' ').replace('』', ' ')
    # 3. 비디오/음원 관련 노이즈 키워드 제거
    patterns = [
        r'(?i)\b(official\s*(music\s*)?video|music\s*video|official\s*audio|official|audio|mv|m/v)\b',
        r'(?i)\b(lyrics|lyric\s*video|가사|자막|special\s*clip|live\s*clip|performance\s*video)\b',
        r'(?i)\b(hd|4k|1080p|remastered|color\s*coded|stage|fancam)\b'
    ]
    for p in patterns:
        s = re.sub(p, ' ', s)
    # 4. 따옴표 및 연속 공백 정리
    s = re.sub(r'[\'\"‘’“”]', '', s)
    return ' '.join(s.split())


class SpotifyHelper:
    def __init__(self):
        self._sp: Optional[spotipy.Spotify] = None
        self._ensure_client()

    def _ensure_client(self):
        """환경 변수를 재로드하고 spotipy 클라이언트 연결을 확인합니다."""
        load_dotenv(dotenv_path=DOTENV_PATH, override=True)
        self.client_id = os.getenv("SPOTIFY_CLIENT_ID") or os.getenv("SPOTIPY_CLIENT_ID")
        self.client_secret = os.getenv("SPOTIFY_CLIENT_SECRET") or os.getenv("SPOTIPY_CLIENT_SECRET")

        if spotipy and self.client_id and self.client_secret and self._sp is None:
            try:
                auth_manager = SpotifyClientCredentials(
                    client_id=self.client_id,
                    client_secret=self.client_secret
                )
                self._sp = spotipy.Spotify(auth_manager=auth_manager)
            except Exception as e:
                print(f"[SpotifyHelper] 클라이언트 초기화 실패: {e}")
                self._sp = None

    def is_configured(self) -> bool:
        self._ensure_client()
        return bool(self.client_id and self.client_secret and self._sp)

    def extract_spotify_track_id(self, text: str) -> Optional[str]:
        """스포티파이 트랙 URL 또는 URI에서 ID를 추출합니다."""
        match = re.search(r"spotify\.com/track/([a-zA-Z0-9]+)", text)
        if match:
            return match.group(1)
        match = re.search(r"spotify:track:([a-zA-Z0-9]+)", text)
        if match:
            return match.group(1)
        return None

    def _fetch_itunes_fallback(self, query: str) -> Optional[Dict[str, Any]]:
        """스포티파이 API 제한 시 무료 iTunes Search API로 메타데이터 및 앨범 아트를 보완합니다."""
        try:
            url = "https://itunes.apple.com/search"
            params = {"term": query, "entity": "song", "limit": 1}
            resp = requests.get(url, params=params, timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("resultCount", 0) > 0:
                    item = data["results"][0]
                    # 고해상도 커버 아트 링크 변환 (100x100 -> 600x600)
                    artwork = item.get("artworkUrl100", "")
                    if artwork:
                        artwork = artwork.replace("100x100bb.jpg", "600x600bb.jpg")
                    
                    release_date = item.get("releaseDate", "")[:10]
                    return {
                        "title": item.get("trackName", "알 수 없음"),
                        "artist": item.get("artistName", "알 수 없음"),
                        "album": item.get("collectionName", "알 수 없음"),
                        "release_date": release_date,
                        "cover_url": artwork,
                        "spotify_url": item.get("trackViewUrl", ""),
                        "popularity": None,
                        "preview_url": item.get("previewUrl"),
                        "duration_ms": item.get("trackTimeMillis"),
                        "source": "itunes",
                        "premium_required": True
                    }
        except Exception as e:
            print(f"[SpotifyHelper] iTunes 폴백 에러: {e}")
        return None

    def _fetch_spotify_oembed(self, track_url: str) -> Optional[Dict[str, Any]]:
        """인증 없이 Spotify 공식 oEmbed API로 곡 제목과 썸네일을 조회합니다."""
        try:
            oembed_url = "https://open.spotify.com/oembed"
            resp = requests.get(oembed_url, params={"url": track_url}, timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                title = data.get("title", "")
                cover = data.get("thumbnail_url", "")
                return {
                    "title": title,
                    "artist": "Spotify Track",
                    "album": "Spotify",
                    "release_date": "정보 없음",
                    "cover_url": cover,
                    "spotify_url": track_url,
                    "popularity": None,
                    "preview_url": None,
                    "source": "spotify_oembed",
                    "premium_required": True
                }
        except Exception:
            pass
        return None

    def search_track(self, query: str) -> Optional[Dict[str, Any]]:
        """
        곡 제목, 아티스트 또는 Spotify 트랙 링크로 곡 정보를 검색합니다.
        스포티파이 공식 API 호출을 우선 시도하며, 오류 시 안전한 폴백을 수행합니다.
        """
        self._ensure_client()
        track_id = self.extract_spotify_track_id(query)
        is_url = track_id is not None

        if self._sp:
            try:
                if track_id:
                    track = self._sp.track(track_id)
                else:
                    results = self._sp.search(q=query, type="track", limit=1)
                    items = results.get("tracks", {}).get("items", [])
                    track = items[0] if items else None

                if track:
                    artists = ", ".join([a.get("name", "") for a in track.get("artists", [])])
                    album = track.get("album", {})
                    album_name = album.get("name", "알 수 없음")
                    release_date = album.get("release_date", "정보 없음")
                    images = album.get("images", [])
                    cover_url = images[0].get("url") if images else ""
                    spotify_url = track.get("external_urls", {}).get("spotify", "")
                    preview_url = track.get("preview_url")
                    popularity = track.get("popularity", 0)

                    return {
                        "title": track.get("name", "알 수 없음"),
                        "artist": artists,
                        "album": album_name,
                        "release_date": release_date,
                        "cover_url": cover_url,
                        "spotify_url": spotify_url,
                        "popularity": popularity,
                        "preview_url": preview_url,
                        "duration_ms": track.get("duration_ms"),
                        "source": "spotify",
                        "premium_required": False
                    }
            except Exception as e:
                err_str = str(e)
                # 스포티파이 2024년 말 정책: App owner active premium subscription required
                if "Active premium subscription required" in err_str:
                    if is_url:
                        oembed_res = self._fetch_spotify_oembed(query)
                        if oembed_res:
                            return oembed_res
                    # 키워드 검색 시 iTunes API로 폴백
                    clean_query = query if not is_url else "Spotify Track"
                    itunes_res = self._fetch_itunes_fallback(clean_query)
                    if itunes_res:
                        return itunes_res
                    return {
                        "error": "spotify_premium_required",
                        "message": "스포티파이 개발자 앱 생성 계정에 Spotify Premium 구독이 필요합니다."
                    }
                else:
                    print(f"[SpotifyHelper] 검색 오류: {e}")

        # Spotify 미설정 시 폴백
        if not is_url:
            return self._fetch_itunes_fallback(query)
        else:
            return self._fetch_spotify_oembed(query)

    def _fetch_recommendations_fallback(self, queries: str | List[str], limit: int = 5) -> Tuple[List[Dict[str, Any]], Optional[str]]:
        """스포티파이 API 미설정/제한 시 최대 5개 시드 곡의 아티스트 및 장르 기반 추천 곡을 교차 수집합니다."""
        try:
            if isinstance(queries, str):
                query_list = [queries]
            else:
                query_list = [q for q in queries if q and q.strip()][:5]

            if not query_list:
                query_list = ["K-Pop Hits"]

            url = "https://itunes.apple.com/search"
            seeds = []
            seed_names = []

            for q in query_list:
                cleaned_q = clean_music_title(q)
                search_candidates = [cleaned_q] if cleaned_q != q else []
                search_candidates.append(q)
                search_candidates.extend(["K-Pop Hits", "Popular Songs"])

                found_seed = None
                for cand in search_candidates:
                    if not cand:
                        continue
                    resp = requests.get(url, params={"term": cand, "entity": "song", "limit": 3}, timeout=5)
                    if resp.status_code == 200 and resp.json().get("results"):
                        found_seed = resp.json()["results"][0]
                        break

                if found_seed:
                    s_name = f"{found_seed.get('artistName', '')} - {found_seed.get('trackName', '')}".strip()
                    if s_name not in seed_names:
                        seeds.append(found_seed)
                        seed_names.append(s_name)

            if not seeds:
                return [], "입력된 시드에 해당하는 곡 정보를 찾지 못했습니다."

            seen_titles = set()
            for s in seeds:
                seen_titles.add(s.get("trackName", "").lower())

            per_seed_tracks: List[List[Dict[str, Any]]] = []

            for s in seeds:
                s_recs: List[Dict[str, Any]] = []
                artist_id = s.get("artistId")
                genre = s.get("primaryGenreName", "")

                # 1. 동일 아티스트 인기곡 조회
                if artist_id:
                    lookup_url = "https://itunes.apple.com/lookup"
                    lookup_resp = requests.get(lookup_url, params={"id": artist_id, "entity": "song", "limit": 8}, timeout=5)
                    if lookup_resp.status_code == 200:
                        for item in lookup_resp.json().get("results", []):
                            t_name = item.get("trackName")
                            if item.get("wrapperType") == "track" and t_name and t_name.lower() not in seen_titles:
                                seen_titles.add(t_name.lower())
                                artwork = item.get("artworkUrl100", "").replace("100x100bb.jpg", "600x600bb.jpg")
                                s_recs.append({
                                    "title": t_name,
                                    "artist": item.get("artistName", "알 수 없음"),
                                    "album": item.get("collectionName", "알 수 없음"),
                                    "spotify_url": item.get("trackViewUrl", ""),
                                    "cover_url": artwork,
                                    "source": "itunes_fallback"
                                })

                # 2. 동일 장르 인기곡 추가
                if len(s_recs) < 5 and genre:
                    genre_resp = requests.get(url, params={"term": genre, "entity": "song", "limit": 15}, timeout=5)
                    if genre_resp.status_code == 200:
                        for item in genre_resp.json().get("results", []):
                            t_name = item.get("trackName")
                            if t_name and t_name.lower() not in seen_titles:
                                seen_titles.add(t_name.lower())
                                artwork = item.get("artworkUrl100", "").replace("100x100bb.jpg", "600x600bb.jpg")
                                s_recs.append({
                                    "title": t_name,
                                    "artist": item.get("artistName", "알 수 없음"),
                                    "album": item.get("collectionName", "알 수 없음"),
                                    "spotify_url": item.get("trackViewUrl", ""),
                                    "cover_url": artwork,
                                    "source": "itunes_fallback"
                                })
                            if len(s_recs) >= 5:
                                break

                per_seed_tracks.append(s_recs)

            # 라운드로빈 방식으로 각 시드의 추천 곡들을 골고루 교차 배치
            combined_recs: List[Dict[str, Any]] = []
            max_len = max((len(st) for st in per_seed_tracks), default=0)
            for i in range(max_len):
                for st in per_seed_tracks:
                    if i < len(st):
                        combined_recs.append(st[i])
                        if len(combined_recs) >= limit:
                            break
                if len(combined_recs) >= limit:
                    break

            summary_name = ", ".join(seed_names[:3])
            if len(seed_names) > 3:
                summary_name += f" 외 {len(seed_names) - 3}곡"

            return combined_recs[:limit], summary_name
        except Exception as e:
            return [], f"추천 곡 탐색 중 오류 발생: {e}"

    def get_recommendations(self, queries: str | List[str], limit: int = 5) -> Tuple[List[Dict[str, Any]], Optional[str]]:
        """
        최대 5개의 기준 곡(단일 문자열 또는 문자열 리스트)을 바탕으로 복합 추천 곡 목록을 가져옵니다.
        Spotify API 호출을 우선 시도하며, 미설정 또는 Premium 정책 제한 시 고품질 다중 시드 폴백으로 자동 전환합니다.
        """
        self._ensure_client()
        if isinstance(queries, str):
            query_list = [queries]
        else:
            query_list = [q for q in queries if q and q.strip()][:5]

        if not query_list:
            query_list = ["K-Pop Hits"]

        if self._sp:
            try:
                seed_tracks = []
                seed_names = []
                for q in query_list:
                    track_id = self.extract_spotify_track_id(q)
                    if track_id:
                        seed_tracks.append(track_id)
                        seed_names.append(q)
                    else:
                        cleaned = clean_music_title(q) or q
                        results = self._sp.search(q=cleaned, type="track", limit=1)
                        items = results.get("tracks", {}).get("items", [])
                        if items:
                            seed_tracks.append(items[0]["id"])
                            seed_names.append(f"{items[0]['artists'][0]['name']} - {items[0]['name']}")
                    if len(seed_tracks) >= 5:
                        break

                if seed_tracks:
                    recs = self._sp.recommendations(seed_tracks=seed_tracks[:5], limit=limit)
                    rec_tracks = []
                    for t in recs.get("tracks", []):
                        artists = ", ".join([a.get("name", "") for a in t.get("artists", [])])
                        album = t.get("album", {})
                        images = album.get("images", [])
                        cover_url = images[0].get("url") if images else ""
                        rec_tracks.append({
                            "title": t.get("name"),
                            "artist": artists,
                            "album": album.get("name"),
                            "spotify_url": t.get("external_urls", {}).get("spotify"),
                            "cover_url": cover_url,
                            "source": "spotify"
                        })
                    if rec_tracks:
                        summary_name = ", ".join(seed_names[:3])
                        if len(seed_names) > 3:
                            summary_name += f" 외 {len(seed_names) - 3}곡"
                        return rec_tracks, summary_name
            except Exception as e:
                err_str = str(e)
                print(f"[SpotifyHelper] 스포티파이 다중 추천 API 제한 또는 오류: {err_str[:120]}")

        # 스포티파이 API 미설정 또는 Premium 403 제한 시 안정적인 다중 시드 폴백 제공
        return self._fetch_recommendations_fallback(query_list, limit=limit)


# 전역 인스턴스
spotify_helper = SpotifyHelper()
