import discord
from discord.ext import commands

class Social(commands.Cog):
    """Sistema social"""
    
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(name='reputacao', aliases=['rep'])
    @commands.cooldown(1, 43200, commands.BucketType.user)
    async def reputacao(self, ctx, member: discord.Member, tipo: str = "+1"):
        """Dar reputação para alguém (+1 ou -1)"""
        if member.bot:
            await ctx.send("❌ Você não pode dar reputação para bots!")
            return
        
        if member.id == ctx.author.id:
            await ctx.send("❌ Você não pode dar reputação para si mesmo!")
            return
        
        if tipo not in ['+1', '-1']:
            await ctx.send("❌ Use +1 ou -1")
            return
        
        user_id = str(member.id)
        self.bot.db.ensure_user_exists(user_id)
        
        conn = self.bot.db.get_connection()
        cursor = conn.cursor()
        
        if tipo == '+1':
            cursor.execute("UPDATE reputacao SET positive = positive + 1, total = total + 1 WHERE user_id = ?", (user_id,))
            msg = f"✅ Você deu +1 reputação para {member.mention}!"
        else:
            cursor.execute("UPDATE reputacao SET negative = negative + 1, total = total - 1 WHERE user_id = ?", (user_id,))
            msg = f"❌ Você deu -1 reputação para {member.mention}!"
        
        conn.commit()
        conn.close()
        
        await ctx.send(msg)
    
    @commands.command(name='presentear', aliases=['gift'])
    async def presentear(self, ctx, member: discord.Member, quantidade: int):
        """Presentear moedas para alguém"""
        if member.bot:
            await ctx.send("❌ Você não pode presentear bots!")
            return
        
        if member.id == ctx.author.id:
            await ctx.send("❌ Você não pode presentear a si mesmo!")
            return
        
        if quantidade < 1:
            await ctx.send("❌ Quantidade inválida!")
            return
        
        user_id = str(ctx.author.id)
        target_id = str(member.id)
        
        self.bot.db.ensure_user_exists(user_id)
        self.bot.db.ensure_user_exists(target_id)
        
        conn = self.bot.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT coins FROM economia WHERE user_id = ?", (user_id,))
        coins = cursor.fetchone()['coins']
        
        if coins < quantidade:
            await ctx.send(f"❌ Você não tem moedas suficientes! Você tem: {coins}")
            conn.close()
            return
        
        cursor.execute("UPDATE economia SET coins = coins - ? WHERE user_id = ?", (quantidade, user_id))
        cursor.execute("UPDATE economia SET coins = coins + ? WHERE user_id = ?", (quantidade, target_id))
        
        conn.commit()
        conn.close()
        
        embed = discord.Embed(
            title="🎁 Presente Enviado!",
            description=f"{ctx.author.mention} presenteou {member.mention} com {quantidade} moedas!",
            color=discord.Color.pink()
        )
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Social(bot))
