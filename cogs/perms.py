import datetime

import discord
from discord.ext import commands


def setup(bot: commands.Bot):
    bot.add_cog(Perms(bot=bot))


class Perms(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_check(self, ctx):
        if ctx.author.guild_permissions.administrator:
            return True

    @commands.command()
    async def allow(self, ctx, name: str):
        """Enable a category to be used by everyone in the server.
        example:
        - allow currency
        - allow tags"""
        if name.lower() == "perms":
            return await ctx.send("**Can not enable this category.**")

        query = """ SELECT * FROM cog_check WHERE guild_id = $1 AND cog_name = $2"""
        data = await self.bot.db.fetch_row(query, ctx.guild.id, name.lower())

        if data is None:
            return await ctx.send("Can not change permission for this category.")
        if data.get("enabled") is True:
            return await ctx.send(f"{name} category is already enabled.")

        query = """UPDATE cog_check SET enabled = $3 WHERE guild_id = $1 AND cog_name = $2"""
        await self.bot.db.execute(query, ctx.guild.id, name.lower(), True)
        return await ctx.send(f"Category {name} enabled!")

    @commands.command()
    async def disallow(self, ctx, name: str):
        """Disable a category for everyone in the server, except admins.
        example:
        - disallow currency"""
        if name.lower() == "perms":
            return await ctx.send("**Can not disable this category.**")

        query = """ SELECT * FROM cog_check WHERE guild_id = $1 AND cog_name = $2"""
        data = await self.bot.db.fetch_row(query, ctx.guild.id, name.lower())
        if data is None:
            return await ctx.send("Can not change permission for this category.")

        if data.get("enabled") is True:
            query = """ UPDATE cog_check SET enabled = $3 WHERE guild_id = $1 AND cog_name = $2"""
            await self.bot.db.execute(query, ctx.guild.id, name.lower(), False)
            return await ctx.send(f"{name} has been disabled")

        return await ctx.send(f"**Category {name} is already disabled!**")

    @commands.command()
    async def listperms(self, ctx):
        """Shows the enabled and disabled categories"""
        query = """SELECT * FROM cog_check WHERE guild_id = $1"""
        data = await self.bot.db.fetch(query, ctx.guild.id)

        embed = discord.Embed(
            title="Categories",
            timestamp=datetime.datetime.utcnow(),
            colour=discord.Colour.blurple(),
        )
        embed.set_footer(
            text="Categories which can not be toggled(setup, help, lock, moderation, roles) are not displayed."
        )
        for i in range(len(data)):
            embed.add_field(
                name=f"{data[i].get('cog_name')}",
                value=f"{data[i].get('enabled')}",
                inline=True,
            )
        await ctx.send(embed=embed)
