import discord
from discord.ext import commands
from datetime import datetime

class Missoes(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(name='missoes', aliases=['quests'])
    async def missoes(self, ctx):
        """Ver suas missoes ativas"""
        user_id = str(ctx.author.id)
        self.bot.db.ensure_user_exists(user_id)
        
        conn = self.bot.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT m.*, mp.current_progress, mp.completed, mp.claimed
            FROM missoes m
            LEFT JOIN missoes_progresso mp ON m.mission_id = mp.mission_id AND mp.user_id = ?
        """, (user_id,))
        
        missions = cursor.fetchall()
        conn.close()
        
        embed = discord.Embed(
            title="Suas Missoes",
            color=discord.Color.blue()
        )
        
        for mission in missions:
            progress = mission['current_progress'] or 0
            target = mission['target_value']
            completed = mission['completed'] == 1 if mission['completed'] else False
            claimed = mission['claimed'] == 1 if mission['claimed'] else False
            
            progress_bar = self.create_progress_bar(progress, target)
            
            if claimed:
                status = "Concluida e Coletada"
            elif completed:
                status = "Pronta para coletar!"
            else:
                status = f"{progress}/{target}"
            
            # Lógica para desbloqueio de profissões secretas na coleta
            if completed and not claimed:
                if mission['title'] == 'O Caminho das Sombras':
                    cursor.execute("INSERT OR IGNORE INTO conquistas_usuario (user_id, achievement_id, earned_at) VALUES (?, ?, ?)",
                                   (user_id, "unlock_ladrao", datetime.now().isoformat()))
                    try:
                        user = self.bot.get_user(int(user_id))
                        if user: await user.send("🕵️ **Profissão Desbloqueada:** Você agora tem acesso à profissão de **Ladrão**! Use `!escolher ladrao` para começar.")
                    except: pass
                elif mission['title'] == 'O Toque do Silêncio':
                    cursor.execute("INSERT OR IGNORE INTO conquistas_usuario (user_id, achievement_id, earned_at) VALUES (?, ?, ?)",
                                   (user_id, "unlock_assassino", datetime.now().isoformat()))
                    try:
                        user = self.bot.get_user(int(user_id))
                        if user: await user.send("🔪 **Profissão Desbloqueada:** Você agora tem acesso à profissão de **Assassino**! Use `!escolher assassino` para começar.")
                    except: pass

            reward_text = f"{mission['reward_value']:,} "
            reward_text += "XP" if mission['reward_type'] == 'xp' else "moedas"
            
            embed.add_field(
                name=f"{'✅' if claimed else '🎯' if completed else '📋'} {mission['title']}",
                value=f"{mission['description']}\n{progress_bar}\n**Status:** {status}\n**Recompensa:** {reward_text}",
                inline=False
            )
        
        embed.set_footer(text="Use !atualizar para atualizar progresso | !coletar para coletar recompensas")
        
        await ctx.send(embed=embed)
    
    def create_progress_bar(self, current: int, target: int, length: int = 10) -> str:
        percentage = min(current / target * 100, 100) if target > 0 else 0
        filled = int(percentage / 100 * length)
        empty = length - filled
        bar = '█' * filled + '░' * empty
        return f"`{bar}` {percentage:.0f}%"
    
    @commands.command(name='atualizar', aliases=['update', 'refresh'])
    async def atualizar(self, ctx):
        """Atualizar progresso de todas as missoes"""
        user_id = str(ctx.author.id)
        self.bot.db.ensure_user_exists(user_id)
        
        conn = self.bot.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT messages, commands_used FROM usuarios WHERE user_id = ?", (user_id,))
        user_stats = cursor.fetchone()
        
        cursor.execute("SELECT coins FROM economia WHERE user_id = ?", (user_id,))
        economy = cursor.fetchone()
        
        cursor.execute("SELECT COUNT(*) as count FROM pets WHERE user_id = ?", (user_id,))
        pets_count = cursor.fetchone()['count']
        
        updates = {
            'messages': user_stats['messages'] or 0,
            'commands': user_stats['commands_used'] or 0,
            'coins_total': economy['coins'] or 0,
            'pets_total': pets_count
        }
        
        updated_missions = []
        
        for mission_type, current_value in updates.items():
            cursor.execute("""
                SELECT m.mission_id, m.title, m.target_value
                FROM missoes m
                WHERE m.mission_type = ?
            """, (mission_type,))
            
            missions = cursor.fetchall()
            
            for mission in missions:
                cursor.execute("""
                    SELECT * FROM missoes_progresso 
                    WHERE user_id = ? AND mission_id = ?
                """, (user_id, mission['mission_id']))
                
                progress = cursor.fetchone()
                
                if progress:
                    old_progress = progress['current_progress'] or 0
                    if current_value != old_progress:
                        completed = 1 if current_value >= mission['target_value'] else 0
                        cursor.execute("""
                            UPDATE missoes_progresso 
                            SET current_progress = ?, completed = ?, completed_at = ?
                            WHERE user_id = ? AND mission_id = ?
                        """, (current_value, completed, 
                              datetime.now().isoformat() if completed else None,
                              user_id, mission['mission_id']))
                        updated_missions.append(mission['title'])
                else:
                    completed = 1 if current_value >= mission['target_value'] else 0
                    cursor.execute("""
                        INSERT INTO missoes_progresso (user_id, mission_id, current_progress, completed, started_at, completed_at)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (user_id, mission['mission_id'], current_value, completed,
                          datetime.now().isoformat(),
                          datetime.now().isoformat() if completed else None))
                    updated_missions.append(mission['title'])
        
        conn.commit()
        conn.close()
        
        if updated_missions:
            embed = discord.Embed(
                title="Missoes Atualizadas!",
                description=f"**{len(updated_missions)}** missoes foram atualizadas:\n" + 
                           "\n".join([f"• {m}" for m in updated_missions]),
                color=discord.Color.green()
            )
        else:
            embed = discord.Embed(
                title="Missoes Atualizadas!",
                description="Todas as missoes ja estavam atualizadas.",
                color=discord.Color.blue()
            )
        
        embed.set_footer(text="Use !missoes para ver o progresso")
        
        await ctx.send(embed=embed)

    @commands.command(name='diariomissao', aliases=['dailyquest'])
    async def diariomissao(self, ctx):
        """Ver uma dica sobre as missões do dia"""
        dicas = [
            "Hoje o dia está bom para trabalhar!",
            "Os pets estão sentindo sua falta, cuide deles.",
            "Interagir com amigos aumenta sua influência social.",
            "Economize suas moedas para grandes conquistas."
        ]
        await ctx.send(f"📜 **Dica do Dia:** {random.choice(dicas)}")
    
    @commands.command(name='coletar', aliases=['claim', 'collect'])
    async def coletar(self, ctx):
        """Coletar recompensas de todas as missoes completadas"""
        user_id = str(ctx.author.id)
        self.bot.db.ensure_user_exists(user_id)
        
        conn = self.bot.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT m.*, mp.progress_id
            FROM missoes m
            JOIN missoes_progresso mp ON m.mission_id = mp.mission_id
            WHERE mp.user_id = ? AND mp.completed = 1 AND (mp.claimed = 0 OR mp.claimed IS NULL)
        """, (user_id,))
        
        claimable = cursor.fetchall()
        
        if not claimable:
            await ctx.send("Voce nao tem missoes completadas para coletar!")
            conn.close()
            return
        
        total_xp = 0
        total_coins = 0
        claimed_missions = []
        
        for mission in claimable:
            if mission['reward_type'] == 'xp':
                total_xp += mission['reward_value']
            else:
                total_coins += mission['reward_value']
            
            claimed_missions.append(mission['title'])
            
            cursor.execute("""
                UPDATE missoes_progresso 
                SET claimed = 1
                WHERE progress_id = ?
            """, (mission['progress_id'],))
        
        if total_xp > 0:
            cursor.execute("""
                UPDATE usuarios SET xp = xp + ? WHERE user_id = ?
            """, (total_xp, user_id))
        
        if total_coins > 0:
            cursor.execute("""
                UPDATE economia SET coins = coins + ?, total_earned = total_earned + ? WHERE user_id = ?
            """, (total_coins, total_coins, user_id))
        
        conn.commit()
        conn.close()
        
        embed = discord.Embed(
            title="Recompensas Coletadas!",
            description=f"**{len(claimed_missions)}** missoes completadas:\n" +
                       "\n".join([f"✅ {m}" for m in claimed_missions]),
            color=discord.Color.gold()
        )
        
        rewards_text = ""
        if total_xp > 0:
            rewards_text += f"**+{total_xp:,}** XP\n"
        if total_coins > 0:
            rewards_text += f"**+{total_coins:,}** moedas"
        
        if rewards_text:
            embed.add_field(
                name="Total de Recompensas",
                value=rewards_text,
                inline=False
            )
        
        await ctx.send(embed=embed)

    @commands.command(name='convidar-coop')
    async def convidar_coop(self, ctx, parceiro: discord.Member, tipo: str, valor: int):
        """Convidar alguém para uma missão cooperativa (mensagens, comandos)"""
        if parceiro.id == ctx.author.id: return await ctx.send("Você não pode convidar a si mesmo!")
        
        user_id = str(ctx.author.id)
        partner_id = str(parceiro.id)
        
        conn = self.bot.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO missoes_coop (leader_id, partner_id, mission_type, target_value) VALUES (?, ?, ?, ?)",
                       (user_id, partner_id, tipo, valor))
        conn.commit()
        conn.close()
        await ctx.send(f"🤝 {ctx.author.mention} convidou {parceiro.mention} para uma missão cooperativa de **{valor} {tipo}**!")

    @commands.command(name='missoes-coop')
    async def missoes_coop_list(self, ctx):
        """Ver suas missões cooperativas ativas"""
        user_id = str(ctx.author.id)
        conn = self.bot.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM missoes_coop WHERE (leader_id = ? OR partner_id = ?) AND active = 1", (user_id, user_id))
        coops = cursor.fetchall()
        conn.close()
        
        if not coops: return await ctx.send("Você não tem missões cooperativas ativas.")
        
        embed = discord.Embed(title="🤝 Missões Cooperativas", color=discord.Color.teal())
        for c in coops:
            parceiro_id = c['partner_id'] if c['leader_id'] == user_id else c['leader_id']
            parceiro = ctx.guild.get_member(int(parceiro_id))
            p_name = parceiro.display_name if parceiro else "Desconhecido"
            embed.add_field(name=f"Com {p_name}", value=f"Tipo: {c['mission_type']}\nProgresso: {c['current_value']}/{c['target_value']}", inline=False)
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Missoes(bot))
