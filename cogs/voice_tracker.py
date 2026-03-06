import discord
from discord.ext import commands
import time
import datetime
import database
from apscheduler.schedulers.asyncio import AsyncioScheduler

class VoiceTracker(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # 유저별 음성채널 접속 시간을 기록하는 딕셔너리
        self.voice_sessions = {}
        
        # 월별 초기화를 위한 스케줄러 세팅
        self.scheduler = AsyncioScheduler()
        # 매월 1일 자정(0시 0분)에 reset_monthly_voice_stats 함수 실행
        self.scheduler.add_job(self.reset_monthly_voice_stats, 'cron', day=1, hour=0, minute=0)
        self.scheduler.start()

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        # 봇은 시간 측정에서 제외 (원한다면 제거 가능)
        if member.bot:
            return
            
        # 입장하는 경우 (이전 채널이 없고, 새로운 채널에 접속)
        # 또는 채널을 이동하는 경우 (이전 채널과 다음 채널이 다름)
        
        # 입장 처리
        if before.channel is None and after.channel is not None:
            self.voice_sessions[member.id] = time.time()
            
        # 퇴장 처리 (이전 채널에 있었고, 이제 채널에서 나감)
        elif before.channel is not None and after.channel is None:
            if member.id in self.voice_sessions:
                join_time = self.voice_sessions.pop(member.id)
                session_time = int(time.time() - join_time)
                
                # 유저 정보 저장 (웹 대시보드 시각화용)
                username = member.display_name
                avatar_url = member.display_avatar.url if member.display_avatar else ""
                db = await database.get_db_connection()
                await db.execute('''
                    INSERT INTO Users (user_id, username, avatar_url)
                    VALUES (?, ?, ?)
                    ON CONFLICT(user_id) DO UPDATE SET
                    username = excluded.username,
                    avatar_url = excluded.avatar_url
                ''', (member.id, username, avatar_url))
                await db.commit()
                await db.close()

                await self.add_voice_time(member.id, session_time)
                
        # 채널 이동 (A채널 -> B채널)
        # 시간은 계속 누적해야 하므로 따로 기록 종료/시작을 하지 않거나,
        # 여기서 정산 후 다시 시작할 수도 있습니다.
        # 이 코드에서는 접속 유지로 간주하여 아무것도 하지 않습니다.

    async def add_voice_time(self, user_id, session_time):
        """DB에 사용자의 음성 채널 체류 시간을 합산하여 저장합니다."""
        db = await database.get_db_connection()
        await db.execute('''
            INSERT INTO VoiceStats (user_id, total_seconds) 
            VALUES (?, ?) 
            ON CONFLICT(user_id) 
            DO UPDATE SET total_seconds = total_seconds + excluded.total_seconds
        ''', (user_id, session_time))
        await db.commit()
        await db.close()

    async def reset_monthly_voice_stats(self):
        """매달 1일 자정에 실행되어 기록을 백업하고 초기화합니다."""
        db = await database.get_db_connection()
        
        # 초기화되기 전, 즉 '해당 기록의 달(지난 달)'을 계산합니다.
        # 실행 시점은 1일 0시 0분 근처이므로 1일 전으로 계산하여 달을 구합니다.
        now = datetime.datetime.now()
        last_month = now - datetime.timedelta(days=1)
        year_month = last_month.strftime("%Y-%m")
        
        # 초기화 전 값을 VoiceHistory에 백업 (방금 달의 기록 복사)
        # 0초보다 큰 유저들만 백업
        await db.execute('''
            INSERT OR REPLACE INTO VoiceHistory (user_id, year_month, total_seconds)
            SELECT user_id, ?, total_seconds 
            FROM VoiceStats 
            WHERE total_seconds > 0
        ''', (year_month,))
        
        # 새로운 달을 위해 기존 테이블 0으로 초기화
        await db.execute('UPDATE VoiceStats SET total_seconds = 0')
        await db.commit()
        await db.close()
        print(f"[{year_month}] 이번 달 음성 채널 누적 시간이 백업 및 초기화되었습니다.")

    @commands.command(name='과거기록')
    async def past_record(self, ctx, year_month: str = None):
        """YYYY-MM 형식으로 지난 달의 음성 누적 시간을 확인합니다. (예: !과거기록 2023-10)"""
        user_id = ctx.author.id
        db = await database.get_db_connection()
        
        # 파라미터가 없으면 직전 달의 기록을 기본적으로 보여줍니다.
        if year_month is None:
            now = datetime.datetime.now()
            # 지금이 만약 1일이라면 저번 달을, 아니면 현재 달을 보여줘야 할 수도 있지만
            # 보통 '과거(이전)' 기록을 보므로 직전 달로 간주
            last_month_date = now.replace(day=1) - datetime.timedelta(days=1)
            year_month = last_month_date.strftime("%Y-%m")
            
        async with db.execute('SELECT total_seconds FROM VoiceHistory WHERE user_id = ? AND year_month = ?', (user_id, year_month)) as cursor:
            row = await cursor.fetchone()
        
        await db.close()
        
        if row:
            total_seconds = row[0]
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            seconds = total_seconds % 60
            
            time_str = ""
            if hours > 0:
                time_str += f"{hours}시간 "
            if minutes > 0:
                time_str += f"{minutes}분 "
            time_str += f"{seconds}초"
            if time_str == "":
                time_str = "0초"
                
            embed = discord.Embed(title=f"⏳ {year_month} 과거 음성 채널 기록", color=discord.Color.blue())
            embed.description = f"{ctx.author.mention}님의 {year_month} 누적 접속 시간은 **{time_str}**입니다."
            await ctx.send(embed=embed)
        else:
            await ctx.send(f"❌ {ctx.author.mention}님, `{year_month}`에 해당하는 음성 채널 기록이 없습니다.\n(*참고: YYYY-MM 형식으로 적어주세요.*)")

async def setup(bot):
    await bot.add_cog(VoiceTracker(bot))
