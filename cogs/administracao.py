import discord
from discord.ext import commands
from datetime import datetime, timedelta

class Administracao(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.stick_messages = {}  # {channel_id: {"content": str, "last_message_id": int}}
        self._load_stick_messages()
    
    def _load_stick_messages(self):
        """Carrega mensagens fixadas do banco de dados"""
        try:
            conn = self.bot.db.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT channel_id, content, last_message_id FROM stick_messages")
            rows = cursor.fetchall()
            conn.close()
            
            for row in rows:
                self.stick_messages[int(row['channel_id'])] = {
                    "content": row['content'],
                    "last_message_id": int(row['last_message_id']) if row['last_message_id'] else None
                }
        except Exception as e:
            print(f"Erro ao carregar stick messages: {e}")
    
    def _save_stick_message(self, channel_id: int, content: str, last_message_id: int):
        """Salva uma mensagem fixada no banco de dados"""
        try:
            conn = self.bot.db.get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO stick_messages (channel_id, content, last_message_id, created_at)
                VALUES (?, ?, ?, ?)
            """, (str(channel_id), content, str(last_message_id), datetime.now().isoformat()))
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Erro ao salvar stick message: {e}")
    
    def _delete_stick_message(self, channel_id: int):
        """Remove uma mensagem fixada do banco de dados"""
        try:
            conn = self.bot.db.get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM stick_messages WHERE channel_id = ?", (str(channel_id),))
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Erro ao deletar stick message: {e}")
    
    @commands.command(name='addemoji', aliases=['addemote'])
    @commands.has_permissions(manage_emojis=True)
    async def addemoji(self, ctx, nome: str = None):
        """Adicionar emoji personalizado ao servidor (anexar imagem)"""
        if nome is None:
            embed = discord.Embed(
                title="❌ Uso Incorreto",
                description="Use: `!addemoji <nome>` e anexe a imagem",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        if not ctx.message.attachments:
            embed = discord.Embed(
                title="❌ Nenhum Anexo",
                description="Anexe uma imagem ao comando!",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return
        
        try:
            anexo = ctx.message.attachments[0]
            emoji_data = await anexo.read()
            
            emoji = await ctx.guild.create_custom_emoji(
                name=nome.replace(" ", "_"),
                image=emoji_data
            )
            
            embed = discord.Embed(
                title="✅ Emoji Adicionado",
                description=f"Emoji criado: {emoji} `{emoji.name}`",
                color=discord.Color.green()
            )
            
            await ctx.send(embed=embed)
        except discord.Forbidden:
            await ctx.send("❌ Nao tenho permissao para criar emojis!")
        except discord.HTTPException as e:
            await ctx.send(f"❌ Erro ao criar emoji: {str(e)}")
        except Exception as e:
            await ctx.send(f"❌ Erro: {str(e)}")
    
    @commands.command(name='limpar', aliases=['clear', 'purge'])
    @commands.has_permissions(manage_messages=True)
    async def limpar(self, ctx, quantidade: int = 10):
        """Limpar mensagens do canal"""
        if quantidade < 1 or quantidade > 100:
            await ctx.send("Quantidade deve ser entre 1 e 100!")
            return
        
        deleted = await ctx.channel.purge(limit=quantidade + 1)
        
        msg = await ctx.send(f"Limpei **{len(deleted) - 1}** mensagens!")
        await msg.delete(delay=3)
    
    @commands.command(name='kick', aliases=['expulsar'])
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx, member: discord.Member = None, *, motivo: str = "Sem motivo"):
        """Expulsar um membro"""
        if member is None:
            await ctx.send("Mencione um membro para expulsar!")
            return
        
        if member.top_role >= ctx.author.top_role:
            await ctx.send("Voce nao pode expulsar alguem com cargo igual ou superior!")
            return
        
        try:
            await member.kick(reason=f"{ctx.author}: {motivo}")
            
            embed = discord.Embed(
                title="Membro Expulso",
                description=f"{member.mention} foi expulso do servidor!",
                color=discord.Color.orange()
            )
            
            embed.add_field(name="Moderador", value=ctx.author.mention, inline=True)
            embed.add_field(name="Motivo", value=motivo, inline=True)
            
            await ctx.send(embed=embed)
        except discord.Forbidden:
            await ctx.send("Nao tenho permissao para expulsar este membro!")
    
    @commands.command(name='ban', aliases=['banir'])
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx, member: discord.Member = None, *, motivo: str = "Sem motivo"):
        """Banir um membro"""
        if member is None:
            await ctx.send("Mencione um membro para banir!")
            return
        
        if member.top_role >= ctx.author.top_role:
            await ctx.send("Voce nao pode banir alguem com cargo igual ou superior!")
            return
        
        try:
            await member.ban(reason=f"{ctx.author}: {motivo}")
            
            embed = discord.Embed(
                title="Membro Banido",
                description=f"{member.mention} foi banido do servidor!",
                color=discord.Color.red()
            )
            
            embed.add_field(name="Moderador", value=ctx.author.mention, inline=True)
            embed.add_field(name="Motivo", value=motivo, inline=True)
            
            await ctx.send(embed=embed)
        except discord.Forbidden:
            await ctx.send("Nao tenho permissao para banir este membro!")
    
    @commands.command(name='unban', aliases=['desbanir'])
    @commands.has_permissions(ban_members=True)
    async def unban(self, ctx, *, usuario: str = None):
        """Desbanir um usuario"""
        if usuario is None:
            await ctx.send("Especifique o usuario (nome#tag ou ID)!")
            return
        
        try:
            if usuario.isdigit():
                user = await self.bot.fetch_user(int(usuario))
            else:
                if '#' in usuario:
                    name, discriminator = usuario.rsplit('#', 1)
                else:
                    name = usuario
                    discriminator = None
                
                bans = [entry async for entry in ctx.guild.bans()]
                user = None
                
                for ban_entry in bans:
                    if ban_entry.user.name == name:
                        if discriminator is None or ban_entry.user.discriminator == discriminator:
                            user = ban_entry.user
                            break
            
            if user is None:
                await ctx.send("Usuario nao encontrado na lista de banidos!")
                return
            
            await ctx.guild.unban(user)
            
            embed = discord.Embed(
                title="Usuario Desbanido",
                description=f"{user.mention} foi desbanido do servidor!",
                color=discord.Color.green()
            )
            
            await ctx.send(embed=embed)
        except discord.NotFound:
            await ctx.send("Usuario nao esta banido ou nao existe!")
        except discord.Forbidden:
            await ctx.send("Nao tenho permissao para desbanir!")
    
    @commands.command(name='warn', aliases=['avisar'])
    @commands.has_permissions(kick_members=True)
    async def warn(self, ctx, member: discord.Member = None, *, motivo: str = "Sem motivo"):
        """Dar um aviso a um membro"""
        if member is None:
            await ctx.send("Mencione um membro para avisar!")
            return
        
        user_id = str(member.id)
        
        conn = self.bot.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO warns (user_id, guild_id, moderator_id, reason, warned_at)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, str(ctx.guild.id), str(ctx.author.id), motivo, datetime.now().isoformat()))
        
        cursor.execute("""
            SELECT COUNT(*) as count FROM warns 
            WHERE user_id = ? AND guild_id = ?
        """, (user_id, str(ctx.guild.id)))
        
        warn_count = cursor.fetchone()['count']
        
        conn.commit()
        conn.close()
        
        embed = discord.Embed(
            title="Aviso Aplicado",
            description=f"{member.mention} recebeu um aviso!",
            color=discord.Color.orange()
        )
        
        embed.add_field(name="Moderador", value=ctx.author.mention, inline=True)
        embed.add_field(name="Motivo", value=motivo, inline=True)
        embed.add_field(name="Total de avisos", value=str(warn_count), inline=True)
        
        await ctx.send(embed=embed)
        
        if warn_count >= 3:
            await ctx.send(f"Atencao: {member.mention} tem {warn_count} avisos!")
    
    @commands.command(name='avisos', aliases=['warns'])
    async def avisos(self, ctx, member: discord.Member = None):
        """Ver avisos de um membro"""
        member = member or ctx.author
        user_id = str(member.id)
        
        conn = self.bot.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM warns 
            WHERE user_id = ? AND guild_id = ?
            ORDER BY warned_at DESC
        """, (user_id, str(ctx.guild.id)))
        
        warns = cursor.fetchall()
        conn.close()
        
        embed = discord.Embed(
            title=f"Avisos de {member.display_name}",
            color=discord.Color.orange() if warns else discord.Color.green()
        )
        
        if not warns:
            embed.description = "Nenhum aviso registrado!"
        else:
            for i, warn in enumerate(warns[:10], 1):
                moderator = ctx.guild.get_member(int(warn['moderator_id']))
                mod_name = moderator.display_name if moderator else "Desconhecido"
                
                warned_at = datetime.fromisoformat(warn['warned_at']).strftime("%d/%m/%Y")
                
                embed.add_field(
                    name=f"Aviso #{i}",
                    value=f"**Motivo:** {warn['reason']}\n**Por:** {mod_name}\n**Data:** {warned_at}",
                    inline=False
                )
        
        embed.set_footer(text=f"Total: {len(warns)} avisos")
        
        await ctx.send(embed=embed)
    
    @commands.command(name='limparavisos', aliases=['clearwarns'])
    @commands.has_permissions(administrator=True)
    async def limparavisos(self, ctx, member: discord.Member = None):
        """Limpar todos os avisos de um membro"""
        if member is None:
            await ctx.send("Mencione um membro!")
            return
        
        user_id = str(member.id)
        
        conn = self.bot.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            DELETE FROM warns WHERE user_id = ? AND guild_id = ?
        """, (user_id, str(ctx.guild.id)))
        
        deleted = cursor.rowcount
        
        conn.commit()
        conn.close()
        
        embed = discord.Embed(
            title="Avisos Limpos",
            description=f"**{deleted}** avisos de {member.mention} foram removidos!",
            color=discord.Color.green()
        )
        
        await ctx.send(embed=embed)
    
    @commands.command(name='mute', aliases=['silenciar'])
    @commands.has_permissions(moderate_members=True)
    async def mute(self, ctx, member: discord.Member = None, tempo: str = "10m", *, motivo: str = "Sem motivo"):
        """Silenciar um membro temporariamente"""
        if member is None:
            await ctx.send("Mencione um membro!")
            return
        
        if member.top_role >= ctx.author.top_role:
            await ctx.send("Voce nao pode silenciar alguem com cargo igual ou superior!")
            return
        
        time_units = {'s': 1, 'm': 60, 'h': 3600, 'd': 86400}
        unit = tempo[-1].lower()
        
        if unit not in time_units:
            await ctx.send("Use: s (segundos), m (minutos), h (horas), d (dias)")
            return
        
        try:
            duration = int(tempo[:-1]) * time_units[unit]
        except ValueError:
            await ctx.send("Formato de tempo invalido!")
            return
        
        if duration > 2419200:
            await ctx.send("Tempo maximo: 28 dias!")
            return
        
        try:
            await member.timeout(timedelta(seconds=duration), reason=f"{ctx.author}: {motivo}")
            
            embed = discord.Embed(
                title="Membro Silenciado",
                description=f"{member.mention} foi silenciado por {tempo}!",
                color=discord.Color.orange()
            )
            
            embed.add_field(name="Moderador", value=ctx.author.mention, inline=True)
            embed.add_field(name="Motivo", value=motivo, inline=True)
            
            await ctx.send(embed=embed)
        except discord.Forbidden:
            await ctx.send("Nao tenho permissao para silenciar este membro!")
    
    @commands.command(name='unmute', aliases=['dessilenciar'])
    @commands.has_permissions(moderate_members=True)
    async def unmute(self, ctx, member: discord.Member = None):
        """Remover silenciamento de um membro"""
        if member is None:
            await ctx.send("Mencione um membro!")
            return
        
        try:
            await member.timeout(None)
            
            embed = discord.Embed(
                title="Silenciamento Removido",
                description=f"{member.mention} pode falar novamente!",
                color=discord.Color.green()
            )
            
            await ctx.send(embed=embed)
        except discord.Forbidden:
            await ctx.send("Nao tenho permissao para fazer isso!")
    
    @commands.command(name='slowmode', aliases=['lento'])
    @commands.has_permissions(manage_channels=True)
    async def slowmode(self, ctx, segundos: int = 0):
        """Definir modo lento no canal"""
        if segundos < 0 or segundos > 21600:
            await ctx.send("O tempo deve ser entre 0 e 21600 segundos (6 horas)!")
            return
        
        await ctx.channel.edit(slowmode_delay=segundos)
        
        if segundos == 0:
            await ctx.send("Modo lento desativado!")
        else:
            await ctx.send(f"Modo lento definido para **{segundos}** segundos!")
    
    @commands.command(name='lock', aliases=['trancar'])
    @commands.has_permissions(manage_channels=True)
    async def lock(self, ctx):
        """Trancar o canal"""
        overwrite = ctx.channel.overwrites_for(ctx.guild.default_role)
        overwrite.send_messages = False
        
        await ctx.channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)
        
        embed = discord.Embed(
            title="Canal Trancado",
            description="Este canal foi trancado por um moderador.",
            color=discord.Color.red()
        )
        
        await ctx.send(embed=embed)
    
    @commands.command(name='unlock', aliases=['destrancar'])
    @commands.has_permissions(manage_channels=True)
    async def unlock(self, ctx):
        """Destrancar o canal"""
        overwrite = ctx.channel.overwrites_for(ctx.guild.default_role)
        overwrite.send_messages = True
        
        await ctx.channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)
        
        embed = discord.Embed(
            title="Canal Destrancado",
            description="Este canal foi destrancado!",
            color=discord.Color.green()
        )
        
        await ctx.send(embed=embed)
    
    @commands.command(name='finalizar', aliases=['finish'])
    async def finalizar(self, ctx, member: discord.Member = None, *, info: str = None):
        """Finalizar um membro (Requer cargo especifico)"""
        REQUIRED_ROLE_ID = 1439486417289084969
        FINAL_ROLE_ID = 1443367621503353004
        ROLE_TO_REMOVE_ID = 1443793735082049536
        
        if member is None:
            await ctx.send("❌ Mencione um membro para finalizar!")
            return
        
        has_required_role = any(role.id == REQUIRED_ROLE_ID for role in ctx.author.roles)
        if not has_required_role:
            await ctx.send("❌ Voce nao tem permissao para usar este comando!")
            return
        
        try:
            # Lógica para alterar o apelido (nickname)
            if info:
                parts = info.split(' ', 1)
                if len(parts) >= 1:
                    emoji = parts[0]
                    personagem = parts[1] if len(parts) > 1 else ""
                    
                    if emoji and personagem:
                        new_nick = f"ৎ{emoji}୭ ⧽ {personagem}   ִ세"
                        try:
                            await member.edit(nick=new_nick)
                        except discord.Forbidden:
                            print(f"Sem permissao para mudar o nick de {member.name}")
                        except Exception as e:
                            print(f"Erro ao mudar nick: {e}")
            
            final_role = ctx.guild.get_role(FINAL_ROLE_ID)
            if final_role is None:
                await ctx.send("❌ Cargo de finalizacao nao encontrado no servidor!")
                return
            
            role_to_remove = ctx.guild.get_role(ROLE_TO_REMOVE_ID)
            if role_to_remove and role_to_remove in member.roles:
                await member.remove_roles(role_to_remove, reason="Membro finalizado")
            
            await member.add_roles(final_role)
            
            embed = discord.Embed(
                color=discord.Color(0xFF66CC)
            )
            
            embed.set_author(name="  ⸝⸝⸝⸝      𝕽aise 𝕬 𝕾̲u̲i̲l̲en !             𝅄‎          사ᦔ", icon_url="https://cdn.discordapp.com/attachments/1315873082904154153/1443097850341756998/41c9668878b889ebff92ced0b75ccb7e.jpg?ex=6927d51a&is=6926839a&hm=7317546b43c3abef8f0307fe81c625f2c18c95be984ce4d37203e7543abc020d&")
            embed.title = "⸻ ﹒ಲೆ   ◤𝗢ne 𝗟ast 𝗕eat﹒✿⁘ "
            embed.description = """"ೀ﹒✿ <a:smt_batom:1443260162159808594> 𝗢lá 𝗔ventureiro! 𝗣arece que falta pouco para você se juntar ao templo! 𝗔penas siga as instruções logo abaixo! 

︵݁ㅤ֪ㅤ⏜ㅤ֪ㅤ︵﹒౨𖹭̍ৎ﹒︵ㅤ֪ㅤ⏜݁ㅤ֪ㅤ︵
[ৎ୭⦙⦙ <a:smt_coracaocunt:1443350039190704278> ﹕𝗟eia 𝗔s 𝗥egras](https://discord.com/channels/1439470989372035177/1439475488723832936)
[ৎ୭⦙⦙ <a:smt_coracaocunt:1443350039190704278> ﹕𝗠oldes](https://discord.com/channels/1439470989372035177/1439850919922765904)
[ৎ୭⦙⦙ <a:smt_coracaocunt:1443350039190704278> ﹕𝗙eche 𝗦ua 𝗩aga](https://discord.com/channels/1439470989372035177/1439494774796193885)
[ৎ୭⦙⦙ <a:smt_coracaocunt:1443350039190704278> ﹕𝗙aça 𝗦eu 𝗥egistro](https://discord.com/channels/1439470989372035177/1439850675721867325)
[ৎ୭⦙⦙ <a:smt_coracaocunt:1443350039190704278> ﹕𝗘scolha 𝗦eus 𝗣ings](https://discord.com/channels/1439470989372035177/1439850689630306475)
[ৎ୭⦙⦙ <a:smt_coracaocunt:1443350039190704278> ﹕𝗦e 𝗔presente](https://discord.com/channels/1439470989372035177/1439850751110156330)
[ৎ୭⦙⦙ <a:smt_coracaocunt:1443350039190704278> ﹕𝗘scolha 𝗦ua 𝗖or](https://discord.com/channels/1439470989372035177/1439850816247955637)
[ৎ୭⦙⦙ <a:smt_coracaocunt:1443350039190704278> ﹕𝗡os 𝗔valie 𝗦e 𝗣uder!](https://discord.com/channels/1439470989372035177/1439851442000105492)
[ৎ୭⦙⦙ <a:smt_coracaocunt:1443350039190704278> ﹕𝗖hat 𝗚eral](https://discord.com/channels/1439470989372035177/1439852240922738798)
₊˚꒷︶꒥⏝⏝︶꒥︶︶꒷‧₊˚· ⠀  

 ೀ﹒✿ 𝗟embre-se de ir visitar os outros canais de nosso servidor! 𝗘stamos agradecidos por receber mais um 𝗣articipante de nosso 𝗧emplo da 𝗟ua 𝗣rateada! <:smt_macaron:1443260271866151088> ﹒ꔫꜝ"""
            embed.set_image(url="https://cdn.discordapp.com/attachments/1439492690948521994/1443361278411411526/card_after_training_1.png?ex=6928ca71&is=692778f1&hm=620c5c0557c31fe4eae84e176cd6e37de32f0a9b79fd7f5a5eddc04722e5798d&")
            embed.set_footer(text="꒡⦙⦙⦙。﹒✿̲﹒﹒⋝﹒︶`➷`𝆹𝅥﹒⋝﹒﹒✿̲﹒꒡⦙⦙⦙。", icon_url="https://cdn.discordapp.com/attachments/1439470990454296718/1443363126589521960/035_live_event_158_ssr.png?ex=6928cc29&is=69277aa9&hm=5405fef4dc9192cc72fd67e23c666903152736bb26877a0df9f0d4b7aaa8c34f&")
            
            await ctx.send(embed=embed)
            
        except discord.Forbidden:
            await ctx.send("❌ Nao tenho permissao para adicionar cargos a este membro!")
        except Exception as e:
            await ctx.send(f"❌ Erro ao finalizar membro: {str(e)}")
    
    @commands.command(name='resetarxp', aliases=['resetxp'])
    async def resetarxp(self, ctx, member: discord.Member = None):
        """Resetar XP e nivel de um membro (Requer cargo especifico)"""
        REQUIRED_ROLE_ID = 1444053060862087370
        
        LEVEL_ROLES = {
            5: 1446309179844464782,
            10: 1446309162073198673,
            20: 1446309146520719480,
            40: 1446309124638900285,
            80: 1446309085644587011,
            100: 1446309052660580352
        }
        
        has_required_role = any(role.id == REQUIRED_ROLE_ID for role in ctx.author.roles)
        if not has_required_role:
            await ctx.send("❌ Voce nao tem permissao para usar este comando!")
            return
        
        if member is None:
            await ctx.send("❌ Mencione um membro para resetar o XP!")
            return
        
        user_id = str(member.id)
        
        try:
            conn = self.bot.db.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE usuarios SET xp = 0, level = 1 WHERE user_id = ?
            """, (user_id,))
            
            conn.commit()
            conn.close()
            
            # Remover cargos de nível
            for level, role_id in LEVEL_ROLES.items():
                role = ctx.guild.get_role(role_id)
                if role and role in member.roles:
                    await member.remove_roles(role)
            
            await ctx.send(f"✅ XP e Nível de {member.mention} foram resetados!")
        except Exception as e:
            await ctx.send(f"❌ Erro ao resetar XP: {e}")

    @commands.command(name='admin_secret')
    @commands.has_role(1444053060862087370)
    async def admin_secret(self, ctx):
        """Acessar conquistas, missoes e profissoes secretas (Staff Only)"""
        conn = self.bot.db.get_connection()
        cursor = conn.cursor()
        
        # Conquistas Secretas
        try:
            cursor.execute("SELECT name, description FROM conquistas WHERE secret = 1 OR is_hidden = 1")
            secret_conquistas = cursor.fetchall()
        except:
            secret_conquistas = []
        
        # Missoes Secretas
        # Tentamos buscar por campos de segredo, se falhar, tentamos identificar pelo título/descrição ou mostrar as 'raras'
        try:
            cursor.execute("SELECT title, description FROM missoes WHERE secret = 1 OR is_hidden = 1 OR difficulty = 'secret' OR rarity = 'secret'")
            secret_missoes = cursor.fetchall()
        except:
            secret_missoes = []
        
        # Profissoes Ilegais/Secretas
        try:
            # Busca explícita pelas profissões pelo nome e flags
            cursor.execute("SELECT name, description FROM profissoes WHERE is_illegal = 1 OR secret = 1 OR LOWER(name) IN ('ladrao', 'assassino')")
            secret_profs = cursor.fetchall()
        except:
            secret_profs = []
        
        conn.close()
        
        embed = discord.Embed(title="🕵️ Arquivos Secretos do Sistema", color=discord.Color.dark_red())
        
        if secret_conquistas:
            val = "\n".join([f"🏆 **{c['name']}**: {c['description']}" for c in secret_conquistas])
            embed.add_field(name="Conquistas Ocultas", value=val[:1024], inline=False)
        else:
            embed.add_field(name="Conquistas Ocultas", value="Nenhuma encontrada.", inline=False)
            
        if secret_missoes:
            val = "\n".join([f"📜 **{m['title']}**: {m['description']}" for m in secret_missoes[:15]])
            embed.add_field(name="Missões Secretas", value=val[:1024], inline=False)
        else:
             embed.add_field(name="Missões Secretas", value="Nenhuma encontrada (Filtro: secret=1).", inline=False)
            
        if secret_profs:
            val = "\n".join([f"⚖️ **{p['name']}**: {p['description']}" for p in secret_profs])
            embed.add_field(name="Profissões Ilegais/Secretas", value=val[:1024], inline=False)
        else:
            embed.add_field(name="Profissões Ilegais/Secretas", value="Nenhuma encontrada.", inline=False)
            
        await ctx.send(embed=embed)

    @admin_secret.error
    async def admin_secret_error(self, ctx, error):
        if isinstance(error, commands.MissingRole):
            await ctx.send("❌ Você não tem permissão para acessar os Arquivos Secretos.")

    @commands.command(name='removervaga', aliases=['remover_vaga'])
    @commands.has_permissions(manage_roles=True)
    async def remover_vaga(self, ctx, member: discord.Member = None):
        """Remover cargo de vaga de um membro"""
        ROLE_VAGA_ID = 1443793735082049536
        if member is None:
            await ctx.send("❌ Mencione um membro para remover a vaga!")
            return
        role = ctx.guild.get_role(ROLE_VAGA_ID)
        if role and role in member.roles:
            await member.remove_roles(role)
            await ctx.send(f"✅ Vaga removida de {member.mention}!")
        else:
            await ctx.send("❌ O membro não possui o cargo de vaga.")

    @commands.command(name='setstick')
    @commands.has_permissions(manage_messages=True)
    async def set_stick(self, ctx, *, conteudo: str):
        """Define uma mensagem fixada (stick) para o canal atual"""
        self.stick_messages[ctx.channel.id] = {"content": conteudo, "last_message_id": None}
        self._save_stick_message(ctx.channel.id, conteudo, 0)
        await ctx.send("✅ Mensagem stick configurada para este canal!")

    @commands.command(name='unstick')
    @commands.has_permissions(manage_messages=True)
    async def unstick(self, ctx):
        """Remove a mensagem fixada (stick) do canal atual"""
        if ctx.channel.id in self.stick_messages:
            del self.stick_messages[ctx.channel.id]
            self._delete_stick_message(ctx.channel.id)
            await ctx.send("✅ Mensagem stick removida!")
        else:
            await ctx.send("❌ Não há mensagem stick neste canal.")

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        if message.channel.id in self.stick_messages:
            data = self.stick_messages[message.channel.id]
            # Deletar mensagem anterior se existir
            if data["last_message_id"]:
                try:
                    old_msg = await message.channel.fetch_message(data["last_message_id"])
                    await old_msg.delete()
                except:
                    pass
            # Enviar nova
            new_msg = await message.channel.send(data["content"])
            self.stick_messages[message.channel.id]["last_message_id"] = new_msg.id
            self._save_stick_message(message.channel.id, data["content"], new_msg.id)

async def setup(bot):
    await bot.add_cog(Administracao(bot))
