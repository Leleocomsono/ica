import discord
from discord.ext import commands
from datetime import datetime, timedelta
import random

class Profissoes(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
        self.PROFISSOES = {
            'cacador': {
                'nome': 'Cacador',
                'emoji': '🏹',
                'descricao': 'Especialista em caca e coleta de recursos',
                'comandos': ['cacar', 'rastrear', 'armar'],
                'recursos': ['Pele de Lobo', 'Carne Fresca', 'Osso Animal', 'Presa de Javali', 'Pena de Aguia'],
                'ferramenta': 'Arco de Precisão',
                'especializacoes': ['Mestre de Feras', 'Atirador de Elite'],
                'illegal': False
            },
            'hacker': {
                'nome': 'Hacker',
                'emoji': '💻',
                'descricao': 'Invasão de sistemas e roubo de dados',
                'comandos': ['invadir', 'criptografar', 'minerar'],
                'recursos': ['Dados Criptografados', 'Hardware Queimado', 'Bitcoins Raros'],
                'ferramenta': 'Laptop Alienware',
                'especializacoes': ['White Hat', 'Black Hat'],
                'illegal': True
            },
            'traficante': {
                'nome': 'Traficante',
                'emoji': '📦',
                'descricao': 'Comércio ilegal de substâncias e itens proibidos',
                'comandos': ['traficar', 'esconder', 'distribuir'],
                'recursos': ['Pacote Suspeito', 'Substância X', 'Dinheiro Sujo'],
                'ferramenta': 'Maleta Blindada',
                'especializacoes': ['Barão do Crime', 'Logístico'],
                'illegal': True
            },
            'engenheiro': {
                'nome': 'Engenheiro',
                'emoji': '⚙️',
                'descricao': 'Especialista em fabricar e construir itens',
                'comandos': ['construir', 'reparar', 'projetar'],
                'recursos': ['Engrenagem', 'Parafuso', 'Circuito', 'Motor', 'Maquina'],
                'ferramenta': 'Chave Inglesa de Ouro',
                'especializacoes': ['Mecatrônico', 'Arquiteto'],
                'illegal': False
            },
            'alquimista': {
                'nome': 'Alquimista',
                'emoji': '⚗️',
                'descricao': 'Especialista em pocoes e transmutacoes',
                'comandos': ['sintetizar', 'transmutar', 'destilar'],
                'recursos': ['Pocao de Vida', 'Elixir de Forca', 'Essencia Magica', 'Pedra Filosofal', 'Extracto Raro'],
                'ferramenta': 'Grimório Arcano',
                'especializacoes': ['Herbolário', 'Transmutador'],
                'illegal': False
            },
            'chef': {
                'nome': 'Chef',
                'emoji': '👨‍🍳',
                'descricao': 'Especialista em culinaria e gastronomia',
                'comandos': ['cozinhar', 'preparar', 'assar'],
                'recursos': ['Prato Gourmet', 'Sobremesa Fina', 'Sopa Especial', 'Banquete Real', 'Doce Raro'],
                'ferramenta': 'Faca de Damasco',
                'especializacoes': ['Pâtissier', 'Gourmet'],
                'illegal': False
            },
            'comerciante': {
                'nome': 'Comerciante',
                'emoji': '💼',
                'descricao': 'Especialista em negocios e comercio',
                'comandos': ['negociar', 'investir', 'especular'],
                'recursos': ['Contrato Lucrativo', 'Acordo Comercial', 'Investimento', 'Lucro Extra', 'Monopolio'],
                'ferramenta': 'Calculadora de Luxo',
                'especializacoes': ['Magnata', 'Broker'],
                'illegal': False
            }
        }
    
    @commands.command(name='especializar')
    async def especializar(self, ctx, especialidade: str):
        """Escolher uma especialização para sua profissão"""
        user_id = str(ctx.author.id)
        conn = self.bot.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT pp.*, p.name FROM profissao_progresso pp JOIN profissoes p ON pp.profession_id = p.profession_id WHERE pp.user_id = ?", (user_id,))
        prog = cursor.fetchone()

        if not prog:
            await ctx.send("Você não tem uma profissão!")
            return
        
        if prog['level'] < 10:
            await ctx.send("Você precisa do nível 10 para se especializar!")
            return

        prof_key = prog['name'].lower()
        if especialidade.title() not in self.PROFISSOES[prof_key]['especializacoes']:
            await ctx.send(f"Especialização inválida! Opções: {', '.join(self.PROFISSOES[prof_key]['especializacoes'])}")
            return

        cursor.execute("UPDATE profissao_progresso SET specialization = ? WHERE user_id = ? AND profession_id = ?", (especialidade.title(), user_id, prog['profession_id']))
        conn.commit()
        conn.close()
        await ctx.send(f"🎓 Agora você é um(a) especializado(a) em **{especialidade.title()}**!")

    async def profession_action(self, ctx, profession_key: str, action_name: str, cooldown_seconds: int):
        # ... (mantendo lógica existente com adição de falha e bônus de pet)
        fail_chance = 0.1
        if random.random() < fail_chance:
            await ctx.send(f"❌ Sua ação de {action_name} falhou miseravelmente! Risco da profissão.")
            return False
        # ... resto da lógica

    
    @commands.command(name='profissoes', aliases=['profissao', 'jobs'])
    async def profissoes(self, ctx):
        """Ver todas as profissoes disponiveis"""
        embed = discord.Embed(
            title="Sistema de Profissoes",
            description="Escolha uma profissao para comecar sua jornada!",
            color=discord.Color.gold()
        )
        
        for key, prof in self.PROFISSOES.items():
            comandos_text = ", ".join([f"`!{cmd}`" for cmd in prof['comandos']])
            embed.add_field(
                name=f"{prof['emoji']} {prof['nome']}",
                value=f"{prof['descricao']}\n**Comandos:** {comandos_text}",
                inline=False
            )
        
        embed.set_footer(text="Use !escolher <profissao> para escolher")
        
        await ctx.send(embed=embed)
    
    @commands.command(name='escolher', aliases=['choose'])
    async def escolher(self, ctx, profissao: str = None):
        """Escolher uma profissao"""
        if profissao is None:
            await ctx.send("Especifique a profissao! Use `!profissoes` para ver a lista.")
            return
        
        profissao = profissao.lower()
        
        if profissao not in self.PROFISSOES:
            await ctx.send(f"Profissao invalida! Use: {', '.join(self.PROFISSOES.keys())}")
            return
        
        user_id = str(ctx.author.id)
        self.bot.db.ensure_user_exists(user_id)
        
        conn = self.bot.db.get_connection()
        cursor = conn.cursor()
        
        prof_name = self.PROFISSOES[profissao]['nome']
        
        cursor.execute("""
            INSERT OR IGNORE INTO profissoes (name, description, icon) VALUES (?, ?, ?)
        """, (prof_name, 
              self.PROFISSOES[profissao]['descricao'],
              self.PROFISSOES[profissao]['emoji']))
        conn.commit()
        
        cursor.execute("SELECT profession_id FROM profissoes WHERE name = ?", (prof_name,))
        prof_data = cursor.fetchone()
        profession_id = prof_data['profession_id']
        
        cursor.execute("""
            SELECT * FROM profissao_progresso WHERE user_id = ? AND profession_id = ?
        """, (user_id, profession_id))
        
        existing = cursor.fetchone()
        
        if existing:
            await ctx.send(f"Voce ja escolheu esta profissao! Nivel atual: {existing['level']}")
            conn.close()
            return
        
        cursor.execute("""
            INSERT INTO profissao_progresso (user_id, profession_id, chosen_at)
            VALUES (?, ?, ?)
        """, (user_id, profession_id, datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
        
        prof = self.PROFISSOES[profissao]
        
        embed = discord.Embed(
            title=f"{prof['emoji']} Profissao Escolhida!",
            description=f"Voce agora e um(a) **{prof['nome']}**!\n\n{prof['descricao']}",
            color=discord.Color.green()
        )
        
        embed.add_field(
            name="Comandos Disponiveis",
            value="\n".join([f"`!{cmd}`" for cmd in prof['comandos']]),
            inline=False
        )
        
        await ctx.send(embed=embed)
    
    @commands.command(name='minhaprofissao', aliases=['myprofession'])
    async def minhaprofissao(self, ctx):
        """Ver sua profissao atual"""
        user_id = str(ctx.author.id)
        
        conn = self.bot.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT p.name, p.icon, pp.level, pp.xp, pp.chosen_at
            FROM profissao_progresso pp
            JOIN profissoes p ON pp.profession_id = p.profession_id
            WHERE pp.user_id = ?
            ORDER BY pp.level DESC
        """, (user_id,))
        
        professions = cursor.fetchall()
        conn.close()
        
        if not professions:
            await ctx.send("Voce ainda nao escolheu nenhuma profissao! Use `!profissoes` para ver as opcoes.")
            return
        
        embed = discord.Embed(
            title=f"Profissoes de {ctx.author.display_name}",
            color=discord.Color.gold()
        )
        
        for prof in professions:
            xp_needed = prof['level'] * 100
            progress = min(prof['xp'] / xp_needed * 100, 100) if xp_needed > 0 else 0
            
            embed.add_field(
                name=f"{prof['icon']} {prof['name']}",
                value=f"Nivel: **{prof['level']}**\nXP: **{prof['xp']}** / {xp_needed}\nProgresso: {progress:.1f}%",
                inline=True
            )
        
        await ctx.send(embed=embed)
    
    async def profession_action(self, ctx, profession_key: str, action_name: str, cooldown_seconds: int):
        """Funcao generica para acoes de profissao"""
        user_id = str(ctx.author.id)
        prof = self.PROFISSOES[profession_key]
        
        # Chance de falha aleatória
        if random.random() < 0.15:
            await ctx.send(f"❌ Sua ação de **{action_name}** falhou! Você perdeu o fôlego e não conseguiu completar o trabalho.")
            return False

        conn = self.bot.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT profession_id FROM profissoes WHERE LOWER(name) = ?", (prof['nome'].lower(),))
        prof_data = cursor.fetchone()
        
        if not prof_data:
            # Tentar criar a profissão se não existir no banco
            cursor.execute("INSERT OR IGNORE INTO profissoes (name, description, icon, is_illegal) VALUES (?, ?, ?, ?)", 
                         (prof['nome'], prof['descricao'], prof['emoji'], 1 if prof.get('illegal') else 0))
            conn.commit()
            cursor.execute("SELECT profession_id FROM profissoes WHERE LOWER(name) = ?", (prof['nome'].lower(),))
            prof_data = cursor.fetchone()

        cursor.execute("""
            SELECT * FROM profissao_progresso 
            WHERE user_id = ? AND profession_id = ?
        """, (user_id, prof_data['profession_id']))
        
        progress = cursor.fetchone()
        
        if not progress:
            await ctx.send(f"Voce precisa escolher a profissao {prof['nome']} primeiro! Use `!escolher {profession_key}`")
            conn.close()
            return False
        
        # Bônus de Pet
        cursor.execute("SELECT rarity FROM pets WHERE user_id = ? LIMIT 1", (user_id,))
        pet_data = cursor.fetchone()
        pet_bonus = 1.0
        if pet_data:
            rarities_bonus = {'mistico': 1.5, 'lendario': 1.3, 'epico': 1.2, 'raro': 1.1}
            pet_bonus = rarities_bonus.get(pet_data['rarity'], 1.0)

        level = progress['level']
        xp = progress['xp']
        
        xp_gain = int((random.randint(10, 25) + (level * 2)) * pet_bonus)
        coins_gain = int((random.randint(50, 150) * level) * pet_bonus)
        
        new_xp = xp + xp_gain
        new_level = level
        
        xp_needed = level * 100
        if new_xp >= xp_needed:
            new_level += 1
            new_xp = new_xp - xp_needed
        
        cursor.execute("""
            UPDATE profissao_progresso 
            SET xp = ?, level = ?
            WHERE user_id = ? AND profession_id = ?
        """, (new_xp, new_level, user_id, prof_data['profession_id']))
        
        cursor.execute("""
            UPDATE economia 
            SET coins = coins + ?, total_earned = total_earned + ?
            WHERE user_id = ?
        """, (coins_gain, coins_gain, user_id))
        
        resource = random.choice(prof['recursos'])
        
        cursor.execute("""
            SELECT * FROM inventario 
            WHERE user_id = ? AND item_name = ?
        """, (user_id, resource))
        
        existing_item = cursor.fetchone()
        
        if existing_item:
            cursor.execute("""
                UPDATE inventario 
                SET quantity = quantity + 1
                WHERE inventory_id = ?
            """, (existing_item['inventory_id'],))
        else:
            cursor.execute("""
                INSERT INTO inventario (user_id, item_name, item_type, quantity, rarity, description)
                VALUES (?, ?, 'material', 1, 'comum', ?)
            """, (user_id, resource, f"Material obtido como {prof['nome']}"))
        
        conn.commit()
        conn.close()
        
        embed = discord.Embed(
            title=f"{prof['emoji']} {action_name}!",
            description=f"Ferramenta utilizada: **{prof.get('ferramenta', 'Básica')}**",
            color=discord.Color.green()
        )
        
        embed.add_field(
            name="Recompensas",
            value=f"Moedas: **+{coins_gain:,}**\nXP: **+{xp_gain}**\nItem: **{resource}**",
            inline=True
        )
        
        if pet_bonus > 1.0:
            embed.set_footer(text=f"🐾 Bônus de Pet aplicado: {pet_bonus}x")
        
        embed.add_field(
            name="Progresso",
            value=f"Nivel: **{new_level}**\nXP: **{new_xp}** / {new_level * 100}\nEspecialização: **{progress['specialization'] or 'Nenhuma'}**",
            inline=True
        )
        
        await ctx.send(embed=embed)
        return True
    
    @commands.command(name='invadir', aliases=['hack'])
    @commands.cooldown(1, 1800, commands.BucketType.user)
    async def invadir(self, ctx):
        """Invadir sistemas (Hacker)"""
        result = await self.profession_action(ctx, 'hacker', 'Invasão Concluída', 1800)
        if not result:
            ctx.command.reset_cooldown(ctx)

    @commands.command(name='traficar', aliases=['smuggle'])
    @commands.cooldown(1, 1800, commands.BucketType.user)
    async def traficar(self, ctx):
        """Traficar itens (Traficante)"""
        result = await self.profession_action(ctx, 'traficante', 'Entrega Realizada', 1800)
        if not result:
            ctx.command.reset_cooldown(ctx)

    
    @commands.command(name='cacar', aliases=['hunt'])
    @commands.cooldown(1, 1800, commands.BucketType.user)
    async def cacar(self, ctx):
        """Ir cacar (Cacador)"""
        result = await self.profession_action(ctx, 'cacador', 'Caca Realizada', 1800)
        if not result:
            ctx.command.reset_cooldown(ctx)
    
    @cacar.error
    async def cacar_error(self, ctx, error):
        pass
    
    @commands.command(name='rastrear', aliases=['track'])
    @commands.cooldown(1, 1800, commands.BucketType.user)
    async def rastrear(self, ctx):
        """Rastrear presas (Cacador)"""
        result = await self.profession_action(ctx, 'cacador', 'Rastreamento Concluido', 1800)
        if not result:
            ctx.command.reset_cooldown(ctx)
    
    @rastrear.error
    async def rastrear_error(self, ctx, error):
        pass
    
    @commands.command(name='armar', aliases=['trap'])
    @commands.cooldown(1, 1800, commands.BucketType.user)
    async def armar(self, ctx):
        """Armar armadilhas (Cacador)"""
        result = await self.profession_action(ctx, 'cacador', 'Armadilha Armada', 1800)
        if not result:
            ctx.command.reset_cooldown(ctx)
    
    @armar.error
    async def armar_error(self, ctx, error):
        pass
    
    @commands.command(name='construir', aliases=['build'])
    @commands.cooldown(1, 1800, commands.BucketType.user)
    async def construir(self, ctx):
        """Construir algo (Engenheiro)"""
        result = await self.profession_action(ctx, 'engenheiro', 'Construcao Concluida', 1800)
        if not result:
            ctx.command.reset_cooldown(ctx)
    
    @construir.error
    async def construir_error(self, ctx, error):
        pass
    
    @commands.command(name='reparar', aliases=['repair'])
    @commands.cooldown(1, 1800, commands.BucketType.user)
    async def reparar(self, ctx):
        """Reparar algo (Engenheiro)"""
        result = await self.profession_action(ctx, 'engenheiro', 'Reparo Concluido', 1800)
        if not result:
            ctx.command.reset_cooldown(ctx)
    
    @reparar.error
    async def reparar_error(self, ctx, error):
        pass
    
    @commands.command(name='projetar', aliases=['design'])
    @commands.cooldown(1, 1800, commands.BucketType.user)
    async def projetar(self, ctx):
        """Projetar algo (Engenheiro)"""
        result = await self.profession_action(ctx, 'engenheiro', 'Projeto Concluido', 1800)
        if not result:
            ctx.command.reset_cooldown(ctx)
    
    @projetar.error
    async def projetar_error(self, ctx, error):
        pass
    
    @commands.command(name='sintetizar', aliases=['synthesize'])
    @commands.cooldown(1, 1800, commands.BucketType.user)
    async def sintetizar(self, ctx):
        """Sintetizar pocoes (Alquimista)"""
        result = await self.profession_action(ctx, 'alquimista', 'Sintese Concluida', 1800)
        if not result:
            ctx.command.reset_cooldown(ctx)
    
    @sintetizar.error
    async def sintetizar_error(self, ctx, error):
        pass
    
    @commands.command(name='transmutar', aliases=['transmute'])
    @commands.cooldown(1, 1800, commands.BucketType.user)
    async def transmutar(self, ctx):
        """Transmutar materiais (Alquimista)"""
        result = await self.profession_action(ctx, 'alquimista', 'Transmutacao Concluida', 1800)
        if not result:
            ctx.command.reset_cooldown(ctx)
    
    @transmutar.error
    async def transmutar_error(self, ctx, error):
        pass
    
    @commands.command(name='destilar', aliases=['distill'])
    @commands.cooldown(1, 1800, commands.BucketType.user)
    async def destilar(self, ctx):
        """Destilar essencias (Alquimista)"""
        result = await self.profession_action(ctx, 'alquimista', 'Destilacao Concluida', 1800)
        if not result:
            ctx.command.reset_cooldown(ctx)
    
    @destilar.error
    async def destilar_error(self, ctx, error):
        pass
    
    @commands.command(name='cozinhar', aliases=['cook'])
    @commands.cooldown(1, 1800, commands.BucketType.user)
    async def cozinhar(self, ctx):
        """Cozinhar um prato (Chef)"""
        result = await self.profession_action(ctx, 'chef', 'Prato Preparado', 1800)
        if not result:
            ctx.command.reset_cooldown(ctx)
    
    @cozinhar.error
    async def cozinhar_error(self, ctx, error):
        pass
    
    @commands.command(name='preparar', aliases=['prepare'])
    @commands.cooldown(1, 1800, commands.BucketType.user)
    async def preparar(self, ctx):
        """Preparar ingredientes (Chef)"""
        result = await self.profession_action(ctx, 'chef', 'Preparacao Concluida', 1800)
        if not result:
            ctx.command.reset_cooldown(ctx)
    
    @preparar.error
    async def preparar_error(self, ctx, error):
        pass
    
    @commands.command(name='assar', aliases=['bake'])
    @commands.cooldown(1, 1800, commands.BucketType.user)
    async def assar(self, ctx):
        """Assar algo (Chef)"""
        result = await self.profession_action(ctx, 'chef', 'Assado Concluido', 1800)
        if not result:
            ctx.command.reset_cooldown(ctx)
    
    @assar.error
    async def assar_error(self, ctx, error):
        pass
    
    @commands.command(name='negociar', aliases=['negotiate'])
    @commands.cooldown(1, 1800, commands.BucketType.user)
    async def negociar(self, ctx):
        """Negociar contratos (Comerciante)"""
        result = await self.profession_action(ctx, 'comerciante', 'Negociacao Concluida', 1800)
        if not result:
            ctx.command.reset_cooldown(ctx)
    
    @negociar.error
    async def negociar_error(self, ctx, error):
        pass
    
    @commands.command(name='investir', aliases=['invest'])
    @commands.cooldown(1, 1800, commands.BucketType.user)
    async def investir(self, ctx):
        """Fazer investimentos (Comerciante)"""
        result = await self.profession_action(ctx, 'comerciante', 'Investimento Realizado', 1800)
        if not result:
            ctx.command.reset_cooldown(ctx)
    
    @investir.error
    async def investir_error(self, ctx, error):
        pass
    
    @commands.command(name='especular', aliases=['speculate'])
    @commands.cooldown(1, 1800, commands.BucketType.user)
    async def especular(self, ctx):
        """Especular no mercado (Comerciante)"""
        result = await self.profession_action(ctx, 'comerciante', 'Especulacao Concluida', 1800)
        if not result:
            ctx.command.reset_cooldown(ctx)
    
    @especular.error
    async def especular_error(self, ctx, error):
        pass

async def setup(bot):
    await bot.add_cog(Profissoes(bot))
