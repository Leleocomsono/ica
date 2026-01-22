# Modified perfil.py (Version 1: Cleaned embed, removed footer and edit bio button, added navigation buttons for sections)

import discord
from discord.ext import commands
from discord.ui import View, Button
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
        self.setup_tables()
    
    def setup_tables(self):
        conn = self.bot.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_titles (
                user_id TEXT,
                title TEXT,
                equipped INTEGER DEFAULT 0,
                PRIMARY KEY (user_id, title)
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_badges (
                user_id TEXT,
                badge_name TEXT,
                PRIMARY KEY (user_id, badge_name)
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_timeline (
                user_id TEXT,
                event_description TEXT,
                timestamp TEXT
            )
        """)
        
        conn.commit()
        conn.close()
    
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
            SELECT p.name, pp.level
            FROM profissao_progresso pp
            JOIN profissoes p ON pp.profession_id = p.profession_id
            WHERE pp.user_id = ?
            ORDER BY pp.level DESC
            LIMIT 1
        """, (user_id,))
        profession = cursor.fetchone()
        
        cursor.execute("""
            SELECT COUNT(*) as count FROM conquistas_usuario WHERE user_id = ?
        """, (user_id,))
        achievements_count = cursor.fetchone()['count']
        
        cursor.execute("SELECT title FROM user_titles WHERE user_id = ? AND equipped = 1", (user_id,))
        title_row = cursor.fetchone()
        equipped_title = title_row['title'] if title_row else None
        
        cursor.execute("SELECT badge_name FROM user_badges WHERE user_id = ?", (user_id,))
        badges = [row['badge_name'] for row in cursor.fetchall()]
        
        cursor.execute("""
            SELECT event_description, timestamp FROM user_timeline WHERE user_id = ? ORDER BY timestamp DESC LIMIT 5
        """, (user_id,))
        timeline = cursor.fetchall()
        
        conn.close()
        
        embed_color = user_data['embed_color'] if user_data['embed_color'] else '#3498db'
        try:
            color = discord.Color(int(embed_color.replace('#', ''), 16))
        except:
            color = discord.Color.blue()
        
        data = {
            'user_data': user_data,
            'pet': pet,
            'marriage': marriage,
            'profession': profession,
            'achievements_count': achievements_count,
            'badges': badges,
            'timeline': timeline,
            'member': member,
            'color': color,
            'equipped_title': equipped_title,
            'multiplier': self.calculate_multiplier(member)
        }
        
        embed = discord.Embed(
            title=f"Perfil de {member.display_name}" + (f" - {equipped_title}" if equipped_title else ""),
            color=color,
            timestamp=datetime.now()
        )
        
        if user_data['banner']:
            embed.set_image(url=user_data['banner'])
        
        embed.set_thumbnail(url=member.display_avatar.url)
        
        level = user_data['level'] or 1
        xp = user_data['xp'] or 0
        xp_needed = (level ** 2) * 100
        xp_progress = min(xp / xp_needed * 100, 100) if xp_needed > 0 else 0
        progress_bar = self.create_progress_bar(xp_progress)
        
        next_role_level, next_role_id = self.get_next_role_level(level)
        if next_role_level:
            xp_for_next_role_level = self.calculate_xp_for_level(next_role_level)
            xp_needed_for_role = max(0, xp_for_next_role_level - xp)
            next_role = ctx.guild.get_role(next_role_id)
            role_name = next_role.name if next_role else f"Nível {next_role_level}"
            role_info = f"\nPróximo cargo: {role_name}\nXP faltando: {xp_needed_for_role:,}"
        else:
            role_info = "\nTodos os cargos conquistados!"
        
        embed.add_field(
            name="🌟 Nível e XP",
            value=f"Nível: {level}\nXP: {xp:,} / {xp_needed:,}\n{progress_bar}{role_info}",
            inline=False
        )
        
        if user_data['bio']:
            embed.add_field(
                name="📝 Bio",
                value=user_data['bio'],
                inline=False
            )
        
        class ProfileView(View):
            def __init__(self, data, cog, timeout=180):
                super().__init__(timeout=timeout)
                self.data = data
                self.cog = cog

            async def update_embed(self, interaction: discord.Interaction, custom_id: str):
                data = self.data
                embed = discord.Embed(
                    title=f"Perfil de {data['member'].display_name}",
                    color=data['color'],
                    timestamp=datetime.now()
                )
                
                if data['user_data']['banner']:
                    embed.set_image(url=data['user_data']['banner'])
                
                embed.set_thumbnail(url=data['member'].display_avatar.url)
                
                if custom_id == 'show_economia_stats':
                    coins = data['user_data']['coins'] or 0
                    bank = data['user_data']['bank'] or 0
                    embed.add_field(
                        name="💰 Economia",
                        value=f"Carteira: {coins:,} moedas\nBanco: {bank:,} moedas",
                        inline=False
                    )
                    embed.add_field(
                        name="📊 Estatísticas",
                        value=f"Mensagens: {data['user_data']['messages'] or 0:,}\nComandos: {data['user_data']['commands_used'] or 0:,}",
                        inline=False
                    )
                    multiplier = data['multiplier']
                    if multiplier:
                        embed.add_field(
                            name="🚀 Multiplicador de XP",
                            value=f"{multiplier}x XP por mensagem",
                            inline=False
                        )
                
                elif custom_id == 'show_pet_prof_casamento':
                    if data['pet']:
                        pet_name = data['pet']['custom_name'] or data['pet']['species']
                        embed.add_field(
                            name="🐶 Pet Principal",
                            value=f"{pet_name} ({data['pet']['species']})\nNível {data['pet']['level']} | {data['pet']['rarity'].capitalize()}",
                            inline=False
                        )
                    if data['profession']:
                        embed.add_field(
                            name="🛠 Profissão",
                            value=f"{data['profession']['name']}\nNível {data['profession']['level']}",
                            inline=False
                        )
                    if data['marriage']:
                        partner_id = data['marriage']['user2_id'] if data['marriage']['user1_id'] == str(data['member'].id) else data['marriage']['user1_id']
                        partner = interaction.guild.get_member(int(partner_id))
                        partner_name = partner.display_name if partner else "Usuário desconhecido"
                        embed.add_field(
                            name="💍 Casado(a) com",
                            value=partner_name,
                            inline=False
                        )
                    embed.add_field(
                        name="🏆 Conquistas",
                        value=f"{data['achievements_count']} desbloqueadas",
                        inline=False
                    )
                
                elif custom_id == 'show_badges':
                    if data['badges']:
                        embed.add_field(
                            name="🔥 Badges",
                            value=" ".join(data['badges']),
                            inline=False
                        )
                    else:
                        embed.add_field(
                            name="🔥 Badges",
                            value="Nenhum badge",
                            inline=False
                        )
                
                elif custom_id == 'full_timeline':
                    if data['timeline']:
                        timeline_str = "\n".join([f"{row['timestamp']}: {row['event_description']}" for row in data['timeline']])
                        embed.add_field(
                            name="🕰 Timeline",
                            value=timeline_str,
                            inline=False
                        )
                    else:
                        embed.add_field(
                            name="🕰 Timeline",
                            value="Vazia",
                            inline=False
                        )
                    self.clear_items()
                    b1 = Button(label="Voltar ao Principal", style=discord.ButtonStyle.primary, custom_id="back_main")
                    b1.callback = self.back_main_callback
                    self.add_item(b1)
                
                elif custom_id == 'back_main':
                    embed = discord.Embed(
                        title=f"Perfil de {data['member'].display_name}" + (f" - {data['equipped_title']}" if data['equipped_title'] else ""),
                        color=data['color'],
                        timestamp=datetime.now()
                    )
                    if data['user_data']['banner']:
                        embed.set_image(url=data['user_data']['banner'])
                    embed.set_thumbnail(url=data['member'].display_avatar.url)
                    level = data['user_data']['level'] or 1
                    xp = data['user_data']['xp'] or 0
                    xp_needed = (level ** 2) * 100
                    xp_progress = min(xp / xp_needed * 100, 100) if xp_needed > 0 else 0
                    progress_bar = self.cog.create_progress_bar(xp_progress)
                    next_role_level, next_role_id = self.cog.get_next_role_level(level)
                    if next_role_level:
                        xp_for_next_role_level = self.cog.calculate_xp_for_level(next_role_level)
                        xp_needed_for_role = max(0, xp_for_next_role_level - xp)
                        next_role = interaction.guild.get_role(next_role_id)
                        role_name = next_role.name if next_role else f"Nível {next_role_level}"
                        role_info = f"\nPróximo cargo: {role_name}\nXP faltando: {xp_needed_for_role:,}"
                    else:
                        role_info = "\nTodos os cargos conquistados!"
                    embed.add_field(name="🌟 Nível e XP", value=f"Nível: {level}\nXP: {xp:,} / {xp_needed:,}\n{progress_bar}{role_info}", inline=False)
                    if data['user_data']['bio']:
                        embed.add_field(name="📝 Bio", value=data['user_data']['bio'], inline=False)
                    
                    self.clear_items()
                    # Re-add original buttons
                    self.add_item(self.economy_button)
                    self.add_item(self.social_button)
                    self.add_item(self.timeline_button)
                    self.add_item(self.title_button)
                    self.add_item(self.badges_button)

                await interaction.response.edit_message(embed=embed, view=self)

            @discord.ui.button(label="Economia & Estatísticas", style=discord.ButtonStyle.primary, custom_id="show_economia_stats")
            async def economy_button(self, interaction: discord.Interaction, button: Button):
                await self.update_embed(interaction, "show_economia_stats")

            @discord.ui.button(label="Pet & Profissão & Casamento", style=discord.ButtonStyle.primary, custom_id="show_pet_prof_casamento")
            async def social_button(self, interaction: discord.Interaction, button: Button):
                await self.update_embed(interaction, "show_pet_prof_casamento")

            @discord.ui.button(label="Ver Timeline", style=discord.ButtonStyle.green, custom_id="full_timeline")
            async def timeline_button(self, interaction: discord.Interaction, button: Button):
                await self.update_embed(interaction, "full_timeline")

            @discord.ui.button(label="Equipar Título", style=discord.ButtonStyle.secondary, custom_id="equip_title")
            async def title_button(self, interaction: discord.Interaction, button: Button):
                await interaction.response.send_message("Função de equipar título em desenvolvimento.", ephemeral=True)

            @discord.ui.button(label="Badges", style=discord.ButtonStyle.primary, custom_id="show_badges")
            async def badges_button(self, interaction: discord.Interaction, button: Button):
                await self.update_embed(interaction, "show_badges")

            async def back_main_callback(self, interaction: discord.Interaction):
                await self.update_embed(interaction, "back_main")

        view = ProfileView(data=data, cog=self)
        await ctx.send(embed=embed, view=view)
        
    def calculate_multiplier(self, member):
        xp_multipliers = {
            1455412884640104509: 2,
            1444792288122241024: 2,
            1443287009144737875: 3,
            1447060588826988645: 5
        }
        multiplier = 1
        for role in member.roles:
            if role.id in xp_multipliers:
                multiplier = max(multiplier, xp_multipliers[role.id])
        return multiplier if multiplier > 1 else None
    
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
        cursor.execute("UPDATE usuarios SET bio = ? WHERE user_id = ?", (bio_text, user_id))
        conn.commit()
        conn.close()
        await ctx.send(f"Bio atualizada com sucesso!")
    
    @commands.command(name='cor', aliases=['color', 'setcolor', 'setcor'])
    async def cor(self, ctx, *, cor_input: str):
        """Definir a cor do embed do perfil com codigo HEX ou nome"""
        color_hex = self.parse_color(cor_input)
        if not color_hex:
            await ctx.send("Cor invalida! Use um codigo HEX (ex: `#FF5733` ou `FF5733`) ou um nome de cor (ex: `vermelho`, `azul`, `roxo`)")
            return
        user_id = str(ctx.author.id)
        self.bot.db.ensure_user_exists(user_id)
        conn = self.bot.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE usuarios SET embed_color = ? WHERE user_id = ?", (color_hex, user_id))
        conn.commit()
        conn.close()
        try:
            preview_color = discord.Color(int(color_hex.replace('#', ''), 16))
        except:
            preview_color = discord.Color.blue()
        embed = discord.Embed(title="Cor do Perfil Atualizada!", description=f"Sua nova cor e: **{color_hex}**", color=preview_color)
        await ctx.send(embed=embed)
    
    @commands.command(name='nivel', aliases=['level', 'xp'])
    async def nivel(self, ctx, member: discord.Member = None):
        """Ver o nivel de um usuario"""
        member = member or ctx.author
        user_id = str(member.id)
        self.bot.db.ensure_user_exists(user_id)
        conn = self.bot.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT xp, level FROM usuarios WHERE user_id = ?", (user_id,))
        data = cursor.fetchone()
        cursor.execute("SELECT COUNT(*) + 1 as rank FROM usuarios WHERE xp > (SELECT xp FROM usuarios WHERE user_id = ?)", (user_id,))
        rank_data = cursor.fetchone()
        conn.close()
        level = data['level'] or 1
        xp = data['xp'] or 0
        xp_needed = (level ** 2) * 100
        xp_progress = min(xp / xp_needed * 100, 100) if xp_needed > 0 else 0
        rank = rank_data['rank']
        progress_bar = self.create_progress_bar(xp_progress, 20)
        embed = discord.Embed(title=f"Nivel de {member.display_name}", color=discord.Color.gold())
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="Nivel", value=f"**{level}**", inline=True)
        embed.add_field(name="XP", value=f"**{xp:,}** / {xp_needed:,}", inline=True)
        embed.add_field(name="Ranking", value=f"**#{rank}**", inline=True)
        embed.add_field(name="Progresso", value=progress_bar, inline=False)
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
    
    @commands.command(name='equipartitulo', aliases=['equiptitle'])
    async def equip_title(self, ctx, title: str):
        """Equipar um titulo customizavel"""
        user_id = str(ctx.author.id)
        conn = self.bot.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM user_titles WHERE user_id = ? AND title = ?", (user_id, title))
        if not cursor.fetchone():
            await ctx.send("Você não possui esse título!")
            conn.close()
            return
        cursor.execute("UPDATE user_titles SET equipped = 0 WHERE user_id = ?", (user_id,))
        cursor.execute("UPDATE user_titles SET equipped = 1 WHERE user_id = ? AND title = ?", (user_id, title))
        conn.commit()
        conn.close()
        await ctx.send(f"Titulo '{title}' equipado!")
    
    @commands.command(name='addtitulo', aliases=['addtitle'])
    @commands.is_owner()
    async def add_title(self, ctx, user: discord.Member, title: str):
        """Adicionar um título (admin)"""
        user_id = str(user.id)
        conn = self.bot.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT OR IGNORE INTO user_titles (user_id, title) VALUES (?, ?)", (user_id, title))
        conn.commit()
        conn.close()
        await ctx.send(f"Título '{title}' adicionado para {user.display_name}!")

    @commands.command(name='addbadge', aliases=['unlockbadge'])
    @commands.is_owner()
    async def add_badge(self, ctx, user: discord.Member, badge_name: str):
        """Adicionar um badge raro (admin)"""
        user_id = str(user.id)
        conn = self.bot.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT OR IGNORE INTO user_badges (user_id, badge_name) VALUES (?, ?)", (user_id, badge_name))
        conn.commit()
        conn.close()
        await ctx.send(f"Badge '{badge_name}' adicionado para {user.display_name}!")

async def setup(bot):
    await bot.add_cog(Perfil(bot))
