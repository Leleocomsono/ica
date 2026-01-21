import discord
from discord.ext import commands
from datetime import datetime
import asyncio

class HelpView(discord.ui.View):
    def __init__(self, pages, current_page=0):
        super().__init__(timeout=180)
        self.pages = pages
        self.current_page = current_page
        self.update_buttons()
    
    def update_buttons(self):
        self.first_page.disabled = self.current_page == 0
        self.prev_page.disabled = self.current_page == 0
        self.next_page.disabled = self.current_page >= len(self.pages) - 1
        self.last_page.disabled = self.current_page >= len(self.pages) - 1
    
    @discord.ui.button(label="<<", style=discord.ButtonStyle.grey)
    async def first_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page = 0
        self.update_buttons()
        await interaction.response.edit_message(embed=self.pages[self.current_page], view=self)
    
    @discord.ui.button(label="<", style=discord.ButtonStyle.primary)
    async def prev_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page = max(0, self.current_page - 1)
        self.update_buttons()
        await interaction.response.edit_message(embed=self.pages[self.current_page], view=self)
    
    @discord.ui.button(label=">", style=discord.ButtonStyle.primary)
    async def next_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page = min(len(self.pages) - 1, self.current_page + 1)
        self.update_buttons()
        await interaction.response.edit_message(embed=self.pages[self.current_page], view=self)
    
    @discord.ui.button(label=">>", style=discord.ButtonStyle.grey)
    async def last_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page = len(self.pages) - 1
        self.update_buttons()
        await interaction.response.edit_message(embed=self.pages[self.current_page], view=self)

class Utilidade(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
        self.COMANDOS = {
            'Perfil e XP': {
                'emoji': '👤',
                'comandos': {
                    'perfil': 'Ver seu perfil ou de outro usuario. Mostra nivel, XP, economia, pet, profissao e conquistas.',
                    'nivel': 'Ver seu nivel e XP atual, incluindo posicao no ranking.',
                    'bio': 'Definir uma biografia para seu perfil. Maximo 200 caracteres.',
                    'cor': 'Alterar a cor do embed do perfil. Aceita codigo HEX (#FF5733) ou nomes (vermelho, azul, etc).',
                    'banner': 'Definir um banner (imagem) do perfil. Use `!banner remover` para remover.',
                    'xp': 'Ver seu XP total e nível.',
                    'mention': 'Desabilitar a mencao quando voce subir de nivel (continua recebendo o embed).'
                }
            },
            'Economia': {
                'emoji': '💰',
                'comandos': {
                    'saldo': 'Ver seu saldo de moedas na carteira e banco.',
                    'trabalhar': 'Trabalhar para ganhar moedas. Cooldown de 1 hora.',
                    'daily': 'Coletar recompensa diaria de moedas.',
                    'depositar': 'Depositar moedas na conta do banco. Use "tudo" para depositar tudo.',
                    'sacar': 'Sacar moedas do banco. Use "tudo" para sacar tudo.',
                    'pagar': 'Transferir moedas para outro usuario.',
                    'roubar': 'Tentar roubar moedas de outro usuario. 50% de chance de sucesso.',
                    'emprestar': 'Oferecer um empréstimo para outro jogador.',
                    'impostos': 'Verificar impostos pendentes para fortunas.'
                }
            },
            'Pets': {
                'emoji': '🐾',
                'comandos': {
                    'caixas': 'Ver informacoes sobre as caixas de pet disponiveis e suas chances.',
                    'comprar': 'Comprar uma caixa de pet (comum, rara ou mistica).',
                    'pets': 'Ver todos os seus pets organizados por raridade.',
                    'pet': 'Ver detalhes de um pet especifico pelo ID.',
                    'alimentar': 'Alimentar um pet para aumentar fome e saude.',
                    'brincar': 'Brincar com um pet para aumentar felicidade.',
                    'banho': 'Dar banho em um pet para aumentar higiene.',
                    'nomear': 'Dar um nome personalizado ao seu pet.',
                    'libertar': 'Libertar um pet (acao irreversivel).'
                }
            },
            'Casamento': {
                'emoji': '💍',
                'comandos': {
                    'casar': 'Pedir alguem em casamento.',
                    'aceitar': 'Aceitar um pedido de casamento.',
                    'recusar': 'Recusar um pedido de casamento.',
                    'divorciar': 'Divorciar-se do parceiro atual. (Atenção: Perda de 20% das moedas)',
                    'parceiro': 'Ver informacoes do casamento.',
                    'rankingcasais': 'Ver os casais mais ricos do servidor.'
                }
            },
            'Profissoes': {
                'emoji': '⚒️',
                'comandos': {
                    'profissoes': 'Ver todas as profissoes disponiveis.',
                    'escolher': 'Escolher uma profissao (cacador, engenheiro, alquimista, chef, comerciante).',
                    'minhaprofissao': 'Ver suas profissoes e progresso.',
                    'cacar': 'Cacador: Cacar animais.',
                    'rastrear': 'Cacador: Rastrear presas.',
                    'armar': 'Cacador: Armar armadilhas.',
                    'construir': 'Engenheiro: Construir itens.',
                    'reparar': 'Engenheiro: Reparar equipamentos.',
                    'projetar': 'Engenheiro: Projetar estruturas.',
                    'sintetizar': 'Alquimista: Sintetizar pocoes.',
                    'transmutar': 'Alquimista: Transmutar elementos.',
                    'destilar': 'Alquimista: Destilar essencias.',
                    'cozinhar': 'Chef: Cozinhar pratos.',
                    'preparar': 'Chef: Preparar refeicoes.',
                    'assar': 'Chef: Assar pães e doces.',
                    'negociar': 'Comerciante: Negociar acordos.',
                    'investir': 'Comerciante: Investir em negocios.',
                    'especular': 'Comerciante: Especular no mercado.'
                }
            },
            'Missoes': {
                'emoji': '📋',
                'comandos': {
                    'missoes': 'Ver suas missoes ativas e progresso.',
                    'atualizar': 'Atualizar progresso de todas as missoes.',
                    'coletar': 'Coletar recompensas de missoes completadas.'
                }
            },
            'Mini-Games': {
                'emoji': '🎮',
                'comandos': {
                    'forca': 'Iniciar jogo da forca multiplayer. A palavra e escolhida via DM.',
                    'quiz': 'Responder uma pergunta de quiz.',
                    'duelo': 'Desafiar alguem para um duelo com aposta opcional.',
                    'dados': 'Rolar dados (1 a 10).',
                    'moeda': 'Jogar cara ou coroa.'
                }
            },
            'Social': {
                'emoji': '💬',
                'comandos': {
                    'abracar': 'Abracar alguem.',
                    'beijar': 'Beijar alguem.',
                    'cafune': 'Fazer cafune em alguem.',
                    'tapa': 'Dar um tapa em alguem.',
                    'cutucar': 'Cutucar alguem.',
                    'highfive': 'Dar high five em alguem.',
                    'reputacao': 'Ver reputacao de um usuario.',
                    'rep+': 'Dar reputacao positiva (1x por dia).',
                    'rep-': 'Dar reputacao negativa (1x por dia).',
                    'resetar rep': 'Resetar reputacao de um usuario (staff).'
                }
            },
            'Mercado e Inventario': {
                'emoji': '🛒',
                'comandos': {
                    'inventario': 'Ver seu inventario de itens com limite de slots.',
                    'upgradeinv': 'Aumentar o limite de slots do inventário.',
                    'item': 'Ver detalhes de um item com raridade visual.',
                    'usar': 'Usar um item consumivel e ver histórico.',
                    'descartar': 'Descartar itens do inventario.',
                    'dar': 'Dar um item para outro jogador.',
                    'mercado': 'Ver itens a venda no mercado P2P.',
                    'leilao': 'Iniciar um leilão de um item.',
                    'lance': 'Dar um lance em um leilão ativo.',
                    'vender': 'Colocar um item a venda.',
                    'compraritem': 'Comprar um item do mercado.',
                    'cancelarvenda': 'Cancelar uma venda.'
                }
            },
            'Entretenimento': {
                'emoji': '🎭',
                'comandos': {
                    '8ball': 'Perguntar a bola 8 magica.',
                    'sortearopcao': 'Escolher aleatoriamente entre opcoes.',
                    'piada': 'Ouvir uma piada.',
                    'fato': 'Aprender um fato interessante.',
                    'ascii': 'Ver arte ASCII.',
                    'sorteio': 'Iniciar um sorteio.',
                    'sortear': 'Sortear vencedor.',
                    'enquete': 'Criar uma enquete.',
                    'avatar': 'Ver avatar de um usuario.',
                    'emoji': 'Ver informacoes de um emoji.',
                    'beber': 'Tomar uma bebida.',
                    'comer': 'Comer um alimento.',
                    'crime': 'Cometer um crime (RP com cooldown).',
                    'lembrete': 'Criar um lembrete (Ex: !lembrete 10 minutos Estudar).',
                    'historia': 'Adicionar uma frase à história coletiva do chat.',
                    'vote': 'Criar uma votação rápida sim/não.'
                }
            },
            'Rankings': {
                'emoji': '🏆',
                'comandos': {
                    'ranking': 'Ver ranking (xp, moedas, mensagens, pets).',
                    'rankingtipo': 'Ver tipos de ranking disponiveis.',
                    'conquistas': 'Ver conquistas desbloqueadas.'
                }
            },
            'Utilidade': {
                'emoji': '⚙️',
                'comandos': {
                    'ajuda': 'Ver este sistema de ajuda interativo.',
                    'ping': 'Ver latencia do bot.',
                    'serverinfo': 'Ver informacoes do servidor.',
                    'userinfo': 'Ver informacoes de um usuario.',
                    'staffhelp': 'Comandos de staff (requer permissao de moderador).'
                }
            }
        }
    
    @commands.command(name='ajuda', aliases=['help', 'comandos'])
    async def ajuda(self, ctx, *, comando: str = None):
        """Sistema de ajuda com paginas interativas"""
        
        if comando:
            comando = comando.lower()
            
            for categoria, info in self.COMANDOS.items():
                for cmd, desc in info['comandos'].items():
                    if comando in cmd.lower().split('/'):
                        embed = discord.Embed(
                            title=f"Comando: !{comando}",
                            description=desc,
                            color=discord.Color.blue()
                        )
                        
                        embed.add_field(
                            name="Categoria",
                            value=f"{info['emoji']} {categoria}",
                            inline=True
                        )
                        
                        embed.set_footer(text="Use !ajuda para ver todos os comandos")
                        
                        await ctx.send(embed=embed)
                        return
            
            await ctx.send(f"Comando `{comando}` nao encontrado! Use `!ajuda` para ver a lista.")
            return
        
        pages = []
        
        main_embed = discord.Embed(
            title="Central de Ajuda",
            description="Bem-vindo ao sistema de ajuda!\n\n"
                       "Use os botoes abaixo para navegar entre as paginas.\n"
                       "Use `!ajuda <comando>` para detalhes de um comando especifico.\n\n"
                       "**Categorias:**",
            color=discord.Color.blue()
        )
        
        for categoria, info in self.COMANDOS.items():
            main_embed.add_field(
                name=f"{info['emoji']} {categoria}",
                value=f"{len(info['comandos'])} comandos",
                inline=True
            )
        
        main_embed.set_footer(text="Pagina 1 | Use os botoes para navegar")
        pages.append(main_embed)
        
        page_num = 2
        for categoria, info in self.COMANDOS.items():
            embed = discord.Embed(
                title=f"{info['emoji']} {categoria}",
                color=discord.Color.blue()
            )
            
            for cmd, desc in info['comandos'].items():
                embed.add_field(
                    name=f"!{cmd}",
                    value=desc[:100] + "..." if len(desc) > 100 else desc,
                    inline=False
                )
            
            embed.set_footer(text=f"Pagina {page_num} | Use !ajuda <comando> para detalhes")
            pages.append(embed)
            page_num += 1
        
        view = HelpView(pages)
        await ctx.send(embed=pages[0], view=view)
    
    @commands.command(name='ping')
    async def ping(self, ctx):
        """Ver latencia do bot"""
        latency = round(self.bot.latency * 1000)
        
        embed = discord.Embed(
            title="Pong!",
            description=f"Latencia: **{latency}ms**",
            color=discord.Color.green() if latency < 200 else discord.Color.orange()
        )
        
        await ctx.send(embed=embed)
    
    @commands.command(name='serverinfo', aliases=['servidor'])
    async def serverinfo(self, ctx):
        """Informacoes do servidor"""
        guild = ctx.guild
        
        embed = discord.Embed(
            title=guild.name,
            color=discord.Color.blue(),
            timestamp=datetime.now()
        )
        
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
        
        embed.add_field(name="ID", value=guild.id, inline=True)
        embed.add_field(name="Dono", value=guild.owner.mention if guild.owner else "Desconhecido", inline=True)
        embed.add_field(name="Membros", value=guild.member_count, inline=True)
        embed.add_field(name="Canais", value=f"Texto: {len(guild.text_channels)} | Voz: {len(guild.voice_channels)}", inline=True)
        embed.add_field(name="Cargos", value=len(guild.roles), inline=True)
        embed.add_field(name="Criado em", value=guild.created_at.strftime("%d/%m/%Y"), inline=True)
        
        await ctx.send(embed=embed)
    
    @commands.command(name='userinfo', aliases=['usuario'])
    async def userinfo(self, ctx, member: discord.Member = None):
        """Informacoes de um usuario"""
        member = member or ctx.author
        
        embed = discord.Embed(
            title=member.display_name,
            color=member.color
        )
        
        embed.set_thumbnail(url=member.display_avatar.url)
        
        embed.add_field(name="ID", value=member.id, inline=True)
        embed.add_field(name="Nick", value=member.nick or "Nenhum", inline=True)
        embed.add_field(name="Bot", value="Sim" if member.bot else "Nao", inline=True)
        embed.add_field(name="Conta criada", value=member.created_at.strftime("%d/%m/%Y"), inline=True)
        embed.add_field(name="Entrou no servidor", value=member.joined_at.strftime("%d/%m/%Y") if member.joined_at else "Desconhecido", inline=True)
        
        roles = [role.mention for role in member.roles[1:]][:10]
        embed.add_field(name=f"Cargos ({len(member.roles) - 1})", value=" ".join(roles) if roles else "Nenhum", inline=False)
        
        await ctx.send(embed=embed)
    
    @commands.command(name='mention', aliases=['disablemention'])
    async def mention(self, ctx):
        """Desabilitar a mencao de level up (continuara recebendo o embed)"""
        user_id = str(ctx.author.id)
        
        conn = self.bot.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT mention_disabled FROM level_notifications WHERE user_id = ?", (user_id,))
        data = cursor.fetchone()
        
        if data is None:
            cursor.execute("""
                INSERT INTO level_notifications (user_id, mention_disabled, last_notified_level, last_notification_time)
                VALUES (?, 1, 0, '')
            """, (user_id,))
            new_state = True
        else:
            new_state = not bool(data['mention_disabled'])
            cursor.execute("""
                UPDATE level_notifications SET mention_disabled = ? WHERE user_id = ?
            """, (1 if new_state else 0, user_id))
        
        conn.commit()
        conn.close()
        
        status = "desabilitada" if new_state else "habilitada"
        embed = discord.Embed(
            title="Preferência Atualizada!",
            description=f"A menção em level up foi {status}",
            color=discord.Color.green() if not new_state else discord.Color.red()
        )
        
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
    
    @commands.command(name='staffhelp', aliases=['ajuda-staff', 'staffajuda'])
    @commands.has_permissions(moderate_members=True)
    async def staffhelp(self, ctx):
        """Comandos de staff (Requer permissao de warn)"""
        embed = discord.Embed(
            title="📋 Comandos de Staff",
            description="Comandos exclusivos para staff com permissao de warn",
            color=discord.Color.red()
        )
        
        embed.add_field(
            name="Moderacao",
            value="```\n!limpar [qty] - Limpar mensagens\n!kick [user] [motivo] - Expulsar membro\n!ban [user] [motivo] - Banir membro\n!warn [user] [motivo] - Avisar membro\n!mute [user] [tempo] - Mutar membro\n!unmute [user] - Desmutar membro\n```",
            inline=False
        )
        
        embed.add_field(
            name="Reputacao",
            value="```\n!resetar rep [user] - Resetar reputacao de um usuario\n```",
            inline=False
        )
        
        embed.add_field(
            name="Finalizacao",
            value="```\n!finalizar [user] - Finalizar um membro (requer cargo especifico)\n```",
            inline=False
        )
        
        embed.add_field(
            name="Emoji",
            value="```\n!addemoji [nome] [URL] - Criar emoji personalizado no servidor\n```",
            inline=False
        )
        
        embed.add_field(
            name="Level/XP",
            value="```\n!resetarxp [user] - Resetar XP e nivel de um membro (requer cargo especifico)\n```",
            inline=False
        )
        
        embed.add_field(
            name="Mensagem Fixa",
            value="```\n!stick [mensagem] - Criar mensagem fixa no canal\n!unstick - Remover mensagem fixa do canal\n```",
            inline=False
        )
        
        embed.add_field(
            name="Casamento",
            value="```\n!fcasar [user] - Forcar casamento entre voce e outro membro\n```",
            inline=False
        )
        
        embed.set_footer(text="Use !ajuda <comando> para mais detalhes")
        
        await ctx.send(embed=embed)
    
    @commands.command(name='teste')
    async def teste(self, ctx):
        """Teste de nivel up (comando provisorio)"""
        user_id = str(ctx.author.id)
        
        conn = self.bot.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT level FROM usuarios WHERE user_id = ?", (user_id,))
        user_data = cursor.fetchone()
        conn.close()
        
        current_level = user_data['level'] if user_data else 1
        new_level = current_level + 5
        
        content_message = f"_ _⠀⠀  ⠀⠀\n_ _⠀⠀  ⠀⠀{ctx.author.mention} s__ubi__u de nível 　　♡ <:smt_plantinhas:1444153646672773253>\n_ _⠀⠀  ⠀⠀"
        
        description = f"""_ _
_ _⠀⠀  ⠀⠀◜　parabéns⠀﹒{ctx.author.name}⠀　！⠀◞
_ _⠀⠀⠀    ᵔᴗᵔ　parece que você avançou　
_ _⠀⠀⠀  　．⠀para o nível {new_level}　<a:smt_controle:1446304645931864235> ⠀  ⠀⌒⌒ 
_ _"""
        
        embed = discord.Embed(
            description=description,
            color=discord.Color.from_str("#FFFFFF"),
            timestamp=datetime.now()
        )
        
        embed.set_image(url="https://media.discordapp.net/attachments/1444795902865965238/1446304310484013056/download_14.gif?ex=69337f5a&is=69322dda&hm=1b9833a8c14bce7815db66d60894a29427e821c353c2fe9efef60126685e1492&=&width=405&height=229")
        embed.set_footer(
            text="⊹　　use !mention para não ser mencionado",
            icon_url="https://64.media.tumblr.com/b812ee8a67816de65891cb37a7d6e5b0/ac931266187ed159-a1/s75x75_c1/b4689f54fa1cf71688b4958b9aab19bcb6648523.gifv"
        )
        
        await ctx.send(content=content_message, embed=embed)

async def setup(bot):
    await bot.add_cog(Utilidade(bot))
