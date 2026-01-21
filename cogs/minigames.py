import discord
from discord.ext import commands
from datetime import datetime
import random
import asyncio

class HangmanView(discord.ui.View):
    def __init__(self, game, cog):
        super().__init__(timeout=300)
        self.game = game
        self.cog = cog
    
    @discord.ui.button(label="Adivinhar Letra", style=discord.ButtonStyle.primary)
    async def guess_letter(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(
            "Digite uma letra no chat para adivinhar!",
            ephemeral=True
        )

class Minigames(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.hangman_games = {}
        
        self.HANGMAN_STAGES = [
            "```\n  +---+\n  |   |\n      |\n      |\n      |\n      |\n=========```",
            "```\n  +---+\n  |   |\n  O   |\n      |\n      |\n      |\n=========```",
            "```\n  +---+\n  |   |\n  O   |\n  |   |\n      |\n      |\n=========```",
            "```\n  +---+\n  |   |\n  O   |\n /|   |\n      |\n      |\n=========```",
            "```\n  +---+\n  |   |\n  O   |\n /|\\  |\n      |\n      |\n=========```",
            "```\n  +---+\n  |   |\n  O   |\n /|\\  |\n /    |\n      |\n=========```",
            "```\n  +---+\n  |   |\n  O   |\n /|\\  |\n / \\  |\n      |\n=========```"
        ]
    
    def format_word_display(self, word: str, guessed: str) -> str:
        display = ""
        for char in word:
            if char.lower() in guessed.lower() or char == ' ':
                display += char.upper() + " "
            else:
                display += "x "
        return display.strip()
    
    @commands.command(name='forca', aliases=['hangman'])
    async def forca(self, ctx):
        """Iniciar jogo da forca multiplayer"""
        if ctx.channel.id in self.hangman_games:
            await ctx.send("Ja existe um jogo de forca ativo neste canal!")
            return
        
        embed = discord.Embed(
            title="Jogo da Forca",
            description=f"{ctx.author.mention} quer iniciar um jogo!\n\n"
                       f"Vou enviar uma mensagem privada para voce escolher a palavra.",
            color=discord.Color.blue()
        )
        
        await ctx.send(embed=embed)
        
        try:
            dm_embed = discord.Embed(
                title="Escolha a Palavra",
                description="Digite a palavra ou frase que os outros jogadores deverao adivinhar.\n\n"
                           "**Regras:**\n"
                           "• Minimo 3 caracteres\n"
                           "• Maximo 30 caracteres\n"
                           "• Apenas letras e espacos",
                color=discord.Color.blue()
            )
            
            dm_msg = await ctx.author.send(embed=dm_embed)
            
            def dm_check(m):
                return m.author == ctx.author and isinstance(m.channel, discord.DMChannel)
            
            try:
                word_msg = await self.bot.wait_for('message', check=dm_check, timeout=60.0)
                word = word_msg.content.strip()
                
                if len(word) < 3 or len(word) > 30:
                    await ctx.author.send("Palavra invalida! Deve ter entre 3 e 30 caracteres.")
                    return
                
                if not all(c.isalpha() or c.isspace() for c in word):
                    await ctx.author.send("A palavra deve conter apenas letras e espacos!")
                    return
                
                word = word.lower()
                
                await ctx.author.send(f"Palavra definida: **{word}**\nO jogo vai comecar!")
                
            except asyncio.TimeoutError:
                await ctx.author.send("Tempo esgotado! Jogo cancelado.")
                return
                
        except discord.Forbidden:
            await ctx.send("Nao consegui enviar mensagem privada! Habilite suas DMs.")
            return
        
        game = {
            'host_id': str(ctx.author.id),
            'word': word,
            'guessed_letters': '',
            'wrong_letters': '',
            'attempts_left': 6,
            'players': set(),
            'channel_id': ctx.channel.id,
            'started_at': datetime.now()
        }
        
        self.hangman_games[ctx.channel.id] = game
        
        conn = self.bot.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO forca_games (channel_id, host_id, word, started_at)
            VALUES (?, ?, ?, ?)
        """, (str(ctx.channel.id), str(ctx.author.id), word, datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
        
        display = self.format_word_display(word, '')
        
        embed = discord.Embed(
            title="Jogo da Forca - Iniciado!",
            description=f"**Anfitriao:** {ctx.author.mention}\n\n"
                       f"**Palavra:** `{display}`\n\n"
                       f"**Tentativas restantes:** 6\n"
                       f"**Letras erradas:** Nenhuma\n\n"
                       f"{self.HANGMAN_STAGES[0]}",
            color=discord.Color.blue()
        )
        
        embed.set_footer(text="Digite uma letra para adivinhar!")
        
        await ctx.send(embed=embed)
    
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        
        if message.channel.id not in self.hangman_games:
            return
        
        content = message.content.strip().lower()
        
        if len(content) != 1 or not content.isalpha():
            return
        
        game = self.hangman_games[message.channel.id]
        
        if str(message.author.id) == game['host_id']:
            return
        
        letter = content
        
        if letter in game['guessed_letters'] or letter in game['wrong_letters']:
            await message.add_reaction('🔄')
            return
        
        game['players'].add(str(message.author.id))
        
        if letter in game['word']:
            game['guessed_letters'] += letter
            await message.add_reaction('✅')
            
            all_guessed = all(c in game['guessed_letters'] or c == ' ' for c in game['word'])
            
            if all_guessed:
                display = self.format_word_display(game['word'], game['guessed_letters'])
                
                embed = discord.Embed(
                    title="Jogo da Forca - Vitoria!",
                    description=f"**Parabens!** A palavra era: `{game['word'].upper()}`\n\n"
                               f"**{message.author.mention}** acertou a ultima letra!\n\n"
                               f"**Jogadores:** {len(game['players'])}",
                    color=discord.Color.green()
                )
                
                await message.channel.send(embed=embed)
                
                for player_id in game['players']:
                    self.bot.db.ensure_user_exists(player_id)
                    conn = self.bot.db.get_connection()
                    cursor = conn.cursor()
                    cursor.execute("""
                        UPDATE economia SET coins = coins + 100, total_earned = total_earned + 100
                        WHERE user_id = ?
                    """, (player_id,))
                    conn.commit()
                    conn.close()
                
                del self.hangman_games[message.channel.id]
                return
        else:
            game['wrong_letters'] += letter
            game['attempts_left'] -= 1
            await message.add_reaction('❌')
            
            if game['attempts_left'] <= 0:
                embed = discord.Embed(
                    title="Jogo da Forca - Derrota!",
                    description=f"**Game Over!** A palavra era: `{game['word'].upper()}`\n\n"
                               f"{self.HANGMAN_STAGES[6]}",
                    color=discord.Color.red()
                )
                
                await message.channel.send(embed=embed)
                
                del self.hangman_games[message.channel.id]
                return
        
        display = self.format_word_display(game['word'], game['guessed_letters'])
        stage_index = 6 - game['attempts_left']
        
        wrong_display = ' '.join(game['wrong_letters'].upper()) if game['wrong_letters'] else 'Nenhuma'
        
        embed = discord.Embed(
            title="Jogo da Forca",
            description=f"**Palavra:** `{display}`\n\n"
                       f"**Tentativas restantes:** {game['attempts_left']}\n"
                       f"**Letras erradas:** {wrong_display}\n\n"
                       f"{self.HANGMAN_STAGES[stage_index]}",
            color=discord.Color.blue()
        )
        
        embed.set_footer(text=f"Jogadores: {len(game['players'])} | Digite uma letra para adivinhar!")
        
        await message.channel.send(embed=embed)
    
    @commands.command(name='quiz', aliases=['trivia'])
    @commands.cooldown(1, 30, commands.BucketType.user)
    async def quiz(self, ctx):
        """Jogar quiz de perguntas"""
        perguntas = [
            {
                "pergunta": "Qual e o maior planeta do sistema solar?",
                "opcoes": ["A) Terra", "B) Jupiter", "C) Saturno", "D) Marte"],
                "resposta": "b"
            },
            {
                "pergunta": "Qual e a capital do Brasil?",
                "opcoes": ["A) Sao Paulo", "B) Rio de Janeiro", "C) Brasilia", "D) Salvador"],
                "resposta": "c"
            },
            {
                "pergunta": "Quantos lados tem um hexagono?",
                "opcoes": ["A) 5", "B) 6", "C) 7", "D) 8"],
                "resposta": "b"
            },
            {
                "pergunta": "Qual e o elemento quimico com simbolo 'O'?",
                "opcoes": ["A) Ouro", "B) Osmio", "C) Oxigenio", "D) Oganesson"],
                "resposta": "c"
            },
            {
                "pergunta": "Em que ano o homem pisou na Lua pela primeira vez?",
                "opcoes": ["A) 1965", "B) 1969", "C) 1972", "D) 1975"],
                "resposta": "b"
            }
        ]
        
        pergunta = random.choice(perguntas)
        
        embed = discord.Embed(
            title="Quiz!",
            description=f"**{pergunta['pergunta']}**\n\n" + "\n".join(pergunta['opcoes']),
            color=discord.Color.blue()
        )
        
        embed.set_footer(text="Responda com A, B, C ou D | 15 segundos")
        
        await ctx.send(embed=embed)
        
        def check(m):
            return (m.author == ctx.author and 
                    m.channel == ctx.channel and 
                    m.content.lower() in ['a', 'b', 'c', 'd'])
        
        try:
            resposta = await self.bot.wait_for('message', check=check, timeout=15.0)
            
            user_id = str(ctx.author.id)
            self.bot.db.ensure_user_exists(user_id)
            
            conn = self.bot.db.get_connection()
            cursor = conn.cursor()
            
            if resposta.content.lower() == pergunta['resposta']:
                premio = random.randint(50, 150)
                
                cursor.execute("""
                    UPDATE economia SET coins = coins + ?, total_earned = total_earned + ?
                    WHERE user_id = ?
                """, (premio, premio, user_id))
                
                cursor.execute("""
                    UPDATE quiz_stats SET correct_answers = correct_answers + 1, total_games = total_games + 1
                    WHERE user_id = ?
                """, (user_id,))
                
                embed = discord.Embed(
                    title="Resposta Correta!",
                    description=f"Parabens! Voce ganhou **{premio}** moedas!",
                    color=discord.Color.green()
                )
            else:
                cursor.execute("""
                    UPDATE quiz_stats SET wrong_answers = wrong_answers + 1, total_games = total_games + 1
                    WHERE user_id = ?
                """, (user_id,))
                
                embed = discord.Embed(
                    title="Resposta Incorreta!",
                    description=f"A resposta correta era **{pergunta['resposta'].upper()}**",
                    color=discord.Color.red()
                )
            
            conn.commit()
            conn.close()
            
            await ctx.send(embed=embed)
            
            from main import update_mission_progress
            await update_mission_progress(user_id, "minigames", 1)
            
        except asyncio.TimeoutError:
            await ctx.send("Tempo esgotado! A resposta correta era " + pergunta['resposta'].upper())
    
    @quiz.error
    async def quiz_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.send(f"Aguarde {error.retry_after:.0f} segundos para jogar novamente.")
        else:
            ctx.command.reset_cooldown(ctx)
    
    @commands.command(name='duelo', aliases=['duel'])
    @commands.cooldown(1, 60, commands.BucketType.user)
    async def duelo(self, ctx, member: discord.Member = None, aposta: int = 0):
        """Desafiar alguem para um duelo"""
        if member is None:
            ctx.command.reset_cooldown(ctx)
            await ctx.send("Mencione um usuario para desafiar!")
            return
        
        if member.id == ctx.author.id:
            ctx.command.reset_cooldown(ctx)
            await ctx.send("Voce nao pode duelar consigo mesmo!")
            return
        
        if member.bot:
            ctx.command.reset_cooldown(ctx)
            await ctx.send("Voce nao pode duelar com um bot!")
            return
        
        if aposta < 0:
            ctx.command.reset_cooldown(ctx)
            await ctx.send("A aposta deve ser positiva!")
            return
        
        user_id = str(ctx.author.id)
        target_id = str(member.id)
        
        self.bot.db.ensure_user_exists(user_id)
        self.bot.db.ensure_user_exists(target_id)
        
        if aposta > 0:
            conn = self.bot.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("SELECT coins FROM economia WHERE user_id = ?", (user_id,))
            user_coins = cursor.fetchone()['coins'] or 0
            
            cursor.execute("SELECT coins FROM economia WHERE user_id = ?", (target_id,))
            target_coins = cursor.fetchone()['coins'] or 0
            
            conn.close()
            
            if user_coins < aposta:
                ctx.command.reset_cooldown(ctx)
                await ctx.send(f"Voce nao tem moedas suficientes! Seu saldo: **{user_coins:,}**")
                return
            
            if target_coins < aposta:
                ctx.command.reset_cooldown(ctx)
                await ctx.send(f"{member.display_name} nao tem moedas suficientes!")
                return
        
        embed = discord.Embed(
            title="Desafio de Duelo!",
            description=f"{ctx.author.mention} desafiou {member.mention} para um duelo!\n\n"
                       f"**Aposta:** {aposta:,} moedas\n\n"
                       f"{member.mention}, digite `aceitar` para aceitar o duelo ou `recusar` para recusar.",
            color=discord.Color.orange()
        )
        
        await ctx.send(embed=embed)
        
        def check(m):
            return (m.author == member and 
                    m.channel == ctx.channel and 
                    m.content.lower() in ['aceitar', 'recusar'])
        
        try:
            resposta = await self.bot.wait_for('message', check=check, timeout=30.0)
            
            if resposta.content.lower() == 'recusar':
                await ctx.send(f"{member.display_name} recusou o duelo!")
                return
            
            user_roll = random.randint(1, 100)
            target_roll = random.randint(1, 100)
            
            embed = discord.Embed(
                title="Duelo!",
                description=f"**{ctx.author.display_name}** rolou: **{user_roll}**\n"
                           f"**{member.display_name}** rolou: **{target_roll}**",
                color=discord.Color.gold()
            )
            
            conn = self.bot.db.get_connection()
            cursor = conn.cursor()
            
            if user_roll > target_roll:
                winner = ctx.author
                loser = member
                winner_id = user_id
                loser_id = target_id
                embed.add_field(name="Vencedor", value=f"**{ctx.author.display_name}**", inline=False)
                embed.color = discord.Color.green()
            elif target_roll > user_roll:
                winner = member
                loser = ctx.author
                winner_id = target_id
                loser_id = user_id
                embed.add_field(name="Vencedor", value=f"**{member.display_name}**", inline=False)
                embed.color = discord.Color.green()
            else:
                embed.add_field(name="Resultado", value="**Empate!**", inline=False)
                embed.color = discord.Color.grey()
                await ctx.send(embed=embed)
                conn.close()
                return
            
            cursor.execute("""
                UPDATE duelos_stats SET wins = wins + 1 WHERE user_id = ?
            """, (winner_id,))
            
            cursor.execute("""
                UPDATE duelos_stats SET losses = losses + 1 WHERE user_id = ?
            """, (loser_id,))
            
            if aposta > 0:
                cursor.execute("""
                    UPDATE economia SET coins = coins + ?, total_earned = total_earned + ?
                    WHERE user_id = ?
                """, (aposta, aposta, winner_id))
                
                cursor.execute("""
                    UPDATE economia SET coins = coins - ?, total_spent = total_spent + ?
                    WHERE user_id = ?
                """, (aposta, aposta, loser_id))
                
                embed.add_field(name="Premio", value=f"**{aposta:,}** moedas", inline=False)
            
            conn.commit()
            conn.close()
            
            await ctx.send(embed=embed)
            
            from main import update_mission_progress
            await update_mission_progress(winner_id, "minigames", 1)
            await update_mission_progress(loser_id, "minigames", 1)
            
        except asyncio.TimeoutError:
            await ctx.send(f"{member.display_name} nao respondeu a tempo!")
    
    @duelo.error
    async def duelo_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.send(f"Aguarde {error.retry_after:.0f} segundos para duelar novamente.")
        elif isinstance(error, commands.MemberNotFound):
            ctx.command.reset_cooldown(ctx)
            await ctx.send("Membro nao encontrado!")
        else:
            ctx.command.reset_cooldown(ctx)
    
    @commands.command(name='dados', aliases=['dice'])
    async def dados(self, ctx, quantidade: int = 1):
        """Rolar dados"""
        if quantidade < 1 or quantidade > 10:
            await ctx.send("Voce pode rolar de 1 a 10 dados!")
            return
        
        resultados = [random.randint(1, 6) for _ in range(quantidade)]
        total = sum(resultados)
        
        dice_emojis = {1: '⚀', 2: '⚁', 3: '⚂', 4: '⚃', 5: '⚄', 6: '⚅'}
        display = ' '.join([dice_emojis[r] for r in resultados])
        
        embed = discord.Embed(
            title="Rolagem de Dados",
            description=f"{display}\n\n**Resultados:** {', '.join(map(str, resultados))}\n**Total:** {total}",
            color=discord.Color.blue()
        )
        
        await ctx.send(embed=embed)
    
    @commands.command(name='moeda', aliases=['flip', 'coinflip'])
    async def moeda(self, ctx, escolha: str = None):
        """Jogar cara ou coroa"""
        if escolha:
            escolha = escolha.lower()
            if escolha not in ['cara', 'coroa']:
                await ctx.send("Escolha `cara` ou `coroa`!")
                return
        
        resultado = random.choice(['cara', 'coroa'])
        emoji = '🪙' if resultado == 'cara' else '⭕'
        
        embed = discord.Embed(
            title=f"{emoji} Cara ou Coroa",
            description=f"A moeda caiu em: **{resultado.capitalize()}**!",
            color=discord.Color.gold()
        )
        
        if escolha:
            if escolha == resultado:
                embed.add_field(name="Resultado", value="Voce acertou!", inline=False)
                embed.color = discord.Color.green()
            else:
                embed.add_field(name="Resultado", value="Voce errou!", inline=False)
                embed.color = discord.Color.red()
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Minigames(bot))
