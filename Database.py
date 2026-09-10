import aiosqlite
import os
from typing import Any, Optional, Tuple, Dict


class LegacyRecord:
    """
    기존 디스코드 메시지 기반 DB(find_id)와의 하위 호환성을 제공하는 레코드 래퍼.
    .content 및 await .edit(content=...) 인터페이스를 지원하여 기존 미니게임들이
    수정 없이도 정상 작동하도록 돕습니다.
    """
    def __init__(self, db: "Database", season: str, user_id: int, selector: str, value: Any):
        self.db = db
        self.season = season
        self.user_id = user_id
        self.selector = selector
        self.value = value

        # 과거 디스코드 메시지 규격 (20자 접두사 + 값)
        # 예: '$123456789012345678;' (20자)
        prefix = f"{selector}{user_id};"
        if len(prefix) < 20:
            prefix = prefix.ljust(20, ' ')
        self.content = f"{prefix}{value}"

    async def edit(self, content: str):
        val_str = content[20:].strip() if len(content) > 20 else content.split(';')[-1].strip()
        try:
            new_val = int(val_str)
        except ValueError:
            new_val = val_str
        self.value = new_val
        self.content = content
        await self.db.update_single_field(self.season, self.user_id, self.selector, new_val)


class Database:
    def __init__(self, db_path: str = "zerogun.db"):
        self.db_path = db_path

    async def init_db(self):
        """데이터베이스 및 테이블을 초기화합니다."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS user_data (
                    season TEXT NOT NULL DEFAULT 'db',
                    user_id INTEGER NOT NULL,
                    coins INTEGER NOT NULL DEFAULT 0,
                    luck INTEGER NOT NULL DEFAULT 0,
                    ability TEXT DEFAULT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (season, user_id)
                )
            """)
            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_season_coins 
                ON user_data(season, coins DESC)
            """)
            await db.commit()

    async def find_data(self, season: str, user_id: int) -> Tuple[Optional[bool], Dict[str, Any]]:
        """
        특정 시즌과 유저 ID에 해당하는 데이터를 조회합니다.
        기존 app.find_data("db", user_id)와 100% 호환되는 반환 형식 (find_marker, data_dict)을 반환합니다.
        """
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT coins, luck, ability FROM user_data WHERE season = ? AND user_id = ?",
                (season, user_id)
            ) as cursor:
                row = await cursor.fetchone()
                if row is None:
                    return None, {}
                
                coins, luck, ability = row
                data: Dict[str, Any] = {
                    '$': coins,
                    '%': luck
                }
                if ability is not None:
                    data['*'] = ability
                return True, data

    async def update_data(self, user_id: int, data: dict, message: Any = None, season: str = 'db'):
        """
        유저 데이터를 갱신하거나 새로 등록(UPSERT)합니다.
        기존 app.update_data(user_id, data, message) 시그니처와 호환됩니다.
        """
        coins = data.get('$')
        luck = data.get('%')
        ability = data.get('*')

        async with aiosqlite.connect(self.db_path) as db:
            # 먼저 기존 레코드 확인
            async with db.execute(
                "SELECT coins, luck, ability FROM user_data WHERE season = ? AND user_id = ?",
                (season, user_id)
            ) as cursor:
                existing = await cursor.fetchone()

            if existing is None:
                # 새 레코드 삽입
                await db.execute(
                    """
                    INSERT INTO user_data (season, user_id, coins, luck, ability, updated_at)
                    VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                    """,
                    (season, user_id, coins if coins is not None else 0, luck if luck is not None else 0, ability)
                )
            else:
                # 기존 레코드 갱신 (제공된 필드만 반영)
                new_coins = coins if coins is not None else existing[0]
                new_luck = luck if luck is not None else existing[1]
                # '*' 키가 data에 명시적으로 있으면 그 값을 쓰고(None일 수도 있음), 없으면 기존 값 유지
                new_ability = ability if '*' in data else existing[2]

                await db.execute(
                    """
                    UPDATE user_data
                    SET coins = ?, luck = ?, ability = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE season = ? AND user_id = ?
                    """,
                    (new_coins, new_luck, new_ability, season, user_id)
                )
            await db.commit()

    async def collect_data(self, season: str = 'db') -> Dict[int, Dict[str, Any]]:
        """
        특정 시즌의 모든 유저 데이터를 코인 내림차순으로 가져옵니다.
        반환 형식: {user_id: {'$': coins, '%': luck, '*': ability, ...}}
        """
        data_dict: Dict[int, Dict[str, Any]] = {}
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT user_id, coins, luck, ability FROM user_data WHERE season = ? ORDER BY coins DESC",
                (season,)
            ) as cursor:
                rows = await cursor.fetchall()
                for row in rows:
                    uid, coins, luck, ability = row
                    d: Dict[str, Any] = {'$': coins, '%': luck}
                    if ability is not None:
                        d['*'] = ability
                    data_dict[uid] = d
        return data_dict

    async def find_id(self, selector: str, user_id: int, season: str = 'db') -> Optional[LegacyRecord]:
        """
        기존 find_id(selector, user_id) 호출과의 하위 호환을 위한 메서드.
        LegacyRecord 객체를 반환하여 .content와 .edit(...) 동작을 지원합니다.
        """
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT coins, luck, ability FROM user_data WHERE season = ? AND user_id = ?",
                (season, user_id)
            ) as cursor:
                row = await cursor.fetchone()
                if row is None:
                    return None

                coins, luck, ability = row
                if selector == '$':
                    val = coins
                elif selector == '%':
                    val = luck
                elif selector == '*':
                    val = ability
                else:
                    val = coins

                return LegacyRecord(self, season, user_id, selector, val)

    async def update_single_field(self, season: str, user_id: int, selector: str, value: Any):
        """단일 속성(선택자)을 갱신합니다."""
        column = "coins"
        if selector == '%':
            column = "luck"
        elif selector == '*':
            column = "ability"

        async with aiosqlite.connect(self.db_path) as db:
            # 존재 확인
            async with db.execute(
                "SELECT 1 FROM user_data WHERE season = ? AND user_id = ?",
                (season, user_id)
            ) as cursor:
                exists = await cursor.fetchone()

            if exists:
                await db.execute(
                    f"UPDATE user_data SET {column} = ?, updated_at = CURRENT_TIMESTAMP WHERE season = ? AND user_id = ?",
                    (value, season, user_id)
                )
            else:
                coins = value if column == "coins" else 0
                luck = value if column == "luck" else 0
                ability = value if column == "ability" else None
                await db.execute(
                    """
                    INSERT INTO user_data (season, user_id, coins, luck, ability, updated_at)
                    VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                    """,
                    (season, user_id, coins, luck, ability)
                )
    async def get_coins(self, user_id: int, season: str = 'db') -> Optional[int]:
        """유저의 토큰 수를 조회합니다. 등록되지 않은 유저인 경우 None을 반환합니다."""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT coins FROM user_data WHERE season = ? AND user_id = ?",
                (season, user_id)
            ) as cursor:
                row = await cursor.fetchone()
                return row[0] if row is not None else None

    async def add_coins(self, user_id: int, amount: int, season: str = 'db') -> int:
        """유저의 토큰을 증감하고 최종 잔액을 반환합니다. 유저가 없으면 새로 등록합니다."""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT coins FROM user_data WHERE season = ? AND user_id = ?",
                (season, user_id)
            ) as cursor:
                row = await cursor.fetchone()

            if row is None:
                new_coins = max(0, amount)
                await db.execute(
                    """
                    INSERT INTO user_data (season, user_id, coins, luck, ability, updated_at)
                    VALUES (?, ?, ?, 0, NULL, CURRENT_TIMESTAMP)
                    """,
                    (season, user_id, new_coins)
                )
            else:
                new_coins = max(0, row[0] + amount)
                await db.execute(
                    """
                    UPDATE user_data
                    SET coins = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE season = ? AND user_id = ?
                    """,
                    (new_coins, season, user_id)
                )
            await db.commit()
            return new_coins

    async def set_coins(self, user_id: int, amount: int, season: str = 'db') -> int:
        """유저의 토큰 잔액을 특정 값으로 설정합니다."""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT 1 FROM user_data WHERE season = ? AND user_id = ?",
                (season, user_id)
            ) as cursor:
                exists = await cursor.fetchone()

            if exists:
                await db.execute(
                    "UPDATE user_data SET coins = ?, updated_at = CURRENT_TIMESTAMP WHERE season = ? AND user_id = ?",
                    (amount, season, user_id)
                )
            else:
                await db.execute(
                    """
                    INSERT INTO user_data (season, user_id, coins, luck, ability, updated_at)
                    VALUES (?, ?, ?, 0, NULL, CURRENT_TIMESTAMP)
                    """,
                    (season, user_id, amount)
                )
            await db.commit()
            return amount

    async def get_luck(self, user_id: int, season: str = 'db') -> Optional[int]:
        """유저의 행운 수치를 조회합니다."""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT luck FROM user_data WHERE season = ? AND user_id = ?",
                (season, user_id)
            ) as cursor:
                row = await cursor.fetchone()
                return row[0] if row is not None else None
