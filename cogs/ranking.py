import discord
from discord.ext import commands
import database

class RankingSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='전체통계', aliases=['랭킹', '유저목록'])
    async def all_stats(self, ctx):
        """서버 내 모든 유저의 레벨, 경험치, 및 음성 시간을 보여줍니다."""
        
        # '봇이 메시지를 타이핑 중' 상태 표시 (명령어 처리가 오래 걸릴 경우 대비)
        async with ctx.typing():
            db = await database.get_db_connection()
            
            # 레벨(LevelStats)과 음성시간(VoiceStats) 데이터를 모두 가져오기 위해 FULL OUTER JOIN과 유사한 효과를 내는 쿼리
            # SQLite는 FULL OUTER JOIN을 기본 지원하지 않는 경우가 있어, UNION ALL 및 LEFT JOIN을 활용하여 직접 병합
            query = '''
            WITH AllUsers AS (
                SELECT user_id FROM LevelStats
                UNION
                SELECT user_id FROM VoiceStats
            )
            SELECT
                AllUsers.user_id,
                COALESCE(LevelStats.level, 1) as level,
                COALESCE(LevelStats.xp, 0) as xp,
                COALESCE(VoiceStats.total_seconds, 0) as total_seconds
            FROM AllUsers
            LEFT JOIN LevelStats ON AllUsers.user_id = LevelStats.user_id
            LEFT JOIN VoiceStats ON AllUsers.user_id = VoiceStats.user_id
            ORDER BY level DESC, xp DESC, total_seconds DESC
            '''
            
            async with db.execute(query) as cursor:
                rows = await cursor.fetchall()
                
            await db.close()

            if not rows:
                await ctx.send("아직 기록된 유저 데이터가 없습니다.")
                return

            embed = discord.Embed(title="📊 서버 전체 유저 통계 (랭킹)", color=discord.Color.gold())
            embed.description = "경험치 및 레벨이 높은 순으로 정렬되었습니다.\n\n"
            
            count = 1
            for row in rows:
                user_id, level, xp, total_seconds = row
                
                # 디스코드 사용자 정보 가져오기 시도
                user = self.bot.get_user(user_id)
                if not user:
                    user_name = f"알 수 없는 유저 ({user_id})"
                else:
                    user_name = user.display_name
                
                # 시간 포맷팅
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
                
                # 레벨업에 필요한 경험치 계산 (level_system.py와 동일한 공식 유지)
                required_xp = 5 * (level ** 2) + 50 * level + 100
                
                # Embed에 추가
                field_value = f"**레벨 {level}** (XP: {xp}/{required_xp})\n🎙️ 음성 시간: {time_str}"
                
                # 디스코드 embed 최대 field 개수 제한 (25개)를 고려
                if count <= 20: 
                    embed.add_field(name=f"#{count} {user_name}", value=field_value, inline=False)
                count += 1
            
            if len(rows) > 20:
                embed.set_footer(text=f"현재 상위 20명만 표시됩니다. (총 기록된 유저 수: {len(rows)}명)")
            else:
                embed.set_footer(text=f"총 기록된 유저 수: {len(rows)}명")
                
            await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(RankingSystem(bot))
