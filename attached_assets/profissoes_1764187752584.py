import discord
from discord.ext import commands
from datetime import datetime
import random

class Profissoes(commands.Cog):
    """Sistema de profissões"""
    
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(name='profissao-escolher', aliases=['escolher-profissao'])
    async def escolher_profissao(self, ctx, *, profissao: str):
        """Escolher uma profissão"""
        profissoes_validas = ['caçador', 'cacador', 'engenheiro', 'alquimista', 'chef', 'comerciante']
        profissao_lower = profissao.lower()
        
        if profissao_lower not in profissoes_validas:
            await ctx.send(f"❌ Profissão inválida! Escolha: Caçador, Engenheiro, Alquimista, Chef ou Comerciante")
            return
        
        # Normalizar nome
        if profissao_lower in ['cacador', 'caçador']:
            profissao_nome = 'Caçador'
        else:
            profissao_nome = profissao.capitalize()
        
        user_id = str(ctx.author.id)
        self.bot.db.ensure_user_exists(user_id)
        
        conn = self.bot.db.get_connection()
        cursor = conn.cursor()
        
        # Buscar ID da profissão
        cursor.execute("SELECT profession_id FROM profissoes WHERE name = ?", (profissao_nome,))
        result = cursor.fetchone()
        
        if not result:
            await ctx.send("❌ Profissão não encontrada!")
            conn.close()
            return
        
        profession_id = result['profession_id']
        
        # Verificar se já escolheu
        cursor.execute("""
            SELECT 1 FROM profissao_progresso WHERE user_id = ? AND profession_id = ?
        """, (user_id, profession_id))
        
        if cursor.fetchone():
            await ctx.send(f"❌ Você já escolheu esta profissão!")
            conn.close()
            return
        
        # Adicionar profissão
        cursor.execute("""
            INSERT INTO profissao_progresso (user_id, profession_id, chosen_at)
            VALUES (?, ?, ?)
        """, (user_id, profession_id, datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
        
        embed = discord.Embed(
            title="✅ Profissão Escolhida!",
            description=f"Você agora é um **{profissao_nome}**!",
            color=discord.Color.green()
        )
        
        await ctx.send(embed=embed)
    
    @commands.command(name='profissao-info', aliases=['prof-info'])
    async def profissao_info(self, ctx):
        """Ver suas profissões"""
        user_id = str(ctx.author.id)
        
        conn = self.bot.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT p.name, p.icon, pp.level, pp.xp
            FROM profissao_progresso pp
            JOIN profissoes p ON pp.profession_id = p.profession_id
            WHERE pp.user_id = ?
        """, (user_id,))
        
        profs = cursor.fetchall()
        conn.close()
        
        if not profs:
            await ctx.send("❌ Você ainda não escolheu nenhuma profissão! Use `!profissao-escolher <nome>`")
            return
        
        embed = discord.Embed(
            title="👔 Suas Profissões",
            color=discord.Color.blue()
        )
        
        for prof in profs:
            icon = prof['icon'] or ''
            embed.add_field(
                name=f"{icon} {prof['name']}",
                value=f"Nível {prof['level']} - {prof['xp']}/100 XP",
                inline=False
            )
        
        await ctx.send(embed=embed)
    
    @commands.command(name='coletar')
    @commands.cooldown(1, 3600, commands.BucketType.user)
    async def coletar(self, ctx):
        """Coletar recursos (Caçador)"""
        user_id = str(ctx.author.id)
        
        conn = self.bot.db.get_connection()
        cursor = conn.cursor()
        
        # Verificar se tem a profissão
        cursor.execute("""
            SELECT pp.level FROM profissao_progresso pp
            JOIN profissoes p ON pp.profession_id = p.profession_id
            WHERE pp.user_id = ? AND p.name = 'Caçador'
        """, (user_id,))
        
        result = cursor.fetchone()
        
        if not result:
            await ctx.send("❌ Você precisa ser Caçador para usar este comando!")
            conn.close()
            return
        
        # Coletar recursos
        items = ["Pele de Lobo", "Carne de Javali", "Penas de Águia", "Chifre de Cervo"]
        item = random.choice(items)
        coins = random.randint(100, 250)
        xp = random.randint(20, 40)
        
        cursor.execute("""
            INSERT INTO inventario (user_id, item_name, item_type, rarity)
            VALUES (?, ?, 'material', 'incomum')
        """, (user_id, item))
        
        cursor.execute("UPDATE economia SET coins = coins + ? WHERE user_id = ?", (coins, user_id))
        cursor.execute("UPDATE profissao_progresso SET xp = xp + ? WHERE user_id = ? AND profession_id = (SELECT profession_id FROM profissoes WHERE name = 'Caçador')", (xp, user_id))
        
        conn.commit()
        conn.close()
        
        embed = discord.Embed(
            title="🏹 Coleta Realizada!",
            description=f"Você coletou:\n• {item}\n• {coins} moedas\n• {xp} XP de profissão",
            color=discord.Color.green()
        )
        
        await ctx.send(embed=embed)
    
    @commands.command(name='fabricar')
    @commands.cooldown(1, 7200, commands.BucketType.user)
    async def fabricar(self, ctx):
        """Fabricar itens (Engenheiro)"""
        user_id = str(ctx.author.id)
        
        conn = self.bot.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT pp.level FROM profissao_progresso pp
            JOIN profissoes p ON pp.profession_id = p.profession_id
            WHERE pp.user_id = ? AND p.name = 'Engenheiro'
        """, (user_id,))
        
        result = cursor.fetchone()
        
        if not result:
            await ctx.send("❌ Você precisa ser Engenheiro para usar este comando!")
            conn.close()
            return
        
        items = ["Engrenagem", "Circuito", "Parafuso Mágico", "Placa de Metal"]
        item = random.choice(items)
        coins = random.randint(150, 300)
        xp = random.randint(25, 50)
        
        cursor.execute("""
            INSERT INTO inventario (user_id, item_name, item_type, rarity)
            VALUES (?, ?, 'material', 'raro')
        """, (user_id, item))
        
        cursor.execute("UPDATE economia SET coins = coins + ? WHERE user_id = ?", (coins, user_id))
        cursor.execute("UPDATE profissao_progresso SET xp = xp + ? WHERE user_id = ? AND profession_id = (SELECT profession_id FROM profissoes WHERE name = 'Engenheiro')", (xp, user_id))
        
        conn.commit()
        conn.close()
        
        embed = discord.Embed(
            title="⚙️ Item Fabricado!",
            description=f"Você fabricou:\n• {item}\n• Ganhou {coins} moedas\n• {xp} XP de profissão",
            color=discord.Color.blue()
        )
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Profissoes(bot))
