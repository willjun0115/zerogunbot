import sys
import re
import yt_dlp

def crawl_song_info(song_title):
    print(f"\n🔍 '{song_title}' 검색 중... (유튜브 메타데이터 수집)", flush=True)
    
    # yt_dlp 검색 설정
    ydl_opts = {
        'extract_flat': False, # 메타데이터 상세 추출을 위해 False 설정
        'skip_download': True,
        'quiet': True,
        'no_warnings': True,
    }
    
    # 유튜브 뮤직 공식 음원 위주로 검색하기 위해 쿼리 최적화
    # 공식 음원(Topic 채널)을 유도하기 위해 'music' 또는 '음원' 키워드를 조합하여 검색합니다.
    query = f"ytsearch1:{song_title} official audio"
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(query, download=False)
            
        if not info or 'entries' not in info or len(info['entries']) == 0:
            # 2차 검색 시도 (가벼운 쿼리)
            query_fallback = f"ytsearch1:{song_title}"
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(query_fallback, download=False)
                
        if not info or 'entries' not in info or len(info['entries']) == 0:
            print("❌ 유튜브에서 검색 결과를 찾을 수 없습니다.")
            return None
            
        video_data = info['entries'][0]
        
        # 1. 메타데이터 필드 우선 탐색
        title = video_data.get('track') or video_data.get('title')
        artist = video_data.get('artist') or video_data.get('creator') or video_data.get('uploader')
        
        # uploader가 Topic(예: '아이유 - Topic')인 경우 가공
        if artist and artist.endswith(" - Topic"):
            artist = artist.replace(" - Topic", "")
            
        description = video_data.get('description') or ""
        
        # 2. 발매연도 추출 (우선순위: release_year -> release_date -> description 정규식)
        release_year = None
        release_date = video_data.get('release_date')
        if release_date and len(release_date) >= 4:
            release_year = release_date[:4]
            
        # description 정규식 파싱
        if not release_year and description:
            # Released on: YYYY-MM-DD 형태 매칭
            match_released = re.search(r'Released on:\s*(\d{4})', description, re.IGNORECASE)
            if match_released:
                release_year = match_released.group(1)
                
            # ℗ YYYY 저작권 표시 매칭
            if not release_year:
                match_copyright = re.search(r'℗\s*(\d{4})', description)
                if match_copyright:
                    release_year = match_copyright.group(1)
            
            # 발매일: YYYY년 MM월 DD일 매칭
            if not release_year:
                match_kor = re.search(r'발매일:\s*(\d{4})', description)
                if match_kor:
                    release_year = match_kor.group(1)

        # 3. 비디오 타이틀 분석을 통한 보완 (가수 - 제목 구조인 경우)
        video_title = video_data.get('title') or ""
        if " - " in video_title:
            parts = video_title.split(" - ")
            # 괄호 제거
            potential_artist = re.sub(r'\[.*?\]|\(.*?\)', '', parts[0]).strip()
            potential_title = re.sub(r'\[.*?\]|\(.*?\)', '', parts[1]).strip()
            
            # 메타데이터가 미흡할 경우 보완
            if not artist or artist.lower() in ["unknown", "topic", "various artists"]:
                artist = potential_artist
            if not title or title.lower() in ["unknown"]:
                title = potential_title

        # 가공 및 최종 정제
        title = re.sub(r'\[.*?\]|\(.*?\)', '', title).strip() if title else song_title
        artist = artist.strip() if artist else "알 수 없음"
        release_year = release_year.strip() if release_year else "알 수 없음"
        
        print(f"✨ 분석 결과:")
        print(f"   - 가수명 (Artist): {artist}")
        print(f"   - 곡제목 (Title): {title}")
        print(f"   - 발매연도 (Year): {release_year}")
        print(f"   - 유튜브 링크: https://www.youtube.com/watch?v={video_data.get('id')}")
        
        return {
            "title": title,
            "artist": artist,
            "year": release_year,
            "link": f"https://www.youtube.com/watch?v={video_data.get('id')}"
        }
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        return None

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("사용법: python crawl_song_info.py \"곡 제목1\" \"곡 제목2\" ...")
        print("예시: python crawl_song_info.py \"아이유 에잇\" \"요네즈 켄시 레몬\"")
        sys.exit(1)
        
    titles = sys.argv[1:]
    results = []
    
    for t in titles:
        res = crawl_song_info(t)
        if res:
            results.append(res)
            
    if results:
        print("\n" + "="*40)
        print("📋 CSV 포맷 변환 결과 (복사용):")
        print("title,artist,synonyms,tags,link")
        for r in results:
            # 아티스트나 타이틀에 쉼표가 있을 시 큰따옴표 처리
            a = f'"{r["artist"]}"' if ',' in r["artist"] else r["artist"]
            t = f'"{r["title"]}"' if ',' in r["title"] else r["title"]
            # tags에 발매 연도를 자동으로 넣어줄 수도 있습니다.
            print(f"{t},{a},,kor,{r['link']}")
        print("="*40)
