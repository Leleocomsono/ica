import discord
from discord.ext import commands
from datetime import datetime, timedelta
import random

class Social(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.hug_cooldown = {}
        self.kiss_cooldown = {}
        self.pat_cooldown = {}
    
    async def social_action(self, ctx, member: discord.Member, action: str, emoji: str, message: str):
        """Funcao generica para acoes sociais"""
        if member is None:
            await ctx.send(f"Mencione alguem para {action}!")
            return
        
        if member.id == ctx.author.id:
            await ctx.send(f"Voce nao pode {action} a si mesmo!")
            return
        
        embed = discord.Embed(
            description=f"{emoji} {ctx.author.mention} {message} {member.mention}!",
            color=discord.Color.pink()
        )
        
        await ctx.send(embed=embed)
        
        user_id = str(ctx.author.id)
        from main import update_mission_progress
        await update_mission_progress(user_id, "social", 1)
    
    @commands.command(name='abracar', aliases=['hug', 'abraco'])
    @commands.cooldown(1, 30, commands.BucketType.user)
    async def abracar(self, ctx, member: discord.Member = None):
        """Abracar alguem"""
        messages = [
            "deu um abraco caloroso em",
            "abracou apertado",
            "deu um super abraco em",
            "envolveu com carinho",
            "esmagou em um abraço de urso"
        ]
        await self.social_action(ctx, member, "abracar", "🫂", random.choice(messages))

    @commands.command(name='morder', aliases=['bite'])
    @commands.cooldown(1, 30, commands.BucketType.user)
    async def morder(self, ctx, member: discord.Member = None):
        """Morder alguem"""
        messages = [
            "deu uma mordidinha em",
            "mordeu o braço de",
            "deu uma dentada carinhosa em"
        ]
        await self.social_action(ctx, member, "morder", "🦷", random.choice(messages))
    
    @commands.command(name='cafune', aliases=['pat', 'headpat'])
    async def cafune(self, ctx, member: discord.Member = None):
        """Fazer cafune em alguem"""
        messages = [
            "fez cafune em",
            "acariciou a cabeca de",
            "deu um carinho em",
            "fez um pat pat em"
        ]
        await self.social_action(ctx, member, "fazer cafune", "🥰", random.choice(messages))
    
    @commands.command(name='tapa', aliases=['slap'])
    async def tapa(self, ctx, member: discord.Member = None):
        """Dar um tapa em alguem"""
        messages = [
            "deu um tapa em",
            "deu um tapao em",
            "estapeou"
        ]
        await self.social_action(ctx, member, "dar tapa", "👋", random.choice(messages))
    
    @commands.command(name='cutucar', aliases=['poke'])
    async def cutucar(self, ctx, member: discord.Member = None):
        """Cutucar alguem"""
        messages = [
            "cutucou",
            "deu um cutucao em",
            "ficou cutucando"
        ]
        await self.social_action(ctx, member, "cutucar", "👉", random.choice(messages))
    
    @commands.command(name='highfive', aliases=['hi5'])
    async def highfive(self, ctx, member: discord.Member = None):
        """Dar high five em alguem"""
        messages = [
            "deu um high five em",
            "bateu aquela high five com",
            "cumprimentou com um high five"
        ]
        await self.social_action(ctx, member, "dar high five", "✋", random.choice(messages))
    
    @commands.command(name='reputacao', aliases=['rep'])
    async def reputacao(self, ctx, member: discord.Member = None):
        """Ver reputacao de um usuario"""
        member = member or ctx.author
        user_id = str(member.id)
        
        self.bot.db.ensure_user_exists(user_id)
        
        conn = self.bot.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT positive, negative, total FROM reputacao WHERE user_id = ?
        """, (user_id,))
        
        data = cursor.fetchone()
        conn.close()
        
        positive = data['positive'] or 0
        negative = data['negative'] or 0
        total = data['total'] or 0
        
        embed = discord.Embed(
            title=f"Reputacao de {member.display_name}",
            color=discord.Color.gold() if total >= 0 else discord.Color.red()
        )
        
        embed.add_field(name="Positivos", value=f"👍 {positive}", inline=True)
        embed.add_field(name="Negativos", value=f"👎 {negative}", inline=True)
        embed.add_field(name="Total", value=f"⭐ {total}", inline=True)
        
        await ctx.send(embed=embed)
    
    @commands.command(name='rep+', aliases=['repplus', 'goodrep'])
    @commands.cooldown(1, 86400, commands.BucketType.user)
    async def rep_plus(self, ctx, member: discord.Member = None):
        """Dar reputacao positiva"""
        # Verificar se tem cargo imune para pular cooldown
        IMMUNE_ROLE_ID = 1439782753007697973
        has_immune_role = any(role.id == IMMUNE_ROLE_ID for role in ctx.author.roles)
        
        if has_immune_role:
            ctx.command.reset_cooldown(ctx)
        
        if member is None:
            ctx.command.reset_cooldown(ctx)
            await ctx.send("Mencione alguem para dar reputacao!")
            return
        
        if member.id == ctx.author.id:
            ctx.command.reset_cooldown(ctx)
            await ctx.send("Voce nao pode dar reputacao a si mesmo!")
            return
        
        if member.bot:
            ctx.command.reset_cooldown(ctx)
            await ctx.send("Voce nao pode dar reputacao a um bot!")
            return
        
        target_id = str(member.id)
        self.bot.db.ensure_user_exists(target_id)
        
        conn = self.bot.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE reputacao 
            SET positive = positive + 1, total = total + 1
            WHERE user_id = ?
        """, (target_id,))
        
        conn.commit()
        conn.close()
        
        embed = discord.Embed(
            description=f"👍 {ctx.author.mention} deu **+1 reputacao** para {member.mention}!",
            color=discord.Color.green()
        )
        
        await ctx.send(embed=embed)
    
    @rep_plus.error
    async def rep_plus_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            hours = int(error.retry_after // 3600)
            minutes = int((error.retry_after % 3600) // 60)
            await ctx.send(f"Voce ja deu reputacao hoje! Volte em **{hours}h {minutes}m**.")
    
    @commands.command(name='rep-', aliases=['repminus', 'badrep'])
    @commands.cooldown(1, 86400, commands.BucketType.user)
    async def rep_minus(self, ctx, member: discord.Member = None):
        """Dar reputacao negativa"""
        # Verificar se tem cargo imune para pular cooldown
        IMMUNE_ROLE_ID = 1439782753007697973
        has_immune_role = any(role.id == IMMUNE_ROLE_ID for role in ctx.author.roles)
        
        if has_immune_role:
            ctx.command.reset_cooldown(ctx)
        
        if member is None:
            ctx.command.reset_cooldown(ctx)
            await ctx.send("Mencione alguem para dar reputacao!")
            return
        
        if member.id == ctx.author.id:
            ctx.command.reset_cooldown(ctx)
            await ctx.send("Voce nao pode dar reputacao a si mesmo!")
            return
        
        if member.bot:
            ctx.command.reset_cooldown(ctx)
            await ctx.send("Voce nao pode dar reputacao a um bot!")
            return
        
        target_id = str(member.id)
        self.bot.db.ensure_user_exists(target_id)
        
        conn = self.bot.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE reputacao 
            SET negative = negative + 1, total = total - 1
            WHERE user_id = ?
        """, (target_id,))
        
        conn.commit()
        conn.close()
        
        embed = discord.Embed(
            description=f"👎 {ctx.author.mention} deu **-1 reputacao** para {member.mention}!",
            color=discord.Color.red()
        )
        
        await ctx.send(embed=embed)
    
    @rep_minus.error
    async def rep_minus_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            hours = int(error.retry_after // 3600)
            minutes = int((error.retry_after % 3600) // 60)
            await ctx.send(f"Voce ja deu reputacao hoje! Volte em **{hours}h {minutes}m**.")
    
    @commands.command(name='resetar rep', aliases=['reset-rep', 'reseterep'])
    @commands.has_permissions(moderate_members=True)
    async def resetar_rep(self, ctx, member: discord.Member = None):
        """Resetar reputacao de um usuario (Requer permissao de warn)"""
        if member is None:
            await ctx.send("Mencione um membro para resetar a reputacao!")
            return
        
        target_id = str(member.id)
        self.bot.db.ensure_user_exists(target_id)
        
        conn = self.bot.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE reputacao 
            SET positive = 0, negative = 0, total = 0
            WHERE user_id = ?
        """, (target_id,))
        
        conn.commit()
        conn.close()
        
        embed = discord.Embed(
            description=f"🔄 {ctx.author.mention} resetou a reputacao de {member.mention}!",
            color=discord.Color.blue()
        )
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Social(bot))
