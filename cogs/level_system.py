import discord
from discord.ext import commands
import time
import database

class LevelSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # 유저별 마지막 메시지 전송 시간을 기록하여 도배 방지 (값: timestamp)
        self.cooldowns = {}
        # 경험치 획득 쿨타임 (초) - 여기서는 60초마다 경험치 획득 가능하도록 설정
        self.cooldown_amount = 60

    def get_xp_requirement(self, level):
        """레벨업에 필요한 경험치 계산 (예: 5 * (level ^ 2) + 50 * level + 100)"""
        return 5 * (level ** 2) + 50 * level + 100

    @commands.Cog.listener()
    async def on_message(self, message):
        # 봇의 메시지는 무시
        if message.author.bot:
            return

        user_id = message.author.id
        current_time = time.time()

        # 쿨타임 체크
        if user_id in self.cooldowns:
            if current_time - self.cooldowns[user_id] < self.cooldown_amount:
                return # 쿨타임 중이면 경험치 부여 안 함

        # 쿨타임 갱신
        self.cooldowns[user_id] = current_time

        # 경험치 부여 (지급량은 15~25 사이 랜덤 등 다양하게 설정 가능, 여기서는 고정값 20 부여)
        xp_to_add = 20

        db = await database.get_db_connection()
        # 데이터가 없으면 삽입하고, 있으면 무시하여 초기 설정
        await db.execute('''
            INSERT OR IGNORE INTO LevelStats (user_id, xp, level)
            VALUES (?, 0, 1)
        ''', (user_id,))
        
        # 현재 유저 정보 가져오기
        async with db.execute('SELECT xp, level FROM LevelStats WHERE user_id = ?', (user_id,)) as cursor:
            row = await cursor.fetchone()
            if row:
                current_xp, current_level = row
                new_xp = current_xp + xp_to_add
                
                # 레벨업 체크
                required_xp = self.get_xp_requirement(current_level)
                if new_xp >= required_xp:
                    current_level += 1
                    new_xp -= required_xp # 남은 경험치 이월
                    await message.channel.send(f"🎉 축하합니다! {message.author.mention}님이 **레벨 {current_level}**(으)로 레벨업 하셨습니다!")

                # DB 업데이트
                await db.execute('UPDATE LevelStats SET xp = ?, level = ? WHERE user_id = ?', (new_xp, current_level, user_id))
                
        await db.commit()
        await db.close()

    @commands.command(name='내정보')
    async def my_info(self, ctx):
        """자신의 레벨, 경험치, 음성 채널 누적 시간을 확인합니다."""
        user_id = ctx.author.id
        db = await database.get_db_connection()
        
        # 레벨 정보 가져오기
        xp, level = 0, 1
        async with db.execute('SELECT xp, level FROM LevelStats WHERE user_id = ?', (user_id,)) as cursor:
            row = await cursor.fetchone()
            if row:
                xp, level = row

        # 음성 시간 가져오기
        total_seconds = 0
        async with db.execute('SELECT total_seconds FROM VoiceStats WHERE user_id = ?', (user_id,)) as cursor:
            row = await cursor.fetchone()
            if row:
                total_seconds = row[0]
                
        await db.close()

        # 만약 유저가 현재 음성 채널에 있다면, 이번 접속으로 쌓인 시간도 실시간으로 보여주기
        cog = self.bot.get_cog('VoiceTracker')
        if cog and user_id in cog.voice_sessions:
            current_session_time = int(time.time() - cog.voice_sessions[user_id])
            total_seconds += current_session_time

        # 시간 포맷팅 (예: 1시간 30분 15초)
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

        required_xp = self.get_xp_requirement(level)

        embed = discord.Embed(title=f"{ctx.author.display_name}님의 통계", color=discord.Color.brand_green())
        
        # 프로필 사진이 있는 경우만 썸네일 설정
        if ctx.author.display_avatar:
            embed.set_thumbnail(url=ctx.author.display_avatar.url)
            
        embed.add_field(name="✨ 레벨", value=f"**{level}**", inline=True)
        embed.add_field(name="📈 경험치 (XP)", value=f"{xp} / {required_xp}", inline=True)
        embed.add_field(name="🎙️ 이번 달 음성 채널 누적 시간", value=time_str, inline=False)
        
        embed.set_footer(text="음성 시간은 매월 1일 자정에 초기화됩니다. 레벨은 계속 누적됩니다.")
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(LevelSystem(bot))
