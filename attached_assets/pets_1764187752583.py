import discord
from discord.ext import commands
from datetime import datetime, timedelta
import random

class Pets(commands.Cog):
    """Sistema completo de pets"""
    
    def __init__(self, bot):
        self.bot = bot
        
        # Espécies disponíveis
        self.species = {
            'cachorro': {'emoji': '🐕', 'evolution': ['Filhote', 'Cachorro', 'Cachorro Alpha']},
            'gato': {'emoji': '🐱', 'evolution': ['Gatinho', 'Gato', 'Gato Mistico']},
            'raposa': {'emoji': '🦊', 'evolution': ['Raposinha', 'Raposa', 'Raposa de Fogo']},
            'dragao': {'emoji': '🐉', 'evolution': ['Ovo', 'Dragãozinho', 'Dragão Anciáo']},
            'coruja': {'emoji': '🦉', 'evolution': ['Corujinha', 'Coruja', 'Coruja Sábia']},
            'slime': {'emoji': '💧', 'evolution': ['Slime Pequeno', 'Slime', 'Slime Rei']}
        }
    
    @commands.command(name='pet')
    async def pet(self, ctx):
        """Ver menu de pets"""
        embed = discord.Embed(
            title="🐾 Sistema de Pets",
            description="Adote e cuide do seu próprio pet!",
            color=discord.Color.blue()
        )
        
        especies_text = "\n".join([
            f"{data['emoji']} **{name.capitalize()}**" 
            for name, data in self.species.items()
        ])
        
        embed.add_field(name="Espécies Disponíveis", value=especies_text, inline=False)
        embed.add_field(
            name="Comandos",
            value=(
                "`!pet-adotar <espécie>` - Adotar um pet\n"
                "`!pet-status` - Ver status do seu pet\n"
                "`!pet-nomear <nome>` - Renomear seu pet\n"
                "`!pet-alimentar` - Alimentar seu pet\n"
                "`!pet-treinar` - Treinar seu pet\n"
                "`!pet-banho` - Dar banho no pet\n"
                "`!pet-brincar` - Brincar com o pet\n"
                "`!pet-aventura` - Enviar em aventura\n"
                "`!pet-loja` - Ver loja de itens"
            ),
            inline=False
        )
        
        await ctx.send(embed=embed)
    
    @commands.command(name='pet-adotar', aliases=['pet-adopt'])
    async def pet_adotar(self, ctx, especie: str):
        """Adotar um pet"""
        especie = especie.lower()
        
        if especie not in self.species:
            await ctx.send(f"❌ Espécie inválida! Use: {', '.join(self.species.keys())}")
            return
        
        user_id = str(ctx.author.id)
        self.bot.db.ensure_user_exists(user_id)
        
        conn = self.bot.db.get_connection()
        cursor = conn.cursor()
        
        # Verificar se já tem um pet
        cursor.execute("SELECT COUNT(*) as count FROM pets WHERE user_id = ?", (user_id,))
        pet_count = cursor.fetchone()['count']
        
        if pet_count >= 10:
            await ctx.send("❌ Você já tem o máximo de 10 pets!")
            conn.close()
            return
        
        # Criar pet
        cursor.execute("""
            INSERT INTO pets (user_id, species, level, adopted_at)
            VALUES (?, ?, 1, ?)
        """, (user_id, especie, datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
        
        emoji = self.species[especie]['emoji']
        
        embed = discord.Embed(
            title="🎉 Pet Adotado!",
            description=f"Você adotou um {emoji} **{especie.capitalize()}**!",
            color=discord.Color.green()
        )
        
        embed.add_field(
            name="Próximos Passos",
            value="Use `!pet-nomear <nome>` para dar um nome ao seu pet!",
            inline=False
        )
        
        await ctx.send(embed=embed)
    
    @commands.command(name='pet-status', aliases=['pet-info'])
    async def pet_status(self, ctx):
        """Ver status do seu pet"""
        user_id = str(ctx.author.id)
        
        conn = self.bot.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM pets WHERE user_id = ? ORDER BY pet_id DESC LIMIT 1
        """, (user_id,))
        
        pet = cursor.fetchone()
        conn.close()
        
        if not pet:
            await ctx.send("❌ Você não tem nenhum pet! Use `!pet-adotar <espécie>`")
            return
        
        species_data = self.species.get(pet['species'], {'emoji': '🐾', 'evolution': ['Pet']})
        emoji = species_data['emoji']
        pet_name = pet['custom_name'] if pet['custom_name'] else pet['species'].capitalize()
        
        # Calcular evolu��ão
        evolution_stage = min(pet['evolution_stage'], len(species_data['evolution']) - 1)
        evolution_name = species_data['evolution'][evolution_stage]
        
        # Calcular tempo de adoção
        adopted = datetime.fromisoformat(pet['adopted_at'])
        days = (datetime.now() - adopted).days
        
        embed = discord.Embed(
            title=f"{emoji} {pet_name}",
            description=f"**Espécie:** {evolution_name}",
            color=discord.Color.blue()
        )
        
        embed.add_field(name="Nível", value=pet['level'], inline=True)
        embed.add_field(name="XP", value=f"{pet['xp']}/100", inline=True)
        embed.add_field(name="Raridade", value=pet['rarity'].capitalize(), inline=True)
        
        # Barras de status
        hunger_bar = self._create_bar(pet['hunger'])
        hygiene_bar = self._create_bar(pet['hygiene'])
        happiness_bar = self._create_bar(pet['happiness'])
        health_bar = self._create_bar(pet['health'])
        
        embed.add_field(name="🍖 Fome", value=hunger_bar, inline=False)
        embed.add_field(name="🛁 Higiene", value=hygiene_bar, inline=False)
        embed.add_field(name="😊 Felicidade", value=happiness_bar, inline=False)
        embed.add_field(name="❤️ Saúde", value=health_bar, inline=False)
        
        embed.set_footer(text=f"Adotado há {days} dia(s)")
        
        await ctx.send(embed=embed)
    
    def _create_bar(self, value):
        """Criar barra de progresso"""
        bars = int(value / 10)
        return f"{'▰' * bars}{'▱' * (10 - bars)} {value}%"
    
    @commands.command(name='pet-nomear', aliases=['pet-name'])
    async def pet_nomear(self, ctx, *, nome: str):
        """Renomear seu pet"""
        if len(nome) > 20:
            await ctx.send("❌ O nome deve ter no máximo 20 caracteres!")
            return
        
        user_id = str(ctx.author.id)
        
        conn = self.bot.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE pets SET custom_name = ? 
            WHERE user_id = ? AND pet_id = (
                SELECT pet_id FROM pets WHERE user_id = ? ORDER BY pet_id DESC LIMIT 1
            )
        """, (nome, user_id, user_id))
        
        if cursor.rowcount == 0:
            await ctx.send("❌ Você não tem nenhum pet!")
            conn.close()
            return
        
        conn.commit()
        conn.close()
        
        await ctx.send(f"✅ Pet renomeado para: **{nome}**!")
    
    @commands.command(name='pet-alimentar', aliases=['pet-feed'])
    @commands.cooldown(1, 3600, commands.BucketType.user)
    async def pet_alimentar(self, ctx):
        """Alimentar seu pet"""
        user_id = str(ctx.author.id)
        
        conn = self.bot.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT pet_id, custom_name, species, hunger, happiness 
            FROM pets WHERE user_id = ? ORDER BY pet_id DESC LIMIT 1
        """, (user_id,))
        
        pet = cursor.fetchone()
        
        if not pet:
            await ctx.send("❌ Você não tem nenhum pet!")
            conn.close()
            return
        
        # Alimentar
        new_hunger = min(100, pet['hunger'] + 30)
        new_happiness = min(100, pet['happiness'] + 10)
        
        cursor.execute("""
            UPDATE pets 
            SET hunger = ?, happiness = ?, last_fed = ?
            WHERE pet_id = ?
        """, (new_hunger, new_happiness, datetime.now().isoformat(), pet['pet_id']))
        
        conn.commit()
        conn.close()
        
        pet_name = pet['custom_name'] if pet['custom_name'] else pet['species'].capitalize()
        
        await ctx.send(f"🍖 Você alimentou **{pet_name}**! (+30 fome, +10 felicidade)")
    
    @commands.command(name='pet-treinar', aliases=['pet-train'])
    @commands.cooldown(1, 7200, commands.BucketType.user)
    async def pet_treinar(self, ctx):
        """Treinar seu pet"""
        user_id = str(ctx.author.id)
        
        conn = self.bot.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM pets WHERE user_id = ? ORDER BY pet_id DESC LIMIT 1
        """, (user_id,))
        
        pet = cursor.fetchone()
        
        if not pet:
            await ctx.send("❌ Você não tem nenhum pet!")
            conn.close()
            return
        
        # Treinar
        xp_gain = random.randint(20, 40)
        new_xp = pet['xp'] + xp_gain
        new_level = pet['level']
        
        # Level up
        while new_xp >= 100:
            new_xp -= 100
            new_level += 1
        
        # Evoluir a cada 10 níveis
        new_evolution = min(2, new_level // 10)
        
        cursor.execute("""
            UPDATE pets 
            SET xp = ?, level = ?, evolution_stage = ?, hunger = hunger - 10, happiness = happiness + 5
            WHERE pet_id = ?
        """, (new_xp, new_level, new_evolution, pet['pet_id']))
        
        conn.commit()
        conn.close()
        
        pet_name = pet['custom_name'] if pet['custom_name'] else pet['species'].capitalize()
        
        msg = f"💪 **{pet_name}** treinou e ganhou {xp_gain} XP!"
        
        if new_level > pet['level']:
            msg += f"\n🎉 Subiu para o nível {new_level}!"
        
        if new_evolution > pet['evolution_stage']:
            species_data = self.species.get(pet['species'], {'evolution': ['Pet']})
            evolution_name = species_data['evolution'][new_evolution]
            msg += f"\n✨ Evoluiu para: **{evolution_name}**!"
        
        await ctx.send(msg)
    
    @commands.command(name='pet-banho', aliases=['pet-bath'])
    @commands.cooldown(1, 7200, commands.BucketType.user)
    async def pet_banho(self, ctx):
        """Dar banho no pet"""
        user_id = str(ctx.author.id)
        
        conn = self.bot.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE pets 
            SET hygiene = 100, happiness = happiness + 15, last_bath = ?
            WHERE user_id = ? AND pet_id = (
                SELECT pet_id FROM pets WHERE user_id = ? ORDER BY pet_id DESC LIMIT 1
            )
        """, (datetime.now().isoformat(), user_id, user_id))
        
        if cursor.rowcount == 0:
            await ctx.send("❌ Você não tem nenhum pet!")
            conn.close()
            return
        
        conn.commit()
        conn.close()
        
        await ctx.send("🛁 Seu pet está limpinho e feliz! (+100 higiene, +15 felicidade)")
    
    @commands.command(name='pet-brincar', aliases=['pet-play'])
    @commands.cooldown(1, 1800, commands.BucketType.user)
    async def pet_brincar(self, ctx):
        """Brincar com o pet"""
        user_id = str(ctx.author.id)
        
        conn = self.bot.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE pets 
            SET happiness = 100, hunger = hunger - 5, last_play = ?
            WHERE user_id = ? AND pet_id = (
                SELECT pet_id FROM pets WHERE user_id = ? ORDER BY pet_id DESC LIMIT 1
            )
        """, (datetime.now().isoformat(), user_id, user_id))
        
        if cursor.rowcount == 0:
            await ctx.send("❌ Você não tem nenhum pet!")
            conn.close()
            return
        
        conn.commit()
        conn.close()
        
        await ctx.send("😊 Você brincou com seu pet! Ele está muito feliz! (+100 felicidade)")
    
    @commands.command(name='pet-aventura', aliases=['pet-adventure'])
    @commands.cooldown(1, 14400, commands.BucketType.user)
    async def pet_aventura(self, ctx):
        """Enviar pet em aventura"""
        user_id = str(ctx.author.id)
        
        conn = self.bot.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM pets WHERE user_id = ? ORDER BY pet_id DESC LIMIT 1
        """, (user_id,))
        
        pet = cursor.fetchone()
        
        if not pet:
            await ctx.send("❌ Você não tem nenhum pet!")
            conn.close()
            return
        
        # Recompensas da aventura
        xp_reward = random.randint(30, 60)
        coin_reward = random.randint(100, 300)
        
        cursor.execute("""
            UPDATE pets SET xp = xp + ? WHERE pet_id = ?
        """, (xp_reward, pet['pet_id']))
        
        cursor.execute("""
            UPDATE economia SET coins = coins + ? WHERE user_id = ?
        """, (coin_reward, user_id))
        
        # Chance de item raro
        if random.random() < 0.3:
            items = ["Osso Raro", "Bola Mágica", "Petisco Especial"]
            item = random.choice(items)
            
            cursor.execute("""
                INSERT INTO inventario (user_id, item_name, item_type, rarity)
                VALUES (?, ?, 'pet_item', 'raro')
            """, (user_id, item))
            
            item_msg = f"\n🎁 Encontrou: **{item}**!"
        else:
            item_msg = ""
        
        conn.commit()
        conn.close()
        
        pet_name = pet['custom_name'] if pet['custom_name'] else pet['species'].capitalize()
        
        embed = discord.Embed(
            title="🗺️ Aventura Completa!",
            description=f"**{pet_name}** voltou da aventura!",
            color=discord.Color.green()
        )
        
        embed.add_field(name="Recompensas", value=f"⭐ {xp_reward} XP\n💰 {coin_reward} moedas{item_msg}", inline=False)
        
        await ctx.send(embed=embed)
    
    @commands.command(name='pet-loja', aliases=['pet-shop'])
    async def pet_loja(self, ctx):
        """Ver loja de itens para pets"""
        embed = discord.Embed(
            title="🏪 Loja de Pets",
            description="Itens para cuidar melhor do seu pet!",
            color=discord.Color.gold()
        )
        
        embed.add_field(
            name="Comida",
            value=(
                "🥩 **Carne** - 50 moedas\n"
                "🐟 **Peixe** - 40 moedas\n"
                "🍖 **Petisco Premium** - 100 moedas"
            ),
            inline=True
        )
        
        embed.add_field(
            name="Brinquedos",
            value=(
                "⚽ **Bola** - 80 moedas\n"
                "🦴 **Osso** - 60 moedas\n"
                "🎾 **Bola Mágica** - 150 moedas"
            ),
            inline=True
        )
        
        embed.add_field(
            name="Acessórios",
            value=(
                "👑 **Coroa** - 500 moedas\n"
                "🎀 **Laço** - 300 moedas\n"
                "⭐ **Colar Estelar** - 1000 moedas"
            ),
            inline=False
        )
        
        embed.set_footer(text="Em breve: sistema de compra!")
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Pets(bot))
