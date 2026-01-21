import discord
from discord.ext import commands
import random

class Minigames(commands.Cog):
    """Mini-games divertidos"""
    
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(name='duelo', aliases=['duel'])
    @commands.cooldown(1, 60, commands.BucketType.user)
    async def duelo(self, ctx, member: discord.Member):
        """Duelar com outro usuário"""
        if member.bot:
            await ctx.send("❌ Você não pode duelar com um bot!")
            return
        
        if member.id == ctx.author.id:
            await ctx.send("❌ Você não pode duelar consigo mesmo!")
            return
        
        # Simular duelo
        winner = random.choice([ctx.author, member])
        loser = member if winner == ctx.author else ctx.author
        
        embed = discord.Embed(
            title="⚔️ Duelo!",
            description=f"{ctx.author.mention} VS {member.mention}",
            color=discord.Color.red()
        )
        
        embed.add_field(name="Vencedor", value=f"🏆 {winner.mention}", inline=False)
        
        # Atualizar estatísticas
        winner_id = str(winner.id)
        loser_id = str(loser.id)
        
        self.bot.db.ensure_user_exists(winner_id)
        self.bot.db.ensure_user_exists(loser_id)
        
        conn = self.bot.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("UPDATE duelos_stats SET wins = wins + 1 WHERE user_id = ?", (winner_id,))
        cursor.execute("UPDATE duelos_stats SET losses = losses + 1 WHERE user_id = ?", (loser_id,))
        
        # Dar recompensa ao vencedor
        reward = random.randint(50, 150)
        cursor.execute("UPDATE economia SET coins = coins + ? WHERE user_id = ?", (reward, winner_id))
        
        conn.commit()
        conn.close()
        
        embed.add_field(name="Recompensa", value=f"{winner.mention} ganhou {reward} moedas!", inline=False)
        
        await ctx.send(embed=embed)
    
    @commands.command(name='caraoucoroa', aliases=['coinflip'])
    async def caraoucoroa(self, ctx, escolha: str = "cara"):
        """Jogar cara ou coroa"""
        escolha = escolha.lower()
        
        if escolha not in ['cara', 'coroa']:
            await ctx.send("❌ Escolha 'cara' ou 'coroa'!")
            return
        
        resultado = random.choice(['cara', 'coroa'])
        
        if resultado == escolha:
            msg = f"🪙 Deu **{resultado}**! Você ganhou!"
            reward = random.randint(20, 50)
            
            user_id = str(ctx.author.id)
            self.bot.db.ensure_user_exists(user_id)
            
            conn = self.bot.db.get_connection()
            cursor = conn.cursor()
            cursor.execute("UPDATE economia SET coins = coins + ? WHERE user_id = ?", (reward, user_id))
            conn.commit()
            conn.close()
            
            msg += f" (+{reward} moedas)"
        else:
            msg = f"🪙 Deu **{resultado}**! Você perdeu!"
        
        await ctx.send(msg)
    
    @commands.command(name='roleta', aliases=['roulette'])
    @commands.cooldown(1, 120, commands.BucketType.user)
    async def roleta(self, ctx):
        """Girar a roleta da sorte"""
        user_id = str(ctx.author.id)
        self.bot.db.ensure_user_exists(user_id)
        
        # Possíveis prêmios
        prizes = [
            {'emoji': '💰', 'nome': 'Jackpot', 'coins': 1000, 'chance': 0.05},
            {'emoji': '💎', 'nome': 'Diamante', 'coins': 500, 'chance': 0.10},
            {'emoji': '⭐', 'nome': 'Estrela', 'coins': 250, 'chance': 0.20},
            {'emoji': '🎁', 'nome': 'Presente', 'coins': 100, 'chance': 0.30},
            {'emoji': '🍀', 'nome': 'Trevo', 'coins': 50, 'chance': 0.35},
        ]
        
        # Escolher prêmio baseado nas chances
        rand = random.random()
        cumulative = 0
        selected = prizes[-1]
        
        for prize in prizes:
            cumulative += prize['chance']
            if rand <= cumulative:
                selected = prize
                break
        
        conn = self.bot.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE economia SET coins = coins + ? WHERE user_id = ?", (selected['coins'], user_id))
        conn.commit()
        conn.close()
        
        embed = discord.Embed(
            title="🎰 Roleta da Sorte",
            description=f"Girando... girando...\n\n{selected['emoji']} **{selected['nome']}**!",
            color=discord.Color.gold()
        )
        
        embed.add_field(name="Prêmio", value=f"+{selected['coins']} moedas", inline=False)
        
        await ctx.send(embed=embed)
    
    @commands.command(name='dado', aliases=['dice'])
    async def dado(self, ctx, lados: int = 6):
        """Jogar um dado (padrão: 6 lados)"""
        if lados < 2 or lados > 100:
            await ctx.send("❌ O dado deve ter entre 2 e 100 lados!")
            return
        
        resultado = random.randint(1, lados)
        
        embed = discord.Embed(
            title="🎲 Dado",
            description=f"Você jogou um dado de {lados} lados\n\n**Resultado: {resultado}**",
            color=discord.Color.blue()
        )
        
        await ctx.send(embed=embed)
    
    @commands.command(name='quiz')
    @commands.cooldown(1, 30, commands.BucketType.user)
    async def quiz(self, ctx):
        """Responder uma pergunta de quiz"""
        perguntas = [
            {
                'pergunta': 'Qual é a capital do Brasil?',
                'opcoes': ['Rio de Janeiro', 'São Paulo', 'Brasília', 'Salvador'],
                'correta': 2
            },
            {
                'pergunta': 'Quanto é 2 + 2?',
                'opcoes': ['3', '4', '5', '6'],
                'correta': 1
            },
            {
                'pergunta': 'Qual é o maior planeta do sistema solar?',
                'opcoes': ['Terra', 'Marte', 'Júpiter', 'Saturno'],
                'correta': 2
            },
            {
                'pergunta': 'Quantos continentes existem?',
                'opcoes': ['5', '6', '7', '8'],
                'correta': 2
            },
            {
                'pergunta': 'Em que ano o Brasil foi descoberto?',
                'opcoes': ['1492', '1500', '1600', '1700'],
                'correta': 1
            }
        ]
        
        pergunta = random.choice(perguntas)
        emojis = ['1️⃣', '2️⃣', '3️⃣', '4️⃣']
        
        desc = f"**{pergunta['pergunta']}**\n\n"
        for i, opcao in enumerate(pergunta['opcoes']):
            desc += f"{emojis[i]} {opcao}\n"
        
        embed = discord.Embed(
            title="❓ Quiz",
            description=desc,
            color=discord.Color.blue()
        )
        
        embed.set_footer(text="Reaja com a resposta correta!")
        
        msg = await ctx.send(embed=embed)
        
        for i in range(len(pergunta['opcoes'])):
            await msg.add_reaction(emojis[i])
        
        def check(reaction, user):
            return user == ctx.author and str(reaction.emoji) in emojis and reaction.message.id == msg.id
        
        try:
            reaction, user = await self.bot.wait_for('reaction_add', timeout=15.0, check=check)
            
            resposta = emojis.index(str(reaction.emoji))
            
            user_id = str(ctx.author.id)
            self.bot.db.ensure_user_exists(user_id)
            
            conn = self.bot.db.get_connection()
            cursor = conn.cursor()
            
            if resposta == pergunta['correta']:
                reward = 100
                cursor.execute("UPDATE economia SET coins = coins + ? WHERE user_id = ?", (reward, user_id))
                cursor.execute("UPDATE quiz_stats SET correct_answers = correct_answers + 1, total_games = total_games + 1 WHERE user_id = ?", (user_id,))
                await ctx.send(f"✅ Correto! Você ganhou {reward} moedas!")
            else:
                cursor.execute("UPDATE quiz_stats SET wrong_answers = wrong_answers + 1, total_games = total_games + 1 WHERE user_id = ?", (user_id,))
                await ctx.send(f"❌ Errado! A resposta correta era: {pergunta['opcoes'][pergunta['correta']]}")
            
            conn.commit()
            conn.close()
            
        except:
            await ctx.send("⏰ Tempo esgotado!")
    
    @commands.command(name='quiz-ranking')
    async def quiz_ranking(self, ctx):
        """Ver ranking do quiz"""
        conn = self.bot.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT user_id, correct_answers, wrong_answers, total_games
            FROM quiz_stats
            WHERE total_games > 0
            ORDER BY correct_answers DESC
            LIMIT 10
        """)
        
        rows = cursor.fetchall()
        conn.close()
        
        if not rows:
            await ctx.send("❌ Ainda não há dados no ranking.")
            return
        
        embed = discord.Embed(
            title="🏆 Ranking do Quiz",
            color=discord.Color.gold()
        )
        
        medals = ["🥇", "🥈", "🥉"]
        
        for i, row in enumerate(rows, 1):
            try:
                user = await self.bot.fetch_user(int(row['user_id']))
                medal = medals[i-1] if i <= 3 else f"{i}."
                
                accuracy = (row['correct_answers'] / row['total_games'] * 100) if row['total_games'] > 0 else 0
                
                embed.add_field(
                    name=f"{medal} {user.name}",
                    value=f"Acertos: {row['correct_answers']} | Precisão: {accuracy:.1f}%",
                    inline=False
                )
            except:
                continue
        
        await ctx.send(embed=embed)
    
    @commands.command(name='corrida', aliases=['race'])
    @commands.cooldown(1, 120, commands.BucketType.user)
    async def corrida(self, ctx):
        """Participar de uma corrida"""
        user_id = str(ctx.author.id)
        self.bot.db.ensure_user_exists(user_id)
        
        participantes = ["🐎 Cavalo Veloz", "🏎️ Carro Turbo", "🚀 Foguete", "🐆 Guepardo", f"👤 {ctx.author.name}"]
        random.shuffle(participantes)
        
        posicoes = [
            "🥇 1º Lugar",
            "🥈 2º Lugar",
            "🥉 3º Lugar",
            "4º Lugar",
            "5º Lugar"
        ]
        
        user_position = participantes.index(f"👤 {ctx.author.name}")
        
        embed = discord.Embed(
            title="🏁 Resultado da Corrida",
            color=discord.Color.blue()
        )
        
        for i, participante in enumerate(participantes):
            embed.add_field(
                name=posicoes[i],
                value=participante,
                inline=False
            )
        
        conn = self.bot.db.get_connection()
        cursor = conn.cursor()
        
        if user_position == 0:
            reward = 500
            embed.add_field(
                name="🎉 Vitória!",
                value=f"Você ganhou a corrida e recebeu **{reward} moedas**!",
                inline=False
            )
            cursor.execute("UPDATE economia SET coins = coins + ? WHERE user_id = ?", (reward, user_id))
        elif user_position <= 2:
            reward = 250
            embed.add_field(
                name="👏 Pódio!",
                value=f"Você ficou no pódio e recebeu **{reward} moedas**!",
                inline=False
            )
            cursor.execute("UPDATE economia SET coins = coins + ? WHERE user_id = ?", (reward, user_id))
        else:
            embed.add_field(
                name="😞 Não foi dessa vez",
                value="Tente novamente na próxima corrida!",
                inline=False
            )
        
        conn.commit()
        conn.close()
        
        await ctx.send(embed=embed)
    
    @commands.command(name='forca', aliases=['hangman'])
    async def forca(self, ctx):
        """Jogar forca"""
        palavras = [
            ("PYTHON", "💻 Linguagem de programação"),
            ("DISCORD", "💬 Plataforma de comunicação"),
            ("REPLIT", "🌐 IDE online"),
            ("DESENVOLVER", "🛠️ Criar software"),
            ("PROGRAMADOR", "👨‍💻 Profissão"),
            ("COMPUTADOR", "🖥️ Máquina eletrônica"),
            ("INTERNET", "🌍 Rede mundial"),
            ("TECNOLOGIA", "📱 Área da ciência"),
        ]
        
        palavra, dica = random.choice(palavras)
        tentativas = 6
        acertos = set()
        erros = set()
        
        def mostrar_palavra():
            return " ".join([letra if letra in acertos else "_" for letra in palavra])
        
        def desenhar_forca(erros_count):
            desenhos = [
                "```\n  +---+\n  |   |\n      |\n      |\n      |\n      |\n=========```",
                "```\n  +---+\n  |   |\n  O   |\n      |\n      |\n      |\n=========```",
                "```\n  +---+\n  |   |\n  O   |\n  |   |\n      |\n      |\n=========```",
                "```\n  +---+\n  |   |\n  O   |\n /|   |\n      |\n      |\n=========```",
                "```\n  +---+\n  |   |\n  O   |\n /|\\  |\n      |\n      |\n=========```",
                "```\n  +---+\n  |   |\n  O   |\n /|\\  |\n /    |\n      |\n=========```",
                "```\n  +---+\n  |   |\n  O   |\n /|\\  |\n / \\  |\n      |\n=========```"
            ]
            return desenhos[min(erros_count, 6)]
        
        embed = discord.Embed(
            title="🎮 Jogo da Forca",
            description=f"**Dica:** {dica}\n\n{desenhar_forca(0)}\n\n**Palavra:** {mostrar_palavra()}\n\n**Tentativas restantes:** {tentativas}",
            color=discord.Color.green()
        )
        embed.set_footer(text="Digite uma letra para adivinhar! (30 segundos por letra)")
        
        await ctx.send(embed=embed)
        
        while tentativas > 0 and set(palavra) != acertos:
            try:
                def check(m):
                    return m.author == ctx.author and m.channel == ctx.channel and len(m.content) == 1 and m.content.isalpha()
                
                msg = await self.bot.wait_for('message', check=check, timeout=30.0)
                letra = msg.content.upper()
                
                if letra in acertos or letra in erros:
                    await ctx.send(f"❌ Você já tentou a letra **{letra}**!")
                    continue
                
                if letra in palavra:
                    acertos.add(letra)
                    if set(palavra) == acertos:
                        user_id = str(ctx.author.id)
                        self.bot.db.ensure_user_exists(user_id)
                        reward = 300
                        
                        conn = self.bot.db.get_connection()
                        cursor = conn.cursor()
                        cursor.execute("UPDATE economia SET coins = coins + ? WHERE user_id = ?", (reward, user_id))
                        conn.commit()
                        conn.close()
                        
                        embed = discord.Embed(
                            title="🎉 Você Venceu!",
                            description=f"**Palavra:** {palavra}\n\nVocê ganhou **{reward} moedas**!",
                            color=discord.Color.gold()
                        )
                        await ctx.send(embed=embed)
                        return
                    else:
                        embed = discord.Embed(
                            title="✅ Letra Correta!",
                            description=f"{desenhar_forca(len(erros))}\n\n**Palavra:** {mostrar_palavra()}\n\n**Tentativas restantes:** {tentativas}",
                            color=discord.Color.green()
                        )
                        await ctx.send(embed=embed)
                else:
                    erros.add(letra)
                    tentativas -= 1
                    
                    if tentativas == 0:
                        embed = discord.Embed(
                            title="💀 Game Over!",
                            description=f"{desenhar_forca(len(erros))}\n\n**A palavra era:** {palavra}",
                            color=discord.Color.red()
                        )
                        await ctx.send(embed=embed)
                        return
                    else:
                        embed = discord.Embed(
                            title="❌ Letra Errada!",
                            description=f"{desenhar_forca(len(erros))}\n\n**Palavra:** {mostrar_palavra()}\n\n**Tentativas restantes:** {tentativas}",
                            color=discord.Color.orange()
                        )
                        await ctx.send(embed=embed)
                        
            except:
                await ctx.send("⏰ Tempo esgotado! O jogo foi cancelado.")
                return
    
    @commands.command(name='futebol', aliases=['penalty'])
    @commands.cooldown(1, 60, commands.BucketType.user)
    async def futebol(self, ctx):
        """Bater um pênalti"""
        user_id = str(ctx.author.id)
        self.bot.db.ensure_user_exists(user_id)
        
        direcoes = ["⬅️ Esquerda", "⬆️ Centro", "➡️ Direita"]
        
        embed = discord.Embed(
            title="⚽ Pênalti!",
            description="Para onde você vai chutar?\n\n⬅️ Esquerda\n⬆️ Centro\n➡️ Direita",
            color=discord.Color.blue()
        )
        embed.set_footer(text="Reaja com a direção escolhida! (10 segundos)")
        
        msg = await ctx.send(embed=embed)
        await msg.add_reaction("⬅️")
        await msg.add_reaction("⬆️")
        await msg.add_reaction("➡️")
        
        def check(reaction, user):
            return user == ctx.author and str(reaction.emoji) in ["⬅️", "⬆️", "➡️"] and reaction.message.id == msg.id
        
        try:
            reaction, user = await self.bot.wait_for('reaction_add', timeout=10.0, check=check)
            
            chute = str(reaction.emoji)
            defesa = random.choice(["⬅️", "⬆️", "➡️"])
            
            if chute == defesa:
                embed = discord.Embed(
                    title="🧤 Defesa do Goleiro!",
                    description=f"**Seu chute:** {chute}\n**Defesa:** {defesa}\n\nO goleiro pegou! Você perdeu.",
                    color=discord.Color.red()
                )
            else:
                reward = random.randint(150, 350)
                
                conn = self.bot.db.get_connection()
                cursor = conn.cursor()
                cursor.execute("UPDATE economia SET coins = coins + ? WHERE user_id = ?", (reward, user_id))
                conn.commit()
                conn.close()
                
                embed = discord.Embed(
                    title="⚽ GOOOOL!",
                    description=f"**Seu chute:** {chute}\n**Defesa:** {defesa}\n\nVocê enganou o goleiro e marcou!\n\n**Recompensa:** {reward} moedas",
                    color=discord.Color.green()
                )
            
            await ctx.send(embed=embed)
            
        except:
            await ctx.send("⏰ Tempo esgotado! O pênalti foi perdido.")

async def setup(bot):
    await bot.add_cog(Minigames(bot))
