from discord.ext.commands import has_permissions
from discord.ext import commands
import discord


def setup(bot: commands.Bot):
    bot.add_cog(Shop(bot=bot))


class Shop(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_check(self, ctx):
        """Check if the category/cog is enabled"""
        if ctx.author.guild_permissions.administrator:
            return True
        query = """ SELECT * FROM cog_check WHERE guild_id = $1 AND cog_name = 'shop'"""
        data = await self.bot.db.fetch_row(query, ctx.guild.id)
        if data.get("enabled") is True:
            return True
        else:
            return False

    async def create_user(self, guild_id, user_id):
        query = """INSERT INTO user_inventory (guild_id, user_id) VALUES($1, $2)"""
        await self.bot.db.execute(query, guild_id, user_id)

    @commands.command(aliases=["inv"])
    async def inventory(self, ctx):
        """Show the items owned by user."""
        # Get the user data from shop db
        query = """SELECT * FROM user_inventory WHERE guild_id = $1 AND user_id = $2"""
        data = await self.bot.db.fetch(query, ctx.guild.id, ctx.author.id)

        # If user doesn't exist then add user to db
        if not data:
            await self.create_user(ctx.guild.id, ctx.author.id)
            data = await self.bot.db.fetch(query, ctx.guild.id, ctx.author.id)

        embed = discord.Embed()

        # if no items
        if not data[0].get("items"):
            embed.add_field(
                name="Your inventory is empty.", value="\u200b", inline=False
            )
        else:
            for i in range(len(data)):
                embed.add_field(
                    name=f"{i+1}: {data[i].get('items')} 🪙 {data[i].get('value')}",
                    value="\u200b",
                    inline=False,
                )

        embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)
        embed.set_footer(text="To buy an item, look at the shop.")
        await ctx.send(embed=embed)

    @commands.group(invoke_without_command=True)
    async def shop(self, ctx):
        """Show all the items in the shop"""
        query = """SELECT * FROM shop WHERE guild_id = $1"""
        data = await self.bot.db.fetch(query, ctx.guild.id)

        embed = discord.Embed()

        # if no items
        if not data:
            embed.add_field(name="No items in the shop.", value="\u200b", inline=False)
        else:
            for i in range(len(data)):
                embed.add_field(
                    name=f"{i + 1}: {data[i].get('items')} 🪙 {data[i].get('value')}  -  {data[i].get('description')}",
                    value="\u200b",
                    inline=False,
                )
        embed.set_author(name=f"{ctx.guild.name}'s shop", icon_url=ctx.guild.icon_url)
        embed.set_footer(
            text="If you are the admin add items by ```shop add``` command."
        )
        await ctx.send(embed=embed)

    @shop.command()
    @has_permissions(administrator=True)
    async def add(
        self, ctx, item: str, value: int, description: str, role: discord.Role = None
    ):
        """Add items in the shop
        example:
        - shop add item item_value "this is an item" @role
        - shop add dog 1000 "a pet for you" @dog"""
        query = """INSERT INTO shop (guild_id, items, value, description, role_id) VALUES($1, $2, $3, $4, $5)"""
        if role is None:
            await self.bot.db.execute(
                query, ctx.guild.id, item.lower(), value, description, None
            )
        else:
            await self.bot.db.execute(
                query, ctx.guild.id, item.lower(), value, description, role.id
            )

        return await ctx.send(f"**{item} added to the shop.**")

    @shop.command()
    @has_permissions(administrator=True)
    async def remove(self, ctx, item: str):
        """Remove items from the shop
        example:
        - shop remove dog"""
        query = """SELECT FROM shop WHERE guild_id=$1 AND items=$2"""
        data = await self.bot.db.fetch_row(query, ctx.guild.id, item.lower())
        if data is None:
            return await ctx.send(f"**{item} not found.**")

        query = """DELETE FROM shop WHERE guild_id=$1 AND items=$2"""
        await self.bot.db.execute(query, ctx.guild.id, item.lower())
        return await ctx.send(f"**{item} removed from the shop.**")

    @shop.command()
    async def buy(self, ctx, item: str):
        """Buy item from the shop
        example:
        - shop buy dog"""
        query = """SELECT * FROM shop WHERE guild_id = $1 AND items = $2"""
        data = await self.bot.db.fetch_row(query, ctx.guild.id, item.lower())
        if data is None:
            return await ctx.send(f"**{item} does not exist.**")

        query = """UPDATE user_inventory SET items = $3, value = $4 WHERE guild_id = $1 AND user_id = $2"""
        await self.bot.db.execute(
            query, ctx.guild.id, ctx.author.id, item.lower(), data.get("value")
        )

        if data.get("role_id") is None:
            return await ctx.send(f"**Successfully added {item} to your inventory.**")

        role = discord.utils.get(ctx.guild.roles, id=data.get("role_id"))
        await ctx.author.add_roles(role)
        await ctx.send(
            f"**Successfully added the role {role} and item {item} to your inventory.**"
        )
