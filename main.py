import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
import database

# .env 파일 로드
load_dotenv()
TOKEN = os.getenv('DISCORD_BOT_TOKEN')

class CustomBot(commands.Bot):
    def __init__(self):
        # 봇의 권한(Intents) 설정
        intents = discord.Intents.default()
        intents.message_content = True  # 메시지 내용을 읽기 위함 (레벨업)
        intents.voice_states = True     # 음성 채널 상태 변경을 읽기 위함 (시간 측정)
        intents.members = True          # 서버 내 멤버 정보 읽기 위함
        
        super().__init__(
            command_prefix='!',         # 명령어 접두사 (예: !내정보)
            intents=intents
        )
        
    async def setup_hook(self):
        # 데이터베이스 초기화
        await database.init_db()
        print("데이터베이스 세팅 완료.")
        
        # 기능 추가 (Cogs)
        # Cogs 파일을 만들기 전에는 주석 처리 또는 try-except 권장
        for cog in ['cogs.voice_tracker', 'cogs.level_system']:
            try:
                await self.load_extension(cog)
                print(f"{cog} 로드 성공!")
            except Exception as e:
                print(f"{cog} 로드 실패: {e}")

bot = CustomBot()

@bot.event
async def on_ready():
    print(f'로그인 성공: {bot.user} (ID: {bot.user.id})')
    print('-----------------------------------------')

if __name__ == '__main__':
    if not TOKEN or TOKEN == '여기에_봇_토큰을_입력하세요':
        print("오류: .env 파일에 올바른 DISCORD_BOT_TOKEN을 입력해주세요!")
    else:
        bot.run(TOKEN)
