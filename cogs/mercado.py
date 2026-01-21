import discord
from discord.ext import commands
from datetime import datetime

class Mercado(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(name='mercado', aliases=['market', 'loja'])
    async def mercado(self, ctx, pagina: int = 1):
        """Ver itens a venda no mercado"""
        conn = self.bot.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) as count FROM mercado")
        total = cursor.fetchone()['count']
        
        items_per_page = 10
        total_pages = max(1, (total + items_per_page - 1) // items_per_page)
        pagina = max(1, min(pagina, total_pages))
        
        offset = (pagina - 1) * items_per_page
        
        cursor.execute("""
            SELECT * FROM mercado 
            ORDER BY listed_at DESC
            LIMIT ? OFFSET ?
        """, (items_per_page, offset))
        
        items = cursor.fetchall()
        conn.close()
        
        embed = discord.Embed(
            title="Mercado P2P",
            description="Itens a venda por outros jogadores",
            color=discord.Color.gold()
        )
        
        if not items:
            embed.description = "Nenhum item a venda no momento!"
        else:
            for item in items:
                seller = ctx.guild.get_member(int(item['seller_id']))
                seller_name = seller.display_name if seller else "Desconhecido"
                
                embed.add_field(
                    name=f"#{item['listing_id']} - {item['item_name']}",
                    value=f"**Preco:** {item['price']:,} moedas\n"
                          f"**Quantidade:** {item['quantity']}\n"
                          f"**Vendedor:** {seller_name}",
                    inline=True
                )
        
        embed.set_footer(text=f"Pagina {pagina}/{total_pages} | Use !compraritem <id> para comprar")
        
        await ctx.send(embed=embed)
    
    @commands.command(name='vender', aliases=['sell'])
    async def vender(self, ctx, item_id: int = None, preco: int = None):
        """Colocar um item do inventario a venda"""
        if item_id is None or preco is None:
            await ctx.send("Use: `!vender <id_item_inventario> <preco>`")
            return
        
        if preco <= 0:
            await ctx.send("O preco deve ser maior que zero!")
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
        
        cursor.execute("""
            INSERT INTO mercado (seller_id, item_name, item_type, price, quantity, listed_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (user_id, item['item_name'], item['item_type'], preco, 1, datetime.now().isoformat()))
        
        if item['quantity'] > 1:
            cursor.execute("""
                UPDATE inventario SET quantity = quantity - 1 WHERE inventory_id = ?
            """, (item_id,))
        else:
            cursor.execute("""
                DELETE FROM inventario WHERE inventory_id = ?
            """, (item_id,))
        
        conn.commit()
        conn.close()
        
        embed = discord.Embed(
            title="Item Listado!",
            description=f"**{item['item_name']}** foi colocado a venda por **{preco:,}** moedas!",
            color=discord.Color.green()
        )
        
        await ctx.send(embed=embed)
    
    @commands.command(name='compraritem', aliases=['buyitem'])
    async def compraritem(self, ctx, listing_id: int = None):
        """Comprar um item do mercado"""
        if listing_id is None:
            await ctx.send("Especifique o ID do item! Use `!mercado` para ver a lista.")
            return
        
        user_id = str(ctx.author.id)
        self.bot.db.ensure_user_exists(user_id)
        
        conn = self.bot.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM mercado WHERE listing_id = ?", (listing_id,))
        listing = cursor.fetchone()
        
        if not listing:
            await ctx.send("Item nao encontrado no mercado!")
            conn.close()
            return
        
        if listing['seller_id'] == user_id:
            await ctx.send("Voce nao pode comprar seu proprio item!")
            conn.close()
            return
        
        cursor.execute("SELECT coins FROM economia WHERE user_id = ?", (user_id,))
        buyer_coins = cursor.fetchone()['coins'] or 0
        
        if buyer_coins < listing['price']:
            await ctx.send(f"Voce nao tem moedas suficientes! Preco: **{listing['price']:,}**")
            conn.close()
            return
        
        cursor.execute("""
            UPDATE economia SET coins = coins - ?, total_spent = total_spent + ?
            WHERE user_id = ?
        """, (listing['price'], listing['price'], user_id))
        
        cursor.execute("""
            UPDATE economia SET coins = coins + ?, total_earned = total_earned + ?
            WHERE user_id = ?
        """, (listing['price'], listing['price'], listing['seller_id']))
        
        cursor.execute("""
            SELECT * FROM inventario 
            WHERE user_id = ? AND item_name = ?
        """, (user_id, listing['item_name']))
        
        existing = cursor.fetchone()
        
        if existing:
            cursor.execute("""
                UPDATE inventario SET quantity = quantity + ?
                WHERE inventory_id = ?
            """, (listing['quantity'], existing['inventory_id']))
        else:
            cursor.execute("""
                INSERT INTO inventario (user_id, item_name, item_type, quantity)
                VALUES (?, ?, ?, ?)
            """, (user_id, listing['item_name'], listing['item_type'], listing['quantity']))
        
        cursor.execute("DELETE FROM mercado WHERE listing_id = ?", (listing_id,))
        
        conn.commit()
        conn.close()
        
        embed = discord.Embed(
            title="Compra Realizada!",
            description=f"Voce comprou **{listing['item_name']}** por **{listing['price']:,}** moedas!",
            color=discord.Color.green()
        )
        
        await ctx.send(embed=embed)
    
    @commands.command(name='cancelarvenda', aliases=['cancelar'])
    async def cancelarvenda(self, ctx, listing_id: int = None):
        """Cancelar uma venda no mercado"""
        if listing_id is None:
            await ctx.send("Especifique o ID do item!")
            return
        
        user_id = str(ctx.author.id)
        
        conn = self.bot.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM mercado WHERE listing_id = ? AND seller_id = ?
        """, (listing_id, user_id))
        
        listing = cursor.fetchone()
        
        if not listing:
            await ctx.send("Venda nao encontrada ou nao pertence a voce!")
            conn.close()
            return
        
        cursor.execute("""
            SELECT * FROM inventario 
            WHERE user_id = ? AND item_name = ?
        """, (user_id, listing['item_name']))
        
        existing = cursor.fetchone()
        
        if existing:
            cursor.execute("""
                UPDATE inventario SET quantity = quantity + ?
                WHERE inventory_id = ?
            """, (listing['quantity'], existing['inventory_id']))
        else:
            cursor.execute("""
                INSERT INTO inventario (user_id, item_name, item_type, quantity)
                VALUES (?, ?, ?, ?)
            """, (user_id, listing['item_name'], listing['item_type'], listing['quantity']))
        
        cursor.execute("DELETE FROM mercado WHERE listing_id = ?", (listing_id,))
        
        conn.commit()
        conn.close()
        
        embed = discord.Embed(
            title="Venda Cancelada",
            description=f"**{listing['item_name']}** foi devolvido ao seu inventario!",
            color=discord.Color.orange()
        )
        
        await ctx.send(embed=embed)
    
    @commands.command(name='minhasvendas', aliases=['mylistings'])
    async def minhasvendas(self, ctx):
        """Ver seus itens a venda"""
        user_id = str(ctx.author.id)
        
        conn = self.bot.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM mercado WHERE seller_id = ?
        """, (user_id,))
        
        listings = cursor.fetchall()
        conn.close()
        
        embed = discord.Embed(
            title="Suas Vendas",
            color=discord.Color.gold()
        )
        
        if not listings:
            embed.description = "Voce nao tem itens a venda!"
        else:
            for listing in listings:
                embed.add_field(
                    name=f"#{listing['listing_id']} - {listing['item_name']}",
                    value=f"**Preco:** {listing['price']:,} moedas\n**Quantidade:** {listing['quantity']}",
                    inline=True
                )
        
        embed.set_footer(text="Use !cancelarvenda <id> para cancelar uma venda")
        
        await ctx.send(embed=embed)

    @commands.command(name='leilao', aliases=['auction'])
    async def leilao(self, ctx, item_id: int, preco_inicial: int, duracao_minutos: int = 60):
        """Iniciar um leilão de um item do seu inventário"""
        user_id = str(ctx.author.id)
        conn = self.bot.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM inventario WHERE inventory_id = ? AND user_id = ?", (item_id, user_id))
        item = cursor.fetchone()
        if not item:
            await ctx.send("Item não encontrado!")
            conn.close()
            return

        ends_at = (datetime.now() + timedelta(minutes=duracao_minutos)).isoformat()
        cursor.execute("""
            INSERT INTO mercado_leiloes (seller_id, item_name, current_bid, ends_at)
            VALUES (?, ?, ?, ?)
        """, (user_id, item['item_name'], preco_inicial, ends_at))
        
        # Remover 1 item do inv
        if item['quantity'] > 1:
            cursor.execute("UPDATE inventario SET quantity = quantity - 1 WHERE inventory_id = ?", (item_id,))
        else:
            cursor.execute("DELETE FROM inventario WHERE inventory_id = ?", (item_id,))
            
        conn.commit()
        conn.close()
        await ctx.send(f"🔨 Leilão de **{item['item_name']}** iniciado! Preço inicial: **{preco_inicial}** moedas.")

    @commands.command(name='lance', aliases=['bid'])
    async def lance(self, ctx, auction_id: int, valor: int):
        """Dar um lance em um leilão ativo"""
        user_id = str(ctx.author.id)
        conn = self.bot.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM mercado_leiloes WHERE auction_id = ? AND active = 1", (auction_id,))
        auction = cursor.fetchone()
        if not auction:
            await ctx.send("Leilão não encontrado ou encerrado!")
            conn.close()
            return

        if valor <= auction['current_bid']:
            await ctx.send(f"O lance deve ser maior que {auction['current_bid']}!")
            conn.close()
            return
            
        cursor.execute("UPDATE mercado_leiloes SET current_bid = ?, highest_bidder_id = ? WHERE auction_id = ?", (valor, user_id, auction_id))
        conn.commit()
        conn.close()
        await ctx.send(f"💰 Novo lance de **{valor}** moedas em {auction['item_name']} por {ctx.author.mention}!")

async def setup(bot):
    await bot.add_cog(Mercado(bot))
