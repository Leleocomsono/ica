import discord
from discord.ext import commands
from discord.enums import TextStyle
from datetime import datetime, timedelta
import psutil
import os
import asyncio
import random
import threading

ADMIN_ROLE_ID = 1444053060862087370

class PainelControle(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.chaos_mode = {}
        self.echo_mode = {}
        self.echo_channel = {}
        self.caps_mode = {}
        self.caps_channel = {}
    
    def has_admin_role(self, ctx):
        """Verifica se o usuário tem o cargo de admin"""
        return any(role.id == ADMIN_ROLE_ID for role in ctx.author.roles)
    
    @commands.Cog.listener()
    async def on_message(self, message):
        """Monitora mensagens para caps_mode e echo_mode"""
        if message.author.bot:
            return
        
        user_id = message.author.id
        
        # Repetir CAPS
        if user_id in self.caps_mode and self.caps_mode.get(user_id):
            if user_id in self.caps_channel and message.channel.id == self.caps_channel[user_id]:
                if message.content and not message.content.startswith('!'):
                    print(f"[CAPS] {message.author}: {message.content}")
                    try:
                        await message.channel.send(f'"{message.content.upper()}"')
                    except Exception as e:
                        print(f"[CAPS ERROR] {e}")
        
        # Modo Eco
        if user_id in self.echo_mode and self.echo_mode.get(user_id):
            if user_id in self.echo_channel and message.channel.id == self.echo_channel[user_id]:
                if message.content and not message.content.startswith('!'):
                    print(f"[ECO] {message.author}: {message.content}")
                    try:
                        await message.channel.send(message.content)
                    except Exception as e:
                        print(f"[ECO ERROR] {e}")
    
    @commands.command(name='painel')
    async def painel(self, ctx):
        """Abre o painel de controle do bot (apenas para admins)"""
        if not self.has_admin_role(ctx):
            await ctx.send("❌ Você não tem permissão para usar este comando!")
            return
        
        embed = discord.Embed(
            title="🎛️ Painel de Controle do Bot",
            description="Use os botões abaixo para controlar o bot\n\nPágina 1/7 - Status & Configuração",
            color=discord.Color.gold()
        )
        
        embed.add_field(
            name="Funcionalidades Disponíveis",
            value="• Status do Bot\n• Mudar Status\n• Informações\n• Ir para Moderação\n• Ir para Diversão\n• Ir para Ferramentas Admin\n• Ir para Estética",
            inline=False
        )
        
        view = PainelView(self.bot, page=1)
        await ctx.send(embed=embed, view=view)

async def setup(bot):
    await bot.add_cog(PainelControle(bot))

class PainelView(discord.ui.View):
    def __init__(self, bot, page=1):
        super().__init__(timeout=600)
        self.bot = bot
        self.page = page
    
    @discord.ui.button(label="Status", style=discord.ButtonStyle.primary)
    async def status_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Ver status do bot"""
        embed = discord.Embed(
            title="📊 Status do Bot",
            color=discord.Color.blue()
        )
        
        embed.add_field(name="Latência", value=f"{round(self.bot.latency * 1000)}ms", inline=True)
        embed.add_field(name="Servidores", value=len(self.bot.guilds), inline=True)
        embed.add_field(name="Usuários", value=len(set(self.bot.get_all_members())), inline=True)
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @discord.ui.button(label="Alterar Status", style=discord.ButtonStyle.primary)
    async def alterar_status(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Modal para alterar status"""
        modal = StatusModal(self.bot)
        await interaction.response.send_modal(modal)
    
    @discord.ui.button(label="Informações", style=discord.ButtonStyle.secondary)
    async def info_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Ver informações do bot"""
        embed = discord.Embed(
            title="ℹ️ Informações do Bot",
            color=discord.Color.blue()
        )
        
        embed.add_field(name="Nome", value=self.bot.user.name, inline=False)
        embed.add_field(name="Versão discord.py", value=discord.__version__, inline=False)
        embed.add_field(name="Servidores", value=len(self.bot.guilds), inline=True)
        embed.add_field(name="Latência", value=f"{round(self.bot.latency * 1000)}ms", inline=True)
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @discord.ui.button(label="➡️ Moderação", style=discord.ButtonStyle.success)
    async def ir_moderation(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Ir para página de moderação"""
        embed = discord.Embed(
            title="🎛️ Painel de Controle - Moderação",
            description="Use os botões abaixo para funções de moderação\n\nPágina 2/7 - Moderação (Página 1)",
            color=discord.Color.red()
        )
        
        view = ModeracaoView1(self.bot)
        await interaction.response.edit_message(embed=embed, view=view)
    
    @discord.ui.button(label="🎭 Diversão", style=discord.ButtonStyle.secondary)
    async def ir_diversao(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Ir para página de diversão"""
        embed = discord.Embed(
            title="🎭 Painel de Diversão - Zoação Staff",
            description="Use os botões abaixo para entreter e trollar membros!\n\nPágina 4/7 - Diversão (Página 1)",
            color=discord.Color.purple()
        )
        
        view = DiversaoView1(self.bot)
        await interaction.response.edit_message(embed=embed, view=view)
    
    @discord.ui.button(label="🧙 Ferramentas Admin", style=discord.ButtonStyle.secondary)
    async def ir_ferramentas(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Ir para ferramentas administrativas"""
        embed = discord.Embed(
            title="🧙 Ferramentas Administrativas Avançadas",
            description="Funções avançadas de moderação\n\nPágina 6/7",
            color=discord.Color.blurple()
        )
        
        view = FerramuentasView(self.bot)
        await interaction.response.edit_message(embed=embed, view=view)
    
    @discord.ui.button(label="🧩 Estética", style=discord.ButtonStyle.secondary)
    async def ir_estetica(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Ir para configurações estéticas"""
        embed = discord.Embed(
            title="🧩 Coisas Estéticas / Extras",
            description="Personalize o painel e bot\n\nPágina 7/7",
            color=discord.Color.magenta()
        )
        
        view = EstéticaView(self.bot)
        await interaction.response.edit_message(embed=embed, view=view)
    
    @discord.ui.button(label="Fechar", style=discord.ButtonStyle.danger)
    async def fechar_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Fechar painel"""
        await interaction.response.defer()
        await interaction.message.delete()

class ModeracaoView1(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=600)
        self.bot = bot
    
    @discord.ui.button(label="🕐 Modo Lento", style=discord.ButtonStyle.primary, row=0)
    async def modo_lento(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Modal para modo lento"""
        modal = ModoLentoModal()
        await interaction.response.send_modal(modal)
    
    @discord.ui.button(label="🔒 Bloquear Canal", style=discord.ButtonStyle.danger, row=0)
    async def bloquear(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Bloquear canal"""
        try:
            await interaction.channel.set_permissions(interaction.guild.default_role, send_messages=False)
            embed = discord.Embed(
                title="🔒 Canal Bloqueado",
                description=f"{interaction.channel.mention} foi bloqueado!",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ Erro: {e}", ephemeral=True)
    
    @discord.ui.button(label="🔓 Desbloquear Canal", style=discord.ButtonStyle.success, row=0)
    async def desbloquear(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Desbloquear canal"""
        try:
            await interaction.channel.set_permissions(interaction.guild.default_role, send_messages=True)
            embed = discord.Embed(
                title="🔓 Canal Desbloqueado",
                description=f"{interaction.channel.mention} foi desbloqueado!",
                color=discord.Color.green()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ Erro: {e}", ephemeral=True)
    
    @discord.ui.button(label="🗑️ Limpar Msgs", style=discord.ButtonStyle.primary, row=1)
    async def limpar_msg(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Modal para limpar mensagens"""
        modal = LimparModal()
        await interaction.response.send_modal(modal)
    
    @discord.ui.button(label="⚠️ Aviso Global", style=discord.ButtonStyle.primary, row=1)
    async def aviso_global(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Modal para aviso global"""
        modal = AvisoGlobalModal(interaction.guild)
        await interaction.response.send_modal(modal)
    
    @discord.ui.button(label="🔄 Sinc. Perms", style=discord.ButtonStyle.secondary, row=1)
    async def sinc_perms(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Sincronizar permissões"""
        try:
            if not interaction.channel.category:
                await interaction.response.send_message("❌ Este canal não tem uma categoria!", ephemeral=True)
                return
            
            await interaction.channel.edit(sync_permissions=True)
            embed = discord.Embed(
                title="✅ Permissões Sincronizadas",
                description=f"Permissões de {interaction.channel.mention} foram sincronizadas!",
                color=discord.Color.green()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ Erro: {e}", ephemeral=True)
    
    @discord.ui.button(label="🎤 Mover Voice", style=discord.ButtonStyle.primary, row=2)
    async def mover_voice(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Modal para mover membros de voz"""
        modal = MoverVoiceModal()
        await interaction.response.send_modal(modal)
    
    @discord.ui.button(label="📝 Anúncio Embed", style=discord.ButtonStyle.primary, row=2)
    async def anuncio_embed(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Modal para anúncio embed"""
        modal = AnuncioEmbedModal(interaction.guild)
        await interaction.response.send_modal(modal)
    
    @discord.ui.button(label="🆕 Criar Canal", style=discord.ButtonStyle.primary, row=2)
    async def criar_canal(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Modal para criar canal"""
        modal = CriarCanalModal()
        await interaction.response.send_modal(modal)
    
    @discord.ui.button(label="▶️ Próxima Página", style=discord.ButtonStyle.success, row=3)
    async def proxima_pagina(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Ir para próxima página"""
        embed = discord.Embed(
            title="🎛️ Painel de Controle - Moderação",
            description="Use os botões abaixo para mais funções de moderação\n\nPágina 3/7 - Moderação (Página 2)",
            color=discord.Color.red()
        )
        
        view = ModeracaoView2(self.bot)
        await interaction.response.edit_message(embed=embed, view=view)
    
    @discord.ui.button(label="⬅️ Voltar", style=discord.ButtonStyle.secondary, row=3)
    async def voltar(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Voltar para página inicial"""
        embed = discord.Embed(
            title="🎛️ Painel de Controle do Bot",
            description="Use os botões abaixo para controlar o bot\n\nPágina 1/7 - Status & Configuração",
            color=discord.Color.gold()
        )
        
        embed.add_field(
            name="Funcionalidades Disponíveis",
            value="• Status do Bot\n• Mudar Status\n• Informações\n• Ir para Moderação\n• Ir para Diversão",
            inline=False
        )
        
        view = PainelView(self.bot, page=1)
        await interaction.response.edit_message(embed=embed, view=view)
    
    @discord.ui.button(label="Fechar", style=discord.ButtonStyle.danger, row=3)
    async def fechar_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Fechar painel"""
        await interaction.response.defer()
        await interaction.message.delete()

class ModeracaoView2(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=600)
        self.bot = bot
    
    @discord.ui.button(label="📊 Ver Ping", style=discord.ButtonStyle.secondary, row=0)
    async def ver_ping(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Ver ping do bot"""
        try:
            process = psutil.Process(os.getpid())
            ram_mb = process.memory_info().rss / 1024 / 1024
            
            embed = discord.Embed(
                title="📊 Performance do Bot",
                color=discord.Color.blue()
            )
            
            embed.add_field(name="🏓 Ping", value=f"{round(self.bot.latency * 1000)}ms", inline=True)
            embed.add_field(name="💾 Uso de RAM", value=f"{ram_mb:.2f} MB", inline=True)
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ Erro: {e}", ephemeral=True)
    
    @discord.ui.button(label="🏷️ Editar Nickname", style=discord.ButtonStyle.primary, row=0)
    async def editar_nickname(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Modal para editar nickname"""
        modal = EditarNicknameModal()
        await interaction.response.send_modal(modal)
    
    @discord.ui.button(label="📦 Ver Versão", style=discord.ButtonStyle.secondary, row=1)
    async def ver_versao(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Ver versão do bot"""
        embed = discord.Embed(
            title="📦 Versão do Bot",
            description="Bot Completo Sistema v1.0",
            color=discord.Color.gold()
        )
        
        embed.add_field(
            name="Changelog v1.0",
            value="✅ Sistema de Perfil\n✅ Economia Completa\n✅ Pets com Blind Box\n✅ Casamento\n✅ Profissões\n✅ Missões\n✅ Mini-Games\n✅ Painel de Controle",
            inline=False
        )
        
        embed.set_footer(text="Desenvolvido com discord.py")
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @discord.ui.button(label="🔇 Mutar Todos", style=discord.ButtonStyle.danger, row=1)
    async def mutar_todos(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Mutar todos em calls"""
        try:
            membros_mutados = 0
            for voice_channel in interaction.guild.voice_channels:
                for member in voice_channel.members:
                    try:
                        await member.edit(mute=True)
                        membros_mutados += 1
                    except:
                        pass
            
            embed = discord.Embed(
                title="✅ Membros Mutados",
                description=f"{membros_mutados} membros foram mutados!",
                color=discord.Color.green()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ Erro: {e}", ephemeral=True)
    
    @discord.ui.button(label="🔊 Desmutar Todos", style=discord.ButtonStyle.success, row=1)
    async def desmutar_todos(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Desmutar todos em calls"""
        try:
            membros_desnutados = 0
            for voice_channel in interaction.guild.voice_channels:
                for member in voice_channel.members:
                    try:
                        await member.edit(mute=False)
                        membros_desnutados += 1
                    except:
                        pass
            
            embed = discord.Embed(
                title="✅ Membros Desnutados",
                description=f"{membros_desnutados} membros foram desnutados!",
                color=discord.Color.green()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ Erro: {e}", ephemeral=True)
    
    @discord.ui.button(label="⏸️ Pausar Comandos", style=discord.ButtonStyle.danger, row=2)
    async def pausar_comandos(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Pausar/Retomar comandos"""
        self.bot.commands_paused = getattr(self.bot, 'commands_paused', False)
        self.bot.commands_paused = not self.bot.commands_paused
        
        status = "PAUSADOS ⏸️" if self.bot.commands_paused else "RETOMADOS ▶️"
        embed = discord.Embed(
            title=f"✅ Comandos {status}",
            description=f"Todos os comandos foram {status}",
            color=discord.Color.orange()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @discord.ui.button(label="⬅️ Página Anterior", style=discord.ButtonStyle.secondary, row=2)
    async def pagina_anterior(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Voltar para página anterior"""
        embed = discord.Embed(
            title="🎛️ Painel de Controle - Moderação",
            description="Use os botões abaixo para funções de moderação\n\nPágina 2/7 - Moderação (Página 1)",
            color=discord.Color.red()
        )
        
        embed.add_field(
            name="Funcionalidades Disponíveis",
            value="Todas as funções de moderação em botões",
            inline=False
        )
        
        view = ModeracaoView1(self.bot)
        await interaction.response.edit_message(embed=embed, view=view)
    
    @discord.ui.button(label="⬅️ Início", style=discord.ButtonStyle.secondary, row=2)
    async def voltar_inicio(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Voltar para página inicial"""
        embed = discord.Embed(
            title="🎛️ Painel de Controle do Bot",
            description="Use os botões abaixo para controlar o bot\n\nPágina 1/7 - Status & Configuração",
            color=discord.Color.gold()
        )
        
        embed.add_field(
            name="Funcionalidades Disponíveis",
            value="• Status do Bot\n• Mudar Status\n• Informações\n• Ir para Moderação\n• Ir para Diversão",
            inline=False
        )
        
        view = PainelView(self.bot, page=1)
        await interaction.response.edit_message(embed=embed, view=view)
    
    @discord.ui.button(label="Fechar", style=discord.ButtonStyle.danger, row=2)
    async def fechar_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Fechar painel"""
        await interaction.response.defer()
        await interaction.message.delete()

class FerramuentasView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=600)
        self.bot = bot
        self.moderation_history = {}
        self.blocked_words = []
        self.member_notes = {}
        self.anti_raid = False
        self.ghost_mode = False
    
    @discord.ui.button(label="🔍 Histórico Membro", style=discord.ButtonStyle.primary, row=0)
    async def historico(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(title="🔍 Histórico de Moderação", description="Digite ID do membro para ver histórico", color=discord.Color.blue())
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @discord.ui.button(label="⛔ Palavras Bloqueadas", style=discord.ButtonStyle.primary, row=0)
    async def palavras_bloqueadas(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = PalavrasBloquadasModal(self)
        await interaction.response.send_modal(modal)
    
    @discord.ui.button(label="📝 Nota Secreta", style=discord.ButtonStyle.primary, row=0)
    async def nota_secreta(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = NotaSecretaModal(self)
        await interaction.response.send_modal(modal)
    
    @discord.ui.button(label="🚨 Anti-Raid/Spam", style=discord.ButtonStyle.danger, row=1)
    async def anti_raid(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.anti_raid = not self.anti_raid
        status = "✅ ATIVADO" if self.anti_raid else "❌ DESATIVADO"
        embed = discord.Embed(title=f"🚨 Anti-Raid {status}", color=discord.Color.red())
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @discord.ui.button(label="💤 Modo Fantasma", style=discord.ButtonStyle.danger, row=1)
    async def modo_fantasma(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.ghost_mode = not self.ghost_mode
        status = "✅ ATIVADO" if self.ghost_mode else "❌ DESATIVADO"
        embed = discord.Embed(title=f"💤 Modo Fantasma {status}", description="Bot só responde staff", color=discord.Color.greyple())
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @discord.ui.button(label="⬅️ Voltar", style=discord.ButtonStyle.secondary, row=2)
    async def voltar(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(title="🎛️ Painel Controle", description="Página 1/7", color=discord.Color.gold())
        view = PainelView(self.bot, page=1)
        await interaction.response.edit_message(embed=embed, view=view)
    
    @discord.ui.button(label="🗣️ TTS", style=discord.ButtonStyle.primary, row=2)
    async def tts_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Botão para abrir modal de TTS"""
        modal = TTSModal()
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="Fechar", style=discord.ButtonStyle.danger, row=2)
    async def fechar(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        await interaction.message.delete()

class TTSModal(discord.ui.Modal, title="Falar via TTS"):
    text = discord.ui.TextInput(
        label="Texto para falar",
        placeholder="Digite o que o bot deve falar...",
        style=discord.TextStyle.paragraph,
        max_length=200
    )

    async def on_submit(self, interaction: discord.Interaction):
        if not interaction.user.voice:
            return await interaction.response.send_message("❌ Você precisa estar em um canal de voz!", ephemeral=True)
        
        await interaction.response.send_message("🗣️ Preparando áudio...", ephemeral=True)
        
        # Simular o comando !tts
        ctx = await interaction.client.get_context(interaction.message)
        ctx.author = interaction.user
        tts_cog = interaction.client.get_cog('TTS')
        if tts_cog:
            await tts_cog.tts(ctx, text=self.text.value)
        else:
            await interaction.followup.send("❌ Sistema de TTS não encontrado!", ephemeral=True)

class EstéticaView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=600)
        self.bot = bot
        self.embed_color = discord.Color.gold()
        self.auto_messages = {}
    
    @discord.ui.button(label="🎨 Cor Embed", style=discord.ButtonStyle.primary, row=0)
    async def cor_embed(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = CorEmbedModal(self)
        await interaction.response.send_modal(modal)
    
    @discord.ui.button(label="🖼 Ícone Bot", style=discord.ButtonStyle.primary, row=0)
    async def icone_bot(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = IconeBotModal(self.bot)
        await interaction.response.send_modal(modal)
    
    @discord.ui.button(label="💬 Msg Automática", style=discord.ButtonStyle.primary, row=0)
    async def msg_automatica(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = MsgAutomaticaModal(self)
        await interaction.response.send_modal(modal)
    
    @discord.ui.button(label="📅 Lembrete", style=discord.ButtonStyle.primary, row=1)
    async def criar_lembrete(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = LembreteModal()
        await interaction.response.send_modal(modal)
    
    @discord.ui.button(label="⬅️ Voltar", style=discord.ButtonStyle.secondary, row=2)
    async def voltar(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(title="🎛️ Painel Controle", description="Página 1/7", color=discord.Color.gold())
        view = PainelView(self.bot, page=1)
        await interaction.response.edit_message(embed=embed, view=view)
    
    @discord.ui.button(label="Fechar", style=discord.ButtonStyle.danger, row=2)
    async def fechar(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        await interaction.message.delete()

class DiversaoView1(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=600)
        self.bot = bot
    
    @discord.ui.button(label="🎭 Entrar Call", style=discord.ButtonStyle.primary, row=0)
    async def entrar_call(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            if not interaction.user.voice:
                await interaction.response.send_message("❌ Você precisa estar em um canal de voz!", ephemeral=True)
                return
            channel = interaction.user.voice.channel
            if interaction.guild.voice_client:
                await interaction.guild.voice_client.move_to(channel)
            else:
                await channel.connect()
            embed = discord.Embed(title="🎭 Bot Entrou", description=f"Entrei em {channel.mention}!", color=discord.Color.purple())
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            print(f"Erro entrar call: {e}")
            await interaction.response.send_message(f"❌ Erro: {str(e)}", ephemeral=True)
    
    @discord.ui.button(label="🎤 Sair Call", style=discord.ButtonStyle.danger, row=0)
    async def sair_call(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            if interaction.guild.voice_client:
                await interaction.guild.voice_client.disconnect()
                embed = discord.Embed(title="🎭 Bot Saiu", color=discord.Color.purple())
                await interaction.response.send_message(embed=embed, ephemeral=True)
            else:
                await interaction.response.send_message("❌ Bot não está em call!", ephemeral=True)
        except: await interaction.response.send_message("❌ Erro!", ephemeral=True)
    
    @discord.ui.button(label="😵 Falso Ban", style=discord.ButtonStyle.danger, row=1)
    async def falso_ban(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = FalsoBanModal()
        await interaction.response.send_modal(modal)
    
    @discord.ui.button(label="💀 Msg Assustadora", style=discord.ButtonStyle.danger, row=1)
    async def msg_assustadora(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = MsgAssustaradoraModal()
        await interaction.response.send_modal(modal)
    
    @discord.ui.button(label="😂 Teleportar", style=discord.ButtonStyle.primary, row=1)
    async def teleportar(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = TeleportarModal()
        await interaction.response.send_modal(modal)
    
    @discord.ui.button(label="⚡ Cargo Aleatório", style=discord.ButtonStyle.primary, row=2)
    async def cargo_aleatorio(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = CargoAleatorioModal()
        await interaction.response.send_modal(modal)
    
    @discord.ui.button(label="📢 Repetir CAPS", style=discord.ButtonStyle.secondary, row=2)
    async def repetir_caps(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = RepetirCapsModalV2()
        await interaction.response.send_modal(modal)
    
    @discord.ui.button(label="➡️ Próxima", style=discord.ButtonStyle.success, row=3)
    async def proxima(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(title="🎭 Diversão (Página 2/2)", description="Mais funções!", color=discord.Color.purple())
        view = DiversaoView2(self.bot)
        await interaction.response.edit_message(embed=embed, view=view)
    
    @discord.ui.button(label="⬅️ Voltar", style=discord.ButtonStyle.secondary, row=3)
    async def voltar(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(title="🎛️ Painel Controle", description="Página 1/7", color=discord.Color.gold())
        embed.add_field(name="Funcionalidades", value="• Status\n• Mudar Status\n• Informações\n• Moderação\n• Diversão", inline=False)
        view = PainelView(self.bot, page=1)
        await interaction.response.edit_message(embed=embed, view=view)
    
    @discord.ui.button(label="Fechar", style=discord.ButtonStyle.gray, row=3)
    async def fechar(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        await interaction.message.delete()

class DiversaoView2(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=600)
        self.bot = bot
    
    @discord.ui.button(label="😂 Sticker", style=discord.ButtonStyle.primary, row=0)
    async def sticker(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            stickers = await interaction.guild.fetch_stickers()
            if not stickers:
                await interaction.response.send_message("❌ Nenhum sticker no servidor!", ephemeral=True)
                return
            sticker_aleatorio = random.choice(stickers)
            embed = discord.Embed(title="😂 Sticker Aleatório", description=f"**{sticker_aleatorio.name}**", color=discord.Color.purple())
            embed.set_image(url=sticker_aleatorio.url)
            await interaction.response.send_message(embed=embed)
        except Exception as e:
            await interaction.response.send_message(f"❌ Erro: {str(e)}", ephemeral=True)
    
    @discord.ui.button(label="🌀 Modo Eco", style=discord.ButtonStyle.primary, row=0)
    async def modo_eco(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = ModoEcoModal(self.bot)
        await interaction.response.send_modal(modal)
    
    @discord.ui.button(label="🎲 Castigo", style=discord.ButtonStyle.danger, row=1)
    async def castigo(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = CastigoAleatorioModal()
        await interaction.response.send_modal(modal)
    
    @discord.ui.button(label="⬅️ Voltar", style=discord.ButtonStyle.secondary, row=2)
    async def voltar(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(title="🎭 Diversão (Página 1/2)", color=discord.Color.purple())
        view = DiversaoView1(self.bot)
        await interaction.response.edit_message(embed=embed, view=view)
    
    @discord.ui.button(label="🏠 Início", style=discord.ButtonStyle.secondary, row=2)
    async def inicio(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(title="🎛️ Painel Controle", description="Página 1/7", color=discord.Color.gold())
        embed.add_field(name="Funcionalidades", value="• Status\n• Mudar Status\n• Informações\n• Moderação\n• Diversão", inline=False)
        view = PainelView(self.bot, page=1)
        await interaction.response.edit_message(embed=embed, view=view)
    
    @discord.ui.button(label="Fechar", style=discord.ButtonStyle.gray, row=2)
    async def fechar(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        await interaction.message.delete()

class StatusModal(discord.ui.Modal):
    def __init__(self, bot):
        super().__init__(title="Alterar Status do Bot")
        self.bot = bot
        self.status = discord.ui.TextInput(label="Novo Status", placeholder="Ex: Jogando com !ajuda", max_length=128)
        self.add_item(self.status)
    
    async def on_submit(self, interaction: discord.Interaction):
        try:
            novo_status = self.status.value
            await self.bot.change_presence(activity=discord.Game(name=novo_status))
            embed = discord.Embed(title="✅ Status Alterado", description=f"Novo status: **{novo_status}**", color=discord.Color.green())
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ Erro: {e}", ephemeral=True)

class ModoLentoModal(discord.ui.Modal):
    def __init__(self):
        super().__init__(title="Configurar Modo Lento")
        self.tempo = discord.ui.TextInput(label="Tempo em segundos (0 = desativar)", placeholder="Ex: 5", max_length=5)
        self.add_item(self.tempo)
    
    async def on_submit(self, interaction: discord.Interaction):
        try:
            tempo = int(self.tempo.value)
            if tempo < 0 or tempo > 21600:
                await interaction.response.send_message("❌ Valor deve estar entre 0 e 21600!", ephemeral=True)
                return
            await interaction.channel.edit(slowmode_delay=tempo)
            embed = discord.Embed(
                title="✅ Modo Lento Ativado" if tempo > 0 else "✅ Modo Lento Desativado",
                description=f"Tempo: {tempo}s" if tempo > 0 else "",
                color=discord.Color.green()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except ValueError:
            await interaction.response.send_message("❌ Valor deve ser um número!", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ Erro: {e}", ephemeral=True)

class LimparModal(discord.ui.Modal):
    def __init__(self):
        super().__init__(title="Limpar Mensagens")
        self.quantidade = discord.ui.TextInput(label="Quantidade de mensagens", placeholder="Ex: 50", max_length=4)
        self.add_item(self.quantidade)
    
    async def on_submit(self, interaction: discord.Interaction):
        try:
            quantidade = int(self.quantidade.value)
            if quantidade < 1 or quantidade > 1000:
                await interaction.response.send_message("❌ Quantidade deve estar entre 1 e 1000!", ephemeral=True)
                return
            deleted = await interaction.channel.purge(limit=quantidade)
            embed = discord.Embed(title="✅ Mensagens Deletadas", description=f"{len(deleted)} mensagens foram deletadas!", color=discord.Color.green())
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except ValueError:
            await interaction.response.send_message("❌ Valor deve ser um número!", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ Erro: {e}", ephemeral=True)

class AvisoGlobalModal(discord.ui.Modal):
    def __init__(self, guild):
        super().__init__(title="Aviso Global")
        self.guild = guild
        self.mensagem = discord.ui.TextInput(label="Mensagem do aviso", placeholder="Digite a mensagem...", style=TextStyle.paragraph, max_length=2000)
        self.add_item(self.mensagem)
    
    async def on_submit(self, interaction: discord.Interaction):
        try:
            embed = discord.Embed(title="⚠️ AVISO GLOBAL", description=self.mensagem.value, color=discord.Color.orange(), timestamp=datetime.now())
            canais_enviados = 0
            for channel in self.guild.text_channels:
                try:
                    if channel.permissions_for(self.guild.me).send_messages:
                        await channel.send(embed=embed)
                        canais_enviados += 1
                except:
                    pass
            embed_resposta = discord.Embed(title="✅ Aviso Enviado", description=f"Aviso enviado em {canais_enviados} canais", color=discord.Color.green())
            await interaction.response.send_message(embed=embed_resposta, ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ Erro: {e}", ephemeral=True)

class MoverVoiceModal(discord.ui.Modal):
    def __init__(self):
        super().__init__(title="Mover Membros de Voz")
        self.canal_id = discord.ui.TextInput(label="ID do Canal de Voz Destino", placeholder="Ex: 123456789", max_length=20)
        self.add_item(self.canal_id)
    
    async def on_submit(self, interaction: discord.Interaction):
        try:
            canal_id = int(self.canal_id.value)
            canal = interaction.guild.get_channel(canal_id)
            if not isinstance(canal, discord.VoiceChannel):
                await interaction.response.send_message("❌ Canal não é um canal de voz!", ephemeral=True)
                return
            membros_movidos = 0
            for voice_channel in interaction.guild.voice_channels:
                for member in voice_channel.members:
                    try:
                        await member.move_to(canal)
                        membros_movidos += 1
                    except:
                        pass
            embed = discord.Embed(title="✅ Membros Movidos", description=f"{membros_movidos} membros foram movidos para {canal.mention}!", color=discord.Color.green())
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except ValueError:
            await interaction.response.send_message("❌ ID inválido!", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ Erro: {e}", ephemeral=True)

class AnuncioEmbedModal(discord.ui.Modal):
    def __init__(self, guild):
        super().__init__(title="Criar Anúncio Embed")
        self.guild = guild
        self.titulo = discord.ui.TextInput(label="Título", placeholder="Ex: Novo Update", max_length=256)
        self.descricao = discord.ui.TextInput(label="Descrição", placeholder="Descrição do anúncio...", style=TextStyle.paragraph, max_length=4000)
        self.add_item(self.titulo)
        self.add_item(self.descricao)
    
    async def on_submit(self, interaction: discord.Interaction):
        try:
            embed = discord.Embed(title=self.titulo.value, description=self.descricao.value, color=discord.Color.gold(), timestamp=datetime.now())
            canais_enviados = 0
            for channel in self.guild.text_channels:
                try:
                    if channel.permissions_for(self.guild.me).send_messages:
                        await channel.send(embed=embed)
                        canais_enviados += 1
                except:
                    pass
            embed_resposta = discord.Embed(title="✅ Anúncio Enviado", description=f"Anúncio enviado em {canais_enviados} canais!", color=discord.Color.green())
            await interaction.response.send_message(embed=embed_resposta, ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ Erro: {e}", ephemeral=True)

class CriarCanalModal(discord.ui.Modal):
    def __init__(self):
        super().__init__(title="Criar Canal")
        self.nome = discord.ui.TextInput(label="Nome do canal", placeholder="Ex: novo-canal", max_length=100)
        self.add_item(self.nome)
    
    async def on_submit(self, interaction: discord.Interaction):
        try:
            canal = await interaction.guild.create_text_channel(self.nome.value)
            embed = discord.Embed(title="✅ Canal Criado", description=f"Canal {canal.mention} foi criado!", color=discord.Color.green())
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except discord.Forbidden:
            await interaction.response.send_message("❌ Não tenho permissão para criar canais!", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ Erro: {e}", ephemeral=True)

class EditarNicknameModal(discord.ui.Modal):
    def __init__(self):
        super().__init__(title="Editar Nickname do Bot")
        self.nickname = discord.ui.TextInput(label="Novo nickname (deixe vazio para remover)", required=False)
        self.add_item(self.nickname)
    
    async def on_submit(self, interaction: discord.Interaction):
        try:
            novo_nick = self.nickname.value if self.nickname.value else None
            await interaction.guild.me.edit(nick=novo_nick)
            embed = discord.Embed(title="✅ Nickname Alterado" if novo_nick else "✅ Nickname Removido", description=f"Novo nickname: **{novo_nick}**" if novo_nick else "", color=discord.Color.green())
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ Erro: {e}", ephemeral=True)

class FalsoBanModal(discord.ui.Modal):
    def __init__(self):
        super().__init__(title="Falso Ban")
        self.membro = discord.ui.TextInput(label="ID/Menção do Membro", max_length=30)
        self.canal = discord.ui.TextInput(label="ID do Canal", max_length=30)
        self.add_item(self.membro)
        self.add_item(self.canal)
    
    async def on_submit(self, interaction: discord.Interaction):
        try:
            membro_id = int(self.membro.value.strip('<>@!'))
            canal_id = int(self.canal.value.strip('<>#!'))
            membro = interaction.guild.get_member(membro_id)
            canal = interaction.guild.get_channel(canal_id)
            if not membro: await interaction.response.send_message("❌ Membro não encontrado!", ephemeral=True); return
            if not canal: await interaction.response.send_message("❌ Canal não encontrado!", ephemeral=True); return
            embed = discord.Embed(title="⛔ BAN!", description=f"{membro.mention} foi banido do {canal.mention}!", color=discord.Color.red())
            msg = await canal.send(embed=embed)
            await interaction.response.send_message("✅ Falso ban enviado!", ephemeral=True)
            await asyncio.sleep(5)
            await msg.delete()
        except Exception as e: await interaction.response.send_message(f"❌ Erro: {str(e)}", ephemeral=True)

class MsgAssustaradoraModal(discord.ui.Modal):
    def __init__(self):
        super().__init__(title="Msg Assustadora")
        self.membro = discord.ui.TextInput(label="ID/Menção", max_length=30)
        self.add_item(self.membro)
    
    async def on_submit(self, interaction: discord.Interaction):
        try:
            membro_id = int(self.membro.value.strip('<>@!'))
            membro = interaction.guild.get_member(membro_id)
            if not membro: await interaction.response.send_message("❌ Não encontrado!", ephemeral=True); return
            msgs = ["👻 Você está sendo observado...", "💀 Seus dias estão contados...", "👁️ Nós estamos aqui..."]
            embed = discord.Embed(title="⚠️ AVISO", description=random.choice(msgs), color=discord.Color.dark_red())
            await membro.send(embed=embed)
            await interaction.response.send_message(f"✅ Enviado para {membro.mention}!", ephemeral=True)
        except: await interaction.response.send_message("❌ Erro!", ephemeral=True)

class TeleportarModal(discord.ui.Modal):
    def __init__(self):
        super().__init__(title="Teleportar")
        self.membro = discord.ui.TextInput(label="ID", max_length=20)
        self.add_item(self.membro)
    
    async def on_submit(self, interaction: discord.Interaction):
        try:
            membro = interaction.guild.get_member(int(self.membro.value))
            if not membro or not membro.voice: await interaction.response.send_message("❌ Erro!", ephemeral=True); return
            canal = random.choice(interaction.guild.voice_channels)
            await membro.move_to(canal)
            embed = discord.Embed(title="😂 TELEPORTE!", description=f"{membro.mention} → {canal.mention}", color=discord.Color.purple())
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except: await interaction.response.send_message("❌ Erro!", ephemeral=True)

class CargoAleatorioModal(discord.ui.Modal):
    def __init__(self):
        super().__init__(title="Cargo Aleatório")
        self.membro = discord.ui.TextInput(label="ID", max_length=20)
        self.add_item(self.membro)
    
    async def on_submit(self, interaction: discord.Interaction):
        try:
            membro = interaction.guild.get_member(int(self.membro.value))
            if not membro: await interaction.response.send_message("❌ Não encontrado!", ephemeral=True); return
            cargos = [r for r in interaction.guild.roles if not r.managed and r.position < interaction.guild.me.top_role.position]
            if not cargos: await interaction.response.send_message("❌ Sem cargos!", ephemeral=True); return
            cargo = random.choice(cargos)
            await membro.add_roles(cargo)
            embed = discord.Embed(title="⚡ CARGO", description=f"{membro.mention} ganhou {cargo.mention}!", color=discord.Color.gold())
            await interaction.response.send_message(embed=embed, ephemeral=True)
            await asyncio.sleep(30)
            await membro.remove_roles(cargo)
        except: await interaction.response.send_message("❌ Erro!", ephemeral=True)

class RepetirCapsModalV2(discord.ui.Modal):
    def __init__(self):
        super().__init__(title="Repetir CAPS")
        self.membro = discord.ui.TextInput(label="ID", max_length=20)
        self.add_item(self.membro)
    
    async def on_submit(self, interaction: discord.Interaction):
        try:
            membro = interaction.guild.get_member(int(self.membro.value))
            if not membro: await interaction.response.send_message("❌ Não encontrado!", ephemeral=True); return
            cog = interaction.client.get_cog('PainelControle')
            cog.caps_mode[membro.id] = True
            cog.caps_channel[membro.id] = interaction.channel.id
            embed = discord.Embed(title="📢 CAPS", description=f"Repetindo {membro.mention} em CAPS por 10s!", color=discord.Color.blue())
            await interaction.response.send_message(embed=embed, ephemeral=True)
            await asyncio.sleep(10)
            cog.caps_mode[membro.id] = False
            cog.caps_channel.pop(membro.id, None)
        except Exception as e: await interaction.response.send_message(f"❌ Erro: {str(e)}", ephemeral=True)

class ModoEcoModal(discord.ui.Modal):
    def __init__(self, bot):
        super().__init__(title="🌀 Modo Eco")
        self.bot = bot
        self.membro = discord.ui.TextInput(label="ID do Membro", max_length=20)
        self.duracao = discord.ui.TextInput(label="Duração (s)", max_length=3, default="15")
        self.add_item(self.membro)
        self.add_item(self.duracao)
    
    async def on_submit(self, interaction: discord.Interaction):
        try:
            await interaction.response.defer(ephemeral=True)
            membro_id = int(self.membro.value.strip())
            membro = interaction.guild.get_member(membro_id)
            if not membro:
                await interaction.followup.send("❌ Membro não encontrado!", ephemeral=True)
                return
            duracao = int(self.duracao.value)
            if duracao < 1 or duracao > 300:
                await interaction.followup.send("❌ Duração entre 1-300s!", ephemeral=True)
                return
            cog = interaction.client.get_cog('PainelControle')
            print(f"[ECO] Ativando para {membro} ({membro_id}) no canal {interaction.channel.id} por {duracao}s")
            cog.echo_mode[membro.id] = True
            cog.echo_channel[membro.id] = interaction.channel.id
            embed = discord.Embed(title="🌀 Modo Eco Ativado", description=f"Repetindo mensagens de {membro.mention} por {duracao}s!", color=discord.Color.teal())
            await interaction.followup.send(embed=embed, ephemeral=True)
            await asyncio.sleep(duracao)
            cog.echo_mode[membro.id] = False
            cog.echo_channel.pop(membro.id, None)
            print(f"[ECO] Desativado para {membro}")
        except ValueError:
            await interaction.response.send_message("❌ ID ou duração inválida!", ephemeral=True)
        except Exception as e:
            print(f"[ECO ERROR] {e}")
            try:
                await interaction.followup.send(f"❌ Erro: {e}", ephemeral=True)
            except:
                pass

class CastigoAleatorioModal(discord.ui.Modal):
    def __init__(self):
        super().__init__(title="Castigo Aleatório")
        self.membro = discord.ui.TextInput(label="ID", max_length=20)
        self.add_item(self.membro)
    
    async def on_submit(self, interaction: discord.Interaction):
        try:
            membro = interaction.guild.get_member(int(self.membro.value))
            if not membro: await interaction.response.send_message("❌ Não encontrado!", ephemeral=True); return
            tipo = random.choice(["timeout", "nickname"])
            if tipo == "timeout":
                await membro.timeout(timedelta(seconds=30))
                embed = discord.Embed(title="🎲 CASTIGO", description=f"{membro.mention}: Timeout 30s!", color=discord.Color.red())
            else:
                nomes = ["Abacaxi", "Frango", "Pinguim"]
                novo_nome = random.choice(nomes)
                await membro.edit(nick=novo_nome)
                embed = discord.Embed(title="🎲 CASTIGO", description=f"{membro.mention}: {novo_nome}!", color=discord.Color.red())
                await asyncio.sleep(30)
                await membro.edit(nick=None)
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except: await interaction.response.send_message("❌ Erro!", ephemeral=True)

class PalavrasBloquadasModal(discord.ui.Modal):
    def __init__(self, view):
        super().__init__(title="Palavras Bloqueadas")
        self.view = view
        self.palavra = discord.ui.TextInput(label="Palavra a bloquear", max_length=50)
        self.add_item(self.palavra)
    
    async def on_submit(self, interaction: discord.Interaction):
        palavra = self.palavra.value.lower()
        if palavra not in self.view.blocked_words:
            self.view.blocked_words.append(palavra)
        embed = discord.Embed(title="✅ Palavra Bloqueada", description=f"'{palavra}' foi adicionada", color=discord.Color.green())
        await interaction.response.send_message(embed=embed, ephemeral=True)

class NotaSecretaModal(discord.ui.Modal):
    def __init__(self, view):
        super().__init__(title="Nota Secreta")
        self.view = view
        self.membro = discord.ui.TextInput(label="ID do Membro", max_length=20)
        self.nota = discord.ui.TextInput(label="Nota", style=discord.TextStyle.paragraph, max_length=500)
        self.add_item(self.membro)
        self.add_item(self.nota)
    
    async def on_submit(self, interaction: discord.Interaction):
        try:
            membro_id = self.membro.value
            self.view.member_notes[membro_id] = self.nota.value
            embed = discord.Embed(title="📝 Nota Criada", description=f"Nota sobre {membro_id} salva!", color=discord.Color.blue())
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except:
            await interaction.response.send_message("❌ Erro!", ephemeral=True)

class CorEmbedModal(discord.ui.Modal):
    def __init__(self, view):
        super().__init__(title="Cor Embed")
        self.view = view
        self.cor = discord.ui.TextInput(label="Código HEX (ex: ff5733)", max_length=6)
        self.add_item(self.cor)
    
    async def on_submit(self, interaction: discord.Interaction):
        try:
            hex_color = self.cor.value.strip('#')
            self.view.embed_color = discord.Color(int(hex_color, 16))
            embed = discord.Embed(title="🎨 Cor Alterada", color=self.view.embed_color)
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except:
            await interaction.response.send_message("❌ Cor inválida!", ephemeral=True)

class IconeBotModal(discord.ui.Modal):
    def __init__(self, bot):
        super().__init__(title="Ícone Bot")
        self.bot = bot
        self.url = discord.ui.TextInput(label="URL da imagem", max_length=255)
        self.add_item(self.url)
    
    async def on_submit(self, interaction: discord.Interaction):
        embed = discord.Embed(title="🖼 Ícone", description=f"URL salva: {self.url.value}", color=discord.Color.blue())
        await interaction.response.send_message(embed=embed, ephemeral=True)

class MsgAutomaticaModal(discord.ui.Modal):
    def __init__(self, view):
        super().__init__(title="Msg Automática")
        self.view = view
        self.tipo = discord.ui.TextInput(label="Tipo (entrada/saída)", max_length=10)
        self.msg = discord.ui.TextInput(label="Mensagem", style=discord.TextStyle.paragraph, max_length=500)
        self.add_item(self.tipo)
        self.add_item(self.msg)
    
    async def on_submit(self, interaction: discord.Interaction):
        self.view.auto_messages[self.tipo.value] = self.msg.value
        embed = discord.Embed(title="💬 Msg Automática", description="Mensagem salva!", color=discord.Color.green())
        await interaction.response.send_message(embed=embed, ephemeral=True)

class LembreteModal(discord.ui.Modal):
    def __init__(self):
        super().__init__(title="Criar Lembrete")
        self.mensagem = discord.ui.TextInput(label="Mensagem do lembrete", max_length=200)
        self.add_item(self.mensagem)
    
    async def on_submit(self, interaction: discord.Interaction):
        embed = discord.Embed(title="📅 Lembrete Criado", description=self.mensagem.value, color=discord.Color.blue())
        await interaction.response.send_message(embed=embed, ephemeral=True)
