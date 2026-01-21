import discord
from discord.ext import commands
from datetime import datetime

class Administracao(commands.Cog):
    """Comandos de administração"""
    
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(name='limpar', aliases=['clear', 'purge'])
    @commands.has_permissions(manage_messages=True)
    async def limpar(self, ctx, quantidade: int):
        """Limpar mensagens do canal"""
        if quantidade < 1 or quantidade > 100:
            await ctx.send("❌ Quantidade deve ser entre 1 e 100!")
            return
        
        await ctx.channel.purge(limit=quantidade + 1)
        msg = await ctx.send(f"🗑️ {quantidade} mensagens foram deletadas!")
        
        import asyncio
        await asyncio.sleep(3)
        await msg.delete()
    
    @commands.command(name='slowmode')
    @commands.has_permissions(manage_channels=True)
    async def slowmode(self, ctx, segundos: int):
        """Definir modo lento no canal"""
        if segundos < 0 or segundos > 21600:
            await ctx.send("❌ Tempo deve ser entre 0 e 21600 segundos (6 horas)!")
            return
        
        await ctx.channel.edit(slowmode_delay=segundos)
        
        if segundos == 0:
            await ctx.send("✅ Modo lento desativado!")
        else:
            await ctx.send(f"✅ Modo lento definido para {segundos} segundos!")
    
    @commands.command(name='warn', aliases=['avisar'])
    @commands.has_permissions(kick_members=True)
    async def warn(self, ctx, member: discord.Member, *, motivo: str = "Sem motivo especificado"):
        """Avisar um usuário"""
        if member.top_role >= ctx.author.top_role and ctx.author != ctx.guild.owner:
            await ctx.send("❌ Você não pode avisar este usuário!")
            return
        
        if member.bot:
            await ctx.send("❌ Você não pode avisar bots!")
            return
        
        user_id = str(member.id)
        mod_id = str(ctx.author.id)
        guild_id = str(ctx.guild.id)
        
        conn = self.bot.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO warns (user_id, guild_id, moderator_id, reason, warned_at)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, guild_id, mod_id, motivo, datetime.now().isoformat()))
        
        # Contar warns
        cursor.execute("""
            SELECT COUNT(*) as total FROM warns WHERE user_id = ? AND guild_id = ?
        """, (user_id, guild_id))
        
        total = cursor.fetchone()['total']
        
        conn.commit()
        conn.close()
        
        embed = discord.Embed(
            title="⚠️ Usuário Avisado",
            color=discord.Color.orange()
        )
        
        embed.add_field(name="Usuário", value=member.mention, inline=True)
        embed.add_field(name="Moderador", value=ctx.author.mention, inline=True)
        embed.add_field(name="Total de Warns", value=total, inline=True)
        embed.add_field(name="Motivo", value=motivo, inline=False)
        
        await ctx.send(embed=embed)
        
        # Tentar enviar DM
        try:
            await member.send(f"⚠️ Você recebeu um aviso em **{ctx.guild.name}**\nMotivo: {motivo}\nTotal de avisos: {total}")
        except:
            pass
    
    @commands.command(name='warns', aliases=['avisos'])
    async def warns(self, ctx, member: discord.Member = None):
        """Ver avisos de um usuário"""
        if member is None:
            member = ctx.author
        
        user_id = str(member.id)
        guild_id = str(ctx.guild.id)
        
        conn = self.bot.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT reason, moderator_id, warned_at FROM warns 
            WHERE user_id = ? AND guild_id = ?
            ORDER BY warned_at DESC
        """, (user_id, guild_id))
        
        warns = cursor.fetchall()
        conn.close()
        
        if not warns:
            await ctx.send(f"✅ {member.mention} não possui avisos!")
            return
        
        embed = discord.Embed(
            title=f"⚠️ Avisos de {member.name}",
            description=f"Total: {len(warns)} aviso(s)",
            color=discord.Color.orange()
        )
        
        for i, warn in enumerate(warns[:10], 1):
            try:
                mod = await self.bot.fetch_user(int(warn['moderator_id']))
                date = datetime.fromisoformat(warn['warned_at']).strftime("%d/%m/%Y")
                
                embed.add_field(
                    name=f"Aviso #{i}",
                    value=f"**Moderador:** {mod.name}\n**Motivo:** {warn['reason']}\n**Data:** {date}",
                    inline=False
                )
            except:
                continue
        
        await ctx.send(embed=embed)
    
    @commands.command(name='clearwarns', aliases=['limparavisos'])
    @commands.has_permissions(administrator=True)
    async def clearwarns(self, ctx, member: discord.Member):
        """Limpar todos os avisos de um usuário"""
        user_id = str(member.id)
        guild_id = str(ctx.guild.id)
        
        conn = self.bot.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            DELETE FROM warns WHERE user_id = ? AND guild_id = ?
        """, (user_id, guild_id))
        
        deleted = cursor.rowcount
        
        conn.commit()
        conn.close()
        
        await ctx.send(f"✅ {deleted} aviso(s) de {member.mention} foram removidos!")
    
    @commands.command(name='set-canal-log', aliases=['setlog'])
    @commands.has_permissions(administrator=True)
    async def set_canal_log(self, ctx, channel: discord.TextChannel):
        """Definir canal de logs"""
        guild_id = str(ctx.guild.id)
        
        conn = self.bot.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO guild_config (guild_id, log_channel_id)
            VALUES (?, ?)
            ON CONFLICT(guild_id) DO UPDATE SET log_channel_id = ?
        """, (guild_id, str(channel.id), str(channel.id)))
        
        conn.commit()
        conn.close()
        
        await ctx.send(f"✅ Canal de logs definido para {channel.mention}!")
    
    @commands.command(name='mute', aliases=['silenciar'])
    @commands.has_permissions(kick_members=True)
    async def mute(self, ctx, member: discord.Member, tempo: int = 10, *, motivo: str = "Sem motivo especificado"):
        """Silenciar um membro (tempo em minutos)"""
        if member.bot:
            await ctx.send("❌ Você não pode silenciar bots!")
            return
        
        if member.id == ctx.author.id:
            await ctx.send("❌ Você não pode silenciar a si mesmo!")
            return
        
        if member.top_role >= ctx.author.top_role:
            await ctx.send("❌ Você não pode silenciar alguém com cargo igual ou superior ao seu!")
            return
        
        duracao = timedelta(minutes=tempo)
        
        try:
            await member.timeout(duracao, reason=motivo)
            
            embed = discord.Embed(
                title="🔇 Membro Silenciado",
                color=discord.Color.orange()
            )
            embed.add_field(name="Usuário", value=member.mention, inline=True)
            embed.add_field(name="Moderador", value=ctx.author.mention, inline=True)
            embed.add_field(name="Duração", value=f"{tempo} minutos", inline=True)
            embed.add_field(name="Motivo", value=motivo, inline=False)
            
            await ctx.send(embed=embed)
            
            conn = self.bot.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT log_channel_id FROM guild_config WHERE guild_id = ?
            """, (str(ctx.guild.id),))
            
            result = cursor.fetchone()
            conn.close()
            
            if result and result['log_channel_id']:
                log_channel = ctx.guild.get_channel(int(result['log_channel_id']))
                if log_channel:
                    await log_channel.send(embed=embed)
        
        except discord.Forbidden:
            await ctx.send("❌ Não tenho permissão para silenciar este usuário!")
        except Exception as e:
            await ctx.send(f"❌ Erro ao silenciar: {e}")
    
    @commands.command(name='unmute', aliases=['dessilenciar'])
    @commands.has_permissions(kick_members=True)
    async def unmute(self, ctx, member: discord.Member):
        """Remover silenciamento de um membro"""
        try:
            await member.timeout(None)
            
            embed = discord.Embed(
                title="🔊 Silenciamento Removido",
                color=discord.Color.green()
            )
            embed.add_field(name="Usuário", value=member.mention, inline=True)
            embed.add_field(name="Moderador", value=ctx.author.mention, inline=True)
            
            await ctx.send(embed=embed)
            
            conn = self.bot.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT log_channel_id FROM guild_config WHERE guild_id = ?
            """, (str(ctx.guild.id),))
            
            result = cursor.fetchone()
            conn.close()
            
            if result and result['log_channel_id']:
                log_channel = ctx.guild.get_channel(int(result['log_channel_id']))
                if log_channel:
                    await log_channel.send(embed=embed)
        
        except discord.Forbidden:
            await ctx.send("❌ Não tenho permissão para remover o silenciamento deste usuário!")
        except Exception as e:
            await ctx.send(f"❌ Erro ao remover silenciamento: {e}")

async def setup(bot):
    await bot.add_cog(Administracao(bot))
