import discord
from discord.ext import commands
import random
import aiohttp

class Entretenimento(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(name='8ball', aliases=['bola8', '8bola'])
    async def bola8(self, ctx, *, pergunta: str = None):
        """Perguntar a bola 8 magica"""
        if pergunta is None:
            await ctx.send("Faca uma pergunta para a bola 8!")
            return
        
        respostas = [
            "Sim, definitivamente!",
            "E certo.",
            "Sem duvida.",
            "Provavelmente sim.",
            "As perspectivas sao boas.",
            "Sim.",
            "Os sinais apontam que sim.",
            "Resposta nebulosa, tente novamente.",
            "Pergunte novamente mais tarde.",
            "Melhor nao te contar agora.",
            "Nao consigo prever agora.",
            "Concentre-se e pergunte novamente.",
            "Nao conte com isso.",
            "Minha resposta e nao.",
            "Minhas fontes dizem que nao.",
            "As perspectivas nao sao boas.",
            "Muito duvidoso."
        ]
        
        resposta = random.choice(respostas)
        
        embed = discord.Embed(
            title="🎱 Bola 8 Magica",
            color=discord.Color.dark_purple()
        )
        
        embed.add_field(name="Pergunta", value=pergunta, inline=False)
        embed.add_field(name="Resposta", value=resposta, inline=False)
        
        await ctx.send(embed=embed)
    
    @commands.command(name='sortearopcao', aliases=['randomchoice'])
    async def escolher_opcao(self, ctx, *, opcoes: str = None):
        """Escolher entre opcoes (separadas por virgula ou |)"""
        if opcoes is None:
            await ctx.send("Forneca opcoes separadas por virgula ou |")
            return
        
        if '|' in opcoes:
            lista = [o.strip() for o in opcoes.split('|') if o.strip()]
        else:
            lista = [o.strip() for o in opcoes.split(',') if o.strip()]
        
        if len(lista) < 2:
            await ctx.send("Forneca pelo menos 2 opcoes!")
            return
        
        escolha = random.choice(lista)
        
        embed = discord.Embed(
            title="Escolha Aleatoria",
            description=f"Entre as opcoes:\n{', '.join(lista)}\n\nEu escolho: **{escolha}**",
            color=discord.Color.blue()
        )
        
        await ctx.send(embed=embed)
    
    @commands.command(name='piada', aliases=['joke'])
    async def piada(self, ctx):
        """Contar uma piada"""
        piadas = [
            ("Por que o programador foi demitido?", "Porque ele nao tinha classe!"),
            ("O que o JavaScript disse para o Java?", "Voce nao e meu tipo!"),
            ("Por que o desenvolvedor foi ao medico?", "Porque tinha muitos bugs!"),
            ("Como o programador resolve seus problemas?", "Com Ctrl+C e Ctrl+V!"),
            ("Por que o banco de dados terminou com a tabela?", "Porque ela tinha muitas relacoes!"),
            ("O que disse uma variavel para outra?", "Voce e muito indefinida!"),
            ("Por que o loop infinito foi ao psicologo?", "Porque nao conseguia parar de pensar!"),
            ("Qual a fruta favorita do programador?", "A laranja, porque tem muito juice (suco)!"),
            ("Por que o commit foi ao bar?", "Para fazer um merge!"),
            ("O que o servidor disse para o cliente?", "Voce faz tantas requisicoes!")
        ]
        
        piada = random.choice(piadas)
        
        embed = discord.Embed(
            title="😂 Piada",
            description=f"**{piada[0]}**\n\n||{piada[1]}||",
            color=discord.Color.orange()
        )
        
        await ctx.send(embed=embed)
    
    @commands.command(name='fato', aliases=['fact'])
    async def fato(self, ctx):
        """Um fato aleatorio"""
        fatos = [
            "O mel nunca estraga. Foi encontrado mel de 3000 anos em tumbas egipcias ainda comestivel!",
            "Os polvos tem tres coracoes e sangue azul.",
            "Uma nuvem media pesa cerca de 500 toneladas.",
            "O DNA humano e 60% identico ao de uma banana.",
            "Os golfinhos dormem com um olho aberto.",
            "A Torre Eiffel pode crescer ate 15 cm durante o verao devido a expansao termica.",
            "O coracao de um camarao fica na cabeca.",
            "Vacas tem melhores amigos e ficam estressadas quando separadas.",
            "Formigas nao tem pulmoes.",
            "Um raio tem temperatura 5 vezes maior que a superficie do Sol."
        ]
        
        fato = random.choice(fatos)
        
        embed = discord.Embed(
            title="📚 Fato Interessante",
            description=fato,
            color=discord.Color.teal()
        )
        
        await ctx.send(embed=embed)
    
    @commands.command(name='ascii')
    async def ascii_art(self, ctx, *, texto: str = None):
        """Converter texto em ASCII art simples"""
        if texto is None:
            await ctx.send("Digite um texto para converter!")
            return
        
        if len(texto) > 10:
            await ctx.send("Texto muito longo! Maximo 10 caracteres.")
            return
        
        resultado = f"```\n{texto.upper()}\n```"
        
        await ctx.send(resultado)
    
    @commands.command(name='sorteio', aliases=['giveaway'])
    async def sorteio(self, ctx, *, premio: str = None):
        """Iniciar um sorteio (reaja com 🎉)"""
        if premio is None:
            await ctx.send("Especifique o premio do sorteio!")
            return
        
        embed = discord.Embed(
            title="🎉 SORTEIO!",
            description=f"**Premio:** {premio}\n\n"
                       f"Reaja com 🎉 para participar!\n"
                       f"Use `!sortear` para sortear o vencedor.",
            color=discord.Color.gold()
        )
        
        embed.set_footer(text=f"Iniciado por {ctx.author.display_name}")
        
        msg = await ctx.send(embed=embed)
        await msg.add_reaction("🎉")
    
    @commands.command(name='sortear', aliases=['draw'])
    async def sortear(self, ctx, message_id: int = None):
        """Sortear vencedor de um sorteio"""
        if message_id is None:
            async for msg in ctx.channel.history(limit=50):
                if msg.embeds and msg.embeds[0].title == "🎉 SORTEIO!":
                    message_id = msg.id
                    break
        
        if message_id is None:
            await ctx.send("Nao encontrei um sorteio recente! Especifique o ID da mensagem.")
            return
        
        try:
            msg = await ctx.channel.fetch_message(message_id)
        except:
            await ctx.send("Mensagem nao encontrada!")
            return
        
        for reaction in msg.reactions:
            if str(reaction.emoji) == "🎉":
                users = []
                async for user in reaction.users():
                    if not user.bot:
                        users.append(user)
                
                if not users:
                    await ctx.send("Ninguem participou do sorteio!")
                    return
                
                winner = random.choice(users)
                
                embed = discord.Embed(
                    title="🎉 Vencedor do Sorteio!",
                    description=f"Parabens {winner.mention}!\n\n"
                               f"Voce ganhou o sorteio!",
                    color=discord.Color.gold()
                )
                
                await ctx.send(embed=embed)
                return
        
        await ctx.send("Nao encontrei reacoes no sorteio!")
    
    @commands.command(name='enquete', aliases=['poll'])
    async def enquete(self, ctx, *, texto: str = None):
        """Criar uma enquete simples (Sim/Nao)"""
        if texto is None:
            await ctx.send("Especifique a pergunta da enquete!")
            return
        
        embed = discord.Embed(
            title="📊 Enquete",
            description=texto,
            color=discord.Color.blue()
        )
        
        embed.set_footer(text=f"Enquete por {ctx.author.display_name}")
        
        msg = await ctx.send(embed=embed)
        await msg.add_reaction("👍")
        await msg.add_reaction("👎")
    
    @commands.command(name='avatar', aliases=['pfp'])
    async def avatar(self, ctx, member: discord.Member = None):
        """Ver avatar de um usuario"""
        member = member or ctx.author
        
        embed = discord.Embed(
            title=f"Avatar de {member.display_name}",
            color=discord.Color.blue()
        )
        
        embed.set_image(url=member.display_avatar.url)
        
        await ctx.send(embed=embed)
    
    @commands.command(name='emoji', aliases=['emote'])
    async def emoji(self, ctx, emoji: discord.Emoji = None):
        """Ver emoji em tamanho grande"""
        if emoji is None:
            await ctx.send("Especifique um emoji customizado!")
            return
        
        embed = discord.Embed(
            title=f":{emoji.name}:",
            color=discord.Color.blue()
        )
        
        embed.set_image(url=emoji.url)
        
        await ctx.send(embed=embed)
    
    @commands.command(name='beber', aliases=['drink'])
    async def beber(self, ctx):
        """Tomar uma bebida"""
        bebidas = [
            "🍺 Cerveja",
            "🍷 Vinho",
            "🍹 Caipirinha",
            "🥤 Refrigerante",
            "🧃 Suco",
            "☕ Café",
            "🍵 Chá",
            "🥛 Leite",
            "🍾 Champagne",
            "🧋 Bubble Tea"
        ]
        
        bebida = random.choice(bebidas)
        
        await ctx.send(f"{ctx.author.mention} tomou {bebida}!")
    
    @commands.command(name='comer', aliases=['eat'])
    async def comer(self, ctx):
        """Comer um alimento"""
        alimentos = [
            "🍕 Pizza",
            "🍔 Hambúrguer",
            "🌮 Taco",
            "🍝 Macarrão",
            "🍜 Ramen",
            "🍱 Sushi",
            "🥗 Salada",
            "🍔 Sanduíche",
            "🍱 Bento",
            "🍲 Sopa",
            "🥘 Panela",
            "🍛 Curry"
        ]
        
        alimento = random.choice(alimentos)
        
        await ctx.send(f"{ctx.author.mention} comeu {alimento}! 😋")

    @commands.command(name='historia')
    async def historia(self, ctx, *, frase: str):
        """Adicionar uma frase à história coletiva do chat"""
        if not hasattr(self.bot, 'collective_story'):
            self.bot.collective_story = []
        
        self.bot.collective_story.append(f"**{ctx.author.display_name}:** {frase}")
        if len(self.bot.collective_story) > 10:
            self.bot.collective_story.pop(0)
            
        story_text = "\n".join(self.bot.collective_story)
        embed = discord.Embed(title="📖 História Coletiva", description=story_text, color=discord.Color.blue())
        await ctx.send(embed=embed)

    @commands.command(name='vote')
    async def vote(self, ctx, *, pergunta: str):
        """Votação rápida sim/não"""
        embed = discord.Embed(title="🗳️ Votação Rápida", description=pergunta, color=discord.Color.gold())
        embed.set_footer(text=f"Iniciado por {ctx.author.display_name}")
        msg = await ctx.send(embed=embed)
        await msg.add_reaction("✅")
        await msg.add_reaction("❌")

async def setup(bot):
    await bot.add_cog(Entretenimento(bot))
