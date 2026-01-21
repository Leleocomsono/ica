import discord
from discord.ext import commands
from datetime import datetime, timedelta
import random

class Economia(commands.Cog):
    """Sistema de economia com moedas e itens"""
    
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(name='daily')
    @commands.cooldown(1, 86400, commands.BucketType.user)
    async def daily(self, ctx):
        """Receber recompensa diária"""
        user_id = str(ctx.author.id)
        self.bot.db.ensure_user_exists(user_id)
        
        reward = random.randint(300, 600)
        
        conn = self.bot.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE economia 
            SET coins = coins + ?, last_daily = ?, total_earned = total_earned + ?
            WHERE user_id = ?
        """, (reward, datetime.now().isoformat(), reward, user_id))
        
        conn.commit()
        conn.close()
        
        embed = discord.Embed(
            title="💰 Recompensa Diária",
            description=f"Você recebeu **{reward} moedas**!",
            color=discord.Color.green()
        )
        
        embed.set_footer(text="Volte amanhã para receber mais!")
        await ctx.send(embed=embed)
    
    @commands.command(name='trabalhar', aliases=['work'])
    @commands.cooldown(1, 3600, commands.BucketType.user)
    async def trabalhar(self, ctx):
        """Trabalhar para ganhar moedas"""
        user_id = str(ctx.author.id)
        self.bot.db.ensure_user_exists(user_id)
        
        trabalhos = [
            ("Programador", random.randint(150, 350)),
            ("Designer", random.randint(120, 280)),
            ("Streamer", random.randint(100, 400)),
            ("Cantor", random.randint(90, 250)),
            ("Chef", random.randint(110, 290)),
            ("Motorista", random.randint(80, 200)),
            ("Professor", random.randint(130, 310)),
            ("Médico", random.randint(200, 450))
        ]
        
        job, reward = random.choice(trabalhos)
        
        conn = self.bot.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE economia 
            SET coins = coins + ?, last_work = ?, total_earned = total_earned + ?
            WHERE user_id = ?
        """, (reward, datetime.now().isoformat(), reward, user_id))
        
        conn.commit()
        conn.close()
        
        # Atualizar missão de trabalho
        from main import update_mission_progress
        await update_mission_progress(user_id, "work", 1)
        
        embed = discord.Embed(
            title=f"💼 {job}",
            description=f"Você trabalhou como **{job}** e ganhou **{reward} moedas**!",
            color=discord.Color.blue()
        )
        
        await ctx.send(embed=embed)
    
    @commands.command(name='saldo', aliases=['bal', 'balance'])
    async def saldo(self, ctx, member: discord.Member = None):
        """Ver saldo de moedas"""
        if member is None:
            member = ctx.author
        
        user_id = str(member.id)
        self.bot.db.ensure_user_exists(user_id)
        
        conn = self.bot.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT coins, bank, total_earned, total_spent
            FROM economia WHERE user_id = ?
        """, (user_id,))
        
        data = cursor.fetchone()
        conn.close()
        
        embed = discord.Embed(
            title=f"💰 Saldo de {member.name}",
            color=discord.Color.gold()
        )
        
        embed.add_field(name="Carteira", value=f"{data['coins']:,} moedas", inline=True)
        embed.add_field(name="Banco", value=f"{data['bank']:,} moedas", inline=True)
        embed.add_field(name="Total", value=f"{data['coins'] + data['bank']:,} moedas", inline=True)
        embed.add_field(name="Ganho Total", value=f"{data['total_earned']:,}", inline=True)
        embed.add_field(name="Gasto Total", value=f"{data['total_spent']:,}", inline=True)
        
        await ctx.send(embed=embed)
    
    @commands.command(name='doar', aliases=['give'])
    async def doar(self, ctx, member: discord.Member, quantia: int):
        """Doar moedas para outro usuário"""
        if member.bot:
            await ctx.send("❌ Você não pode doar moedas para bots!")
            return
        
        if member.id == ctx.author.id:
            await ctx.send("❌ Você não pode doar moedas para si mesmo!")
            return
        
        if quantia <= 0:
            await ctx.send("❌ A quantia deve ser maior que zero!")
            return
        
        user_id = str(ctx.author.id)
        target_id = str(member.id)
        
        self.bot.db.ensure_user_exists(user_id)
        self.bot.db.ensure_user_exists(target_id)
        
        conn = self.bot.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT coins FROM economia WHERE user_id = ?", (user_id,))
        sender_coins = cursor.fetchone()['coins']
        
        if sender_coins < quantia:
            await ctx.send(f"❌ Você não tem moedas suficientes! Você tem: {sender_coins:,}")
            conn.close()
            return
        
        # Transferir moedas
        cursor.execute("""
            UPDATE economia 
            SET coins = coins - ?, total_spent = total_spent + ?
            WHERE user_id = ?
        """, (quantia, quantia, user_id))
        
        cursor.execute("""
            UPDATE economia 
            SET coins = coins + ?, total_earned = total_earned + ?
            WHERE user_id = ?
        """, (quantia, quantia, target_id))
        
        conn.commit()
        conn.close()
        
        embed = discord.Embed(
            title="💸 Doação Realizada",
            description=f"{ctx.author.mention} doou **{quantia:,} moedas** para {member.mention}!",
            color=discord.Color.green()
        )
        
        await ctx.send(embed=embed)
    
    @commands.command(name='caixa', aliases=['box'])
    @commands.cooldown(1, 7200, commands.BucketType.user)
    async def caixa(self, ctx):
        """Abrir uma caixa misteriosa"""
        user_id = str(ctx.author.id)
        self.bot.db.ensure_user_exists(user_id)
        
        # Tipos de recompensas
        rewards = []
        
        # Moedas (70% de chance)
        if random.random() < 0.7:
            coins = random.randint(100, 500)
            rewards.append(f"💰 {coins:,} moedas")
            
            conn = self.bot.db.get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE economia SET coins = coins + ? WHERE user_id = ?
            """, (coins, user_id))
            conn.commit()
            conn.close()
        
        # XP (50% de chance)
        if random.random() < 0.5:
            xp = random.randint(50, 200)
            rewards.append(f"⭐ {xp} XP")
            
            conn = self.bot.db.get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE usuarios SET xp = xp + ? WHERE user_id = ?
            """, (xp, user_id))
            conn.commit()
            conn.close()
        
        # Item raro (20% de chance)
        if random.random() < 0.2:
            items = ["Poção Mágica", "Cristal Raro", "Amuleto da Sorte", "Elixir Dourado"]
            item = random.choice(items)
            rewards.append(f"✨ {item}")
            
            conn = self.bot.db.get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO inventario (user_id, item_name, item_type, rarity, description)
                VALUES (?, ?, 'consumivel', 'raro', 'Item obtido de caixa misteriosa')
            """, (user_id, item))
            conn.commit()
            conn.close()
        
        if not rewards:
            rewards.append("😢 Nada desta vez... tente novamente mais tarde!")
        
        embed = discord.Embed(
            title="📦 Caixa Misteriosa Aberta!",
            description="Você recebeu:\n\n" + "\n".join(rewards),
            color=discord.Color.purple()
        )
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Economia(bot))
