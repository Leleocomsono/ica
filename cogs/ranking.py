import discord
from discord.ext import commands

class Ranking(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(name='ranking', aliases=['top', 'leaderboard'])
    async def ranking(self, ctx, tipo: str = "xp"):
        """Ver ranking de usuarios"""
        tipo = tipo.lower()
        
        conn = self.bot.db.get_connection()
        cursor = conn.cursor()
        
        if tipo in ['xp', 'nivel', 'level']:
            cursor.execute("""
                SELECT user_id, xp, level FROM usuarios 
                ORDER BY xp DESC LIMIT 10
            """)
            title = "Ranking de XP"
            value_key = 'xp'
            suffix = "XP"
        elif tipo in ['moedas', 'coins', 'dinheiro', 'money']:
            cursor.execute("""
                SELECT user_id, coins + bank as total FROM economia 
                ORDER BY total DESC LIMIT 10
            """)
            title = "Ranking de Moedas"
            value_key = 'total'
            suffix = "moedas"
        elif tipo in ['mensagens', 'messages', 'msgs']:
            cursor.execute("""
                SELECT user_id, messages FROM usuarios 
                ORDER BY messages DESC LIMIT 10
            """)
            title = "Ranking de Mensagens"
            value_key = 'messages'
            suffix = "msgs"
        elif tipo in ['pets']:
            cursor.execute("""
                SELECT user_id, COUNT(*) as count FROM pets 
                GROUP BY user_id ORDER BY count DESC LIMIT 10
            """)
            title = "Ranking de Pets"
            value_key = 'count'
            suffix = "pets"
        else:
            await ctx.send("Tipo invalido! Use: `xp`, `moedas`, `mensagens` ou `pets`")
            conn.close()
            return
        
        rankings = cursor.fetchall()
        conn.close()
        
        embed = discord.Embed(
            title=f"🏆 {title}",
            color=discord.Color.gold()
        )
        
        medals = ['🥇', '🥈', '🥉']
        ranking_text = ""
        
        for i, row in enumerate(rankings):
            user = ctx.guild.get_member(int(row['user_id']))
            username = user.display_name if user else f"Usuario {row['user_id'][:8]}..."
            
            medal = medals[i] if i < 3 else f"**{i+1}.**"
            value = row[value_key] or 0
            
            ranking_text += f"{medal} {username} - **{value:,}** {suffix}\n"
        
        embed.description = ranking_text or "Nenhum usuario encontrado."
        
        user_id = str(ctx.author.id)
        user_rank = None
        
        cursor = conn.cursor() if not conn else self.bot.db.get_connection().cursor()
        
        await ctx.send(embed=embed)
    
    @commands.command(name='rankingtipo', aliases=['ranktypes'])
    async def rankingtipo(self, ctx):
        """Ver tipos de ranking disponiveis"""
        embed = discord.Embed(
            title="Tipos de Ranking",
            color=discord.Color.gold()
        )
        
        embed.add_field(
            name="Disponiveis",
            value="• `!ranking xp` - Ranking de XP e nivel\n"
                  "• `!ranking moedas` - Ranking de moedas\n"
                  "• `!ranking mensagens` - Ranking de mensagens\n"
                  "• `!ranking pets` - Ranking de pets",
            inline=False
        )
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Ranking(bot))
