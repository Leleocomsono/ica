import discord
from discord.ext import commands
from datetime import datetime

class Casamento(commands.Cog):
    """Sistema de casamento entre usuários"""
    
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(name='casar', aliases=['marry'])
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def casar(self, ctx, member: discord.Member):
        """Pedir alguém em casamento"""
        if member.bot:
            await ctx.send("❌ Você não pode se casar com um bot!")
            return
        
        if member.id == ctx.author.id:
            await ctx.send("❌ Você não pode se casar consigo mesmo!")
            return
        
        user_id = str(ctx.author.id)
        target_id = str(member.id)
        
        self.bot.db.ensure_user_exists(user_id)
        self.bot.db.ensure_user_exists(target_id)
        
        conn = self.bot.db.get_connection()
        cursor = conn.cursor()
        
        # Verificar se já está casado
        cursor.execute("""
            SELECT 1 FROM casamentos WHERE user1_id = ? OR user2_id = ?
        """, (user_id, user_id))
        
        if cursor.fetchone():
            await ctx.send("❌ Você já está casado!")
            conn.close()
            return
        
        cursor.execute("""
            SELECT 1 FROM casamentos WHERE user1_id = ? OR user2_id = ?
        """, (target_id, target_id))
        
        if cursor.fetchone():
            await ctx.send("❌ Esta pessoa já está casada!")
            conn.close()
            return
        
        # Verificar se já existe pedido
        cursor.execute("""
            SELECT 1 FROM casamento_pedidos 
            WHERE proposer_id = ? AND target_id = ?
        """, (user_id, target_id))
        
        if cursor.fetchone():
            await ctx.send("❌ Você já propôs casamento para esta pessoa!")
            conn.close()
            return
        
        # Criar pedido
        cursor.execute("""
            INSERT INTO casamento_pedidos (proposer_id, target_id, proposed_at)
            VALUES (?, ?, ?)
        """, (user_id, target_id, datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
        
        embed = discord.Embed(
            title="💍 Pedido de Casamento",
            description=f"{ctx.author.mention} pediu {member.mention} em casamento!",
            color=discord.Color.pink()
        )
        
        embed.add_field(
            name="Como aceitar?",
            value=f"{member.mention}, use `!aceitar {ctx.author.mention}` para aceitar\nou `!recusar {ctx.author.mention}` para recusar",
            inline=False
        )
        
        await ctx.send(embed=embed)
    
    @commands.command(name='aceitar', aliases=['accept'])
    async def aceitar(self, ctx, member: discord.Member):
        """Aceitar pedido de casamento"""
        user_id = str(ctx.author.id)
        proposer_id = str(member.id)
        
        conn = self.bot.db.get_connection()
        cursor = conn.cursor()
        
        # Verificar se existe pedido
        cursor.execute("""
            SELECT 1 FROM casamento_pedidos 
            WHERE proposer_id = ? AND target_id = ?
        """, (proposer_id, user_id))
        
        if not cursor.fetchone():
            await ctx.send("❌ Não há pedido de casamento desta pessoa para você!")
            conn.close()
            return
        
        # Verificar se ainda estão solteiros
        cursor.execute("""
            SELECT 1 FROM casamentos WHERE user1_id IN (?, ?) OR user2_id IN (?, ?)
        """, (user_id, proposer_id, user_id, proposer_id))
        
        if cursor.fetchone():
            await ctx.send("❌ Um de vocês já está casado!")
            conn.close()
            return
        
        # Criar casamento
        now = datetime.now().isoformat()
        cursor.execute("""
            INSERT INTO casamentos (user1_id, user2_id, married_at)
            VALUES (?, ?, ?)
        """, (proposer_id, user_id, now))
        
        # Remover pedido
        cursor.execute("""
            DELETE FROM casamento_pedidos WHERE proposer_id = ? AND target_id = ?
        """, (proposer_id, user_id))
        
        conn.commit()
        conn.close()
        
        embed = discord.Embed(
            title="🎉 Casamento Realizado!",
            description=f"{member.mention} e {ctx.author.mention} agora estão casados!",
            color=discord.Color.gold()
        )
        
        embed.set_footer(text="Parabéns pelo casamento! 💑")
        await ctx.send(embed=embed)
    
    @commands.command(name='recusar', aliases=['reject'])
    async def recusar(self, ctx, member: discord.Member):
        """Recusar pedido de casamento"""
        user_id = str(ctx.author.id)
        proposer_id = str(member.id)
        
        conn = self.bot.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 1 FROM casamento_pedidos 
            WHERE proposer_id = ? AND target_id = ?
        """, (proposer_id, user_id))
        
        if not cursor.fetchone():
            await ctx.send("❌ Não há pedido de casamento desta pessoa para você!")
            conn.close()
            return
        
        cursor.execute("""
            DELETE FROM casamento_pedidos WHERE proposer_id = ? AND target_id = ?
        """, (proposer_id, user_id))
        
        conn.commit()
        conn.close()
        
        await ctx.send(f"💔 {ctx.author.mention} recusou o pedido de {member.mention}.")
    
    @commands.command(name='divorciar', aliases=['divorce'])
    async def divorciar(self, ctx):
        """Divorciar do parceiro atual"""
        user_id = str(ctx.author.id)
        
        conn = self.bot.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT user1_id, user2_id FROM casamentos 
            WHERE user1_id = ? OR user2_id = ?
        """, (user_id, user_id))
        
        marriage = cursor.fetchone()
        
        if not marriage:
            await ctx.send("❌ Você não está casado!")
            conn.close()
            return
        
        partner_id = marriage['user2_id'] if marriage['user1_id'] == user_id else marriage['user1_id']
        
        cursor.execute("""
            DELETE FROM casamentos WHERE user1_id IN (?, ?) OR user2_id IN (?, ?)
        """, (user_id, partner_id, user_id, partner_id))
        
        conn.commit()
        conn.close()
        
        try:
            partner = await self.bot.fetch_user(int(partner_id))
            await ctx.send(f"💔 {ctx.author.mention} e {partner.mention} se divorciaram.")
        except:
            await ctx.send("💔 Divórcio realizado.")
    
    @commands.command(name='casais', aliases=['couples'])
    async def casais(self, ctx):
        """Ver todos os casais do servidor"""
        conn = self.bot.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT user1_id, user2_id, married_at FROM casamentos
            ORDER BY married_at DESC LIMIT 10
        """, ())
        
        marriages = cursor.fetchall()
        conn.close()
        
        if not marriages:
            await ctx.send("❌ Ainda não há casais neste servidor.")
            return
        
        embed = discord.Embed(
            title="💑 Casais do Servidor",
            description=f"Total de {len(marriages)} casamento(s)",
            color=discord.Color.pink()
        )
        
        for i, marriage in enumerate(marriages, 1):
            try:
                user1 = await self.bot.fetch_user(int(marriage['user1_id']))
                user2 = await self.bot.fetch_user(int(marriage['user2_id']))
                date = datetime.fromisoformat(marriage['married_at']).strftime("%d/%m/%Y")
                
                embed.add_field(
                    name=f"{i}. {user1.name} & {user2.name}",
                    value=f"Casados desde: {date}",
                    inline=False
                )
            except:
                continue
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Casamento(bot))
