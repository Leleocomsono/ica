import discord
from discord.ext import commands
import random

class Entretenimento(commands.Cog):
    """Comandos de entretenimento"""
    
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(name='carinho', aliases=['pat'])
    async def carinho(self, ctx, member: discord.Member):
        """Fazer carinho em alguém"""
        gifs = [
            "https://media.tenor.com/VrCrINkYFJkAAAAC/anime-head-pat.gif",
            "https://media.tenor.com/4j0bQ8aKgH8AAAAC/anime-pat.gif"
        ]
        
        embed = discord.Embed(
            description=f"{ctx.author.mention} fez carinho em {member.mention}! 💕",
            color=discord.Color.pink()
        )
        
        embed.set_image(url=random.choice(gifs))
        
        await ctx.send(embed=embed)
    
    @commands.command(name='8ball')
    async def eightball(self, ctx, *, pergunta: str):
        """Perguntar à bola mágica"""
        respostas = [
            "Sim, definitivamente",
            "Não tenho dúvidas",
            "Provavelmente sim",
            "As perspectivas são boas",
            "Tente novamente mais tarde",
            "Melhor não te dizer agora",
            "Não conte com isso",
            "Minhas fontes dizem que não",
            "Muito duvidoso",
            "Não é possível prever agora"
        ]
        
        resposta = random.choice(respostas)
        
        embed = discord.Embed(
            title="🎱 Bola Mágica",
            color=discord.Color.purple()
        )
        
        embed.add_field(name="Pergunta", value=pergunta, inline=False)
        embed.add_field(name="Resposta", value=resposta, inline=False)
        
        await ctx.send(embed=embed)
    
    @commands.command(name='ship')
    async def ship(self, ctx, user1: discord.Member, user2: discord.Member = None):
        """Ver compatibilidade entre usuários"""
        if user2 is None:
            user2 = user1
            user1 = ctx.author
        
        # Calcular porcentagem baseado nos IDs
        seed = int(str(user1.id) + str(user2.id))
        random.seed(seed)
        percentage = random.randint(0, 100)
        random.seed()
        
        if percentage < 25:
            msg = "Péssima combinação! 💔"
            color = discord.Color.red()
        elif percentage < 50:
            msg = "Pode dar certo... ou não 😅"
            color = discord.Color.orange()
        elif percentage < 75:
            msg = "Boa combinação! 💕"
            color = discord.Color.blue()
        else:
            msg = "Combinação perfeita! 💖"
            color = discord.Color.pink()
        
        bar = "▰" * (percentage // 10) + "▱" * (10 - percentage // 10)
        
        embed = discord.Embed(
            title="💘 Ship Meter",
            description=f"{user1.mention} x {user2.mention}",
            color=color
        )
        
        embed.add_field(name="Compatibilidade", value=f"{bar} {percentage}%", inline=False)
        embed.add_field(name="Resultado", value=msg, inline=False)
        
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
    
    @commands.command(name='crime')
    @commands.cooldown(1, 300, commands.BucketType.user)
    async def crime(self, ctx):
        """Cometer um crime (RP)"""
        crimes = [
            {"nome": "Assaltar um banco", "sucesso": 0.3, "ganho": (500, 1000), "perda": (200, 500)},
            {"nome": "Roubar uma loja", "sucesso": 0.5, "ganho": (200, 500), "perda": (100, 300)},
            {"nome": "Hackear um sistema", "sucesso": 0.6, "ganho": (300, 700), "perda": (150, 350)},
            {"nome": "Contrabandear itens", "sucesso": 0.4, "ganho": (400, 800), "perda": (200, 400)}
        ]
        
        crime = random.choice(crimes)
        sucesso = random.random() < crime['sucesso']
        
        user_id = str(ctx.author.id)
        self.bot.db.ensure_user_exists(user_id)
        
        conn = self.bot.db.get_connection()
        cursor = conn.cursor()
        
        if sucesso:
            ganho = random.randint(*crime['ganho'])
            cursor.execute("UPDATE economia SET coins = coins + ? WHERE user_id = ?", (ganho, user_id))
            msg = f"✅ Você conseguiu {crime['nome']} e ganhou **{ganho} moedas**!"
        else:
            perda = random.randint(*crime['perda'])
            cursor.execute("UPDATE economia SET coins = CASE WHEN coins >= ? THEN coins - ? ELSE 0 END WHERE user_id = ?", (perda, perda, user_id))
            msg = f"❌ Você falhou em {crime['nome']} e perdeu **{perda} moedas**!"
        
        conn.commit()
        conn.close()
        
        await ctx.send(msg)
    
    @commands.command(name='hackear', aliases=['hack'])
    async def hackear(self, ctx, member: discord.Member):
        """Hackear alguém (RP)"""
        if member.bot:
            await ctx.send("❌ Bots têm firewall muito forte!")
            return
        
        if member.id == ctx.author.id:
            await ctx.send("❌ Você não pode hackear a si mesmo!")
            return
        
        await ctx.send(f"💻 Hackeando {member.mention}...")
        await ctx.send("```\n[████████████████████] 100%\n```")
        await ctx.send(f"✅ Hack completo! Email: {member.name}@discord.com | Senha: ********")
    
    @commands.command(name='matar', aliases=['kill'])
    async def matar(self, ctx, member: discord.Member):
        """Matar alguém (RP)"""
        if member.id == ctx.author.id:
            await ctx.send("❌ Você não pode se matar!")
            return
        
        armas = ["espada", "machado", "arco", "magia", "veneno", "armadilha"]
        arma = random.choice(armas)
        
        await ctx.send(f"⚔️ {ctx.author.mention} matou {member.mention} com {arma}!")
    
    @commands.command(name='frase', aliases=['quote'])
    async def frase(self, ctx):
        """Mostrar uma frase motivacional"""
        frases = [
            "A persistência é o caminho do êxito.",
            "Acredite em si mesmo e tudo será possível.",
            "O sucesso é a soma de pequenos esforços repetidos dia após dia.",
            "Não espere por oportunidades extraordinárias. Aproveite as comuns e as torne grandiosas.",
            "O único lugar onde o sucesso vem antes do trabalho é no dicionário.",
            "Você é mais corajoso do que acredita, mais forte do que parece e mais esperto do que pensa.",
            "A vida é 10% o que acontece com você e 90% como você reage a isso.",
            "O fracasso é apenas a oportunidade de começar de novo de forma mais inteligente."
        ]
        
        frase = random.choice(frases)
        
        embed = discord.Embed(
            title="💭 Frase Motivacional",
            description=f"*\"{frase}\"*",
            color=discord.Color.blue()
        )
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Entretenimento(bot))
