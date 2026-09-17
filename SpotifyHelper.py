import os
import re
import requests
from typing import Optional, Dict, Any, List, Tuple
from dotenv import load_dotenv

load_dotenv()

try:
    import spotipy
    from spotipy.oauth2 import SpotifyClientCredentials
    from spotipy.exceptions import SpotifyException
except ImportError:
    spotipy = None
    SpotifyClientCredentials = None
    SpotifyException = Exception


class SpotifyHelper:
    def __init__(self):
        self.client_id = os.getenv("SPOTIFY_CLIENT_ID") or os.getenv("SPOTIPY_CLIENT_ID")
        self.client_secret = os.getenv("SPOTIFY_CLIENT_SECRET") or os.getenv("SPOTIPY_CLIENT_SECRET")
        self._sp: Optional[spotipy.Spotify] = None
        self._init_client()

    def _init_client(self):
        if spotipy and self.client_id and self.client_secret:
            try:
                auth_manager = SpotifyClientCredentials(
                    client_id=self.client_id,
                    client_secret=self.client_secret
                )
                self._sp = spotipy.Spotify(auth_manager=auth_manager)
            except Exception as e:
                print(f"[SpotifyHelper] 클라이언트 초기화 실패: {e}")
                self._sp = None
        else:
            self._sp = None

    def is_configured(self) -> bool:
        return bool(self.client_id and self.client_secret)

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
        스포티파이 공식 API 호출을 우선 시도하며, 앱 소유자 Premium 정책 오류 시 안전한 폴백을 수행합니다.
        """
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

    def get_recommendations(self, query: str, limit: int = 5) -> Tuple[List[Dict[str, Any]], Optional[str]]:
        """
        기준 곡을 바탕으로 스포티파이 추천 곡 목록을 가져옵니다.
        """
        if not self._sp:
            return [], "스포티파이 API가 설정되지 않았습니다."

        track_id = self.extract_spotify_track_id(query)
        track_name = query

        try:
            if not track_id:
                results = self._sp.search(q=query, type="track", limit=1)
                items = results.get("tracks", {}).get("items", [])
                if not items:
                    return [], f"'{query}'에 해당하는 곡을 찾지 못했습니다."
                track_id = items[0]["id"]
                track_name = f"{items[0]['artists'][0]['name']} - {items[0]['name']}"

            recs = self._sp.recommendations(seed_tracks=[track_id], limit=limit)
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
                    "cover_url": cover_url
                })
            return rec_tracks, track_name
        except Exception as e:
            err_str = str(e)
            if "Active premium subscription required" in err_str:
                return [], "Spotify Premium 정책: 앱을 생성한 스포티파이 계정에 활성화된 Premium 구독이 필요합니다."
            return [], f"추천 곡을 가져오는 중 오류가 발생했습니다: {e}"


# 전역 인스턴스
spotify_helper = SpotifyHelper()
