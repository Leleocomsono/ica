import discord
from discord.ext import commands
import os
import logging
import asyncio
from datetime import datetime
from database.db_manager import DatabaseManager

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)

logger = logging.getLogger("DiscordBot")

DISCORD_TOKEN = os.environ.get("DISCORD_TOKEN", "")

if not DISCORD_TOKEN:
    logger.error("ERRO: Token do Discord nao encontrado!")
    logger.info("Configure a variavel de ambiente DISCORD_TOKEN")
    exit(1)

db = DatabaseManager()

IMMUNE_ROLE_ID = 1439782753007697973

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True

bot = commands.Bot(
    command_prefix='!',
    intents=intents,
    help_command=None,
    case_insensitive=True
)

bot.db = db

xp_cooldowns = {}

@bot.event
async def on_ready():
    logger.info(f"Bot conectado como {bot.user}!")
    logger.info(f"Bot ID: {bot.user.id}")
    logger.info(f"Conectado a {len(bot.guilds)} servidor(es)")
    
    for guild in bot.guilds:
        logger.info(f"   - {guild.name} (ID: {guild.id})")
    
    logger.info("=" * 60)
    logger.info("SISTEMAS ATIVOS:")
    logger.info("   - Sistema de Perfil e XP")
    logger.info("   - Sistema de Economia")
    logger.info("   - Sistema de Pets com Blind Box")
    logger.info("   - Sistema de Casamento")
    logger.info("   - Sistema de Profissoes")
    logger.info("   - Sistema de Missoes")
    logger.info("   - Sistema de Conquistas")
    logger.info("   - Sistema de Rankings")
    logger.info("   - Sistema de Mini-Games")
    logger.info("   - Sistema Social")
    logger.info("   - Sistema de Mercado P2P")
    logger.info("   - Sistema de Inventario")
    logger.info("   - Sistema de Administracao")
    logger.info("=" * 60)
    logger.info("Use !ajuda para ver todos os comandos")
    
    load_cooldowns_from_db()
    
    # Sincronizar slash commands com Discord
    try:
        synced = await bot.tree.sync()
        logger.info(f"✅ {len(synced)} slash command(s) sincronizado(s)")
    except Exception as e:
        logger.error(f"Erro ao sincronizar slash commands: {e}")
    
    await bot.change_presence(
        activity=discord.Game(name="!ajuda | Doot doot!")
    )

@bot.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return
    
    user_id = str(message.author.id)
    bot.db.ensure_user_exists(user_id)
    
    current_time = datetime.now().timestamp()
    last_xp_time = xp_cooldowns.get(user_id, 0)
    
    if current_time - last_xp_time >= 60:
        try:
            conn = bot.db.get_connection()
            cursor = conn.cursor()
            
            import random
            xp_gain = random.randint(5, 15)
            
            # Multiplicadores de XP por cargo
            xp_multipliers = {
                1455412884640104509: 2,  # Cargo 1
                1444792288122241024: 2,  # Cargo 2
                1443287009144737875: 3,  # Cargo 3
                1447060588826988645: 5   # Cargo 5x
            }
            
            # Verificar multiplicador do membro
            multiplier = 1
            for role in message.author.roles:
                if role.id in xp_multipliers:
                    multiplier = max(multiplier, xp_multipliers[role.id])
            
            xp_gain = xp_gain * multiplier
            
            cursor.execute("""
                SELECT xp, level FROM usuarios WHERE user_id = ?
            """, (user_id,))
            
            row = cursor.fetchone()
            old_xp = row['xp']
            old_level = row['level']
            new_xp = old_xp + xp_gain
            new_level = int((new_xp / 100) ** 0.5) + 1
            
            cursor.execute("""
                UPDATE usuarios 
                SET messages = messages + 1, xp = ?, level = ?, last_seen = ?
                WHERE user_id = ?
            """, (new_xp, new_level, datetime.now().isoformat(), user_id))
            
            conn.commit()
            conn.close()
            
            if new_level > old_level:
                await check_achievements(user_id, "level", new_level)
                await send_level_notification(message.author, old_level, new_level, user_id)
            
            await update_mission_progress(user_id, "messages", 1)
            xp_cooldowns[user_id] = current_time
        except Exception as e:
            logger.error(f"Erro ao atualizar mensagens: {e}")
    
    await bot.process_commands(message)

@bot.event
async def on_command_completion(ctx):
    user_id = str(ctx.author.id)
    bot.db.ensure_user_exists(user_id)
    
    conn = bot.db.get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        UPDATE usuarios 
        SET commands_used = commands_used + 1
        WHERE user_id = ?
    """, (user_id,))
    
    if ctx.command:
        cursor.execute("""
            INSERT OR REPLACE INTO command_cooldowns (user_id, command_name, last_used)
            VALUES (?, ?, ?)
        """, (user_id, ctx.command.name, datetime.now().isoformat()))
    
    conn.commit()
    conn.close()
    
    await update_mission_progress(user_id, "commands", 1)

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandInvokeError):
        error = error.original
    
    if isinstance(error, commands.CommandOnCooldown):
        has_immune_role = any(role.id == IMMUNE_ROLE_ID for role in ctx.author.roles)
        if has_immune_role:
            ctx.command.reset_cooldown(ctx)
            await bot.invoke(ctx)
        else:
            retry_after = check_persistent_cooldown(str(ctx.author.id), ctx.command.name, error)
            minutes = int(retry_after // 60)
            await ctx.send(f"Aguarde {minutes} minuto(s) para usar este comando novamente.")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"Argumento faltando! Use `!ajuda {ctx.command}` para ver como usar.")
    elif isinstance(error, commands.CommandNotFound):
        pass
    elif isinstance(error, commands.MemberNotFound):
        await ctx.send("Membro nao encontrado! Certifique-se de mencionar corretamente.")
    elif isinstance(error, commands.BadArgument):
        await ctx.send(f"Argumento invalido! Use `!ajuda {ctx.command}` para ver como usar.")
    elif isinstance(error, commands.MissingPermissions):
        await ctx.send("Voce nao tem permissao para usar este comando!")
    elif isinstance(error, commands.BotMissingPermissions):
        await ctx.send("Eu nao tenho permissao para executar esta acao!")
    elif isinstance(error, commands.CheckFailure):
        pass
    else:
        logger.error(f"Erro no comando '{ctx.command}': {error}", exc_info=True)
        try:
            await ctx.send("Ocorreu um erro ao executar este comando.")
        except:
            pass

async def update_mission_progress(user_id: str, mission_type: str, progress: int):
    try:
        conn = bot.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT m.mission_id, m.target_value, mp.current_progress, mp.claimed
            FROM missoes m
            LEFT JOIN missoes_progresso mp ON m.mission_id = mp.mission_id AND mp.user_id = ?
            WHERE m.mission_type = ? AND (mp.claimed IS NULL OR mp.claimed = 0)
        """, (user_id, mission_type))
        
        for row in cursor.fetchall():
            mission_id = row['mission_id']
            target = row['target_value']
            current = row['current_progress'] if row['current_progress'] else 0
            
            if current is None or row['current_progress'] is None:
                cursor.execute("""
                    INSERT OR REPLACE INTO missoes_progresso (user_id, mission_id, current_progress, started_at)
                    VALUES (?, ?, ?, ?)
                """, (user_id, mission_id, progress, datetime.now().isoformat()))
            else:
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
        logger.error(f"Erro ao atualizar progresso de missao: {e}")

def load_cooldowns_from_db():
    try:
        conn = bot.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT user_id, command_name, last_used FROM command_cooldowns")
        cooldowns = cursor.fetchall()
        conn.close()
        
        for row in cooldowns:
            last_used = datetime.fromisoformat(row['last_used'])
            elapsed = (datetime.now() - last_used).total_seconds()
            
            if elapsed < 86400:
                try:
                    command = bot.get_command(row['command_name'])
                    if command and hasattr(command, '_cooldowns'):
                        user_id = int(row['user_id'])
                        bucket = command._cooldowns.get_bucket(discord.utils.get(bot.get_all_members(), id=user_id))
                        if bucket:
                            bucket._last.append(last_used.timestamp())
                except:
                    pass
    except Exception as e:
        logger.error(f"Erro ao carregar cooldowns do DB: {e}")

def check_persistent_cooldown(user_id: str, command_name: str, error) -> float:
    try:
        conn = bot.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT last_used FROM command_cooldowns 
            WHERE user_id = ? AND command_name = ?
        """, (user_id, command_name))
        
        data = cursor.fetchone()
        conn.close()
        
        if data:
            last_used = datetime.fromisoformat(data['last_used'])
            elapsed = (datetime.now() - last_used).total_seconds()
            
            if elapsed < error.retry_after:
                return error.retry_after - elapsed
        
        return error.retry_after
    except:
        return error.retry_after

LEVEL_ROLES = {
    5: 1446309179844464782,
    10: 1446309162073198673,
    20: 1446309146520719480,
    40: 1446309124638900285,
    80: 1446309085644587011,
    100: 1446309052660580352
}

async def send_level_notification(member: discord.Member, old_level: int, new_level: int, user_id: str):
    try:
        from datetime import timedelta
        
        NOTIFICATION_CHANNEL_ID = 1443354796517228665
        
        conn = bot.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM level_notifications WHERE user_id = ?
        """, (user_id,))
        notif_data = cursor.fetchone()
        
        if notif_data is None:
            cursor.execute("""
                INSERT INTO level_notifications (user_id, last_notified_level, last_notification_time, mention_disabled)
                VALUES (?, ?, ?, 0)
            """, (user_id, 0, datetime.now().isoformat()))
            conn.commit()
            cursor.execute("""
                SELECT * FROM level_notifications WHERE user_id = ?
            """, (user_id,))
            notif_data = cursor.fetchone()
        
        last_time_str = notif_data['last_notification_time']
        mention_disabled = notif_data['mention_disabled']
        
        should_notify = False
        
        if new_level % 5 == 0 and old_level < new_level:
            last_time = datetime.fromisoformat(last_time_str) if last_time_str else datetime.now() - timedelta(hours=11)
            current_time = datetime.now()
            
            if current_time - last_time >= timedelta(hours=10):
                should_notify = True
                cursor.execute("""
                    UPDATE level_notifications 
                    SET last_notified_level = ?, last_notification_time = ?
                    WHERE user_id = ?
                """, (new_level, current_time.isoformat(), user_id))
                conn.commit()
        
        conn.close()
        
        earned_role = None
        try:
            guild = member.guild
            
            highest_unlocked_level = None
            for lvl in sorted(LEVEL_ROLES.keys(), reverse=True):
                if new_level >= lvl and old_level < lvl:
                    highest_unlocked_level = lvl
                    break
            
            if highest_unlocked_level is None:
                for lvl in sorted(LEVEL_ROLES.keys(), reverse=True):
                    if new_level >= lvl:
                        highest_unlocked_level = lvl
                        break
            
            if highest_unlocked_level:
                new_role_id = LEVEL_ROLES[highest_unlocked_level]
                new_role = guild.get_role(new_role_id)
                
                if new_role and new_role not in member.roles:
                    previous_level_roles = []
                    for lvl, role_id in LEVEL_ROLES.items():
                        if lvl < highest_unlocked_level:
                            role = guild.get_role(role_id)
                            if role and role in member.roles:
                                previous_level_roles.append(role)
                    
                    if previous_level_roles:
                        await member.remove_roles(*previous_level_roles, reason="Level up - removendo cargo anterior")
                    
                    await member.add_roles(new_role, reason=f"Atingiu nivel {highest_unlocked_level}")
                    earned_role = new_role
        except Exception as e:
            logger.error(f"Erro ao dar cargo de nivel: {e}")
        
        if should_notify:
            try:
                channel = bot.get_channel(NOTIFICATION_CHANNEL_ID)
                
                if not channel:
                    return
                
                if not mention_disabled:
                    content_message = f"_ _⠀⠀  ⠀⠀\n_ _⠀⠀  ⠀⠀{member.mention} s__ubi__u de nível 　　♡ <:smt_plantinhas:1444153646672773253>\n_ _⠀⠀  ⠀⠀"
                else:
                    content_message = f"_ _⠀⠀  ⠀⠀\n_ _⠀⠀  ⠀⠀{member.name} s__ubi__u de nível 　　♡ <:smt_plantinhas:1444153646672773253>\n_ _⠀⠀  ⠀⠀"
                
                if earned_role:
                    role_display = earned_role.mention if not mention_disabled else f"**{earned_role.name}**"
                    description = f"""_ _
_ _⠀⠀  ⠀⠀◜　parabéns⠀﹒{member.name}⠀　！⠀◞
_ _⠀⠀⠀    ᵔᴗᵔ　parece que você avançou　
_ _⠀⠀⠀  　．⠀para o nível {new_level}　<a:smt_controle:1446304645931864235> ⠀  ⠀⌒⌒ 
_ _⠀⠀  　
_ _⠀⠀  　⠀⠀  　◞ ◟ 𑁬 uau! parece que você 
_ _⠀⠀  　⠀⠀  　conquistou o cargo 
_ _⠀⠀  　⠀⠀  　{role_display} !  ⠀  　<a:smt_link:1446307245502763160>
_ _⠀⠀  　⠀"""
                else:
                    description = f"""_ _
_ _⠀⠀  ⠀⠀◜　parabéns⠀﹒{member.name}⠀　！⠀◞
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
                
                await channel.send(content=content_message, embed=embed)
            except Exception as e:
                logger.error(f"Erro ao enviar mensagem de level up: {e}")
    except Exception as e:
        logger.error(f"Erro ao enviar notificacao de level: {e}")

async def check_achievements(user_id: str, achievement_type: str, current_value: int):
    try:
        conn = bot.db.get_connection()
        cursor = conn.cursor()
        
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
            cursor.execute("""
                INSERT INTO conquistas_usuario (user_id, achievement_id, unlocked_at)
                VALUES (?, ?, ?)
            """, (user_id, row['achievement_id'], datetime.now().isoformat()))
            
            if row['reward_xp'] > 0:
                cursor.execute("""
                    UPDATE usuarios SET xp = xp + ? WHERE user_id = ?
                """, (row['reward_xp'], user_id))
            
            if row['reward_coins'] > 0:
                cursor.execute("""
                    UPDATE economia SET coins = coins + ? WHERE user_id = ?
                """, (row['reward_coins'], user_id))
            
            logger.info(f"Conquista desbloqueada: {row['name']} para usuario {user_id}")
        
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"Erro ao verificar conquistas: {e}")

BOOST_SOURCE_CHANNEL = 1439470990454296718
BOOST_ANNOUNCE_CHANNEL = 1440179826924195900
REPEAT_BOOSTER_ROLE = 1447060588826988645

@bot.event
async def on_member_update(before: discord.Member, after: discord.Member):
    if before.premium_since is None and after.premium_since is not None:
        await handle_boost(after)

async def handle_boost(member: discord.Member):
    try:
        user_id = str(member.id)
        current_time = datetime.now()
        
        conn = bot.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT boosted_at FROM boost_tracking 
            WHERE user_id = ? 
            ORDER BY boosted_at DESC LIMIT 1
        """, (user_id,))
        last_boost = cursor.fetchone()
        
        is_repeat_booster = False
        if last_boost:
            last_boost_time = datetime.fromisoformat(last_boost['boosted_at'])
            days_diff = (current_time - last_boost_time).days
            if days_diff <= 6:
                is_repeat_booster = True
        
        cursor.execute("""
            INSERT INTO boost_tracking (user_id, boosted_at)
            VALUES (?, ?)
        """, (user_id, current_time.isoformat()))
        conn.commit()
        conn.close()
        
        if is_repeat_booster:
            role = member.guild.get_role(REPEAT_BOOSTER_ROLE)
            if role and role not in member.roles:
                try:
                    await member.add_roles(role)
                    logger.info(f"Cargo de repeat booster adicionado a {member.name}")
                except Exception as e:
                    logger.error(f"Erro ao adicionar cargo de repeat booster: {e}")
        
        announce_channel = bot.get_channel(BOOST_ANNOUNCE_CHANNEL)
        if announce_channel:
            content_message = f"""_ _⠀⠀  ⠀⠀
_ _⠀⠀  ⠀⠀{member.mention} acabou de im__pulsio__nar　　꒧𓂃 
_ _⠀⠀  ⠀⠀o servidor ⠀  ⠀ 지 𔘓 민 
_ _⠀⠀  ⠀⠀"""
            
            description = f"""_ _
_ _⠀⠀  ⠀⠀◜　obrigado⠀﹒{member.name}⠀　！⠀◞
_ _⠀⠀⠀    𐃆　agradecemos pelo seu　
_ _⠀⠀⠀  　．⠀apoio　 ⠀  ⠀﹒ノᩚ﹙◞◟꒽᪲﹚
_ _⠀⠀  　⠀  ⠀  ⠀   ︶⊹︶︶୨୧︶︶⊹︶
_ _⠀⠀⠀  　
_ _⠀⠀  　⠀⠀  　➜﹕ caso queira pedir
_ _⠀⠀  　⠀⠀  　algum dos benefícios
_ _⠀⠀  　⠀⠀  　por favor se dirija ao   ⠀  　
_ _⠀⠀  　⠀⠀  　devido chat !   ⠀  　<a:smt_redheart:1447653701903716463>
_ _⠀⠀  　⠀⠀  　"""
            
            embed = discord.Embed(
                description=description,
                color=discord.Color.from_str("#631515"),
                timestamp=current_time
            )
          
            embed.set_image(url="https://media.discordapp.net/attachments/1439492690948521994/1447655698677760244/tumblr_b09504ae2c7f4b62005acbb8e21cc91f_422fe46f_500-ezgif.com-webp-to-gif-converter.gif?ex=693869ee&is=6937186e&hm=9fac5f6d8570aa62499c4719e251f4c67994d53996fdbbd0889ea5409bfa4652&=&width=450&height=217")
            embed.set_footer(text="﹐⠀ ⠀  ⠀　     ⠀⏝︰﹒⠀   　⠀ ⠀▧！@ house smt ﹑✿")
            
            await announce_channel.send(content=content_message, embed=embed)
            logger.info(f"Boost de {member.name} anunciado no canal")
    except Exception as e:
        logger.error(f"Erro ao processar boost: {e}")

async def load_cogs():
    # Cogs para carregar
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
        'cogs.administracao',
        'cogs.painel_controle',
        'cogs.tts'
    ]
    
    for cog in cogs_list:
        try:
            await bot.load_extension(cog)
            logger.info(f"Cog carregado: {cog}")
        except Exception as e:
            logger.error(f"Erro ao carregar {cog}: {e}")

async def main():
    async with bot:
        await load_cogs()
        await bot.start(DISCORD_TOKEN)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot desligado pelo usuario")
    except Exception as e:
        logger.error(f"Erro fatal: {e}", exc_info=True)
