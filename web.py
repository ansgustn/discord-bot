import sqlite3
from flask import Flask, render_template

app = Flask(__name__)
DB_PATH = "bot_data.db"

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    conn = get_db_connection()
    # 전체 랭킹 조회 (경험치, 레벨, 음성 시간) 및 Users 테이블을 통한 유저정보 획득
    query = '''
        WITH AllUsers AS (
            SELECT user_id FROM Users
            UNION
            SELECT user_id FROM LevelStats
            UNION
            SELECT user_id FROM VoiceStats
        )
        SELECT
            AllUsers.user_id,
            COALESCE(Users.username, '알 수 없는 유저') as username,
            COALESCE(Users.avatar_url, '') as avatar_url,
            COALESCE(LevelStats.level, 1) as level,
            COALESCE(LevelStats.xp, 0) as xp,
            COALESCE(VoiceStats.total_seconds, 0) as total_seconds
        FROM AllUsers
        LEFT JOIN Users ON AllUsers.user_id = Users.user_id
        LEFT JOIN LevelStats ON AllUsers.user_id = LevelStats.user_id
        LEFT JOIN VoiceStats ON AllUsers.user_id = VoiceStats.user_id
        ORDER BY level DESC, xp DESC, total_seconds DESC
    '''
    users = conn.execute(query).fetchall()
    
    # 각 유저의 다음 레벨 필요 경험치 등 계산용 딕셔너리 리스트 생성
    user_list = []
    for u in users:
        level = u['level']
        req_xp = 5 * (level ** 2) + 50 * level + 100
        
        # 시간 포맷팅
        secs = u['total_seconds']
        h, remainder = divmod(secs, 3600)
        m, s = divmod(remainder, 60)
        time_str = ""
        if h > 0: time_str += f"{h}h "
        if m > 0: time_str += f"{m}m "
        time_str += f"{s}s"
        if time_str == "0s": time_str = "-"
        
        user_list.append({
            'username': u['username'],
            'avatar_url': u['avatar_url'] if u['avatar_url'] else "https://cdn.discordapp.com/embed/avatars/0.png",
            'level': level,
            'xp': u['xp'],
            'req_xp': req_xp,
            'xp_percent': min(100, int((u['xp'] / req_xp) * 100)),
            'total_seconds': time_str
        })
        
    conn.close()
    return render_template('index.html', users=user_list)

if __name__ == '__main__':
    # 외부망 접속 허용을 위해 host를 0.0.0.0으로 엽니다.
    app.run(host='0.0.0.0', port=5000, debug=True)
