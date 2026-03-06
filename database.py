import aiosqlite
import os

DB_PATH = "bot_data.db"

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        # 음성 시간 측정 테이블 (월마다 초기화)
        # user_id: 디스코드 유저 ID
        # total_seconds: 이번 달 누적 음성 채널 접속 시간 (초)
        await db.execute('''
            CREATE TABLE IF NOT EXISTS VoiceStats (
                user_id INTEGER PRIMARY KEY,
                total_seconds INTEGER DEFAULT 0
            )
        ''')

        # 텍스트 채팅 레벨업 테이블 (계속 누적)
        # user_id: 디스코드 유저 ID
        # xp: 현재 누적 경험치
        # level: 현재 레벨
        await db.execute('''
            CREATE TABLE IF NOT EXISTS LevelStats (
                user_id INTEGER PRIMARY KEY,
                xp INTEGER DEFAULT 0,
                level INTEGER DEFAULT 1
            )
        ''')
        
        # 월별 과거 음성 기록 보관 테이블
        # user_id: 디스코드 유저 ID
        # year_month: "YYYY-MM" 형식의 월
        # total_seconds: 해당 월의 음성 채널 누적 시간 (초)
        await db.execute('''
            CREATE TABLE IF NOT EXISTS VoiceHistory (
                user_id INTEGER,
                year_month TEXT,
                total_seconds INTEGER,
                PRIMARY KEY (user_id, year_month)
            )
        ''')
        
        # 유저 메타데이터 보관 테이블 (웹 대시보드용)
        # user_id: 디스코드 유저 ID
        # username: 디스코드 닉네임 (display_name)
        # avatar_url: 프로필 사진 URL
        await db.execute('''
            CREATE TABLE IF NOT EXISTS Users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                avatar_url TEXT
            )
        ''')
        
        await db.commit()

async def get_db_connection():
    return await aiosqlite.connect(DB_PATH)
