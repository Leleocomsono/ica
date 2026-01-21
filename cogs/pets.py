import discord
from discord.ext import commands
from datetime import datetime
import random
import asyncio

class Pets(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
        self.RARIDADES = {
            'comum': {'emoji': '⚪', 'cor': 0x808080, 'multiplicador': 1.0, 'habilidade': 'Nenhuma'},
            'incomum': {'emoji': '🟢', 'cor': 0x00FF00, 'multiplicador': 1.2, 'habilidade': 'Sorte Pequena (+5% moedas)'},
            'raro': {'emoji': '🔵', 'cor': 0x0000FF, 'multiplicador': 1.5, 'habilidade': 'Sorte Média (+10% moedas)'},
            'epico': {'emoji': '🟣', 'cor': 0x800080, 'multiplicador': 2.0, 'habilidade': 'Mestre Coletor (+15% XP)'},
            'lendario': {'emoji': '🟡', 'cor': 0xFFD700, 'multiplicador': 3.0, 'habilidade': 'Divindade (+25% Moedas/XP)'},
            'mistico': {'emoji': '🔴', 'cor': 0xFF0000, 'multiplicador': 5.0, 'habilidade': 'Anomalia (+50% Tudo)'}
        }
        
        self.PETS = {
            'Lobo': '🐺', 'Raposa': '🦊', 'Gato': '🐱', 'Cachorro': '🐕',
            'Coelho': '🐰', 'Urso': '🐻', 'Leao': '🦁', 'Tigre': '🐯',
            'Panda': '🐼', 'Coruja': '🦉', 'Aguia': '🦅', 'Dragao': '🐉',
            'Unicornio': '🦄', 'Fenix': '🔥', 'Serpente': '🐍', 'Pantera': '🐆',
            'Cervo': '🦌', 'Falcao': '🦅', 'Grifo': '🦅', 'Hidra': '🐉'
        }
        
        self.CAIXAS = {
            'comum': {
                'preco': 500,
                'emoji': '📦',
                'cor': 0x808080,
                'chances': {
                    'comum': 50,
                    'incomum': 30,
                    'raro': 15,
                    'epico': 4,
                    'lendario': 0.9,
                    'mistico': 0.1
                }
            },
            'rara': {
                'preco': 2000,
                'emoji': '🎁',
                'cor': 0x0000FF,
                'chances': {
                    'comum': 0,
                    'incomum': 40,
                    'raro': 35,
                    'epico': 18,
                    'lendario': 6,
                    'mistico': 1
                }
            },
            'mistica': {
                'preco': 10000,
                'emoji': '✨',
                'cor': 0xFF0000,
                'chances': {
                    'comum': 0,
                    'incomum': 0,
                    'raro': 30,
                    'epico': 40,
                    'lendario': 25,
                    'mistico': 5
                }
            }
        }
        self.bot.loop.create_task(self.attribute_decay())

    async def attribute_decay(self):
        while True:
            await asyncio.sleep(3600) # 1 hora
            conn = self.bot.db.get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE pets 
                SET hunger = MAX(0, hunger - 10),
                    happiness = MAX(0, happiness - 15),
                    hygiene = MAX(0, hygiene - 10),
                    health = CASE WHEN hunger < 20 OR hygiene < 20 THEN MAX(0, health - 5) ELSE health END
            """)
            conn.commit()
            conn.close()

    @commands.command(name='evoluir')
    async def evoluir(self, ctx, pet_id: int):
        """Evoluir um pet se ele atingir o nível necessário"""
        user_id = str(ctx.author.id)
        conn = self.bot.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM pets WHERE pet_id = ? AND user_id = ?", (pet_id, user_id))
        pet = cursor.fetchone()
        
        if not pet:
            await ctx.send("Pet não encontrado!")
            return

        level_req = (pet['evolution_stage'] + 1) * 20
        if pet['level'] < level_req:
            await ctx.send(f"Seu pet precisa do nível {level_req} para evoluir! Nível atual: {pet['level']}")
            return

        new_stage = pet['evolution_stage'] + 1
        cursor.execute("UPDATE pets SET evolution_stage = ? WHERE pet_id = ?", (new_stage, pet_id))
        conn.commit()
        conn.close()
        
        await ctx.send(f"✨ Seu pet evoluiu para o estágio {new_stage}!")

    
    def sortear_raridade(self, box_type: str) -> str:
        chances = self.CAIXAS[box_type]['chances']
        roll = random.uniform(0, 100)
        cumulative = 0
        
        for rarity, chance in chances.items():
            cumulative += chance
            if roll <= cumulative:
                return rarity
        
        return 'comum'
    
    def sortear_pet(self) -> str:
        return random.choice(list(self.PETS.keys()))
    
    @commands.command(name='caixas', aliases=['blindbox', 'boxes'])
    async def caixas(self, ctx):
        """Ver informacoes sobre as caixas de pet"""
        embed = discord.Embed(
            title="Sistema de Blind Box de Pets",
            description="Compre caixas para obter pets aleatorios!",
            color=discord.Color.gold()
        )
        
        for box_name, box_info in self.CAIXAS.items():
            chances_text = ""
            for rarity, chance in box_info['chances'].items():
                if chance > 0:
                    rarity_info = self.RARIDADES[rarity]
                    chances_text += f"{rarity_info['emoji']} {rarity.capitalize()}: {chance}%\n"
            
            embed.add_field(
                name=f"{box_info['emoji']} Caixa {box_name.capitalize()} - {box_info['preco']:,} moedas",
                value=chances_text,
                inline=False
            )
        
        embed.set_footer(text="Use !comprar <tipo> para comprar uma caixa")
        
        await ctx.send(embed=embed)
    
    @commands.command(name='comprar', aliases=['buy'])
    async def comprar(self, ctx, tipo: str = None):
        """Comprar uma caixa de pet"""
        if not tipo:
            await ctx.send("Especifique o tipo de caixa: `comum`, `rara` ou `mistica`\nUse `!caixas` para ver os precos.")
            return
        
        tipo = tipo.lower()
        if tipo not in self.CAIXAS:
            await ctx.send("Tipo invalido! Use: `comum`, `rara` ou `mistica`")
            return
        
        user_id = str(ctx.author.id)
        self.bot.db.ensure_user_exists(user_id)
        
        box = self.CAIXAS[tipo]
        
        conn = self.bot.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT coins FROM economia WHERE user_id = ?", (user_id,))
        data = cursor.fetchone()
        coins = data['coins'] or 0
        
        if coins < box['preco']:
            await ctx.send(f"Voce precisa de **{box['preco']:,}** moedas para comprar esta caixa! Seu saldo: **{coins:,}**")
            conn.close()
            return
        
        cursor.execute("""
            UPDATE economia 
            SET coins = coins - ?, total_spent = total_spent + ?
            WHERE user_id = ?
        """, (box['preco'], box['preco'], user_id))
        
        rarity = self.sortear_raridade(tipo)
        species = self.sortear_pet()
        rarity_info = self.RARIDADES[rarity]
        
        cursor.execute("""
            INSERT INTO pets (user_id, species, rarity, adopted_at, last_fed, last_bath, last_play)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (user_id, species, rarity, datetime.now().isoformat(), 
              datetime.now().isoformat(), datetime.now().isoformat(), datetime.now().isoformat()))
        
        pet_id = cursor.lastrowid
        
        cursor.execute("""
            INSERT INTO blind_boxes (user_id, box_type, opened_at, pet_rarity, pet_species)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, tipo, datetime.now().isoformat(), rarity, species))
        
        conn.commit()
        conn.close()
        
        embed = discord.Embed(
            title=f"{box['emoji']} Abrindo Caixa {tipo.capitalize()}...",
            color=rarity_info['cor']
        )
        
        msg = await ctx.send(embed=embed)
        
        await asyncio.sleep(2)
        
        pet_emoji = self.PETS.get(species, '🐾')
        
        embed = discord.Embed(
            title=f"Voce obteve um novo pet!",
            description=f"{rarity_info['emoji']} **{species}** {pet_emoji}\n\n"
                       f"Raridade: **{rarity.capitalize()}**\n"
                       f"Multiplicador: **{rarity_info['multiplicador']}x**",
            color=rarity_info['cor']
        )
        
        embed.set_footer(text=f"Pet ID: #{pet_id} | Use !pets para ver seus pets")
        
        await msg.edit(embed=embed)
        
        from main import update_mission_progress
        await update_mission_progress(user_id, "pets_total", 1)
    
    @commands.command(name='pets', aliases=['meuspets'])
    async def pets(self, ctx, member: discord.Member = None):
        """Ver todos os seus pets"""
        member = member or ctx.author
        user_id = str(member.id)
        
        conn = self.bot.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM pets WHERE user_id = ? ORDER BY rarity DESC, level DESC
        """, (user_id,))
        pets_list = cursor.fetchall()
        conn.close()
        
        if not pets_list:
            await ctx.send(f"{member.display_name} nao possui nenhum pet! Use `!comprar <tipo>` para adquirir uma caixa.")
            return
        
        embed = discord.Embed(
            title=f"Pets de {member.display_name}",
            color=discord.Color.blue()
        )
        
        rarity_order = ['mistico', 'lendario', 'epico', 'raro', 'incomum', 'comum']
        pets_by_rarity = {}
        
        for pet in pets_list:
            rarity = pet['rarity']
            if rarity not in pets_by_rarity:
                pets_by_rarity[rarity] = []
            pets_by_rarity[rarity].append(pet)
        
        for rarity in rarity_order:
            if rarity in pets_by_rarity:
                rarity_info = self.RARIDADES[rarity]
                pets_text = ""
                
                for pet in pets_by_rarity[rarity]:
                    pet_emoji = self.PETS.get(pet['species'], '🐾')
                    name = pet['custom_name'] or pet['species']
                    pets_text += f"{pet_emoji} **{name}** (Lv.{pet['level']}) `#{pet['pet_id']}`\n"
                
                embed.add_field(
                    name=f"{rarity_info['emoji']} {rarity.capitalize()} ({len(pets_by_rarity[rarity])})",
                    value=pets_text[:1024],
                    inline=False
                )
        
        embed.set_footer(text=f"Total: {len(pets_list)} pets | Use !pet <id> para detalhes")
        
        await ctx.send(embed=embed)
    
    @commands.command(name='pet', aliases=['verpet'])
    async def pet(self, ctx, pet_id: int = None):
        """Ver detalhes de um pet especifico"""
        if pet_id is None:
            await ctx.send("Especifique o ID do pet! Use `!pets` para ver a lista.")
            return
        
        user_id = str(ctx.author.id)
        
        conn = self.bot.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM pets WHERE pet_id = ? AND user_id = ?
        """, (pet_id, user_id))
        pet = cursor.fetchone()
        conn.close()
        
        if not pet:
            await ctx.send("Pet nao encontrado ou nao pertence a voce!")
            return
        
        rarity_info = self.RARIDADES[pet['rarity']]
        pet_emoji = self.PETS.get(pet['species'], '🐾')
        name = pet['custom_name'] or pet['species']
        
        embed = discord.Embed(
            title=f"{pet_emoji} {name}",
            color=rarity_info['cor']
        )
        
        embed.add_field(
            name="Informacoes",
            value=f"Especie: **{pet['species']}**\n"
                  f"Raridade: {rarity_info['emoji']} **{pet['rarity'].capitalize()}**\n"
                  f"Nivel: **{pet['level']}**\n"
                  f"XP: **{pet['xp']}**\n"
                  f"Estágio: **{pet['evolution_stage']}**\n"
                  f"Habilidade: **{rarity_info['habilidade']}**",
            inline=True
        )
        
        def status_bar(value):
            filled = int(value / 10)
            empty = 10 - filled
            return '🟩' * filled + '⬜' * empty
        
        embed.add_field(
            name="Status",
            value=f"Fome: {status_bar(pet['hunger'])} {pet['hunger']}%\n"
                  f"Felicidade: {status_bar(pet['happiness'])} {pet['happiness']}%\n"
                  f"Higiene: {status_bar(pet['hygiene'])} {pet['hygiene']}%\n"
                  f"Saude: {status_bar(pet['health'])} {pet['health']}%",
            inline=False
        )
        
        embed.set_footer(text=f"ID: #{pet['pet_id']} | Adotado em: {pet['adopted_at'][:10]}")
        
        await ctx.send(embed=embed)

    @commands.command(name='carinho', aliases=['petpet'])
    @commands.cooldown(1, 600, commands.BucketType.user)
    async def carinho(self, ctx, pet_id: int = None):
        """Fazer carinho em um pet"""
        if pet_id is None:
            ctx.command.reset_cooldown(ctx)
            await ctx.send("Especifique o ID do pet!")
            return
        
        user_id = str(ctx.author.id)
        conn = self.bot.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM pets WHERE pet_id = ? AND user_id = ?", (pet_id, user_id))
        pet = cursor.fetchone()
        
        if not pet:
            ctx.command.reset_cooldown(ctx)
            await ctx.send("Pet não encontrado!")
            conn.close()
            return
        
        new_happiness = min(100, pet['happiness'] + 15)
        cursor.execute("UPDATE pets SET happiness = ? WHERE pet_id = ?", (new_happiness, pet_id))
        conn.commit()
        conn.close()
        
        await ctx.send(f"❤️ Você fez carinho em **{pet['custom_name'] or pet['species']}**! Ele parece mais feliz.")
    
    @commands.command(name='alimentar', aliases=['feed'])
    @commands.cooldown(1, 1800, commands.BucketType.user)
    async def alimentar(self, ctx, pet_id: int = None):
        """Alimentar um pet"""
        if pet_id is None:
            ctx.command.reset_cooldown(ctx)
            await ctx.send("Especifique o ID do pet! Use `!pets` para ver a lista.")
            return
        
        user_id = str(ctx.author.id)
        
        conn = self.bot.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM pets WHERE pet_id = ? AND user_id = ?
        """, (pet_id, user_id))
        pet = cursor.fetchone()
        
        if not pet:
            ctx.command.reset_cooldown(ctx)
            await ctx.send("Pet nao encontrado ou nao pertence a voce!")
            conn.close()
            return
        
        new_hunger = min(100, pet['hunger'] + 30)
        new_health = min(100, pet['health'] + 10)
        xp_gain = random.randint(5, 15)
        new_xp = pet['xp'] + xp_gain
        new_level = pet['level']
        
        xp_needed = new_level * 50
        if new_xp >= xp_needed:
            new_level += 1
            new_xp = new_xp - xp_needed
        
        cursor.execute("""
            UPDATE pets 
            SET hunger = ?, health = ?, xp = ?, level = ?, last_fed = ?
            WHERE pet_id = ?
        """, (new_hunger, new_health, new_xp, new_level, datetime.now().isoformat(), pet_id))
        
        conn.commit()
        conn.close()
        
        pet_emoji = self.PETS.get(pet['species'], '🐾')
        name = pet['custom_name'] or pet['species']
        
        embed = discord.Embed(
            title=f"Alimentando {pet_emoji} {name}",
            description=f"Fome: {pet['hunger']}% → **{new_hunger}%**\n"
                       f"Saude: {pet['health']}% → **{new_health}%**\n"
                       f"XP: +{xp_gain}",
            color=discord.Color.green()
        )
        
        if new_level > pet['level']:
            embed.add_field(
                name="Subiu de nivel!",
                value=f"Nivel {pet['level']} → **Nivel {new_level}**",
                inline=False
            )
        
        await ctx.send(embed=embed)
    
    @alimentar.error
    async def alimentar_error(self, ctx, error):
        if not isinstance(error, commands.CommandOnCooldown):
            ctx.command.reset_cooldown(ctx)
    
    @commands.command(name='brincar', aliases=['play'])
    @commands.cooldown(1, 1800, commands.BucketType.user)
    async def brincar(self, ctx, pet_id: int = None):
        """Brincar com um pet"""
        if pet_id is None:
            ctx.command.reset_cooldown(ctx)
            await ctx.send("Especifique o ID do pet! Use `!pets` para ver a lista.")
            return
        
        user_id = str(ctx.author.id)
        
        conn = self.bot.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM pets WHERE pet_id = ? AND user_id = ?
        """, (pet_id, user_id))
        pet = cursor.fetchone()
        
        if not pet:
            ctx.command.reset_cooldown(ctx)
            await ctx.send("Pet nao encontrado ou nao pertence a voce!")
            conn.close()
            return
        
        new_happiness = min(100, pet['happiness'] + 30)
        new_hunger = max(0, pet['hunger'] - 10)
        xp_gain = random.randint(10, 20)
        new_xp = pet['xp'] + xp_gain
        new_level = pet['level']
        
        xp_needed = new_level * 50
        if new_xp >= xp_needed:
            new_level += 1
            new_xp = new_xp - xp_needed
        
        cursor.execute("""
            UPDATE pets 
            SET happiness = ?, hunger = ?, xp = ?, level = ?, last_play = ?
            WHERE pet_id = ?
        """, (new_happiness, new_hunger, new_xp, new_level, datetime.now().isoformat(), pet_id))
        
        conn.commit()
        conn.close()
        
        pet_emoji = self.PETS.get(pet['species'], '🐾')
        name = pet['custom_name'] or pet['species']
        
        embed = discord.Embed(
            title=f"Brincando com {pet_emoji} {name}",
            description=f"Felicidade: {pet['happiness']}% → **{new_happiness}%**\n"
                       f"Fome: {pet['hunger']}% → **{new_hunger}%**\n"
                       f"XP: +{xp_gain}",
            color=discord.Color.green()
        )
        
        if new_level > pet['level']:
            embed.add_field(
                name="Subiu de nivel!",
                value=f"Nivel {pet['level']} → **Nivel {new_level}**",
                inline=False
            )
        
        await ctx.send(embed=embed)
    
    @brincar.error
    async def brincar_error(self, ctx, error):
        if not isinstance(error, commands.CommandOnCooldown):
            ctx.command.reset_cooldown(ctx)
    
    @commands.command(name='banho', aliases=['bath'])
    @commands.cooldown(1, 1800, commands.BucketType.user)
    async def banho(self, ctx, pet_id: int = None):
        """Dar banho em um pet"""
        if pet_id is None:
            ctx.command.reset_cooldown(ctx)
            await ctx.send("Especifique o ID do pet! Use `!pets` para ver a lista.")
            return
        
        user_id = str(ctx.author.id)
        
        conn = self.bot.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM pets WHERE pet_id = ? AND user_id = ?
        """, (pet_id, user_id))
        pet = cursor.fetchone()
        
        if not pet:
            ctx.command.reset_cooldown(ctx)
            await ctx.send("Pet nao encontrado ou nao pertence a voce!")
            conn.close()
            return
        
        new_hygiene = min(100, pet['hygiene'] + 40)
        new_health = min(100, pet['health'] + 15)
        xp_gain = random.randint(5, 10)
        new_xp = pet['xp'] + xp_gain
        new_level = pet['level']
        
        xp_needed = new_level * 50
        if new_xp >= xp_needed:
            new_level += 1
            new_xp = new_xp - xp_needed
        
        cursor.execute("""
            UPDATE pets 
            SET hygiene = ?, health = ?, xp = ?, level = ?, last_bath = ?
            WHERE pet_id = ?
        """, (new_hygiene, new_health, new_xp, new_level, datetime.now().isoformat(), pet_id))
        
        conn.commit()
        conn.close()
        
        pet_emoji = self.PETS.get(pet['species'], '🐾')
        name = pet['custom_name'] or pet['species']
        
        embed = discord.Embed(
            title=f"Dando banho em {pet_emoji} {name}",
            description=f"Higiene: {pet['hygiene']}% → **{new_hygiene}%**\n"
                       f"Saude: {pet['health']}% → **{new_health}%**\n"
                       f"XP: +{xp_gain}",
            color=discord.Color.blue()
        )
        
        if new_level > pet['level']:
            embed.add_field(
                name="Subiu de nivel!",
                value=f"Nivel {pet['level']} → **Nivel {new_level}**",
                inline=False
            )
        
        await ctx.send(embed=embed)
    
    @banho.error
    async def banho_error(self, ctx, error):
        if not isinstance(error, commands.CommandOnCooldown):
            ctx.command.reset_cooldown(ctx)
    
    @commands.command(name='nomear', aliases=['rename'])
    async def nomear(self, ctx, pet_id: int = None, *, nome: str = None):
        """Dar um nome personalizado ao pet"""
        if pet_id is None or nome is None:
            await ctx.send("Use: `!nomear <id_pet> <nome>`")
            return
        
        if len(nome) > 30:
            await ctx.send("O nome deve ter no maximo 30 caracteres!")
            return
        
        user_id = str(ctx.author.id)
        
        conn = self.bot.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM pets WHERE pet_id = ? AND user_id = ?
        """, (pet_id, user_id))
        pet = cursor.fetchone()
        
        if not pet:
            await ctx.send("Pet nao encontrado ou nao pertence a voce!")
            conn.close()
            return
        
        cursor.execute("""
            UPDATE pets SET custom_name = ? WHERE pet_id = ?
        """, (nome, pet_id))
        
        conn.commit()
        conn.close()
        
        pet_emoji = self.PETS.get(pet['species'], '🐾')
        
        embed = discord.Embed(
            title="Nome Atualizado!",
            description=f"Seu {pet_emoji} {pet['species']} agora se chama **{nome}**!",
            color=discord.Color.green()
        )
        
        await ctx.send(embed=embed)
    
    @commands.command(name='libertar', aliases=['release'])
    async def libertar(self, ctx, pet_id: int = None):
        """Libertar um pet"""
        if pet_id is None:
            await ctx.send("Especifique o ID do pet! Use `!pets` para ver a lista.")
            return
        
        user_id = str(ctx.author.id)
        
        conn = self.bot.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM pets WHERE pet_id = ? AND user_id = ?
        """, (pet_id, user_id))
        pet = cursor.fetchone()
        
        if not pet:
            await ctx.send("Pet nao encontrado ou nao pertence a voce!")
            conn.close()
            return
        
        pet_emoji = self.PETS.get(pet['species'], '🐾')
        name = pet['custom_name'] or pet['species']
        
        await ctx.send(
            f"Tem certeza que deseja libertar {pet_emoji} **{name}**? "
            f"Esta acao e irreversivel! Digite `confirmar` para prosseguir."
        )
        
        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel and m.content.lower() == 'confirmar'
        
        try:
            await self.bot.wait_for('message', check=check, timeout=30.0)
            
            cursor.execute("DELETE FROM pets WHERE pet_id = ?", (pet_id,))
            conn.commit()
            
            embed = discord.Embed(
                title="Pet Libertado",
                description=f"{pet_emoji} **{name}** foi libertado e agora vive na natureza.",
                color=discord.Color.orange()
            )
            
            await ctx.send(embed=embed)
        except:
            await ctx.send("Operacao cancelada.")
        finally:
            conn.close()

async def setup(bot):
    await bot.add_cog(Pets(bot))
