import discord
from discord.ext import commands
from datetime import datetime
import aiohttp

class Perfil(commands.Cog):
    """Sistema de perfil de usuários"""
    
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(name='perfil')
    async def perfil(self, ctx, member: discord.Member = None):
        """Ver perfil completo de um usuário"""
        if member is None:
            member = ctx.author
        
        user_id = str(member.id)
        self.bot.db.ensure_user_exists(user_id)
        
        conn = self.bot.db.get_connection()
        cursor = conn.cursor()
        
        # Buscar dados do usuário
        cursor.execute("""
            SELECT u.*, e.coins, e.bank
            FROM usuarios u
            LEFT JOIN economia e ON u.user_id = e.user_id
            WHERE u.user_id = ?
        """, (user_id,))
        
        user_data = cursor.fetchone()
        
        # Buscar casamento
        cursor.execute("""
            SELECT user2_id, married_at FROM casamentos WHERE user1_id = ?
            UNION
            SELECT user1_id, married_at FROM casamentos WHERE user2_id = ?
        """, (user_id, user_id))
        
        marriage_data = cursor.fetchone()
        
        # Buscar pet ativo
        cursor.execute("""
            SELECT species, custom_name, level FROM pets 
            WHERE user_id = ? ORDER BY pet_id DESC LIMIT 1
        """, (user_id,))
        
        pet_data = cursor.fetchone()
        
        # Buscar conquistas
        cursor.execute("""
            SELECT COUNT(*) as total FROM conquistas_usuario WHERE user_id = ?
        """, (user_id,))
        
        achievements = cursor.fetchone()['total']
        
        conn.close()
        
        # Criar embed
        embed = discord.Embed(
            title=f"👤 Perfil de {member.name}",
            color=discord.Color.blue()
        )
        
        # Banner
        if user_data['banner']:
            embed.set_image(url=user_data['banner'])
        
        embed.set_thumbnail(url=member.display_avatar.url)
        
        # Bio
        bio = user_data['bio'] if user_data['bio'] else "Sem biografia definida"
        embed.add_field(name="📝 Biografia", value=bio, inline=False)
        
        # Estatísticas
        embed.add_field(name="💬 Mensagens", value=f"{user_data['messages']:,}", inline=True)
        embed.add_field(name="⌨️ Comandos", value=f"{user_data['commands_used']:,}", inline=True)
        embed.add_field(name="💰 Moedas", value=f"{user_data['coins']:,}", inline=True)
        
        # XP e Nível
        xp = user_data['xp']
        level = user_data['level']
        next_level_xp = (level ** 2) * 100
        current_level_xp = ((level - 1) ** 2) * 100 if level > 1 else 0
        xp_progress = xp - current_level_xp
        xp_needed = next_level_xp - current_level_xp
        
        percentage = int((xp_progress / xp_needed) * 100) if xp_needed > 0 else 0
        progress_bar = "▰" * int((xp_progress / xp_needed) * 10) + "▱" * (10 - int((xp_progress / xp_needed) * 10))
        
        embed.add_field(
            name=f"⭐ Nível {level}",
            value=f"{progress_bar}\nXP: {xp:,} ({percentage}%)",
            inline=False
        )
        
        # Pet
        if pet_data:
            pet_name = pet_data['custom_name'] if pet_data['custom_name'] else pet_data['species']
            embed.add_field(
                name="🐾 Pet Ativo",
                value=f"{pet_name} (Nv. {pet_data['level']})",
                inline=True
            )
        
        # Casamento
        if marriage_data:
            try:
                partner_id = marriage_data['user2_id'] if marriage_data['user2_id'] != user_id else marriage_data['user1_id']
                partner = await self.bot.fetch_user(int(partner_id))
                date = datetime.fromisoformat(marriage_data['married_at']).strftime("%d/%m/%Y")
                embed.add_field(
                    name="💍 Estado Civil",
                    value=f"Casado(a) com {partner.name}\nDesde: {date}",
                    inline=True
                )
            except:
                embed.add_field(name="💍 Estado Civil", value="Casado(a)", inline=True)
        else:
            embed.add_field(name="💍 Estado Civil", value="Solteiro(a)", inline=True)
        
        # Conquistas
        embed.add_field(name="🏆 Conquistas", value=f"{achievements} desbloqueadas", inline=True)
        
        # Rodapé
        created = datetime.fromisoformat(user_data['created_at']).strftime("%d/%m/%Y")
        embed.set_footer(text=f"Membro desde: {created}")
        
        await ctx.send(embed=embed)
    
    @commands.command(name='bio')
    async def bio(self, ctx, *, text: str):
        """Definir sua biografia (máx. 200 caracteres)"""
        if len(text) > 200:
            await ctx.send("❌ A biografia deve ter no máximo 200 caracteres!")
            return
        
        user_id = str(ctx.author.id)
        self.bot.db.ensure_user_exists(user_id)
        
        conn = self.bot.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE usuarios SET bio = ? WHERE user_id = ?
        """, (text, user_id))
        
        conn.commit()
        conn.close()
        
        await ctx.send("✅ Biografia atualizada com sucesso!")
    
    @commands.command(name='xp')
    async def xp(self, ctx, member: discord.Member = None):
        """Ver XP e nível"""
        if member is None:
            member = ctx.author
        
        user_id = str(member.id)
        self.bot.db.ensure_user_exists(user_id)
        
        conn = self.bot.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT xp, level FROM usuarios WHERE user_id = ?", (user_id,))
        data = cursor.fetchone()
        conn.close()
        
        xp = data['xp']
        level = data['level']
        next_level_xp = (level ** 2) * 100
        
        embed = discord.Embed(
            title=f"⭐ XP de {member.name}",
            color=discord.Color.gold()
        )
        
        embed.add_field(name="Nível", value=level, inline=True)
        embed.add_field(name="XP Total", value=f"{xp:,}", inline=True)
        embed.add_field(name="Próximo Nível", value=f"{next_level_xp:,} XP", inline=True)
        
        await ctx.send(embed=embed)
    
    @commands.command(name='nivel', aliases=['level'])
    async def nivel(self, ctx, member: discord.Member = None):
        """Ver nível e progresso"""
        if member is None:
            member = ctx.author
        
        user_id = str(member.id)
        self.bot.db.ensure_user_exists(user_id)
        
        conn = self.bot.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT xp, level FROM usuarios WHERE user_id = ?", (user_id,))
        data = cursor.fetchone()
        conn.close()
        
        xp = data['xp']
        level = data['level']
        next_level_xp = (level ** 2) * 100
        current_level_xp = ((level - 1) ** 2) * 100 if level > 1 else 0
        
        xp_progress = xp - current_level_xp
        xp_needed = next_level_xp - current_level_xp
        percentage = int((xp_progress / xp_needed) * 100) if xp_needed > 0 else 0
        
        progress_bar = "▰" * int((xp_progress / xp_needed) * 20) + "▱" * (20 - int((xp_progress / xp_needed) * 20))
        
        embed = discord.Embed(
            title=f"📊 Progresso de {member.name}",
            description=f"**Nível {level}** ({percentage}%)",
            color=discord.Color.blue()
        )
        
        embed.add_field(
            name="Progresso",
            value=f"{progress_bar}\n{xp_progress:,} / {xp_needed:,} XP",
            inline=False
        )
        
        embed.add_field(name="XP Total", value=f"{xp:,}", inline=True)
        embed.add_field(name="Faltam", value=f"{next_level_xp - xp:,} XP", inline=True)
        
        await ctx.send(embed=embed)
    
    @commands.command(name='avatar')
    async def avatar(self, ctx, member: discord.Member = None):
        """Ver avatar de um usuário"""
        if member is None:
            member = ctx.author
        
        embed = discord.Embed(
            title=f"Avatar de {member.name}",
            color=discord.Color.blue()
        )
        
        embed.set_image(url=member.display_avatar.url)
        embed.set_footer(text=f"ID: {member.id}")
        
        await ctx.send(embed=embed)
    
    @commands.command(name='banner', aliases=['profile-bg'])
    async def banner(self, ctx, *, url: str = None):
        """Definir banner do perfil ou removê-lo"""
        user_id = str(ctx.author.id)
        self.bot.db.ensure_user_exists(user_id)
        
        if url is None:
            await ctx.send("Use `!banner [url]` para definir ou `!banner remover` para remover.")
            return
        
        if url.lower() == "remover":
            conn = self.bot.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("UPDATE usuarios SET banner = NULL WHERE user_id = ?", (user_id,))
            conn.commit()
            conn.close()
            
            await ctx.send("✅ Banner removido com sucesso!")
            return
        
        if not url.startswith(('http://', 'https://')):
            await ctx.send("❌ URL inválida! Deve começar com http:// ou https://")
            return
        
        # Validar se é imagem
        try:
            async with aiohttp.ClientSession() as session:
                async with session.head(url, timeout=aiohttp.ClientTimeout(total=5)) as response:
                    if response.status != 200:
                        await ctx.send("❌ URL inválida ou inacessível!")
                        return
                    
                    content_type = response.headers.get('Content-Type', '')
                    if not content_type.startswith('image/'):
                        await ctx.send("❌ A URL deve ser uma imagem válida!")
                        return
        except:
            await ctx.send("❌ Não foi possível validar a URL!")
            return
        
        conn = self.bot.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("UPDATE usuarios SET banner = ? WHERE user_id = ?", (url, user_id))
        conn.commit()
        conn.close()
        
        await ctx.send("✅ Banner atualizado! Use `!perfil` para visualizar.")

async def setup(bot):
    await bot.add_cog(Perfil(bot))
