import discord
from discord.ext import commands
from datetime import datetime
import re
import aiohttp

LEVEL_ROLES = {
    5: 1446309179844464782,
    10: 1446309162073198673,
    20: 1446309146520719480,
    40: 1446309124638900285,
    80: 1446309085644587011,
    100: 1446309052660580352
}

class Perfil(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    def get_next_role_level(self, current_level: int) -> tuple:
        levels = sorted(LEVEL_ROLES.keys())
        for lvl in levels:
            if current_level < lvl:
                return lvl, LEVEL_ROLES[lvl]
        return None, None
    
    def calculate_xp_for_level(self, level: int) -> int:
        return ((level - 1) ** 2) * 100
    
    def parse_color(self, color_str: str) -> str:
        color_str = color_str.strip().upper()
        
        if color_str.startswith('#'):
            color_str = color_str[1:]
        
        if re.match(r'^[0-9A-F]{6}$', color_str):
            return f"#{color_str}"
        
        color_names = {
            'VERMELHO': '#FF0000', 'RED': '#FF0000',
            'VERDE': '#00FF00', 'GREEN': '#00FF00',
            'AZUL': '#0000FF', 'BLUE': '#0000FF',
            'AMARELO': '#FFFF00', 'YELLOW': '#FFFF00',
            'ROXO': '#800080', 'PURPLE': '#800080',
            'ROSA': '#FFC0CB', 'PINK': '#FFC0CB',
            'LARANJA': '#FFA500', 'ORANGE': '#FFA500',
            'BRANCO': '#FFFFFF', 'WHITE': '#FFFFFF',
            'PRETO': '#000000', 'BLACK': '#000000',
            'CIANO': '#00FFFF', 'CYAN': '#00FFFF',
            'MAGENTA': '#FF00FF',
            'DOURADO': '#FFD700', 'GOLD': '#FFD700',
            'PRATA': '#C0C0C0', 'SILVER': '#C0C0C0'
        }
        
        return color_names.get(color_str, None)

    @commands.command(name='perfil', aliases=['profile'])
    async def perfil(self, ctx, member: discord.Member = None):
        """Ver o perfil de um usuario"""
        member = member or ctx.author
        user_id = str(member.id)
        
        self.bot.db.ensure_user_exists(user_id)
        
        conn = self.bot.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT u.*, e.coins, e.bank
            FROM usuarios u
            LEFT JOIN economia e ON u.user_id = e.user_id
            WHERE u.user_id = ?
        """, (user_id,))
        user_data = cursor.fetchone()
        
        cursor.execute("SELECT titulo_nome FROM titulos WHERE user_id = ?", (user_id,))
        titulos = cursor.fetchall()
        
        cursor.execute("SELECT * FROM timeline WHERE user_id = ? ORDER BY timestamp DESC LIMIT 5", (user_id,))
        timeline = cursor.fetchall()
        
        # ... resto das consultas (pets, casamentos, etc - mantidas como antes)
        cursor.execute("""
            SELECT p.species, p.custom_name, p.level, p.rarity
            FROM pets p
            WHERE p.user_id = ?
            ORDER BY p.level DESC
            LIMIT 1
        """, (user_id,))
        pet = cursor.fetchone()
        
        cursor.execute("""
            SELECT m.user1_id, m.user2_id
            FROM casamentos m
            WHERE m.user1_id = ? OR m.user2_id = ?
        """, (user_id, user_id))
        marriage = cursor.fetchone()
        
        cursor.execute("""
            SELECT COUNT(*) as count FROM conquistas_usuario WHERE user_id = ?
        """, (user_id,))
        achievements_count = cursor.fetchone()['count']
        conn.close()

        # Melhoria Visual e Título
        titulo = f"「{user_data['titulo_ativo']}」" if user_data['titulo_ativo'] else "「Sem Título」"
        
        embed = discord.Embed(
            title=f"{titulo} {member.display_name}",
            description=user_data['bio'] or "Sem bio definida.",
            color=discord.Color(int(user_data['embed_color'].replace('#', ''), 16)) if user_data['embed_color'] else discord.Color.blue(),
            timestamp=datetime.now()
        )
        
        if user_data['banner']: embed.set_image(url=user_data['banner'])
        embed.set_thumbnail(url=member.display_avatar.url)
        
        # Timeline
        if timeline:
            timeline_text = "\n".join([f"🕒 {t['description']}" for t in timeline])
            embed.add_field(name="📜 Timeline Recente", value=timeline_text, inline=False)

        # ... campos de XP e Economia (simplificados para visual)
        level = user_data['level'] or 1
        embed.add_field(name="📊 Nível", value=f"**{level}**", inline=True)
        embed.add_field(name="💰 Saldo", value=f"**{(user_data['coins'] or 0) + (user_data['bank'] or 0):,}**", inline=True)
        embed.add_field(name="🏆 Conquistas", value=f"**{achievements_count}**", inline=True)

        class ProfileView(discord.ui.View):
            def __init__(self, user_id, titulos, timeline):
                super().__init__(timeout=60)
                self.user_id = user_id
                self.titulos = titulos
                self.timeline = timeline

            @discord.ui.button(label="Títulos", style=discord.ButtonStyle.primary, emoji="🏷️")
            async def titles_button(self, interaction: discord.Interaction, button: discord.ui.Button):
                if str(interaction.user.id) != self.user_id:
                    return await interaction.response.send_message("Este não é seu perfil!", ephemeral=True)
                
                if not self.titulos:
                    return await interaction.response.send_message("Você não possui títulos!", ephemeral=True)
                
                titles_list = "\n".join([f"• {t['titulo_nome']}" for t in self.titulos])
                await interaction.response.send_message(f"**Seus títulos:**\n{titles_list}\n\nUse `!set-titulo <nome>` para equipar.", ephemeral=True)

            @discord.ui.button(label="Histórico", style=discord.ButtonStyle.secondary, emoji="📜")
            async def history_button(self, interaction: discord.Interaction, button: discord.ui.Button):
                if not self.timeline:
                    return await interaction.response.send_message("Nenhum evento registrado na timeline.", ephemeral=True)
                
                history_text = "\n".join([f"• [{t['timestamp'][:16]}] {t['description']}" for t in self.timeline])
                await interaction.response.send_message(f"**Timeline Completa:**\n{history_text}", ephemeral=True)

        await ctx.send(embed=embed, view=ProfileView(user_id, titulos, timeline))

    @commands.command(name='set-titulo')
    async def set_titulo(self, ctx, *, nome: str):
        """Equipar um título que você possui"""
        user_id = str(ctx.author.id)
        conn = self.bot.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM titulos WHERE user_id = ? AND titulo_nome = ?", (user_id, nome))
        if not cursor.fetchone():
            await ctx.send("Você não possui este título!")
            conn.close()
            return
        cursor.execute("UPDATE usuarios SET titulo_ativo = ? WHERE user_id = ?", (nome, user_id))
        conn.commit()
        conn.close()
        await ctx.send(f"✅ Título **{nome}** equipado!")
    
    def create_progress_bar(self, percentage: float, length: int = 10) -> str:
        filled = int(percentage / 100 * length)
        empty = length - filled
        bar = '█' * filled + '░' * empty
        return f"`{bar}` {percentage:.1f}%"
    
    @commands.command(name='bio', aliases=['setbio'])
    async def bio(self, ctx, *, bio_text: str):
        """Definir sua bio"""
        if len(bio_text) > 200:
            await ctx.send("A bio deve ter no maximo 200 caracteres!")
            return
        
        user_id = str(ctx.author.id)
        self.bot.db.ensure_user_exists(user_id)
        
        conn = self.bot.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE usuarios SET bio = ? WHERE user_id = ?
        """, (bio_text, user_id))
        
        conn.commit()
        conn.close()
        
        await ctx.send(f"Bio atualizada com sucesso!")
    
    @commands.command(name='cor', aliases=['color', 'setcolor', 'setcor'])
    async def cor(self, ctx, *, cor_input: str):
        """Definir a cor do embed do perfil com codigo HEX ou nome"""
        color_hex = self.parse_color(cor_input)
        
        if not color_hex:
            await ctx.send(
                "Cor invalida! Use um codigo HEX (ex: `#FF5733` ou `FF5733`) "
                "ou um nome de cor (ex: `vermelho`, `azul`, `roxo`)"
            )
            return
        
        user_id = str(ctx.author.id)
        self.bot.db.ensure_user_exists(user_id)
        
        conn = self.bot.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE usuarios SET embed_color = ? WHERE user_id = ?
        """, (color_hex, user_id))
        
        conn.commit()
        conn.close()
        
        try:
            preview_color = discord.Color(int(color_hex.replace('#', ''), 16))
        except:
            preview_color = discord.Color.blue()
        
        embed = discord.Embed(
            title="Cor do Perfil Atualizada!",
            description=f"Sua nova cor e: **{color_hex}**",
            color=preview_color
        )
        
        await ctx.send(embed=embed)
    
    @commands.command(name='nivel', aliases=['level', 'xp'])
    async def nivel(self, ctx, member: discord.Member = None):
        """Ver o nivel de um usuario"""
        member = member or ctx.author
        user_id = str(member.id)
        
        self.bot.db.ensure_user_exists(user_id)
        
        conn = self.bot.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT xp, level FROM usuarios WHERE user_id = ?
        """, (user_id,))
        data = cursor.fetchone()
        
        cursor.execute("""
            SELECT COUNT(*) + 1 as rank FROM usuarios 
            WHERE xp > (SELECT xp FROM usuarios WHERE user_id = ?)
        """, (user_id,))
        rank_data = cursor.fetchone()
        
        conn.close()
        
        level = data['level'] or 1
        xp = data['xp'] or 0
        xp_needed = (level ** 2) * 100
        xp_progress = min(xp / xp_needed * 100, 100) if xp_needed > 0 else 0
        rank = rank_data['rank']
        
        progress_bar = self.create_progress_bar(xp_progress, 20)
        
        embed = discord.Embed(
            title=f"Nivel de {member.display_name}",
            color=discord.Color.gold()
        )
        
        embed.set_thumbnail(url=member.display_avatar.url)
        
        embed.add_field(
            name="Nivel",
            value=f"**{level}**",
            inline=True
        )
        
        embed.add_field(
            name="XP",
            value=f"**{xp:,}** / {xp_needed:,}",
            inline=True
        )
        
        embed.add_field(
            name="Ranking",
            value=f"**#{rank}**",
            inline=True
        )
        
        embed.add_field(
            name="Progresso",
            value=progress_bar,
            inline=False
        )
        
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
