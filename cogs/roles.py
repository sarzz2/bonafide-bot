from discord.ext.commands import has_permissions
from discord.ext import commands
import datetime
import discord

from database.roles import Roles


def setup(bot: commands.Bot):
    bot.add_cog(Role(bot=bot))


class Role(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @has_permissions(manage_roles=True)
    async def addrole(self, ctx, member: discord.Member, role: discord.Role):
        """Add role to the Member
        example:
        - addrole @plasticfoods @test"""
        role = discord.utils.get(ctx.guild.roles, id=role.id)

        muted_role = discord.utils.get(ctx.guild.roles, name="Muted")
        punished_role = discord.utils.get(ctx.guild.roles, name="Punished")

        if role > ctx.author.top_role:
            return await ctx.send(
                embed=discord.Embed(
                    title="You don't have permission to add this role",
                    timestamp=datetime.datetime.utcnow(),
                    colour=discord.Colour.darker_grey(),
                )
            )

        if role == muted_role or role == punished_role:
            return await ctx.send(
                embed=discord.Embed(
                    title=f"Can not assign *{role}*  role using this command.",
                    description="For more information run ```.help addrole```",
                    timestamp=datetime.datetime.utcnow(),
                    colour=discord.Colour.red(),
                )
            )

        if role in member.roles:
            return await ctx.channel.send(
                embed=discord.Embed(
                    title=f"*{member}* already has *{role}* Role!",
                    timestamp=datetime.datetime.utcnow(),
                    colour=discord.Colour.greyple(),
                )
            )

        await member.add_roles(role)
        await ctx.send(
            embed=discord.Embed(
                title=f"*{role}* has been added to *{member}*",
                timestamp=datetime.datetime.utcnow(),
                colour=discord.Colour.green(),
            )
        )

    @commands.command()
    @has_permissions(manage_roles=True)
    async def removerole(self, ctx, member: discord.Member, role: discord.Role):
        """Remove a role from the member
        example:
        - removerole @plasticfoods @test"""
        role = discord.utils.get(ctx.guild.roles, id=role.id)

        muted_role = discord.utils.get(ctx.guild.roles, name="Muted")
        punished_role = discord.utils.get(ctx.guild.roles, name="Punished")

        if role > ctx.author.top_role:
            return await ctx.send(
                embed=discord.Embed(
                    title="You don't have permission to remove this role",
                    timestamp=datetime.datetime.utcnow(),
                    colour=discord.Colour.darker_grey(),
                )
            )

        if role == muted_role or role == punished_role:
            return await ctx.send(
                embed=discord.Embed(
                    title=f"Can not remove *{role}*  role using this command.",
                    description="For more information run ```.help removerole```",
                    timestamp=datetime.datetime.utcnow(),
                    colour=discord.Colour.red(),
                )
            )

        if role not in member.roles:
            return await ctx.channel.send(
                embed=discord.Embed(
                    title=f"{member} doesn't have *{role}* Role!",
                    timestamp=datetime.datetime.utcnow(),
                    colour=discord.Colour.greyple(),
                )
            )

        await member.remove_roles(role)
        await ctx.send(
            embed=discord.Embed(
                title=f"*{role}* has been removed from *{member}*",
                timestamp=datetime.datetime.utcnow(),
                colour=discord.Colour.green(),
            )
        )

    @commands.command()
    @has_permissions(manage_roles=True)
    async def persistrole(self, ctx, member: discord.Member, role: discord.Role):
        """Add a persisting role to the member"""
        role = discord.utils.get(ctx.guild.roles, id=role.id)

        muted_role = discord.utils.get(ctx.guild.roles, name="Muted")
        punished_role = discord.utils.get(ctx.guild.roles, name="Punished")

        if role > ctx.author.top_role:
            return await ctx.send(
                embed=discord.Embed(
                    title="You don't have permission to add this role",
                    timestamp=datetime.datetime.utcnow(),
                    colour=discord.Colour.darker_grey(),
                )
            )

        if role == muted_role or role == punished_role:
            return await ctx.send(
                embed=discord.Embed(
                    title=f"Can not assign *{role}*  role using this command.",
                    description="For more information run ```.help persistrole```",
                    timestamp=datetime.datetime.utcnow(),
                    colour=discord.Colour.red(),
                )
            )

        if role in member.roles:
            return await ctx.channel.send(
                embed=discord.Embed(
                    title=f"*{member}* already has *{role}* Role!",
                    timestamp=datetime.datetime.utcnow(),
                    colour=discord.Colour.greyple(),
                )
            )

        await member.add_roles(role)
        persistent_role = Roles(
            bot=self.bot,
            guild_id=ctx.guild.id,
            user_id=member.id,
            roles=role.id,
        )
        # Post to db for persistent role
        await persistent_role.post()

        await ctx.send(
            embed=discord.Embed(
                title=f"Persisting Role: *{role}* has been added to *{member}*",
                timestamp=datetime.datetime.utcnow(),
                colour=discord.Colour.green(),
            )
        )

    @commands.command()
    @has_permissions(manage_roles=True)
    async def removepersistrole(self, ctx, member: discord.Member, role: discord.Role):
        """Remove a persisting role from the member"""
        role = discord.utils.get(ctx.guild.roles, id=role.id)

        muted_role = discord.utils.get(ctx.guild.roles, name="Muted")
        punished_role = discord.utils.get(ctx.guild.roles, name="Punished")

        if role > ctx.author.top_role:
            return await ctx.send(
                embed=discord.Embed(
                    title="You don't have permission to add this role",
                    timestamp=datetime.datetime.utcnow(),
                    colour=discord.Colour.darker_grey(),
                )
            )

        if role == muted_role or role == punished_role:
            return await ctx.send(
                embed=discord.Embed(
                    title=f"Can not remove *{role}*  role using this command.",
                    description="For more information run ```.help removepersistrole```",
                    timestamp=datetime.datetime.utcnow(),
                    colour=discord.Colour.red(),
                )
            )

        if role not in member.roles:
            return await ctx.channel.send(
                embed=discord.Embed(
                    title=f"*{member}* doesn't have *{role}* Role!",
                    timestamp=datetime.datetime.utcnow(),
                    colour=discord.Colour.greyple(),
                )
            )

        await member.remove_roles(role)
        persistent_role = Roles(
            bot=self.bot,
            guild_id=ctx.guild.id,
            user_id=member.id,
            roles=role.id,
        )
        # Post to db for persistent role
        await persistent_role.delete()

        await ctx.send(
            embed=discord.Embed(
                title=f"Persisting Role *{role}* has been removed from *{member}*",
                timestamp=datetime.datetime.utcnow(),
                colour=discord.Colour.green(),
            )
        )

    @commands.command()
    @has_permissions(manage_roles=True)
    async def createrole(self, ctx, role: str):
        """Create a new role"""
        if role.lower() == "muted" or role.lower() == "punished":
            return await ctx.send("Can not create this roles.")
        """Create a new role"""
        role = await ctx.guild.create_role(name=role)
        return await ctx.send(
            embed=discord.Embed(
                title=f"Role *{role}* has been created!",
                timestamp=datetime.datetime.utcnow(),
                colour=discord.Colour.green(),
            )
        )

    @commands.command()
    @has_permissions(manage_roles=True)
    async def deleterole(self, ctx, role: discord.Role):
        """Delete a Role"""
        if role.name == "Muted" or role.name == "Punished":
            return await ctx.send("Can not delete this role.")
        if role > ctx.author.top_role:
            return await ctx.send(
                embed=discord.Embed(
                    title="You don't have permission to delete this role",
                    timestamp=datetime.datetime.utcnow(),
                    colour=discord.Colour.darker_grey(),
                )
            )

        role = discord.utils.get(ctx.guild.roles, id=role.id)
        await role.delete()
        return await ctx.send(
            embed=discord.Embed(
                title=f"Role *{role}* has been deleted!",
                timestamp=datetime.datetime.utcnow(),
                colour=discord.Colour.red(),
            )
        )

    @commands.command()
    @has_permissions(manage_roles=True)
    async def massadd(
        self,
        ctx,
        role: discord.Role,
        member: commands.Greedy[discord.Member],
    ):
        """Add the role to specified members in the guild"""
        role = discord.utils.get(ctx.guild.roles, id=role.id)

        muted_role = discord.utils.get(ctx.guild.roles, name="Muted")
        punished_role = discord.utils.get(ctx.guild.roles, name="Punished")

        if role > ctx.author.top_role:
            return await ctx.send(
                embed=discord.Embed(
                    title="You don't have permission to add this role",
                    timestamp=datetime.datetime.utcnow(),
                    colour=discord.Colour.darker_grey(),
                )
            )

        if role == muted_role or role == punished_role:
            return await ctx.send(
                embed=discord.Embed(
                    title=f"Can not assign *{role}*  role using this command.",
                    description="For more information run ```.help massadd```",
                    timestamp=datetime.datetime.utcnow(),
                    colour=discord.Colour.red(),
                )
            )

        for i in member:
            if role in i.roles:
                await ctx.channel.send(
                    embed=discord.Embed(
                        title=f"*{i}* already has *{role}* Role!",
                        timestamp=datetime.datetime.utcnow(),
                        colour=discord.Colour.greyple(),
                    )
                )

            await i.add_roles(role)

        await ctx.send(
            embed=discord.Embed(
                title=f"*{role}* has been added to **{len(member)}** members!",
                timestamp=datetime.datetime.utcnow(),
                colour=discord.Colour.green(),
            )
        )

    @commands.command()
    @has_permissions(manage_roles=True)
    async def massremove(
        self,
        ctx,
        role: discord.Role,
        member: commands.Greedy[discord.Member],
    ):
        """Remove the role from specified members in the guild"""

        role = discord.utils.get(ctx.guild.roles, id=role.id)

        muted_role = discord.utils.get(ctx.guild.roles, name="Muted")
        punished_role = discord.utils.get(ctx.guild.roles, name="Punished")

        if role > ctx.author.top_role:
            return await ctx.send(
                embed=discord.Embed(
                    title="You don't have permission to remove this role",
                    timestamp=datetime.datetime.utcnow(),
                    colour=discord.Colour.darker_grey(),
                )
            )

        if role == muted_role or role == punished_role:
            return await ctx.send(
                embed=discord.Embed(
                    title=f"Can not remove *{role}*  role using this command.",
                    description="For more information run ```.help massremove```",
                    timestamp=datetime.datetime.utcnow(),
                    colour=discord.Colour.red(),
                )
            )

        for i in member:
            if role not in i.roles:
                await ctx.channel.send(
                    embed=discord.Embed(
                        title=f"*{i}* doesn't have *{role}* Role!",
                        timestamp=datetime.datetime.utcnow(),
                        colour=discord.Colour.greyple(),
                    )
                )

            await i.remove_roles(role)

        await ctx.send(
            embed=discord.Embed(
                title=f"*{role}* has been removed from **{len(member)}** members!",
                timestamp=datetime.datetime.utcnow(),
                colour=discord.Colour.green(),
            )
        )

    @commands.command()
    @has_permissions(manage_roles=True)
    async def addroleall(self, ctx, role: discord.Role):
        """Add a role to all members in the guild"""
        muted_role = discord.utils.get(ctx.guild.roles, name="Muted")
        punished_role = discord.utils.get(ctx.guild.roles, name="Punished")

        if role > ctx.author.top_role:
            return await ctx.send(
                embed=discord.Embed(
                    title="You don't have permission to add this role",
                    timestamp=datetime.datetime.utcnow(),
                    colour=discord.Colour.darker_grey(),
                )
            )

        if role == muted_role or role == punished_role:
            return await ctx.send(
                embed=discord.Embed(
                    title=f"Can not assign *{role}*  role using this command.",
                    description="For more information run ```.help addroleall```",
                    timestamp=datetime.datetime.utcnow(),
                    colour=discord.Colour.red(),
                )
            )

        for i in ctx.guild.members:
            if not i.bot:
                await i.add_roles(role)

        await ctx.send(
            embed=discord.Embed(
                title=f"*{role}* has been added  to **{len(ctx.guild.members)}** members!",
                timestamp=datetime.datetime.utcnow(),
                colour=discord.Colour.green(),
            )
        )

    @commands.command()
    @has_permissions(manage_roles=True)
    async def removeroleall(self, ctx, role: discord.Role):
        """Remove the role from all members in the guild"""
        muted_role = discord.utils.get(ctx.guild.roles, name="Muted")
        punished_role = discord.utils.get(ctx.guild.roles, name="Punished")

        if role > ctx.author.top_role:
            return await ctx.send(
                embed=discord.Embed(
                    title="You don't have permission to remove this role",
                    timestamp=datetime.datetime.utcnow(),
                    colour=discord.Colour.darker_grey(),
                )
            )

        if role == muted_role or role == punished_role:
            return await ctx.send(
                embed=discord.Embed(
                    title=f"Can not remove *{role}*  role using this command.",
                    description="For more information run ```.help removeroleall```",
                    timestamp=datetime.datetime.utcnow(),
                    colour=discord.Colour.red(),
                )
            )

        for i in ctx.guild.members:
            if not i.bot:
                await i.remove_roles(role)

        await ctx.send(
            embed=discord.Embed(
                title=f"*{role}* has been removed  from **{len(ctx.guild.members)}** members!",
                timestamp=datetime.datetime.utcnow(),
                colour=discord.Colour.green(),
            )
        )

    # @commands.command()
    # async def reactrole(self, ctx, roles: commands.Greedy[discord.Role], *, emojis):
    #     for i in roles:
    #         try:
    #             discord.utils.get(ctx.guild.roles, name=i)
    #         except:
    #             return await ctx.send(f"**{i} role not found.**")

    @commands.command()
    async def roleinfo(self, ctx, role: discord.Role):
        """Get the information about the role"""
        embed = discord.Embed(
            title="Role Info", colour=role.colour, timestamp=datetime.datetime.utcnow()
        )
        embed.add_field(name="ID", value=role.id)
        embed.add_field(name="Name", value=role.name)
        embed.add_field(name="Members", value=str(len(role.members)))
        embed.add_field(
            name="Created At", value=role.created_at.strftime("%d/%m/%Y, %H:%M")
        )
        embed.add_field(name="Hoisted", value=role.hoist)
        embed.add_field(name="Mentionable", value=role.mentionable)
        if role.name == "@everyone":
            embed.add_field(name="Mention", value=role.name)
        else:
            embed.add_field(name="Mention", value=role.mention)
        embed.add_field(name="Position", value=role.position)
        await ctx.send(embed=embed)

    @commands.command()
    async def rolecolor(self, ctx, role: discord.Role):
        """Get the RGB and HEX value of role color."""
        embed = discord.Embed(colour=role.colour, timestamp=datetime.datetime.utcnow())
        embed.add_field(name="Name", value=role.name)
        embed.add_field(name="Hex Value", value=role.color)
        await ctx.send(embed=embed)
