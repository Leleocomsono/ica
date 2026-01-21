import discord
from discord.ext import commands

class Inventario(commands.Cog):
    """Sistema de inventário de itens"""
    
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(name='inventario', aliases=['inv', 'bag'])
    async def inventario(self, ctx):
        """Ver seu inventário"""
        user_id = str(ctx.author.id)
        self.bot.db.ensure_user_exists(user_id)
        
        conn = self.bot.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT item_name, item_type, quantity, rarity
            FROM inventario
            WHERE user_id = ?
            ORDER BY rarity DESC, item_name ASC
        """, (user_id,))
        
        items = cursor.fetchall()
        conn.close()
        
        if not items:
            await ctx.send("📦 Seu inventário está vazio!")
            return
        
        embed = discord.Embed(
            title=f"🎒 Inventário de {ctx.author.name}",
            color=discord.Color.blue()
        )
        
        # Agrupar por raridade
        rarities = {
            'lendario': {'emoji': '🌟', 'items': []},
            'epico': {'emoji': '💜', 'items': []},
            'raro': {'emoji': '💙', 'items': []},
            'incomum': {'emoji': '💚', 'items': []},
            'comum': {'emoji': '⚪', 'items': []}
        }
        
        for item in items:
            rarity = item['rarity'] or 'comum'
            if rarity in rarities:
                rarities[rarity]['items'].append(
                    f"{item['item_name']} x{item['quantity']}"
                )
        
        for rarity, data in rarities.items():
            if data['items']:
                items_text = "\n".join(data['items'])
                embed.add_field(
                    name=f"{data['emoji']} {rarity.capitalize()}",
                    value=items_text,
                    inline=False
                )
        
        embed.set_footer(text=f"Total de {len(items)} tipo(s) de item")
        await ctx.send(embed=embed)
    
    @commands.command(name='usar', aliases=['use'])
    async def usar(self, ctx, *, item_name: str):
        """Usar um item do inventário"""
        user_id = str(ctx.author.id)
        self.bot.db.ensure_user_exists(user_id)
        
        conn = self.bot.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT inventory_id, item_type, quantity, description
            FROM inventario
            WHERE user_id = ? AND LOWER(item_name) = LOWER(?)
        """, (user_id, item_name))
        
        item = cursor.fetchone()
        
        if not item:
            await ctx.send(f"❌ Você não possui o item: {item_name}")
            conn.close()
            return
        
        # Efeitos dos itens
        effects = {
            'poção mágica': {'xp': 100, 'msg': 'Você ganhou 100 XP!'},
            'cristal raro': {'coins': 500, 'msg': 'Você ganhou 500 moedas!'},
            'amuleto da sorte': {'xp': 200, 'coins': 200, 'msg': 'Você ganhou 200 XP e 200 moedas!'},
            'elixir dourado': {'xp': 500, 'msg': 'Você ganhou 500 XP!'}
        }
        
        item_lower = item_name.lower()
        effect = effects.get(item_lower, {'msg': 'Item usado!'})
        
        # Aplicar efeitos
        if 'xp' in effect:
            cursor.execute("""
                UPDATE usuarios SET xp = xp + ? WHERE user_id = ?
            """, (effect['xp'], user_id))
        
        if 'coins' in effect:
            cursor.execute("""
                UPDATE economia SET coins = coins + ? WHERE user_id = ?
            """, (effect['coins'], user_id))
        
        # Remover item
        if item['quantity'] > 1:
            cursor.execute("""
                UPDATE inventario SET quantity = quantity - 1
                WHERE inventory_id = ?
            """, (item['inventory_id'],))
        else:
            cursor.execute("""
                DELETE FROM inventario WHERE inventory_id = ?
            """, (item['inventory_id'],))
        
        conn.commit()
        conn.close()
        
        embed = discord.Embed(
            title="✨ Item Usado",
            description=f"Você usou: **{item_name}**\n\n{effect['msg']}",
            color=discord.Color.green()
        )
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Inventario(bot))
