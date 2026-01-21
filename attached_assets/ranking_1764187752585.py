import discord
from discord.ext import commands

class Ranking(commands.Cog):
    """Sistema de rankings"""
    
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(name='ranking', aliases=['rank', 'top'])
    async def ranking(self, ctx, tipo: str = "xp"):
        """Ver rankings (xp, nivel, mensagens, comandos, dinheiro)"""
        tipo = tipo.lower()
        
        conn = self.bot.db.get_connection()
        cursor = conn.cursor()
        
        if tipo in ["xp", "experiencia"]:
            cursor.execute("""
                SELECT user_id, xp, level FROM usuarios 
                ORDER BY xp DESC LIMIT 10
            """)
            title = "🏆 Top 10 - XP"
            rows = cursor.fetchall()
            value_format = lambda r: f"**Nível {r['level']}** - {r['xp']:,} XP"
            
        elif tipo in ["nivel", "level", "lvl"]:
            cursor.execute("""
                SELECT user_id, level, xp FROM usuarios 
                ORDER BY level DESC, xp DESC LIMIT 10
            """)
            title = "🏆 Top 10 - Nível"
            rows = cursor.fetchall()
            value_format = lambda r: f"**Nível {r['level']}** ({r['xp']:,} XP)"
            
        elif tipo in ["mensagens", "mensagem", "msg"]:
            cursor.execute("""
                SELECT user_id, messages FROM usuarios 
                ORDER BY messages DESC LIMIT 10
            """)
            title = "🏆 Top 10 - Mensagens"
            rows = cursor.fetchall()
            value_format = lambda r: f"{r['messages']:,} mensagens"
            
        elif tipo in ["comandos", "comando", "cmd"]:
            cursor.execute("""
                SELECT user_id, commands_used FROM usuarios 
                ORDER BY commands_used DESC LIMIT 10
            """)
            title = "🏆 Top 10 - Comandos"
            rows = cursor.fetchall()
            value_format = lambda r: f"{r['commands_used']:,} comandos"
            
        elif tipo in ["dinheiro", "moedas", "coins"]:
            cursor.execute("""
                SELECT e.user_id, e.coins + e.bank as total
                FROM economia e
                ORDER BY total DESC LIMIT 10
            """)
            title = "🏆 Top 10 - Dinheiro"
            rows = cursor.fetchall()
            value_format = lambda r: f"{r['total']:,} moedas"
            
        else:
            await ctx.send("❌ Tipo inválido! Use: `xp`, `nivel`, `mensagens`, `comandos` ou `dinheiro`")
            conn.close()
            return
        
        conn.close()
        
        if not rows:
            await ctx.send("❌ Ainda não há dados para exibir.")
            return
        
        embed = discord.Embed(
            title=title,
            color=discord.Color.gold()
        )
        
        medals = ["🥇", "🥈", "🥉"]
        
        for i, row in enumerate(rows, 1):
            try:
                user = await self.bot.fetch_user(int(row['user_id']))
                medal = medals[i-1] if i <= 3 else f"{i}."
                
                embed.add_field(
                    name=f"{medal} {user.name}",
                    value=value_format(row),
                    inline=False
                )
            except:
                continue
        
        await ctx.send(embed=embed)
    
    @commands.command(name='pet-ranking')
    async def pet_ranking(self, ctx):
        """Ver ranking de pets"""
        conn = self.bot.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT user_id, species, custom_name, level, xp
            FROM pets
            ORDER BY level DESC, xp DESC
            LIMIT 10
        """)
        
        pets = cursor.fetchall()
        conn.close()
        
        if not pets:
            await ctx.send("❌ Ainda não há pets no ranking.")
            return
        
        embed = discord.Embed(
            title="🐾 Top 10 - Pets",
            color=discord.Color.purple()
        )
        
        medals = ["🥇", "🥈", "🥉"]
        
        for i, pet in enumerate(pets, 1):
            try:
                user = await self.bot.fetch_user(int(pet['user_id']))
                pet_name = pet['custom_name'] if pet['custom_name'] else pet['species'].capitalize()
                medal = medals[i-1] if i <= 3 else f"{i}."
                
                embed.add_field(
                    name=f"{medal} {pet_name}",
                    value=f"Dono: {user.name} | Nível {pet['level']} ({pet['xp']} XP)",
                    inline=False
                )
            except:
                continue
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Ranking(bot))
