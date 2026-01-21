import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime
from typing import Optional

class Casamento(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.pending_proposals = {}
        self.register_slash_commands()
    
    def register_slash_commands(self):
        """Registra os slash commands no bot.tree"""
        @self.bot.tree.command(name='casar', description='Pedir alguem em casamento')
        async def slash_casar(interaction: discord.Interaction, member: discord.User):
            if member.id == interaction.user.id:
                await interaction.response.send_message("Voce nao pode casar consigo mesmo!", ephemeral=True)
                return
            
            if member.bot:
                await interaction.response.send_message("Voce nao pode casar com um bot!", ephemeral=True)
                return
            
            user_id = str(interaction.user.id)
            target_id = str(member.id)
            
            self.bot.db.ensure_user_exists(user_id)
            self.bot.db.ensure_user_exists(target_id)
            
            conn = self.bot.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM casamentos 
                WHERE user1_id = ? OR user2_id = ?
            """, (user_id, user_id))
            
            if cursor.fetchone():
                await interaction.response.send_message("Voce ja esta casado(a)!", ephemeral=True)
                conn.close()
                return
            
            cursor.execute("""
                SELECT * FROM casamentos 
                WHERE user1_id = ? OR user2_id = ?
            """, (target_id, target_id))
            
            if cursor.fetchone():
                await interaction.response.send_message(f"{member.display_name} ja esta casado(a)!", ephemeral=True)
                conn.close()
                return
            
            conn.close()
            
            proposal_key = f"{user_id}_{target_id}"
            self.pending_proposals[proposal_key] = {
                'proposer': interaction.user,
                'target': member,
                'timestamp': datetime.now()
            }
            
            embed = discord.Embed(
                title="Pedido de Casamento!",
                description=f"{interaction.user.mention} esta pedindo {member.mention} em casamento!\n\n"
                           f"{member.mention}, use `/aceitar` para aceitar ou `/recusar` para recusar.",
                color=discord.Color.pink()
            )
            
            await interaction.response.send_message(embed=embed)
        
        @self.bot.tree.command(name='aceitar', description='Aceitar um pedido de casamento')
        async def slash_aceitar(interaction: discord.Interaction, member: discord.User):
            user_id = str(interaction.user.id)
            proposer_id = str(member.id)
            
            proposal_key = f"{proposer_id}_{user_id}"
            
            if proposal_key not in self.pending_proposals:
                await interaction.response.send_message("Nao ha pedido de casamento pendente desta pessoa!", ephemeral=True)
                return
            
            conn = self.bot.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO casamentos (user1_id, user2_id, married_at)
                VALUES (?, ?, ?)
            """, (proposer_id, user_id, datetime.now().isoformat()))
            
            conn.commit()
            conn.close()
            
            del self.pending_proposals[proposal_key]
            
            embed = discord.Embed(
                title="Casamento Realizado!",
                description=f"{member.mention} e {interaction.user.mention} agora estao casados!",
                color=discord.Color.pink()
            )
            
            await interaction.response.send_message(embed=embed)
        
        @self.bot.tree.command(name='recusar', description='Recusar um pedido de casamento')
        async def slash_recusar(interaction: discord.Interaction, member: discord.User):
            user_id = str(interaction.user.id)
            proposer_id = str(member.id)
            
            proposal_key = f"{proposer_id}_{user_id}"
            
            if proposal_key not in self.pending_proposals:
                await interaction.response.send_message("Nao ha pedido de casamento pendente desta pessoa!", ephemeral=True)
                return
            
            del self.pending_proposals[proposal_key]
            
            embed = discord.Embed(
                title="Pedido Recusado",
                description=f"{interaction.user.mention} recusou o pedido de casamento de {member.mention}.",
                color=discord.Color.red()
            )
            
            await interaction.response.send_message(embed=embed)
        
        @self.bot.tree.command(name='divorciar', description='Divorciar-se do parceiro atual (Custo: 20% do saldo)')
        async def slash_divorciar(interaction: discord.Interaction):
            user_id = str(interaction.user.id)
            
            conn = self.bot.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM casamentos 
                WHERE user1_id = ? OR user2_id = ?
            """, (user_id, user_id))
            
            marriage = cursor.fetchone()
            
            if not marriage:
                await interaction.response.send_message("Voce nao esta casado(a)!", ephemeral=True)
                conn.close()
                return
            
            # Consequência: Perda de 20% do saldo
            cursor.execute("SELECT coins FROM economia WHERE user_id = ?", (user_id,))
            eco_data = cursor.fetchone()
            if eco_data:
                penalty = int(eco_data['coins'] * 0.2)
                cursor.execute("UPDATE economia SET coins = coins - ? WHERE user_id = ?", (penalty, user_id))

            partner_id = marriage['user2_id'] if marriage['user1_id'] == user_id else marriage['user1_id']
            partner = interaction.guild.get_member(int(partner_id)) if interaction.guild else None
            partner_name = partner.display_name if partner else "Usuario desconhecido"
            
            cursor.execute("""
                DELETE FROM casamentos 
                WHERE user1_id = ? OR user2_id = ?
            """, (user_id, user_id))
            
            conn.commit()
            conn.close()
            
            embed = discord.Embed(
                title="Divorcio Realizado",
                description=f"{interaction.user.mention} se divorciou de **{partner_name}**.\nPerdeu **{penalty} moedas** como consequência.",
                color=discord.Color.dark_grey()
            )
            
            await interaction.response.send_message(embed=embed)
        
        @self.bot.tree.command(name='parceiro', description='Ver informacoes do casamento')
        async def slash_parceiro(interaction: discord.Interaction, member: Optional[discord.User] = None):
            member = member or interaction.user
            user_id = str(member.id)
            
            conn = self.bot.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM casamentos 
                WHERE user1_id = ? OR user2_id = ?
            """, (user_id, user_id))
            
            marriage = cursor.fetchone()
            conn.close()
            
            if not marriage:
                if member == interaction.user:
                    await interaction.response.send_message("Voce nao esta casado(a)!", ephemeral=True)
                else:
                    await interaction.response.send_message(f"{member.display_name} nao esta casado(a)!", ephemeral=True)
                return
            
            partner_id = marriage['user2_id'] if marriage['user1_id'] == user_id else marriage['user1_id']
            partner = interaction.guild.get_member(int(partner_id)) if interaction.guild else None
            partner_name = partner.display_name if partner else "Usuario desconhecido"
            
            married_at = datetime.fromisoformat(marriage['married_at'])
            days_married = (datetime.now() - married_at).days
            
            embed = discord.Embed(
                title="💓 Status de Casamento",
                color=discord.Color.pink()
            )
            
            embed.add_field(
                name="💍 Casal",
                value=f"{member.display_name} e {partner_name}",
                inline=False
            )
            
            embed.add_field(
                name="📅 Data do Casamento",
                value=married_at.strftime("%d/%m/%Y"),
                inline=True
            )
            
            embed.add_field(
                name="⏳ Dias Juntos",
                value=f"{days_married} dias",
                inline=True
            )
            
            await interaction.response.send_message(embed=embed)

        @self.bot.tree.command(name='beijar', description='Dar um beijo carinhoso no seu parceiro')
        async def slash_beijar(interaction: discord.Interaction):
            user_id = str(interaction.user.id)
            conn = self.bot.db.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM casamentos WHERE user1_id = ? OR user2_id = ?", (user_id, user_id))
            marriage = cursor.fetchone()
            conn.close()

            if not marriage:
                await interaction.response.send_message("Você precisa estar casado para beijar seu parceiro!", ephemeral=True)
                return

            partner_id = marriage['user2_id'] if marriage['user1_id'] == user_id else marriage['user1_id']
            embed = discord.Embed(
                description=f"💋 {interaction.user.mention} deu um beijo super carinhoso em <@{partner_id}>! O amor está no ar!",
                color=discord.Color.pink()
            )
            await interaction.response.send_message(embed=embed)
    
    @commands.command(name='casar', aliases=['marry', 'propor'])
    async def casar(self, ctx, member: Optional[discord.Member] = None):
        """Pedir alguem em casamento"""
        if member is None:
            await ctx.send("Mencione a pessoa com quem deseja casar!")
            return
        
        if member.id == ctx.author.id:
            await ctx.send("Voce nao pode casar consigo mesmo!")
            return
        
        if member.bot:
            await ctx.send("Voce nao pode casar com um bot!")
            return
        
        user_id = str(ctx.author.id)
        target_id = str(member.id)
        
        self.bot.db.ensure_user_exists(user_id)
        self.bot.db.ensure_user_exists(target_id)
        
        conn = self.bot.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM casamentos 
            WHERE user1_id = ? OR user2_id = ?
        """, (user_id, user_id))
        
        if cursor.fetchone():
            await ctx.send("Voce ja esta casado(a)!")
            conn.close()
            return
        
        cursor.execute("""
            SELECT * FROM casamentos 
            WHERE user1_id = ? OR user2_id = ?
        """, (target_id, target_id))
        
        if cursor.fetchone():
            await ctx.send(f"{member.display_name} ja esta casado(a)!")
            conn.close()
            return
        
        conn.close()
        
        proposal_key = f"{user_id}_{target_id}"
        self.pending_proposals[proposal_key] = {
            'proposer': ctx.author,
            'target': member,
            'timestamp': datetime.now()
        }
        
        embed = discord.Embed(
            title="Pedido de Casamento!",
            description=f"{ctx.author.mention} esta pedindo {member.mention} em casamento!\n\n"
                       f"{member.mention}, digite `!aceitar @{ctx.author.display_name}` para aceitar "
                       f"ou `!recusar @{ctx.author.display_name}` para recusar.",
            color=discord.Color.pink()
        )
        
        await ctx.send(embed=embed)
    
    @commands.command(name='aceitar', aliases=['accept'])
    async def aceitar(self, ctx, member: Optional[discord.Member] = None):
        """Aceitar um pedido de casamento"""
        if member is None:
            await ctx.send("Mencione a pessoa cujo pedido deseja aceitar!")
            return
        
        user_id = str(ctx.author.id)
        proposer_id = str(member.id)
        
        proposal_key = f"{proposer_id}_{user_id}"
        
        if proposal_key not in self.pending_proposals:
            await ctx.send("Nao ha pedido de casamento pendente desta pessoa!")
            return
        
        conn = self.bot.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO casamentos (user1_id, user2_id, married_at)
            VALUES (?, ?, ?)
        """, (proposer_id, user_id, datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
        
        del self.pending_proposals[proposal_key]
        
        embed = discord.Embed(
            title="Casamento Realizado!",
            description=f"{member.mention} e {ctx.author.mention} agora estao casados!",
            color=discord.Color.pink()
        )
        
        await ctx.send(embed=embed)
    
    @commands.command(name='recusar', aliases=['reject'])
    async def recusar(self, ctx, member: Optional[discord.Member] = None):
        """Recusar um pedido de casamento"""
        if member is None:
            await ctx.send("Mencione a pessoa cujo pedido deseja recusar!")
            return
        
        user_id = str(ctx.author.id)
        proposer_id = str(member.id)
        
        proposal_key = f"{proposer_id}_{user_id}"
        
        if proposal_key not in self.pending_proposals:
            await ctx.send("Nao ha pedido de casamento pendente desta pessoa!")
            return
        
        del self.pending_proposals[proposal_key]
        
        embed = discord.Embed(
            title="Pedido Recusado",
            description=f"{ctx.author.mention} recusou o pedido de casamento de {member.mention}.",
            color=discord.Color.red()
        )
        
        await ctx.send(embed=embed)
    
    @commands.command(name='divorciar', aliases=['divorce'])
    async def divorciar(self, ctx):
        """Divorciar-se do parceiro atual"""
        user_id = str(ctx.author.id)
        
        conn = self.bot.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM casamentos 
            WHERE user1_id = ? OR user2_id = ?
        """, (user_id, user_id))
        
        marriage = cursor.fetchone()
        
        if not marriage:
            await ctx.send("Voce nao esta casado(a)!")
            conn.close()
            return
        
        partner_id = marriage['user2_id'] if marriage['user1_id'] == user_id else marriage['user1_id']
        partner = ctx.guild.get_member(int(partner_id))
        partner_name = partner.display_name if partner else "Usuario desconhecido"
        
        await ctx.send(
            f"Tem certeza que deseja se divorciar de **{partner_name}**? "
            f"Digite `confirmar` para prosseguir."
        )
        
        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel and m.content.lower() == 'confirmar'
        
        try:
            await self.bot.wait_for('message', check=check, timeout=30.0)
            
            cursor.execute("""
                DELETE FROM casamentos 
                WHERE user1_id = ? OR user2_id = ?
            """, (user_id, user_id))
            
            conn.commit()
            
            embed = discord.Embed(
                title="Divorcio Realizado",
                description=f"{ctx.author.mention} se divorciou de **{partner_name}**.",
                color=discord.Color.dark_grey()
            )
            
            await ctx.send(embed=embed)
        except:
            await ctx.send("Operacao cancelada.")
        finally:
            conn.close()
    
    @commands.command(name='parceiro', aliases=['partner'])
    async def parceiro(self, ctx, member: Optional[discord.Member] = None):
        """Ver informacoes do casamento"""
        member = member or ctx.author
        user_id = str(member.id)
        
        conn = self.bot.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM casamentos 
            WHERE user1_id = ? OR user2_id = ?
        """, (user_id, user_id))
        
        marriage = cursor.fetchone()
        conn.close()
        
        if not marriage:
            if member == ctx.author:
                await ctx.send("Voce nao esta casado(a)!")
            else:
                await ctx.send(f"{member.display_name} nao esta casado(a)!")
            return
        
        partner_id = marriage['user2_id'] if marriage['user1_id'] == user_id else marriage['user1_id']
        partner = ctx.guild.get_member(int(partner_id))
        partner_name = partner.display_name if partner else "Usuario desconhecido"
        
        married_at = datetime.fromisoformat(marriage['married_at'])
        days_married = (datetime.now() - married_at).days
        
        embed = discord.Embed(
            title="Status de Casamento",
            color=discord.Color.pink()
        )
        
        embed.add_field(
            name="Casal",
            value=f"{member.display_name} x {partner_name}",
            inline=False
        )
        
        embed.add_field(
            name="Data do Casamento",
            value=married_at.strftime("%d/%m/%Y"),
            inline=True
        )
        
        embed.add_field(
            name="Dias Casados",
            value=f"{days_married} dias",
            inline=True
        )
        
        await ctx.send(embed=embed)
    
        @self.bot.tree.command(name='rankingcasais', description='Ver os casais mais ricos do servidor')
        async def slash_rankingcasais(interaction: discord.Interaction):
            conn = self.bot.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT c.user1_id, c.user2_id, (e1.coins + e1.bank + e2.coins + e2.bank) as total_wealth
                FROM casamentos c
                JOIN economia e1 ON c.user1_id = e1.user_id
                JOIN economia e2 ON c.user2_id = e2.user_id
                ORDER BY total_wealth DESC
                LIMIT 10
            """)
            
            rankings = cursor.fetchall()
            conn.close()
            
            embed = discord.Embed(
                title="🏆 Ranking de Casais Mais Ricos",
                color=discord.Color.gold()
            )
            
            description = ""
            for i, row in enumerate(rankings, 1):
                user1 = interaction.guild.get_member(int(row['user1_id']))
                user2 = interaction.guild.get_member(int(row['user2_id']))
                u1_name = user1.display_name if user1 else "Usuário 1"
                u2_name = user2.display_name if user2 else "Usuário 2"
                wealth = row['total_wealth']
                description += f"**{i}.** {u1_name} & {u2_name} — 💰 {wealth:,} moedas\n"
            
            embed.description = description or "Nenhum casal encontrado."
            await interaction.response.send_message(embed=embed)

    @commands.command(name='rankingcasais', aliases=['richestcouples'])
    async def ranking_casais(self, ctx):
        """Ver os casais mais ricos do servidor"""
        conn = self.bot.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT c.user1_id, c.user2_id, (e1.coins + e1.bank + e2.coins + e2.bank) as total_wealth
            FROM casamentos c
            JOIN economia e1 ON c.user1_id = e1.user_id
            JOIN economia e2 ON c.user2_id = e2.user_id
            ORDER BY total_wealth DESC
            LIMIT 10
        """)
        
        rankings = cursor.fetchall()
        conn.close()
        
        embed = discord.Embed(
            title="🏆 Ranking de Casais Mais Ricos",
            color=discord.Color.gold()
        )
        
        description = ""
        for i, row in enumerate(rankings, 1):
            user1 = ctx.guild.get_member(int(row['user1_id']))
            user2 = ctx.guild.get_member(int(row['user2_id']))
            u1_name = user1.display_name if user1 else "Usuário 1"
            u2_name = user2.display_name if user2 else "Usuário 2"
            wealth = row['total_wealth']
            description += f"**{i}.** {u1_name} & {u2_name} — 💰 {wealth:,} moedas\n"
        
        embed.description = description or "Nenhum casal encontrado."
        await ctx.send(embed=embed)

    @commands.command(name='beijar', aliases=['kiss'])
    async def beijar_prefix(self, ctx):
        """Dar um beijo carinhoso no seu parceiro"""
        user_id = str(ctx.author.id)
        conn = self.bot.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM casamentos WHERE user1_id = ? OR user2_id = ?", (user_id, user_id))
        marriage = cursor.fetchone()
        conn.close()

        if not marriage:
            await ctx.send("❌ Você precisa estar casado para beijar seu parceiro!")
            return

        partner_id = marriage['user2_id'] if marriage['user1_id'] == user_id else marriage['user1_id']
        embed = discord.Embed(
            description=f"💋 {ctx.author.mention} deu um beijo super carinhoso em <@{partner_id}>! O amor está no ar!",
            color=discord.Color.pink()
        )
        await ctx.send(embed=embed)

    @commands.command(name='abracar_casal', aliases=['hug_marriage', 'abracar_marry'])
    async def abracar_prefix(self, ctx):
        """Dar um abraço apertado no seu parceiro"""
        user_id = str(ctx.author.id)
        conn = self.bot.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM casamentos WHERE user1_id = ? OR user2_id = ?", (user_id, user_id))
        marriage = cursor.fetchone()
        conn.close()

        if not marriage:
            await ctx.send("❌ Você precisa estar casado para abraçar seu parceiro!")
            return

        partner_id = marriage['user2_id'] if marriage['user1_id'] == user_id else marriage['user1_id']
        embed = discord.Embed(
            description=f"🫂 {ctx.author.mention} deu um abraço super apertado em <@{partner_id}>! Sentindo o calor do amor!",
            color=discord.Color.pink()
        )
        await ctx.send(embed=embed)

    @commands.command(name='presentear_casal', aliases=['gift_marriage', 'presentear_marry'])
    async def presentear_prefix(self, ctx):
        """Dar um presente especial para seu parceiro"""
        user_id = str(ctx.author.id)
        conn = self.bot.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM casamentos WHERE user1_id = ? OR user2_id = ?", (user_id, user_id))
        marriage = cursor.fetchone()
        
        if not marriage:
            conn.close()
            await ctx.send("❌ Você precisa estar casado para presentear seu parceiro!")
            return
        
        cursor.execute("SELECT coins FROM economia WHERE user_id = ?", (user_id,))
        eco_data = cursor.fetchone()
        if not eco_data or eco_data['coins'] < 500:
            conn.close()
            await ctx.send("❌ Você precisa de pelo menos 500 moedas para comprar um presente!")
            return
        
        cursor.execute("UPDATE economia SET coins = coins - 500 WHERE user_id = ?", (user_id,))
        conn.commit()
        conn.close()

        partner_id = marriage['user2_id'] if marriage['user1_id'] == user_id else marriage['user1_id']
        import random
        presentes = ["uma caixa de bombons 🍫", "um buquê de flores 💐", "um anel de brilhantes 💍", "uma carta de amor 💌"]
        presente = random.choice(presentes)
        
        embed = discord.Embed(
            description=f"🎁 {ctx.author.mention} comprou **{presente}** para <@{partner_id}>! Que gesto lindo!",
            color=discord.Color.pink()
        )
        await ctx.send(embed=embed)

        @self.bot.tree.command(name='rankingcasais', description='Ver os casais mais ricos do servidor')
        async def slash_rankingcasais(interaction: discord.Interaction):
            conn = self.bot.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT c.user1_id, c.user2_id, (e1.coins + e1.bank + e2.coins + e2.bank) as total_wealth
                FROM casamentos c
                JOIN economia e1 ON c.user1_id = e1.user_id
                JOIN economia e2 ON c.user2_id = e2.user_id
                ORDER BY total_wealth DESC
                LIMIT 10
            """)
            
            rankings = cursor.fetchall()
            conn.close()
            
            embed = discord.Embed(
                title="🏆 Ranking de Casais Mais Ricos",
                color=discord.Color.gold()
            )
            
            description = ""
            for i, row in enumerate(rankings, 1):
                user1 = interaction.guild.get_member(int(row['user1_id']))
                user2 = interaction.guild.get_member(int(row['user2_id']))
                u1_name = user1.display_name if user1 else "Usuário 1"
                u2_name = user2.display_name if user2 else "Usuário 2"
                wealth = row['total_wealth']
                description += f"**{i}.** {u1_name} & {u2_name} — 💰 {wealth:,} moedas\n"
            
            embed.description = description or "Nenhum casal encontrado."
            await interaction.response.send_message(embed=embed)

    @commands.command(name='rankingcasais', aliases=['richestcouples'])
    async def ranking_casais(self, ctx):
        """Ver os casais mais ricos do servidor"""
        conn = self.bot.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT c.user1_id, c.user2_id, (e1.coins + e1.bank + e2.coins + e2.bank) as total_wealth
            FROM casamentos c
            JOIN economia e1 ON c.user1_id = e1.user_id
            JOIN economia e2 ON c.user2_id = e2.user_id
            ORDER BY total_wealth DESC
            LIMIT 10
        """)
        
        rankings = cursor.fetchall()
        conn.close()
        
        embed = discord.Embed(
            title="🏆 Ranking de Casais Mais Ricos",
            color=discord.Color.gold()
        )
        
        description = ""
        for i, row in enumerate(rankings, 1):
            user1 = ctx.guild.get_member(int(row['user1_id']))
            user2 = ctx.guild.get_member(int(row['user2_id']))
            u1_name = user1.display_name if user1 else "Usuário 1"
            u2_name = user2.display_name if user2 else "Usuário 2"
            wealth = row['total_wealth']
            description += f"**{i}.** {u1_name} & {u2_name} — 💰 {wealth:,} moedas\n"
        
        embed.description = description or "Nenhum casal encontrado."
        await ctx.send(embed=embed)

    @commands.command(name='beijar', aliases=['kiss'])
    async def beijar_prefix(self, ctx):
        """Dar um beijo carinhoso no seu parceiro"""
        user_id = str(ctx.author.id)
        conn = self.bot.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM casamentos WHERE user1_id = ? OR user2_id = ?", (user_id, user_id))
        marriage = cursor.fetchone()
        conn.close()

        if not marriage:
            await ctx.send("❌ Você precisa estar casado para beijar seu parceiro!")
            return

        partner_id = marriage['user2_id'] if marriage['user1_id'] == user_id else marriage['user1_id']
        embed = discord.Embed(
            description=f"💋 {ctx.author.mention} deu um beijo super carinhoso em <@{partner_id}>! O amor está no ar!",
            color=discord.Color.pink()
        )
        await ctx.send(embed=embed)

    @commands.command(name='abracar_casal', aliases=['hug_marriage', 'abracar_marry'])
    async def abracar_prefix(self, ctx):
        """Dar um abraço apertado no seu parceiro"""
        user_id = str(ctx.author.id)
        conn = self.bot.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM casamentos WHERE user1_id = ? OR user2_id = ?", (user_id, user_id))
        marriage = cursor.fetchone()
        conn.close()

        if not marriage:
            await ctx.send("❌ Você precisa estar casado para abraçar seu parceiro!")
            return

        partner_id = marriage['user2_id'] if marriage['user1_id'] == user_id else marriage['user1_id']
        embed = discord.Embed(
            description=f"🫂 {ctx.author.mention} deu um abraço super apertado em <@{partner_id}>! Sentindo o calor do amor!",
            color=discord.Color.pink()
        )
        await ctx.send(embed=embed)

    @commands.command(name='presentear_casal', aliases=['gift_marriage', 'presentear_marry'])
    async def presentear_prefix(self, ctx):
        """Dar um presente especial para seu parceiro"""
        user_id = str(ctx.author.id)
        conn = self.bot.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM casamentos WHERE user1_id = ? OR user2_id = ?", (user_id, user_id))
        marriage = cursor.fetchone()
        
        if not marriage:
            conn.close()
            await ctx.send("❌ Você precisa estar casado para presentear seu parceiro!")
            return
        
        cursor.execute("SELECT coins FROM economia WHERE user_id = ?", (user_id,))
        eco_data = cursor.fetchone()
        if not eco_data or eco_data['coins'] < 500:
            conn.close()
            await ctx.send("❌ Você precisa de pelo menos 500 moedas para comprar um presente!")
            return
        
        cursor.execute("UPDATE economia SET coins = coins - 500 WHERE user_id = ?", (user_id,))
        conn.commit()
        conn.close()

        partner_id = marriage['user2_id'] if marriage['user1_id'] == user_id else marriage['user1_id']
        import random
        presentes = ["uma caixa de bombons 🍫", "um buquê de flores 💐", "um anel de brilhantes 💍", "uma carta de amor 💌"]
        presente = random.choice(presentes)
        
        embed = discord.Embed(
            description=f"🎁 {ctx.author.mention} comprou **{presente}** para <@{partner_id}>! Que gesto lindo!",
            color=discord.Color.pink()
        )
        await ctx.send(embed=embed)

    @commands.command(name='fcasar', aliases=['forcasar', 'forcedarriagem'])
    async def fcasar(self, ctx, member: Optional[discord.Member] = None):
        """Forcar casamento de alguem (apenas admin)"""
        ADMIN_ROLE_ID = 1444053060862087370
        
        if not any(role.id == ADMIN_ROLE_ID for role in ctx.author.roles):
            await ctx.send("Voce nao tem permissao para usar este comando!")
            return
        
        if member is None:
            await ctx.send("Mencione a pessoa com quem deseja casar!")
            return
        
        if member.id == ctx.author.id:
            await ctx.send("Voce nao pode casar consigo mesmo!")
            return
        
        if member.bot:
            await ctx.send("Voce nao pode casar com um bot!")
            return
        
        user_id = str(ctx.author.id)
        target_id = str(member.id)
        
        self.bot.db.ensure_user_exists(user_id)
        self.bot.db.ensure_user_exists(target_id)
        
        conn = self.bot.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM casamentos 
            WHERE user1_id = ? OR user2_id = ?
        """, (user_id, user_id))
        
        if cursor.fetchone():
            await ctx.send("Voce ja esta casado(a)!")
            conn.close()
            return
        
        cursor.execute("""
            SELECT * FROM casamentos 
            WHERE user1_id = ? OR user2_id = ?
        """, (target_id, target_id))
        
        if cursor.fetchone():
            await ctx.send(f"{member.display_name} ja esta casado(a)!")
            conn.close()
            return
        
        cursor.execute("""
            INSERT INTO casamentos (user1_id, user2_id, married_at)
            VALUES (?, ?, ?)
        """, (user_id, target_id, datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
        
        embed = discord.Embed(
            title="Casamento Forcado!",
            description=f"{ctx.author.mention} forcou o casamento entre {ctx.author.mention} e {member.mention}!\n\nParabens aos noivos!",
            color=discord.Color.pink()
        )
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Casamento(bot))
