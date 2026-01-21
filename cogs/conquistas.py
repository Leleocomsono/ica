import discord
from discord.ext import commands
from datetime import datetime

class Conquistas(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    async def unlock_achievement(self, user_id: str, achievement_name: str):
        """Desbloquear uma conquista para um usuário"""
        try:
            conn = self.bot.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("SELECT achievement_id FROM conquistas WHERE name = ?", (achievement_name,))
            ach = cursor.fetchone()
            
            if not ach:
                conn.close()
                return
            
            achievement_id = ach['achievement_id']
            
            cursor.execute("SELECT * FROM conquistas_usuario WHERE user_id = ? AND achievement_id = ?", (user_id, achievement_id))
            if not cursor.fetchone():
                cursor.execute("""
                    INSERT INTO conquistas_usuario (user_id, achievement_id, unlocked_at)
                    VALUES (?, ?, ?)
                """, (user_id, achievement_id, datetime.now().isoformat()))
                conn.commit()
            
            conn.close()
        except:
            pass
    
    @commands.Cog.listener()
    async def on_message(self, message):
        """Verificar conquistas ao receber mensagens"""
        if message.author.bot:
            return
        
        user_id = str(message.author.id)
        
        try:
            conn = self.bot.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("SELECT messages FROM usuarios WHERE user_id = ?", (user_id,))
            user_data = cursor.fetchone()
            conn.close()
            
            if not user_data:
                return
            
            message_count = user_data['messages'] or 0
            
            if message_count == 1:
                await self.unlock_achievement(user_id, "Primeiro Passo")
            elif message_count == 100:
                await self.unlock_achievement(user_id, "Mensageiro")
            elif message_count == 500:
                await self.unlock_achievement(user_id, "Tagarela")
            elif message_count == 1000:
                await self.unlock_achievement(user_id, "Locutor")
        except:
            pass
    
    @commands.command(name='conquistas', aliases=['achievements'])
    async def conquistas(self, ctx, member: discord.Member = None):
        """Ver conquistas desbloqueadas"""
        member = member or ctx.author
        user_id = str(member.id)
        
        conn = self.bot.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT c.*, cu.unlocked_at,
            (SELECT COUNT(*) FROM conquistas_usuario WHERE achievement_id = c.achievement_id) * 100.0 / (SELECT COUNT(*) FROM usuarios) as current_rarity
            FROM conquistas c
            LEFT JOIN conquistas_usuario cu ON c.achievement_id = cu.achievement_id AND cu.user_id = ?
            ORDER BY cu.unlocked_at DESC NULLS LAST, c.achievement_id
        """, (user_id,))
        
        achievements = cursor.fetchall()
        conn.close()
        
        embed = discord.Embed(
            title=f"Conquistas de {member.display_name}",
            color=discord.Color.gold()
        )
        
        unlocked = []
        locked = []
        
        for ach in achievements:
            if ach['unlocked_at']:
                unlocked.append(ach)
            elif not ach['secret']:
                locked.append(ach)
        
        embed.description = f"**{len(unlocked)}** conquistas desbloqueadas"
        
        if unlocked:
            unlocked_text = ""
            for ach in unlocked[:10]:
                rarity = ach['current_rarity'] or 0.0
                unlocked_text += f"{ach['icon']} **{ach['name']}** ({rarity:.1f}%)\n└ {ach['description']}\n"
            embed.add_field(
                name="Desbloqueadas",
                value=unlocked_text[:1024] or "Nenhuma",
                inline=False
            )
        
        if locked:
            locked_text = ""
            for ach in locked[:5]:
                locked_text += f"🔒 **{ach['name']}**\n└ {ach['description']}\n"
            embed.add_field(
                name="Bloqueadas",
                value=locked_text[:1024] or "Nenhuma",
                inline=False
            )
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Conquistas(bot))
