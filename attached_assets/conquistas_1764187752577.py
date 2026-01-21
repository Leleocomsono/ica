import discord
from discord.ext import commands

class Conquistas(commands.Cog):
    """Sistema de conquistas"""
    
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(name='conquistas', aliases=['achievements'])
    async def conquistas(self, ctx):
        """Ver suas conquistas"""
        user_id = str(ctx.author.id)
        
        conn = self.bot.db.get_connection()
        cursor = conn.cursor()
        
        # Conquistas desbloqueadas
        cursor.execute("""
            SELECT a.name, a.description, a.icon, cu.unlocked_at
            FROM conquistas_usuario cu
            JOIN conquistas a ON cu.achievement_id = a.achievement_id
            WHERE cu.user_id = ?
            ORDER BY cu.unlocked_at DESC
        """, (user_id,))
        
        unlocked = cursor.fetchall()
        
        # Total de conquistas
        cursor.execute("SELECT COUNT(*) as total FROM conquistas")
        total = cursor.fetchone()['total']
        
        conn.close()
        
        embed = discord.Embed(
            title=f"🏆 Conquistas de {ctx.author.name}",
            description=f"Desbloqueadas: {len(unlocked)}/{total}",
            color=discord.Color.gold()
        )
        
        if unlocked:
            for achievement in unlocked[:10]:
                icon = achievement['icon'] or '🏆'
                embed.add_field(
                    name=f"{icon} {achievement['name']}",
                    value=achievement['description'],
                    inline=False
                )
        else:
            embed.add_field(
                name="Nenhuma conquista",
                value="Continue jogando para desbloquear conquistas!",
                inline=False
            )
        
        await ctx.send(embed=embed)
    
    @commands.command(name='conquistas-top', aliases=['achievements-top'])
    async def conquistas_top(self, ctx):
        """Ver ranking de conquistas"""
        conn = self.bot.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT user_id, COUNT(*) as total
            FROM conquistas_usuario
            GROUP BY user_id
            ORDER BY total DESC
            LIMIT 10
        """)
        
        top = cursor.fetchall()
        conn.close()
        
        if not top:
            await ctx.send("❌ Ainda não há conquistas desbloqueadas!")
            return
        
        embed = discord.Embed(
            title="🏆 Top 10 - Conquistas",
            color=discord.Color.gold()
        )
        
        medals = ["🥇", "🥈", "🥉"]
        
        for i, row in enumerate(top, 1):
            try:
                user = await self.bot.fetch_user(int(row['user_id']))
                medal = medals[i-1] if i <= 3 else f"{i}."
                
                embed.add_field(
                    name=f"{medal} {user.name}",
                    value=f"{row['total']} conquistas",
                    inline=False
                )
            except:
                continue
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Conquistas(bot))
