#===============================================================================
# BOT DISCORD COMPLETO - PYTHON
# 
# CONFIGURAÇÃO DO TOKEN:
# Defina a variável de ambiente DISCORD_TOKEN com o token do seu bot
# ou insira diretamente abaixo (não recomendado para produção)
#===============================================================================

import discord
from discord.ext import commands
import os
import logging
import asyncio
from datetime import datetime
from database.db_manager import DatabaseManager

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)

logger = logging.getLogger("DiscordBot")

#===============================================================================
# INSIRA SEU TOKEN AQUI (ou use variável de ambiente DISCORD_TOKEN)
#===============================================================================
DISCORD_TOKEN = os.environ.get("DISCORD_TOKEN", "")

if not DISCORD_TOKEN:
    logger.error("❌ ERRO: Token do Discord não encontrado!")
    logger.info("📝 Configure a variável de ambiente DISCORD_TOKEN")
    logger.info("   ou insira o token diretamente no arquivo main.py")
    exit(1)

# Inicializar banco de dados
db = DatabaseManager()

# Configurar intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True

# Criar bot
bot = commands.Bot(
    command_prefix='!',
    intents=intents,
    help_command=None,
    case_insensitive=True
)

# Armazenar referência ao database no bot
bot.db = db

# Cooldowns para XP (evitar spam)
xp_cooldowns = {}

@bot.event
async def on_ready():
    """Evento quando o bot fica online"""
    logger.info(f"✅ Bot conectado como {bot.user}!")
    logger.info(f"📊 Bot ID: {bot.user.id}")
    logger.info(f"🌐 Conectado a {len(bot.guilds)} servidor(es)")
    
    for guild in bot.guilds:
        logger.info(f"   • {guild.name} (ID: {guild.id})")
    
    logger.info("=" * 60)
    logger.info("🎮 SISTEMAS ATIVOS:")
    logger.info("   • Sistema de Perfil e XP")
    logger.info("   • Sistema de Economia")
    logger.info("   • Sistema de Pets Completo")
    logger.info("   • Sistema de Casamento")
    logger.info("   • Sistema de Profissões")
    logger.info("   • Sistema de Missões")
    logger.info("   • Sistema de Conquistas")
    logger.info("   • Sistema de Rankings")
    logger.info("   • Sistema de Mini-Games")
    logger.info("   • Sistema Social")
    logger.info("   • Sistema de Mercado P2P")
    logger.info("   • Sistema de Inventário")
    logger.info("   • Sistema de Administração")
    logger.info("=" * 60)
    logger.info("✨ Use !ajuda para ver todos os comandos")
    
    # Atualizar status do bot
    await bot.change_presence(
        activity=discord.Game(name="!ajuda | Sistema Completo")
    )

@bot.event
async def on_message(message: discord.Message):
    """Evento quando uma mensagem é enviada"""
    if message.author.bot:
        return
    
    user_id = str(message.author.id)
    
    # Garantir que o usuário existe
    bot.db.ensure_user_exists(user_id)
    
    # Sistema de XP com cooldown (1 mensagem por minuto ganha XP)
    current_time = datetime.now().timestamp()
    last_xp_time = xp_cooldowns.get(user_id, 0)
    
    if current_time - last_xp_time >= 60:
        conn = bot.db.get_connection()
        cursor = conn.cursor()
        
        # Atualizar mensagens
        cursor.execute("""
            UPDATE usuarios 
            SET messages = messages + 1, last_seen = ?
            WHERE user_id = ?
        """, (datetime.now().isoformat(), user_id))
        
        # Adicionar XP aleatório (5-15)
        import random
        xp_gain = random.randint(5, 15)
        
        cursor.execute("""
            SELECT xp, level FROM usuarios WHERE user_id = ?
        """, (user_id,))
        
        row = cursor.fetchone()
        old_xp = row['xp']
        old_level = row['level']
        new_xp = old_xp + xp_gain
        
        # Calcular novo nível
        new_level = int((new_xp / 100) ** 0.5) + 1
        
        cursor.execute("""
            UPDATE usuarios 
            SET xp = ?, level = ?
            WHERE user_id = ?
        """, (new_xp, new_level, user_id))
        
        conn.commit()
        
        # Verificar level up
        if new_level > old_level:
            try:
                await message.channel.send(
                    f"🎉 Parabéns {message.author.mention}! "
                    f"Você subiu para o **nível {new_level}**!"
                )
                # Verificar conquistas de nível
                await check_achievements(user_id, "level", new_level)
            except:
                pass
        
        # Atualizar progresso de missões (mensagens)
        await update_mission_progress(user_id, "messages", 1)
        
        conn.close()
        xp_cooldowns[user_id] = current_time
    
    await bot.process_commands(message)

@bot.event
async def on_command(ctx):
    """Evento quando um comando é usado"""
    user_id = str(ctx.author.id)
    bot.db.ensure_user_exists(user_id)
    
    conn = bot.db.get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        UPDATE usuarios 
        SET commands_used = commands_used + 1
        WHERE user_id = ?
    """, (user_id,))
    
    conn.commit()
    conn.close()
    
    # Atualizar progresso de missões (comandos)
    await update_mission_progress(user_id, "commands", 1)

@bot.event
async def on_command_error(ctx, error):
    """Tratamento de erros de comandos"""
    if isinstance(error, commands.CommandInvokeError):
        error = error.original
    
    if isinstance(error, commands.CommandOnCooldown):
        await ctx.send(f"⏰ Aguarde {error.retry_after:.1f}s para usar este comando novamente.")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"❌ Argumento faltando! Use `!ajuda` para ver como usar.")
    elif isinstance(error, commands.CommandNotFound):
        pass
    elif isinstance(error, commands.MemberNotFound):
        await ctx.send("❌ Membro não encontrado! Certifique-se de mencionar corretamente.")
    elif isinstance(error, commands.BadArgument):
        await ctx.send(f"❌ Argumento inválido! Use `!ajuda` para ver como usar.")
    elif isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ Você não tem permissão para usar este comando!")
    elif isinstance(error, commands.BotMissingPermissions):
        await ctx.send("❌ Eu não tenho permissão para executar esta ação!")
    else:
        logger.error(f"Erro no comando '{ctx.command}': {error}", exc_info=True)
        try:
            await ctx.send("❌ Ocorreu um erro ao executar este comando.")
        except:
            pass

async def update_mission_progress(user_id: str, mission_type: str, progress: int):
    """Atualizar progresso de missões"""
    try:
        conn = bot.db.get_connection()
        cursor = conn.cursor()
        
        # Buscar missões ativas deste tipo
        cursor.execute("""
            SELECT m.mission_id, m.target_value, mp.current_progress
            FROM missoes m
            LEFT JOIN missoes_progresso mp ON m.mission_id = mp.mission_id AND mp.user_id = ?
            WHERE m.mission_type = ? AND (mp.completed IS NULL OR mp.completed = 0)
        """, (user_id, mission_type))
        
        for row in cursor.fetchall():
            mission_id = row['mission_id']
            target = row['target_value']
            current = row['current_progress'] if row['current_progress'] else 0
            
            if current is None:
                # Iniciar missão
                cursor.execute("""
                    INSERT INTO missoes_progresso (user_id, mission_id, current_progress, started_at)
                    VALUES (?, ?, ?, ?)
                """, (user_id, mission_id, progress, datetime.now().isoformat()))
            else:
                # Atualizar progresso
                new_progress = current + progress
                completed = 1 if new_progress >= target else 0
                
                cursor.execute("""
                    UPDATE missoes_progresso
                    SET current_progress = ?, completed = ?, completed_at = ?
                    WHERE user_id = ? AND mission_id = ?
                """, (new_progress, completed, datetime.now().isoformat() if completed else None, user_id, mission_id))
        
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"Erro ao atualizar progresso de missão: {e}")

async def check_achievements(user_id: str, achievement_type: str, current_value: int):
    """Verificar e desbloquear conquistas"""
    try:
        conn = bot.db.get_connection()
        cursor = conn.cursor()
        
        # Buscar conquistas não desbloqueadas deste tipo
        cursor.execute("""
            SELECT a.achievement_id, a.name, a.reward_xp, a.reward_coins
            FROM conquistas a
            WHERE a.requirement_type = ? AND a.requirement_value <= ?
            AND NOT EXISTS (
                SELECT 1 FROM conquistas_usuario cu 
                WHERE cu.achievement_id = a.achievement_id AND cu.user_id = ?
            )
        """, (achievement_type, current_value, user_id))
        
        for row in cursor.fetchall():
            # Desbloquear conquista
            cursor.execute("""
                INSERT INTO conquistas_usuario (user_id, achievement_id, unlocked_at)
                VALUES (?, ?, ?)
            """, (user_id, row['achievement_id'], datetime.now().isoformat()))
            
            # Dar recompensas
            if row['reward_xp'] > 0:
                cursor.execute("""
                    UPDATE usuarios SET xp = xp + ? WHERE user_id = ?
                """, (row['reward_xp'], user_id))
            
            if row['reward_coins'] > 0:
                cursor.execute("""
                    UPDATE economia SET coins = coins + ? WHERE user_id = ?
                """, (row['reward_coins'], user_id))
            
            logger.info(f"🏆 Conquista desbloqueada: {row['name']} para usuário {user_id}")
        
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"Erro ao verificar conquistas: {e}")

async def load_cogs():
    """Carregar todos os cogs"""
    cogs_list = [
        'cogs.perfil',
        'cogs.economia',
        'cogs.pets',
        'cogs.casamento',
        'cogs.profissoes',
        'cogs.missoes',
        'cogs.conquistas',
        'cogs.ranking',
        'cogs.minigames',
        'cogs.social',
        'cogs.mercado',
        'cogs.inventario',
        'cogs.entretenimento',
        'cogs.utilidade',
        'cogs.administracao'
    ]
    
    for cog in cogs_list:
        try:
            await bot.load_extension(cog)
            logger.info(f"✅ Cog carregado: {cog}")
        except Exception as e:
            logger.error(f"❌ Erro ao carregar {cog}: {e}")

async def main():
    """Função principal para iniciar o bot"""
    async with bot:
        await load_cogs()
        await bot.start(DISCORD_TOKEN)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot desligado pelo usuário")
    except Exception as e:
        logger.error(f"Erro fatal: {e}", exc_info=True)
