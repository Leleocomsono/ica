import discord
from discord.ext import commands

class Inventario(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(name='inventario', aliases=['inv', 'mochila'])
    async def inventario(self, ctx, member: discord.Member = None):
        """Ver seu inventario"""
        member = member or ctx.author
        user_id = str(member.id)
        
        conn = self.bot.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT inventory_slots FROM usuarios WHERE user_id = ?", (user_id,))
        slots_data = cursor.fetchone()
        max_slots = slots_data['inventory_slots'] if slots_data else 10

        cursor.execute("""
            SELECT * FROM inventario WHERE user_id = ?
            ORDER BY item_type, item_name
        """, (user_id,))
        
        items = cursor.fetchall()
        conn.close()
        
        embed = discord.Embed(
            title=f"Inventário de {member.display_name}",
            description=f"Capacidade: **{len(items)}**/**{max_slots}** slots",
            color=discord.Color.blue()
        )
        
        if not items:
            embed.description += "\n\nInventário vazio!"
        else:
            items_by_type = {}
            for item in items:
                item_type = item['item_type'] or 'Outros'
                if item_type not in items_by_type:
                    items_by_type[item_type] = []
                items_by_type[item_type].append(item)
            
            rarity_emojis = {
                'comum': '⚪',
                'incomum': '🟢',
                'raro': '🔵',
                'epico': '🟣',
                'lendario': '🟡',
                'mistico': '🔴'
            }
            
            for item_type, type_items in items_by_type.items():
                items_text = ""
                for item in type_items:
                    r_emoji = rarity_emojis.get(item['rarity'], '⚪')
                    items_text += f"{r_emoji} **{item['item_name']}** x{item['quantity']} `#{item['inventory_id']}`\n"
                
                embed.add_field(
                    name=f"{item_type.capitalize()}",
                    value=items_text[:1024] or "Nenhum",
                    inline=False
                )
        
        await ctx.send(embed=embed)

    @commands.command(name='upgradeinv', aliases=['uinv'])
    async def upgrade_inventario(self, ctx):
        """Aumentar limite de slots do inventário (Custo: 5000)"""
        user_id = str(ctx.author.id)
        conn = self.bot.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT coins FROM economia WHERE user_id = ?", (user_id,))
        coins = cursor.fetchone()['coins']
        if coins < 5000:
            await ctx.send("Você precisa de 5000 moedas para o upgrade!")
            conn.close()
            return

        cursor.execute("UPDATE economia SET coins = coins - 5000 WHERE user_id = ?", (user_id,))
        cursor.execute("UPDATE usuarios SET inventory_slots = inventory_slots + 5 WHERE user_id = ?", (user_id,))
        conn.commit()
        conn.close()
        await ctx.send("✅ Inventário expandido em +5 slots!")
    
    @commands.command(name='item', aliases=['veritem'])
    async def item(self, ctx, item_id: int = None):
        """Ver detalhes de um item"""
        if item_id is None:
            await ctx.send("Especifique o ID do item! Use `!inventario` para ver a lista.")
            return
        
        user_id = str(ctx.author.id)
        
        conn = self.bot.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM inventario WHERE inventory_id = ? AND user_id = ?
        """, (item_id, user_id))
        
        item = cursor.fetchone()
        conn.close()
        
        if not item:
            await ctx.send("Item nao encontrado no seu inventario!")
            return
        
        rarity_colors = {
            'comum': discord.Color.light_grey(),
            'incomum': discord.Color.green(),
            'raro': discord.Color.blue(),
            'epico': discord.Color.purple(),
            'lendario': discord.Color.gold(),
            'mistico': discord.Color.red()
        }
        
        color = rarity_colors.get(item['rarity'], discord.Color.grey())
        
        embed = discord.Embed(
            title=item['item_name'],
            color=color
        )
        
        embed.add_field(name="Tipo", value=item['item_type'] or "Desconhecido", inline=True)
        embed.add_field(name="Raridade", value=item['rarity'].capitalize() if item['rarity'] else "Comum", inline=True)
        embed.add_field(name="Quantidade", value=str(item['quantity']), inline=True)
        
        if item['description']:
            embed.add_field(name="Descricao", value=item['description'], inline=False)
        
        embed.set_footer(text=f"ID: #{item['inventory_id']}")
        
        await ctx.send(embed=embed)

    @commands.command(name='organizar', aliases=['sort'])
    async def organizar(self, ctx):
        """Dica de como organizar o inventário"""
        await ctx.send("🎒 **Dica:** Você pode ver itens por tipo usando `!inventario`! Tente manter apenas o necessário.")
    
    @commands.command(name='usar', aliases=['use'])
    async def usar(self, ctx, item_id: int = None):
        """Usar um item consumivel"""
        if item_id is None:
            await ctx.send("Especifique o ID do item!")
            return
        
        user_id = str(ctx.author.id)
        
        conn = self.bot.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM inventario WHERE inventory_id = ? AND user_id = ?
        """, (item_id, user_id))
        
        item = cursor.fetchone()
        
        if not item:
            await ctx.send("Item nao encontrado no seu inventario!")
            conn.close()
            return
        
        if item['item_type'] != 'consumivel':
            await ctx.send("Este item nao pode ser usado!")
            conn.close()
            return
        
        effect = "Efeito aplicado!"
        
        if item['quantity'] > 1:
            cursor.execute("""
                UPDATE inventario SET quantity = quantity - 1 WHERE inventory_id = ?
            """, (item_id,))
        else:
            cursor.execute("DELETE FROM inventario WHERE inventory_id = ?", (item_id,))
        
        conn.commit()
        conn.close()
        
        embed = discord.Embed(
            title=f"Usando {item['item_name']}",
            description=effect,
            color=discord.Color.green()
        )
        
        await ctx.send(embed=embed)
    
    @commands.command(name='descartar', aliases=['discard', 'drop'])
    async def descartar(self, ctx, item_id: int = None, quantidade: int = 1):
        """Descartar itens do inventario"""
        if item_id is None:
            await ctx.send("Especifique o ID do item!")
            return
        
        if quantidade < 1:
            await ctx.send("Quantidade deve ser maior que zero!")
            return
        
        user_id = str(ctx.author.id)
        
        conn = self.bot.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM inventario WHERE inventory_id = ? AND user_id = ?
        """, (item_id, user_id))
        
        item = cursor.fetchone()
        
        if not item:
            await ctx.send("Item nao encontrado no seu inventario!")
            conn.close()
            return
        
        if quantidade > item['quantity']:
            await ctx.send(f"Voce so tem {item['quantity']} unidades deste item!")
            conn.close()
            return
        
        if quantidade >= item['quantity']:
            cursor.execute("DELETE FROM inventario WHERE inventory_id = ?", (item_id,))
        else:
            cursor.execute("""
                UPDATE inventario SET quantity = quantity - ? WHERE inventory_id = ?
            """, (quantidade, item_id))
        
        conn.commit()
        conn.close()
        
        embed = discord.Embed(
            title="Item Descartado",
            description=f"Voce descartou **{quantidade}x {item['item_name']}**",
            color=discord.Color.orange()
        )
        
        await ctx.send(embed=embed)
    
    @commands.command(name='dar', aliases=['give', 'presentear'])
    async def dar(self, ctx, member: discord.Member = None, item_id: int = None, quantidade: int = 1):
        """Dar um item para outro jogador"""
        if member is None or item_id is None:
            await ctx.send("Use: `!dar @usuario <id_item> [quantidade]`")
            return
        
        if member.id == ctx.author.id:
            await ctx.send("Voce nao pode dar itens para si mesmo!")
            return
        
        if member.bot:
            await ctx.send("Voce nao pode dar itens para um bot!")
            return
        
        if quantidade < 1:
            await ctx.send("Quantidade deve ser maior que zero!")
            return
        
        user_id = str(ctx.author.id)
        target_id = str(member.id)
        
        self.bot.db.ensure_user_exists(target_id)
        
        conn = self.bot.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM inventario WHERE inventory_id = ? AND user_id = ?
        """, (item_id, user_id))
        
        item = cursor.fetchone()
        
        if not item:
            await ctx.send("Item nao encontrado no seu inventario!")
            conn.close()
            return
        
        if quantidade > item['quantity']:
            await ctx.send(f"Voce so tem {item['quantity']} unidades deste item!")
            conn.close()
            return
        
        cursor.execute("""
            SELECT * FROM inventario 
            WHERE user_id = ? AND item_name = ?
        """, (target_id, item['item_name']))
        
        target_item = cursor.fetchone()
        
        if target_item:
            cursor.execute("""
                UPDATE inventario SET quantity = quantity + ?
                WHERE inventory_id = ?
            """, (quantidade, target_item['inventory_id']))
        else:
            cursor.execute("""
                INSERT INTO inventario (user_id, item_name, item_type, quantity, rarity, description)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (target_id, item['item_name'], item['item_type'], quantidade, item['rarity'], item['description']))
        
        if quantidade >= item['quantity']:
            cursor.execute("DELETE FROM inventario WHERE inventory_id = ?", (item_id,))
        else:
            cursor.execute("""
                UPDATE inventario SET quantity = quantity - ? WHERE inventory_id = ?
            """, (quantidade, item_id))
        
        conn.commit()
        conn.close()
        
        embed = discord.Embed(
            title="Item Enviado!",
            description=f"{ctx.author.mention} deu **{quantidade}x {item['item_name']}** para {member.mention}!",
            color=discord.Color.green()
        )
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Inventario(bot))
