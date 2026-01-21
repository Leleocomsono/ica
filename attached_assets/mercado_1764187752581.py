import discord
from discord.ext import commands
from datetime import datetime

class Mercado(commands.Cog):
    """Sistema de mercado P2P"""
    
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(name='mercado', aliases=['market'])
    async def mercado(self, ctx):
        """Ver itens à venda no mercado"""
        conn = self.bot.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT listing_id, seller_id, item_name, price, quantity
            FROM mercado
            ORDER BY listed_at DESC
            LIMIT 10
        """)
        
        listings = cursor.fetchall()
        conn.close()
        
        if not listings:
            await ctx.send("📦 O mercado está vazio!")
            return
        
        embed = discord.Embed(
            title="🏪 Mercado",
            description="Itens à venda",
            color=discord.Color.blue()
        )
        
        for listing in listings:
            try:
                seller = await self.bot.fetch_user(int(listing['seller_id']))
                
                embed.add_field(
                    name=f"ID: {listing['listing_id']} - {listing['item_name']}",
                    value=f"Vendedor: {seller.name}\nQuantidade: {listing['quantity']}\nPreço: {listing['price']} moedas",
                    inline=False
                )
            except:
                continue
        
        embed.set_footer(text="Use !comprar <ID> para comprar")
        
        await ctx.send(embed=embed)
    
    @commands.command(name='anunciar', aliases=['sell'])
    async def anunciar(self, ctx, preco: int, *, item_name: str):
        """Anunciar item para venda"""
        if preco < 1:
            await ctx.send("❌ Preço inválido!")
            return
        
        user_id = str(ctx.author.id)
        self.bot.db.ensure_user_exists(user_id)
        
        conn = self.bot.db.get_connection()
        cursor = conn.cursor()
        
        # Verificar se tem o item
        cursor.execute("""
            SELECT inventory_id, quantity, item_type
            FROM inventario
            WHERE user_id = ? AND LOWER(item_name) = LOWER(?)
        """, (user_id, item_name))
        
        item = cursor.fetchone()
        
        if not item:
            await ctx.send(f"❌ Você não possui: {item_name}")
            conn.close()
            return
        
        # Remover do inventário
        if item['quantity'] > 1:
            cursor.execute("UPDATE inventario SET quantity = quantity - 1 WHERE inventory_id = ?", (item['inventory_id'],))
        else:
            cursor.execute("DELETE FROM inventario WHERE inventory_id = ?", (item['inventory_id'],))
        
        # Adicionar ao mercado
        cursor.execute("""
            INSERT INTO mercado (seller_id, item_name, item_type, price, listed_at)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, item_name, item['item_type'], preco, datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
        
        await ctx.send(f"✅ **{item_name}** foi anunciado por {preco} moedas!")
    
    @commands.command(name='comprar', aliases=['buy'])
    async def comprar(self, ctx, listing_id: int):
        """Comprar item do mercado"""
        user_id = str(ctx.author.id)
        self.bot.db.ensure_user_exists(user_id)
        
        conn = self.bot.db.get_connection()
        cursor = conn.cursor()
        
        # Buscar anúncio
        cursor.execute("""
            SELECT seller_id, item_name, item_type, price
            FROM mercado WHERE listing_id = ?
        """, (listing_id,))
        
        listing = cursor.fetchone()
        
        if not listing:
            await ctx.send("❌ Anúncio não encontrado!")
            conn.close()
            return
        
        if listing['seller_id'] == user_id:
            await ctx.send("❌ Você não pode comprar seu próprio item!")
            conn.close()
            return
        
        # Verificar moedas
        cursor.execute("SELECT coins FROM economia WHERE user_id = ?", (user_id,))
        coins = cursor.fetchone()['coins']
        
        if coins < listing['price']:
            await ctx.send(f"❌ Você não tem moedas suficientes! Preço: {listing['price']}")
            conn.close()
            return
        
        # Realizar compra
        cursor.execute("UPDATE economia SET coins = coins - ? WHERE user_id = ?", (listing['price'], user_id))
        cursor.execute("UPDATE economia SET coins = coins + ? WHERE user_id = ?", (listing['price'], listing['seller_id']))
        
        # Adicionar item ao comprador
        cursor.execute("""
            INSERT INTO inventario (user_id, item_name, item_type)
            VALUES (?, ?, ?)
        """, (user_id, listing['item_name'], listing['item_type']))
        
        # Remover anúncio
        cursor.execute("DELETE FROM mercado WHERE listing_id = ?", (listing_id,))
        
        conn.commit()
        conn.close()
        
        embed = discord.Embed(
            title="✅ Compra Realizada!",
            description=f"Você comprou **{listing['item_name']}** por {listing['price']} moedas!",
            color=discord.Color.green()
        )
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Mercado(bot))
