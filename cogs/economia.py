import discord
from discord.ext import commands
from datetime import datetime, timedelta
import random

class Economia(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.work_cooldown = {}
        self.daily_cooldown = {}
    
    @commands.group(name='saldo', aliases=['balance', 'bal', 'carteira'], invoke_without_command=True)
    async def saldo(self, ctx, member: discord.Member = None):
        """Ver saldo de moedas"""
        if ctx.invoked_subcommand is not None:
            return
        
        member = member or ctx.author
        user_id = str(member.id)
        
        self.bot.db.ensure_user_exists(user_id)
        
        conn = self.bot.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT coins, bank, total_earned, total_spent FROM economia WHERE user_id = ?
        """, (user_id,))
        data = cursor.fetchone()
        conn.close()
        
        coins = data['coins'] or 0
        bank = data['bank'] or 0
        total_earned = data['total_earned'] or 0
        total_spent = data['total_spent'] or 0
        
        embed = discord.Embed(
            title=f"Saldo de {member.display_name}",
            color=discord.Color.gold()
        )
        
        embed.set_thumbnail(url=member.display_avatar.url)
        
        embed.add_field(
            name="Carteira",
            value=f"**{coins:,}** moedas",
            inline=True
        )
        
        embed.add_field(
            name="Banco",
            value=f"**{bank:,}** moedas",
            inline=True
        )
        
        embed.add_field(
            name="Total",
            value=f"**{coins + bank:,}** moedas",
            inline=True
        )
        
        embed.add_field(
            name="Estatisticas",
            value=f"Total Ganho: **{total_earned:,}**\nTotal Gasto: **{total_spent:,}**",
            inline=False
        )
        
        await ctx.send(embed=embed)
    
    @saldo.command(name='editar')
    async def saldo_editar(self, ctx, member: discord.Member, carteira: int = None, banco: int = None):
        """Editar saldo de um usuario (somente admins)"""
        IMMUNE_ROLE_ID = 1439782753007697973
        has_immune_role = any(role.id == IMMUNE_ROLE_ID for role in ctx.author.roles)
        
        if not has_immune_role:
            await ctx.send("Voce nao tem permissao para usar este comando!")
            return
        
        if carteira is None and banco is None:
            await ctx.send("Especifique pelo menos um valor: `!saldo editar @usuario [carteira] [banco]`")
            return
        
        if carteira is not None and carteira < 0:
            await ctx.send("A carteira nao pode ser negativa!")
            return
        
        if banco is not None and banco < 0:
            await ctx.send("O banco nao pode ser negativo!")
            return
        
        user_id = str(member.id)
        self.bot.db.ensure_user_exists(user_id)
        
        conn = self.bot.db.get_connection()
        cursor = conn.cursor()
        
        if carteira is not None:
            cursor.execute("""
                UPDATE economia SET coins = ? WHERE user_id = ?
            """, (carteira, user_id))
        
        if banco is not None:
            cursor.execute("""
                UPDATE economia SET bank = ? WHERE user_id = ?
            """, (banco, user_id))
        
        conn.commit()
        
        cursor.execute("""
            SELECT coins, bank FROM economia WHERE user_id = ?
        """, (user_id,))
        data = cursor.fetchone()
        conn.close()
        
        embed = discord.Embed(
            title="Saldo Editado!",
            description=f"Saldo de {member.mention} atualizado com sucesso!",
            color=discord.Color.green()
        )
        
        embed.add_field(name="Carteira", value=f"**{data['coins']:,}** moedas", inline=True)
        embed.add_field(name="Banco", value=f"**{data['bank']:,}** moedas", inline=True)
        
        await ctx.send(embed=embed)
    
    @commands.command(name='trabalhar', aliases=['work'])
    @commands.cooldown(1, 3600, commands.BucketType.user)
    async def trabalhar(self, ctx):
        """Trabalhar para ganhar moedas (1h cooldown)"""
        user_id = str(ctx.author.id)
        self.bot.db.ensure_user_exists(user_id)
        
        jobs = [
            ("Programador", 150, 300),
            ("Motorista", 100, 200),
            ("Chef", 120, 250),
            ("Jardineiro", 80, 180),
            ("Medico", 200, 400),
            ("Professor", 100, 220),
            ("Artista", 90, 280),
            ("Vendedor", 110, 230)
        ]
        
        job = random.choice(jobs)
        earnings = random.randint(job[1], job[2])
        
        # Chance de evento especial no trabalho
        event_msg = ""
        if random.random() < 0.1:
            bonus = random.randint(50, 150)
            earnings += bonus
            event_msg = f"\n✨ **Bônus de Produtividade!** Você recebeu um extra de **{bonus}** moedas."

        conn = self.bot.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE economia 
            SET coins = coins + ?, total_earned = total_earned + ?, last_work = ?
            WHERE user_id = ?
        """, (earnings, earnings, datetime.now().isoformat(), user_id))
        
        conn.commit()
        conn.close()
        
        embed = discord.Embed(
            title="💼 Trabalho Concluido!",
            description=f"Você trabalhou duro como **{job[0]}** e sua dedicação rendeu **{earnings:,}** moedas!{event_msg}",
            color=discord.Color.green()
        )
        embed.set_footer(text="A economia agradece o seu esforço!")
        
        await ctx.send(embed=embed)

    @commands.command(name='crime')
    @commands.cooldown(1, 1800, commands.BucketType.user)
    async def crime(self, ctx):
        """Cometer um crime para ganhar moedas (Arriscado)"""
        user_id = str(ctx.author.id)
        self.bot.db.ensure_user_exists(user_id)
        
        crimes = [
            ("Assaltar uma padaria", 100, 400),
            ("Hackear um caixa eletrônico", 200, 600),
            ("Contrabandear doces raros", 150, 500),
            ("Pivete de rua", 50, 200)
        ]
        
        crime_chosen = random.choice(crimes)
        success = random.random() < 0.4 # 40% de chance
        
        if success:
            earnings = random.randint(crime_chosen[1], crime_chosen[2])
            conn = self.bot.db.get_connection()
            cursor = conn.cursor()
            cursor.execute("UPDATE economia SET coins = coins + ? WHERE user_id = ?", (earnings, user_id))
            conn.commit()
            conn.close()
            
            embed = discord.Embed(
                title="🥷 Crime Bem-sucedido!",
                description=f"Você decidiu **{crime_chosen[0]}** e conseguiu escapar com **{earnings:,}** moedas!",
                color=discord.Color.green()
            )
        else:
            loss = random.randint(100, 300)
            conn = self.bot.db.get_connection()
            cursor = conn.cursor()
            cursor.execute("UPDATE economia SET coins = MAX(0, coins - ?) WHERE user_id = ?", (loss, user_id))
            conn.commit()
            conn.close()
            
            embed = discord.Embed(
                title="👮 Deu Ruim!",
                description=f"Ao tentar **{crime_chosen[0]}**, a polícia te cercou! Você teve que pagar uma fiança de **{loss:,}** moedas para não ser preso.",
                color=discord.Color.red()
            )
            
        await ctx.send(embed=embed)
        
        from main import update_mission_progress
        await update_mission_progress(user_id, "work", 1)
    
    @trabalhar.error
    async def trabalhar_error(self, ctx, error):
        pass
    
    @commands.command(name='daily', aliases=['diario'])
    async def daily(self, ctx):
        """Coletar recompensa diaria"""
        user_id = str(ctx.author.id)
        self.bot.db.ensure_user_exists(user_id)
        
        conn = self.bot.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT last_daily FROM economia WHERE user_id = ?", (user_id,))
        data = cursor.fetchone()
        
        last_daily = data['last_daily']
        now = datetime.now()
        
        if last_daily:
            last_daily_dt = datetime.fromisoformat(last_daily)
            if now - last_daily_dt < timedelta(hours=24):
                remaining = timedelta(hours=24) - (now - last_daily_dt)
                hours = int(remaining.total_seconds() // 3600)
                minutes = int((remaining.total_seconds() % 3600) // 60)
                await ctx.send(f"Voce ja coletou o daily hoje! Volte em **{hours}h {minutes}m**.")
                conn.close()
                return
        
        daily_amount = random.randint(500, 1000)
        
        cursor.execute("""
            UPDATE economia 
            SET coins = coins + ?, total_earned = total_earned + ?, last_daily = ?
            WHERE user_id = ?
        """, (daily_amount, daily_amount, now.isoformat(), user_id))
        
        conn.commit()
        conn.close()
        
        embed = discord.Embed(
            title="Recompensa Diaria!",
            description=f"Voce coletou **{daily_amount:,}** moedas!",
            color=discord.Color.gold()
        )
        embed.set_footer(text="Volte amanha para coletar novamente!")
        
        await ctx.send(embed=embed)
    
    @commands.command(name='depositar', aliases=['dep', 'deposit'])
    async def depositar(self, ctx, quantia: str):
        """Depositar moedas no banco"""
        user_id = str(ctx.author.id)
        self.bot.db.ensure_user_exists(user_id)
        
        conn = self.bot.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT coins FROM economia WHERE user_id = ?", (user_id,))
        data = cursor.fetchone()
        coins = data['coins'] or 0
        
        if quantia.lower() == 'tudo' or quantia.lower() == 'all':
            amount = coins
        else:
            try:
                amount = int(quantia)
            except ValueError:
                await ctx.send("Valor invalido! Use um numero ou 'tudo'.")
                conn.close()
                return
        
        if amount <= 0:
            await ctx.send("Valor deve ser maior que zero!")
            conn.close()
            return
        
        if amount > coins:
            await ctx.send(f"Voce nao tem moedas suficientes! Seu saldo: **{coins:,}** moedas.")
            conn.close()
            return
        
        cursor.execute("""
            UPDATE economia 
            SET coins = coins - ?, bank = bank + ?
            WHERE user_id = ?
        """, (amount, amount, user_id))
        
        conn.commit()
        conn.close()
        
        embed = discord.Embed(
            title="Deposito Realizado!",
            description=f"Voce depositou **{amount:,}** moedas no banco.",
            color=discord.Color.green()
        )
        
        await ctx.send(embed=embed)
    
    @commands.command(name='sacar', aliases=['withdraw'])
    async def sacar(self, ctx, quantia: str):
        """Sacar moedas do banco"""
        user_id = str(ctx.author.id)
        self.bot.db.ensure_user_exists(user_id)
        
        conn = self.bot.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT bank FROM economia WHERE user_id = ?", (user_id,))
        data = cursor.fetchone()
        bank = data['bank'] or 0
        
        if quantia.lower() == 'tudo' or quantia.lower() == 'all':
            amount = bank
        else:
            try:
                amount = int(quantia)
            except ValueError:
                await ctx.send("Valor invalido! Use um numero ou 'tudo'.")
                conn.close()
                return
        
        if amount <= 0:
            await ctx.send("Valor deve ser maior que zero!")
            conn.close()
            return
        
        if amount > bank:
            await ctx.send(f"Voce nao tem moedas suficientes no banco! Saldo: **{bank:,}** moedas.")
            conn.close()
            return
        
        cursor.execute("""
            UPDATE economia 
            SET coins = coins + ?, bank = bank - ?
            WHERE user_id = ?
        """, (amount, amount, user_id))
        
        conn.commit()
        conn.close()
        
        embed = discord.Embed(
            title="Saque Realizado!",
            description=f"Voce sacou **{amount:,}** moedas do banco.",
            color=discord.Color.green()
        )
        
        await ctx.send(embed=embed)
    
    @commands.command(name='pagar', aliases=['pay', 'transferir', 'transfer'])
    async def pagar(self, ctx, member: discord.Member, quantia: int):
        """Pagar moedas para outro usuario"""
        if member.id == ctx.author.id:
            await ctx.send("Voce nao pode pagar para si mesmo!")
            return
        
        if member.bot:
            await ctx.send("Voce nao pode pagar para um bot!")
            return
        
        if quantia <= 0:
            await ctx.send("Valor deve ser maior que zero!")
            return
        
        user_id = str(ctx.author.id)
        target_id = str(member.id)
        
        self.bot.db.ensure_user_exists(user_id)
        self.bot.db.ensure_user_exists(target_id)
        
        conn = self.bot.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT coins FROM economia WHERE user_id = ?", (user_id,))
        data = cursor.fetchone()
        coins = data['coins'] or 0
        
        if quantia > coins:
            await ctx.send(f"Voce nao tem moedas suficientes! Seu saldo: **{coins:,}** moedas.")
            conn.close()
            return
        
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
            title="Pagamento Realizado!",
            description=f"{ctx.author.mention} pagou **{quantia:,}** moedas para {member.mention}!",
            color=discord.Color.green()
        )
        
        await ctx.send(embed=embed)
    
    @commands.command(name='roubar', aliases=['rob', 'steal'])
    @commands.cooldown(1, 7200, commands.BucketType.user)
    async def roubar(self, ctx, member: discord.Member):
        """Tentar roubar moedas de outro usuario (50% chance)"""
        if member.id == ctx.author.id:
            ctx.command.reset_cooldown(ctx)
            await ctx.send("Voce nao pode roubar de si mesmo!")
            return
        
        if member.bot:
            ctx.command.reset_cooldown(ctx)
            await ctx.send("Voce nao pode roubar de um bot!")
            return
        
        user_id = str(ctx.author.id)
        target_id = str(member.id)
        
        self.bot.db.ensure_user_exists(user_id)
        self.bot.db.ensure_user_exists(target_id)
        
        conn = self.bot.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT coins FROM economia WHERE user_id = ?", (target_id,))
        target_data = cursor.fetchone()
        target_coins = target_data['coins'] or 0
        
        if target_coins < 100:
            ctx.command.reset_cooldown(ctx)
            await ctx.send(f"{member.display_name} nao tem moedas suficientes para roubar!")
            conn.close()
            return
        
        success = random.random() < 0.5
        
        if success:
            steal_amount = random.randint(int(target_coins * 0.1), int(target_coins * 0.3))
            steal_amount = max(10, steal_amount)
            
            cursor.execute("""
                UPDATE economia SET coins = coins - ? WHERE user_id = ?
            """, (steal_amount, target_id))
            
            cursor.execute("""
                UPDATE economia SET coins = coins + ?, total_earned = total_earned + ? WHERE user_id = ?
            """, (steal_amount, steal_amount, user_id))
            
            conn.commit()
            
            embed = discord.Embed(
                title="Roubo Bem-sucedido!",
                description=f"Voce roubou **{steal_amount:,}** moedas de {member.mention}!",
                color=discord.Color.green()
            )
        else:
            cursor.execute("SELECT coins FROM economia WHERE user_id = ?", (user_id,))
            user_data = cursor.fetchone()
            user_coins = user_data['coins'] or 0
            
            fine = min(int(user_coins * 0.2), 500)
            fine = max(fine, 50)
            
            if user_coins >= fine:
                cursor.execute("""
                    UPDATE economia SET coins = coins - ?, total_spent = total_spent + ? WHERE user_id = ?
                """, (fine, fine, user_id))
                conn.commit()
                
                embed = discord.Embed(
                    title="Roubo Falhou!",
                    description=f"Voce foi pego tentando roubar e pagou **{fine:,}** moedas de multa!",
                    color=discord.Color.red()
                )
            else:
                embed = discord.Embed(
                    title="Roubo Falhou!",
                    description="Voce foi pego, mas nao tinha moedas para pagar a multa!",
                    color=discord.Color.red()
                )
        
        conn.close()
        await ctx.send(embed=embed)
    
    @roubar.error
    async def roubar_error(self, ctx, error):
        if isinstance(error, commands.MemberNotFound):
            ctx.command.reset_cooldown(ctx)
            await ctx.send("Membro nao encontrado!")

    @commands.command(name='emprestar')
    async def emprestar(self, ctx, member: discord.Member, quantia: int):
        """Oferecer um empréstimo para outro jogador com 10% de juros"""
        if member.id == ctx.author.id:
            await ctx.send("Você não pode emprestar para si mesmo!")
            return
        
        if quantia <= 0:
            await ctx.send("Valor inválido!")
            return

        conn = self.bot.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT coins FROM economia WHERE user_id = ?", (str(ctx.author.id),))
        if cursor.fetchone()['coins'] < quantia:
            await ctx.send("Você não tem saldo suficiente!")
            conn.close()
            return
        
        due_at = (datetime.now() + timedelta(days=7)).isoformat()
        cursor.execute("""
            INSERT INTO emprestimos (lender_id, borrower_id, amount, interest_rate, due_at)
            VALUES (?, ?, ?, 0.1, ?)
        """, (str(ctx.author.id), str(member.id), quantia, due_at))
        conn.commit()
        conn.close()
        await ctx.send(f"✅ Oferta de empréstimo de **{quantia}** moedas enviada para {member.mention}! (Vence em 7 dias)")

    @commands.command(name='impostos')
    async def impostos(self, ctx):
        """Verificar se há impostos pendentes (para jogadores com +50k)"""
        user_id = str(ctx.author.id)
        conn = self.bot.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT (coins + bank) as total FROM economia WHERE user_id = ?", (user_id,))
        total = cursor.fetchone()['total']
        
        if total > 50000:
            tax = int(total * 0.05)
            await ctx.send(f"⚠️ Sua fortuna atrai olhares! Imposto semanal estimado: **{tax}** moedas.")
        else:
            await ctx.send("✅ Você está isento de impostos por enquanto.")
        conn.close()

async def setup(bot):
    await bot.add_cog(Economia(bot))
