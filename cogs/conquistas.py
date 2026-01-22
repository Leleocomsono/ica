# cogs/conquistas.py completo com fixes (adicionado update de messages no on_message para rastrear atributos/conquistas)

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
            
            achievement_id = ach['achievement_id'] if 'achievement_id' in ach else None
            
            if achievement_id is None:
                conn.close()
                return
            
            cursor.execute("SELECT * FROM conquistas_usuario WHERE user_id = ? AND achievement_id = ?", (user_id, achievement_id))
            if not cursor.fetchone():
                cursor.execute("""
                    INSERT INTO conquistas_usuario (user_id, achievement_id, unlocked_at)
                    VALUES (?, ?, ?)
                """, (user_id, achievement_id, datetime.now().isoformat()))
                conn.commit()
            
            conn.close()
        except Exception as e:
            print(f"Erro ao desbloquear conquista: {e}")
    
    @commands.Cog.listener()
    async def on_message(self, message):
        """Verificar conquistas ao receber mensagens e atualizar contador"""
        if message.author.bot:
            return
        
        user_id = str(message.author.id)
        
        try:
            conn = self.bot.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("SELECT messages FROM usuarios WHERE user_id = ?", (user_id,))
            user_data = cursor.fetchone()
            
            message_count = user_data['messages'] if user_data and 'messages' in user_data else 0
            message_count += 1  # Incrementar contador
            
            cursor.execute("UPDATE usuarios SET messages = ? WHERE user_id = ?", (message_count, user_id))
            conn.commit()
            
            conn.close()
            
            # Agora verificar conquistas com o novo count
            if message_count == 1:
                await self.unlock_achievement(user_id, "Primeiro Passo")
            elif message_count == 100:
                await self.unlock_achievement(user_id, "Mensageiro")
            elif message_count == 500:
                await self.unlock_achievement(user_id, "Tagarela")
            elif message_count == 1000:
                await self.unlock_achievement(user_id, "Locutor")
        except Exception as e:
            print(f"Erro no on_message conquistas: {e}")
    
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
            if 'unlocked_at' in ach and ach['unlocked_at']:
                unlocked.append(ach)
            elif 'secret' in ach and not ach['secret']:
                locked.append(ach)
        
        embed.description = f"**{len(unlocked)}** conquistas desbloqueadas"
        
        if unlocked:
            unlocked_text = ""
            for ach in unlocked[:10]:
                rarity = ach['current_rarity'] if 'current_rarity' in ach else 0.0
                icon = ach['icon'] if 'icon' in ach else ''
                name = ach['name'] if 'name' in ach else 'Desconhecido'
                description = ach['description'] if 'description' in ach else 'Sem descrição'
                unlocked_text += f"{icon} **{name}** ({rarity:.1f}%)\n└ {description}\n"
            embed.add_field(
                name="Desbloqueadas",
                value=unlocked_text[:1024] or "Nenhuma",
                inline=False
            )
        
        if locked:
            locked_text = ""
            for ach in locked[:5]:
                name = ach['name'] if 'name' in ach else 'Desconhecido'
                description = ach['description'] if 'description' in ach else 'Sem descrição'
                locked_text += f"Locked **{name}**\n└ {description}\n"
            embed.add_field(
                name="Bloqueadas",
                value=locked_text[:1024] or "Nenhuma",
                inline=False
            )
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Conquistas(bot))
