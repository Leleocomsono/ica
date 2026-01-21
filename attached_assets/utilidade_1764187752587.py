import discord
from discord.ext import commands
from datetime import datetime
import asyncio

class Utilidade(commands.Cog):
    """Comandos de utilidade"""
    
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(name='ping')
    async def ping(self, ctx):
        """Ver latência do bot"""
        latency = round(self.bot.latency * 1000)
        
        embed = discord.Embed(
            title="🏓 Pong!",
            description=f"Latência: **{latency}ms**",
            color=discord.Color.green()
        )
        
        await ctx.send(embed=embed)
    
    @commands.command(name='info')
    async def info(self, ctx):
        """Informações sobre o bot"""
        embed = discord.Embed(
            title="ℹ️ Informações do Bot",
            description="Bot Discord completo com múltiplos sistemas!",
            color=discord.Color.blue()
        )
        
        embed.add_field(name="Servidores", value=len(self.bot.guilds), inline=True)
        embed.add_field(name="Usuários", value=len(self.bot.users), inline=True)
        embed.add_field(name="Prefixo", value="!", inline=True)
        
        # Contar casamentos
        conn = self.bot.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) as total FROM casamentos")
        marriages = cursor.fetchone()['total']
        conn.close()
        
        embed.add_field(name="Casamentos", value=marriages, inline=True)
        
        embed.set_footer(text="Use !ajuda para ver todos os comandos")
        
        await ctx.send(embed=embed)
    
    @commands.command(name='serverinfo', aliases=['servidor'])
    async def serverinfo(self, ctx):
        """Informações do servidor"""
        guild = ctx.guild
        
        embed = discord.Embed(
            title=f"📊 {guild.name}",
            color=discord.Color.blue()
        )
        
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
        
        embed.add_field(name="ID", value=guild.id, inline=True)
        embed.add_field(name="Dono", value=guild.owner.mention if guild.owner else "Desconhecido", inline=True)
        embed.add_field(name="Região", value=str(guild.preferred_locale), inline=True)
        embed.add_field(name="Membros", value=guild.member_count, inline=True)
        embed.add_field(name="Canais", value=len(guild.channels), inline=True)
        embed.add_field(name="Cargos", value=len(guild.roles), inline=True)
        
        created = guild.created_at.strftime("%d/%m/%Y")
        embed.set_footer(text=f"Criado em: {created}")
        
        await ctx.send(embed=embed)
    
    @commands.command(name='userinfo', aliases=['usuario'])
    async def userinfo(self, ctx, member: discord.Member = None):
        """Informações de um usuário"""
        if member is None:
            member = ctx.author
        
        embed = discord.Embed(
            title=f"👤 {member.name}",
            color=member.color
        )
        
        embed.set_thumbnail(url=member.display_avatar.url)
        
        embed.add_field(name="ID", value=member.id, inline=True)
        embed.add_field(name="Apelido", value=member.display_name, inline=True)
        embed.add_field(name="Bot", value="Sim" if member.bot else "Não", inline=True)
        
        created = member.created_at.strftime("%d/%m/%Y")
        joined = member.joined_at.strftime("%d/%m/%Y") if member.joined_at else "Desconhecido"
        
        embed.add_field(name="Conta Criada", value=created, inline=True)
        embed.add_field(name="Entrou no Servidor", value=joined, inline=True)
        
        roles = [role.mention for role in member.roles if role.name != "@everyone"]
        if roles:
            embed.add_field(name=f"Cargos ({len(roles)})", value=" ".join(roles), inline=False)
        
        await ctx.send(embed=embed)
    
    @commands.command(name='lembrete', aliases=['remind'])
    async def lembrete(self, ctx, tempo: int, unidade: str, *, mensagem: str):
        """Criar um lembrete (Ex: !lembrete 10 minutos Estudar)"""
        unidades = {
            's': 1, 'seg': 1, 'segundo': 1, 'segundos': 1,
            'm': 60, 'min': 60, 'minuto': 60, 'minutos': 60,
            'h': 3600, 'hora': 3600, 'horas': 3600,
            'd': 86400, 'dia': 86400, 'dias': 86400
        }
        
        unidade = unidade.lower()
        if unidade not in unidades:
            await ctx.send("❌ Unidade inválida! Use: s, m, h ou d")
            return
        
        segundos = tempo * unidades[unidade]
        
        if segundos > 604800:  # 7 dias
            await ctx.send("❌ Tempo máximo: 7 dias")
            return
        
        await ctx.send(f"✅ Lembrete criado! Vou te lembrar em {tempo} {unidade}.")
        
        await asyncio.sleep(segundos)
        
        try:
            await ctx.author.send(f"⏰ **Lembrete:** {mensagem}")
        except:
            await ctx.send(f"{ctx.author.mention} ⏰ **Lembrete:** {mensagem}")
    
    @commands.command(name='votar', aliases=['poll'])
    async def votar(self, ctx, *, pergunta: str):
        """Criar votação (use | para separar opções)"""
        if '|' not in pergunta:
            await ctx.send("❌ Use | para separar a pergunta das opções!\nEx: !votar Pizza ou Hambúrguer? | Pizza | Hambúrguer")
            return
        
        partes = [p.strip() for p in pergunta.split('|')]
        
        if len(partes) < 3:
            await ctx.send("❌ Você precisa de pelo menos 2 opções!")
            return
        
        if len(partes) > 11:
            await ctx.send("❌ Máximo de 10 opções!")
            return
        
        titulo = partes[0]
        opcoes = partes[1:]
        
        # Emojis numéricos
        emojis = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣', '🔟']
        
        desc = "\n".join([f"{emojis[i]} {opcao}" for i, opcao in enumerate(opcoes)])
        
        embed = discord.Embed(
            title=f"📊 {titulo}",
            description=desc,
            color=discord.Color.blue()
        )
        
        embed.set_footer(text=f"Votação criada por {ctx.author.name}")
        
        msg = await ctx.send(embed=embed)
        
        for i in range(len(opcoes)):
            await msg.add_reaction(emojis[i])
    
    @commands.command(name='ajuda', aliases=['help', 'comandos'])
    async def ajuda(self, ctx):
        """Mostrar todos os comandos"""
        embed = discord.Embed(
            title="📖 Comandos do Bot",
            description="Lista completa de comandos disponíveis",
            color=discord.Color.blue()
        )
        
        embed.add_field(
            name="👤 Perfil",
            value=(
                "`!perfil [@usuário]` - Ver perfil completo\n"
                "`!bio <texto>` - Definir biografia\n"
                "`!xp [@usuário]` - Ver XP\n"
                "`!nivel [@usuário]` - Ver nível e progresso\n"
                "`!avatar [@usuário]` - Ver avatar\n"
                "`!banner <url>` - Definir banner"
            ),
            inline=False
        )
        
        embed.add_field(
            name="💰 Economia",
            value=(
                "`!daily` - Recompensa diária\n"
                "`!trabalhar` - Trabalhar por moedas\n"
                "`!saldo [@usuário]` - Ver saldo\n"
                "`!doar @usuário <quantia>` - Doar moedas\n"
                "`!caixa` - Abrir caixa misteriosa\n"
                "`!inventario` - Ver inventário\n"
                "`!usar <item>` - Usar item"
            ),
            inline=False
        )
        
        embed.add_field(
            name="🐾 Pets",
            value=(
                "`!pet` - Menu de pets\n"
                "`!pet-adotar <espécie>` - Adotar pet\n"
                "`!pet-status` - Ver status do pet\n"
                "`!pet-alimentar` - Alimentar pet\n"
                "`!pet-treinar` - Treinar pet\n"
                "`!pet-aventura` - Enviar em aventura"
            ),
            inline=False
        )
        
        embed.add_field(
            name="💍 Casamento",
            value=(
                "`!casar @usuário` - Pedir em casamento\n"
                "`!aceitar @usuário` - Aceitar pedido\n"
                "`!recusar @usuário` - Recusar pedido\n"
                "`!divorciar` - Divorciar\n"
                "`!casais` - Ver casais"
            ),
            inline=False
        )
        
        embed.add_field(
            name="🏆 Rankings",
            value=(
                "`!ranking xp` - Top XP\n"
                "`!ranking nivel` - Top Nível\n"
                "`!ranking mensagens` - Top Mensagens\n"
                "`!ranking dinheiro` - Top Dinheiro\n"
                "`!pet-ranking` - Top Pets"
            ),
            inline=False
        )
        
        embed.add_field(
            name="ℹ️ Utilidade",
            value=(
                "`!ping` - Ver latência\n"
                "`!info` - Info do bot\n"
                "`!serverinfo` - Info do servidor\n"
                "`!userinfo [@usuário]` - Info do usuário\n"
                "`!votar <pergunta | opção1 | opção2>` - Criar votação\n"
                "`!lembrete <tempo> <unidade> <msg>` - Criar lembrete"
            ),
            inline=False
        )
        
        embed.set_footer(text="Use ! antes de cada comando | Ganhe XP enviando mensagens!")
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Utilidade(bot))
