#  Discord Activity Tracker Bot

> 디스코드 서버 내 유저들의 활동량(음성 채널 접속 시간, 텍스트 채팅)을 기록하고 통계를 제공하는 디스코드 봇 토이 프로젝트입니다.

##  주요 기능 (Features)

*  **음성 채널 통계 (Voice Stats):** 유저별 음성 채널 접속 시간을 초 단위로 측정하고 누적 기록합니다. 당월 통계는 매월 초기화되며, 과거 기록은 히스토리 테이블에 영구 보관됩니다.
*  **채팅 레벨링 시스템 (Chat Leveling):** 텍스트 채팅 참여도에 따라 경험치(XP)를 부여하고 레벨을 산정하여 서버 내 활동을 독려합니다.
*  **웹 대시보드 연동 (Web Dashboard):** 유저의 닉네임과 프로필 사진(Avatar URL) 메타데이터를 저장하여, 추후 외부 웹 대시보드에서 서버 활동 통계를 시각화할 수 있도록 아키텍처를 구성했습니다.

## 기술 스택 (Tech Stack)

* **Language:** Python
* **Database:** SQLite (`aiosqlite` 기반 비동기 DB 처리)
* **Library:** `discord.py` (추정)

##  데이터베이스 구조 (DB Schema)

비동기 봇 환경의 성능 최적화를 위해 `aiosqlite`를 활용하여 설계했습니다.

| 테이블명 | 역할 | 주요 컬럼 |
| :--- | :--- | :--- |
| **VoiceStats** | 당월 음성 시간 기록 | `user_id`, `total_seconds` |
| **LevelStats** | 누적 경험치 및 레벨 | `user_id`, `xp`, `level` |
| **VoiceHistory** | 월별 과거 기록 아카이브 | `user_id`, `year_month`, `total_seconds` |
| **Users** | 웹 대시보드용 메타데이터 | `user_id`, `username`, `avatar_url` |
