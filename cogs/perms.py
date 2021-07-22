import datetime
import os

import discord
from discord.ext import commands

cogs = []
for filename in os.listdir("cogs"):
    if filename.endswith(".py"):
        cogs.append(f"{filename[:-3]}")


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

    @commands.command()
    async def allow_role(self, ctx, role: discord.Role, category: str):
        """Allow a role to use a certain category/cogs
        example:
        - allow_role @role fun
        - allow_role @role poll"""
        not_allowed_cogs = [
            "perms",
            "basic_setup",
            "help",
            "message",
            "moderation",
            "roles",
            "filter",
        ]
        if category.lower() not in cogs or category.lower() in not_allowed_cogs:
            return await ctx.send(
                "**Category does not exist or can't be granted role permissions.**"
            )

        query = """SELECT * FROM role_check WHERE guild_id = $1 AND cog_name = $2"""
        data = await self.bot.db.fetch(query, ctx.guild.id, category.lower())

        for i in range(len(data)):
            if data[i].get("enabled") and data[i].get("role_id") == role.id:
                return await ctx.send(
                    f"**{role.name} is already enabled for {category.lower()}.**"
                )

        query = """INSERT INTO role_check (guild_id, cog_name, role_id, enabled) VALUES ($1, $2, $3, True)"""
        await self.bot.db.execute(query, ctx.guild.id, category.lower(), role.id)
        return await ctx.send(f"**Category {category} enabled for {role.name}.**")

    @commands.command()
    async def disallow_role(self, ctx, role: discord.Role, category: str):
        """Disallow a role to use a certain category/cogs
        example:
        - disallow_role @role fun
        - disallow_role @role poll"""
        not_allowed_cogs = [
            "perms",
            "basic_setup",
            "help",
            "message",
            "moderation",
            "roles",
            "filter",
        ]
        if category.lower() not in cogs or category.lower() in not_allowed_cogs:
            return await ctx.send(
                "**Category does not exist or can't be granted role permissions.**"
            )

        query = """SELECT * FROM role_check WHERE guild_id = $1 AND cog_name = $2"""
        data = await self.bot.db.fetch_row(query, ctx.guild.id, category.lower())

        if data is None:
            return await ctx.send(
                f"**Category {category} is already disabled for {role.name}.**"
            )
        elif data.get("enabled"):
            query = """ UPDATE role_check SET enabled = False WHERE guild_id = $1 AND cog_name = $2  AND role_id = $3"""
            await self.bot.db.execute(query, ctx.guild.id, category.lower(), role.id)
            return await ctx.send(f"**Category {category} disabled for {role.name}.**")
        else:
            return await ctx.send(
                f"**Category {category} is already disabled for {role.name}.**"
            )

    @commands.command()
    async def list_role(self, ctx):
        """Check which all roles have perms to use which category/cog"""
        query = """SELECT * FROM role_check WHERE guild_id = $1"""
        data = await self.bot.db.fetch(query, ctx.guild.id)
        embed = discord.Embed(
            title="Roles Permission",
            timestamp=datetime.datetime.utcnow(),
            colour=discord.Colour.blurple(),
        )
        for i in range(len(data)):
            embed.add_field(
                name=f"{data[i].get('cog_name')}",
                value=f"<@&{data[i].get('role_id')}>, {data[i].get('enabled')}",
                inline=True,
            )
        await ctx.send(embed=embed)
