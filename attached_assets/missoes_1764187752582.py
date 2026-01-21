import discord
from discord.ext import commands
from datetime import datetime

class Missoes(commands.Cog):
    """Sistema de missões"""
    
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(name='missao', aliases=['missoes', 'quests'])
    async def missao(self, ctx):
        """Ver missões disponíveis"""
        user_id = str(ctx.author.id)
        self.bot.db.ensure_user_exists(user_id)
        
        conn = self.bot.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT m.mission_id, m.title, m.description, m.target_value, m.reward_type, m.reward_value,
                   COALESCE(mp.current_progress, 0) as progress, COALESCE(mp.completed, 0) as completed
            FROM missoes m
            LEFT JOIN missoes_progresso mp ON m.mission_id = mp.mission_id AND mp.user_id = ?
        """, (user_id,))
        
        missions = cursor.fetchall()
        conn.close()
        
        if not missions:
            await ctx.send("❌ Não há missões disponíveis!")
            return
        
        embed = discord.Embed(
            title="📜 Missões Disponíveis",
            color=discord.Color.blue()
        )
        
        for mission in missions[:10]:
            if mission['completed']:
                status = "✅ Completa"
            else:
                progress = mission['progress']
                target = mission['target_value']
                percentage = int((progress / target) * 100) if target > 0 else 0
                status = f"📊 {progress}/{target} ({percentage}%)"
            
            reward_emoji = "💰" if mission['reward_type'] == "coins" else "⭐"
            reward_text = f"{mission['reward_value']} {'moedas' if mission['reward_type'] == 'coins' else 'XP'}"
            
            embed.add_field(
                name=f"{mission['title']}",
                value=f"{mission['description']}\n{status}\n{reward_emoji} Recompensa: {reward_text}",
                inline=False
            )
        
        await ctx.send(embed=embed)
    
    @commands.command(name='missao-concluir', aliases=['claim-mission'])
    async def missao_concluir(self, ctx, mission_id: int):
        """Concluir uma missão"""
        user_id = str(ctx.author.id)
        
        conn = self.bot.db.get_connection()
        cursor = conn.cursor()
        
        # Verificar se a missão está completa
        cursor.execute("""
            SELECT m.title, m.reward_type, m.reward_value, mp.completed
            FROM missoes m
            JOIN missoes_progresso mp ON m.mission_id = mp.mission_id
            WHERE m.mission_id = ? AND mp.user_id = ? AND mp.completed = 1
        """, (mission_id, user_id))
        
        mission = cursor.fetchone()
        
        if not mission:
            await ctx.send("❌ Missão não encontrada ou não completa!")
            conn.close()
            return
        
        # Dar recompensa
        if mission['reward_type'] == 'coins':
            cursor.execute("UPDATE economia SET coins = coins + ? WHERE user_id = ?", (mission['reward_value'], user_id))
            reward_text = f"{mission['reward_value']} moedas"
        else:  # xp
            cursor.execute("UPDATE usuarios SET xp = xp + ? WHERE user_id = ?", (mission['reward_value'], user_id))
            reward_text = f"{mission['reward_value']} XP"
        
        # Remover missão do progresso
        cursor.execute("DELETE FROM missoes_progresso WHERE mission_id = ? AND user_id = ?", (mission_id, user_id))
        
        conn.commit()
        conn.close()
        
        embed = discord.Embed(
            title="🎉 Missão Concluída!",
            description=f"**{mission['title']}**\n\nVocê recebeu: {reward_text}",
            color=discord.Color.green()
        )
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Missoes(bot))
