import aiosqlite
import os
import datetime
from typing import Any, Optional, Tuple, Dict


class LegacyRecord:
    """
    기존 디스코드 메시지 기반 DB(find_id)와의 하위 호환성을 제공하는 레코드 래퍼.
    .content 및 await .edit(content=...) 인터페이스를 지원하여 기존 미니게임들이
    수정 없이도 정상 작동하도록 돕습니다.
    """
    def __init__(self, db: "Database", user_id: int, selector: str, value: Any):
        self.db = db
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
        await self.db.update_single_field(self.user_id, self.selector, new_val)


class Database:
    def __init__(self, db_path: str = "zerogun.db"):
        self.db_path = db_path

    async def init_db(self):
        """데이터베이스 및 테이블을 초기화합니다."""
        async with aiosqlite.connect(self.db_path, timeout=10.0) as db:
            await db.execute("PRAGMA journal_mode = WAL;")
            await db.execute("PRAGMA synchronous = NORMAL;")
            await db.execute("PRAGMA busy_timeout = 5000;")
            await db.execute("""
                CREATE TABLE IF NOT EXISTS user_data (
                    user_id INTEGER PRIMARY KEY,
                    coins INTEGER NOT NULL DEFAULT 0,
                    luck INTEGER NOT NULL DEFAULT 0,
                    ability TEXT DEFAULT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_coins 
                ON user_data(coins DESC)
            """)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS daily_rewards (
                    user_id INTEGER NOT NULL,
                    reward_type TEXT NOT NULL,
                    reward_date TEXT NOT NULL,
                    PRIMARY KEY (user_id, reward_type)
                )
            """)
            await db.commit()

    async def find_data(self, user_id_or_season: Any, user_id: Optional[int] = None) -> Tuple[Optional[bool], Dict[str, Any]]:
        """
        유저 ID에 해당하는 데이터를 조회합니다.
        하위 호환성을 위해 find_data('db', user_id) 및 find_data(user_id) 형태 모두 지원합니다.
        반환 형식: (find_marker, data_dict)
        """
        target_id = user_id if user_id is not None else int(user_id_or_season)
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT coins, luck, ability FROM user_data WHERE user_id = ?",
                (target_id,)
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

    async def update_data(self, user_id: int, data: dict, message: Any = None, *args, **kwargs):
        """
        유저 데이터를 갱신하거나 새로 등록(UPSERT)합니다.
        """
        coins = data.get('$')
        luck = data.get('%')
        ability = data.get('*')

        async with aiosqlite.connect(self.db_path) as db:
            # 기존 레코드 확인
            async with db.execute(
                "SELECT coins, luck, ability FROM user_data WHERE user_id = ?",
                (user_id,)
            ) as cursor:
                existing = await cursor.fetchone()

            if existing is None:
                # 새 레코드 삽입
                await db.execute(
                    """
                    INSERT INTO user_data (user_id, coins, luck, ability, updated_at)
                    VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                    """,
                    (user_id, coins if coins is not None else 0, luck if luck is not None else 0, ability)
                )
            else:
                # 기존 레코드 갱신 (제공된 필드만 반영)
                new_coins = coins if coins is not None else existing[0]
                new_luck = luck if luck is not None else existing[1]
                new_ability = ability if '*' in data else existing[2]

                await db.execute(
                    """
                    UPDATE user_data
                    SET coins = ?, luck = ?, ability = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE user_id = ?
                    """,
                    (new_coins, new_luck, new_ability, user_id)
                )
            await db.commit()

    async def collect_data(self, *args, **kwargs) -> Dict[int, Dict[str, Any]]:
        """
        모든 유저 데이터를 코인 내림차순으로 가져옵니다.
        반환 형식: {user_id: {'$': coins, '%': luck, '*': ability, ...}}
        """
        data_dict: Dict[int, Dict[str, Any]] = {}
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT user_id, coins, luck, ability FROM user_data ORDER BY coins DESC"
            ) as cursor:
                rows = await cursor.fetchall()
                for row in rows:
                    uid, coins, luck, ability = row
                    d: Dict[str, Any] = {'$': coins, '%': luck}
                    if ability is not None:
                        d['*'] = ability
                    data_dict[uid] = d
        return data_dict

    async def dump_data(self, *args, **kwargs) -> list[Dict[str, Any]]:
        """
        데이터베이스의 전체 유저 데이터를 상세 리스트로 반환합니다.
        """
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT user_id, coins, luck, ability, updated_at FROM user_data ORDER BY coins DESC"
            ) as cursor:
                rows = await cursor.fetchall()
                results = []
                for row in rows:
                    uid, coins, luck, ability, updated_at = row
                    results.append({
                        "user_id": uid,
                        "coins": coins,
                        "luck": luck,
                        "ability": ability,
                        "updated_at": updated_at
                    })
                return results

    async def find_id(self, selector: str, user_id: int, *args, **kwargs) -> Optional[LegacyRecord]:
        """
        기존 find_id(selector, user_id) 호출과의 하위 호환을 위한 메서드.
        LegacyRecord 객체를 반환하여 .content와 .edit(...) 동작을 지원합니다.
        """
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT coins, luck, ability FROM user_data WHERE user_id = ?",
                (user_id,)
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

                return LegacyRecord(self, user_id, selector, val)

    async def update_single_field(self, user_id: int, selector: str, value: Any, *args, **kwargs):
        """단일 속성(선택자)을 갱신합니다."""
        column = "coins"
        if selector == '%':
            column = "luck"
        elif selector == '*':
            column = "ability"

        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT 1 FROM user_data WHERE user_id = ?",
                (user_id,)
            ) as cursor:
                exists = await cursor.fetchone()

            if exists:
                await db.execute(
                    f"UPDATE user_data SET {column} = ?, updated_at = CURRENT_TIMESTAMP WHERE user_id = ?",
                    (value, user_id)
                )
            else:
                coins = value if column == "coins" else 0
                luck = value if column == "luck" else 0
                ability = value if column == "ability" else None
                await db.execute(
                    """
                    INSERT INTO user_data (user_id, coins, luck, ability, updated_at)
                    VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                    """,
                    (user_id, coins, luck, ability)
                )
            await db.commit()

    async def get_coins(self, user_id: int, *args, **kwargs) -> Optional[int]:
        """유저의 토큰 수를 조회합니다. 등록되지 않은 유저인 경우 None을 반환합니다."""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT coins FROM user_data WHERE user_id = ?",
                (user_id,)
            ) as cursor:
                row = await cursor.fetchone()
                return row[0] if row is not None else None

    async def add_coins(self, user_id: int, amount: int, *args, **kwargs) -> int:
        """
        유저의 토큰을 원자적으로 증감하고 최종 잔액을 반환합니다.
        유저가 없으면 새로 등록하며, 결과는 0 미만으로 내려가지 않습니다.
        """
        async with aiosqlite.connect(self.db_path, timeout=10.0) as db:
            async with db.execute(
                """
                INSERT INTO user_data (user_id, coins, luck, ability, updated_at)
                VALUES (?, MAX(0, ?), 0, NULL, CURRENT_TIMESTAMP)
                ON CONFLICT(user_id) DO UPDATE SET
                    coins = MAX(0, user_data.coins + ?),
                    updated_at = CURRENT_TIMESTAMP
                RETURNING coins
                """,
                (user_id, amount, amount)
            ) as cursor:
                row = await cursor.fetchone()
                await db.commit()
                return row[0] if row is not None else 0

    async def consume_coins(self, user_id: int, amount: int, *args, **kwargs) -> Tuple[bool, Optional[int]]:
        """
        유저의 토큰을 원자적으로(atomically) 차감합니다.
        - 잔액이 amount 이상일 때만 차감하고 (True, new_coins)를 반환합니다.
        - 잔액이 부족하거나 미등록 유저인 경우 (False, current_coins)를 반환합니다 (미등록 시 None).
        - 단일 SQL UPDATE WHERE 절로 처리되어 동시 요청(Race Condition) 시에도 중복 소모가 원천 차단됩니다.
        """
        if amount <= 0:
            coins = await self.get_coins(user_id)
            return (True, coins) if coins is not None else (False, None)

        async with aiosqlite.connect(self.db_path, timeout=10.0) as db:
            async with db.execute(
                """
                UPDATE user_data
                SET coins = coins - ?, updated_at = CURRENT_TIMESTAMP
                WHERE user_id = ? AND coins >= ?
                RETURNING coins
                """,
                (amount, user_id, amount)
            ) as cursor:
                row = await cursor.fetchone()
                if row is not None:
                    await db.commit()
                    return True, row[0]

            # 차감 실패 시 현재 잔액 및 등록 상태 확인
            async with db.execute("SELECT coins FROM user_data WHERE user_id = ?", (user_id,)) as cursor:
                row = await cursor.fetchone()
                if row is None:
                    return False, None
                return False, row[0]

    async def set_coins(self, user_id: int, amount: int, *args, **kwargs) -> int:
        """유저의 토큰 잔액을 특정 값으로 원자적으로 설정합니다."""
        target_amount = max(0, amount)
        async with aiosqlite.connect(self.db_path, timeout=10.0) as db:
            async with db.execute(
                """
                INSERT INTO user_data (user_id, coins, luck, ability, updated_at)
                VALUES (?, ?, 0, NULL, CURRENT_TIMESTAMP)
                ON CONFLICT(user_id) DO UPDATE SET
                    coins = ?,
                    updated_at = CURRENT_TIMESTAMP
                RETURNING coins
                """,
                (user_id, target_amount, target_amount)
            ) as cursor:
                row = await cursor.fetchone()
                await db.commit()
                return row[0] if row is not None else target_amount

    async def get_luck(self, user_id: int, *args, **kwargs) -> Optional[int]:
        """유저의 행운 수치를 조회합니다."""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT luck FROM user_data WHERE user_id = ?",
                (user_id,)
            ) as cursor:
                row = await cursor.fetchone()
                return row[0] if row is not None else None

    async def claim_daily_reward(
        self, user_id: int, reward_type: str = "greeting", amount: int = 10, date_str: Optional[str] = None
    ) -> Tuple[bool, int]:
        """
        유저별 일일 보상을 지급합니다.
        - 오늘 이미 보상을 수령했으면 (False, 현재 코인 수)를 반환합니다.
        - 오늘 첫 수령이면 보상(amount)을 원자적으로 추가하고 (True, 갱신된 코인 수)를 반환합니다.
        - 날짜는 기본적으로 한국 표준시(KST, UTC+9) 기준 YYYY-MM-DD 형식으로 관리됩니다.
        """
        if date_str is None:
            kst = datetime.timezone(datetime.timedelta(hours=9))
            date_str = datetime.datetime.now(kst).strftime("%Y-%m-%d")

        async with aiosqlite.connect(self.db_path, timeout=10.0) as db:
            await db.execute("PRAGMA busy_timeout = 5000;")
            await db.execute("""
                CREATE TABLE IF NOT EXISTS daily_rewards (
                    user_id INTEGER NOT NULL,
                    reward_type TEXT NOT NULL,
                    reward_date TEXT NOT NULL,
                    PRIMARY KEY (user_id, reward_type)
                )
            """)
            cursor = await db.execute(
                """
                INSERT INTO daily_rewards (user_id, reward_type, reward_date)
                VALUES (?, ?, ?)
                ON CONFLICT(user_id, reward_type) DO UPDATE SET
                    reward_date = excluded.reward_date
                WHERE daily_rewards.reward_date != excluded.reward_date
                """,
                (user_id, reward_type, date_str)
            )
            claimed = cursor.rowcount > 0

            if claimed:
                # 당일 첫 수령: 코인 지급 (원자적 UPSERT)
                async with db.execute(
                    """
                    INSERT INTO user_data (user_id, coins, luck, ability, updated_at)
                    VALUES (?, MAX(0, ?), 0, NULL, CURRENT_TIMESTAMP)
                    ON CONFLICT(user_id) DO UPDATE SET
                        coins = MAX(0, user_data.coins + ?),
                        updated_at = CURRENT_TIMESTAMP
                    RETURNING coins
                    """,
                    (user_id, amount, amount)
                ) as coin_cur:
                    coin_row = await coin_cur.fetchone()
                    new_coins = coin_row[0] if coin_row is not None else amount
                await db.commit()
                return True, new_coins
            else:
                # 이미 수령함: 현재 코인 잔액 조회
                async with db.execute(
                    "SELECT coins FROM user_data WHERE user_id = ?",
                    (user_id,)
                ) as coin_cur:
                    coin_row = await coin_cur.fetchone()
                    current_coins = coin_row[0] if coin_row is not None else 0
                return False, current_coins

