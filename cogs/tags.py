from discord.ext import commands
import datetime
import discord
import asyncio


from database.tags import Tag


def setup(bot: commands.Bot):
    bot.add_cog(Tags(bot=bot))


class Tags(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_check(self, ctx):
        """Check if the category/cog is enabled"""

        if ctx.author.guild_permissions.administrator:
            return True
        query = """ SELECT * FROM cog_check WHERE guild_id = $1 AND cog_name = 'tags'"""
        data = await self.bot.db.fetch_row(query, ctx.guild.id)
        if data.get("enabled") is True:
            return True
        else:
            return False

    @commands.command()
    async def tagcreate(self, ctx, name: lambda inp: inp.lower(), *, desc: str):
        """Create a new tag return error if tag exists
        example:
        - tagcreate test this is a test tag
        - tagcreate 'two words' this is a tag with 2 words in name"""
        name = await commands.clean_content().convert(ctx=ctx, argument=name)
        desc = await commands.clean_content().convert(ctx=ctx, argument=desc)

        # Convert the arguments to clean text

        # Check if the tag exists
        query = """SELECT * FROM tag WHERE guild_id = $1 AND name = $2"""
        record = await self.bot.db.fetch_row(query, ctx.guild.id, name)
        if record is not None:
            return await ctx.send("A tag with that name already exists.")

        # Create a new tag
        tag = Tag(
            bot=self.bot,
            guild_id=ctx.guild.id,
            name=name,
            description=desc,
            creator=ctx.author.id,
        )
        await tag.post()
        await ctx.send("You have successfully created your tag!")

    @commands.command()
    async def tag(self, ctx, *, name):
        """Get the tag
        example:
        - tag test
        - tag two words"""
        # Check if the tag exists
        query = """SELECT * FROM tag WHERE guild_id = $1 AND name = $2"""
        record = await self.bot.db.fetch_row(query, ctx.guild.id, name)
        if record is None:
            await ctx.message.delete(delay=6.0)
            message = await ctx.send("Tag with that name doesn't exist!")
            return await message.delete(delay=6.0)

        # Update tag uses if it exists and return the tag
        update_query = (
            """ UPDATE tag SET uses = uses+1 WHERE guild_id = $1 AND name = $2"""
        )
        await self.bot.db.fetch_row(update_query, ctx.guild.id, name)

        return await ctx.send(f"{record.get('description')}")

    @commands.command()
    async def taginfo(self, ctx, *, name: lambda inp: inp.lower()):
        """Get information regarding the specified tag.
        example:
        - taginfo test"""
        # Get the tag from the db
        query = """SELECT * FROM tag WHERE guild_id = $1 AND name = $2"""
        record = await self.bot.db.fetch_row(query, ctx.guild.id, name)

        # If tag doesn't exist return error
        if record is None:
            await ctx.message.delete(delay=6.0)
            message = await ctx.send("Could not find a tag with that name!")
            return await message.delete(delay=6.0)

        embed = discord.Embed(
            title=f"{name}",
            timestamp=datetime.datetime.utcnow(),
            colour=discord.Colour.blurple(),
        )
        embed.add_field(
            name="Created by:", value=f"<@{record.get('creator')}>", inline=True
        )
        embed.add_field(name="Uses:", value=f"{record.get('uses')}", inline=True)
        embed.add_field(
            name="Created at:", value=f"{record.get('created_at')}", inline=True
        )
        await ctx.send(embed=embed)

    @commands.command()
    async def tagdelete(self, ctx, *, name: lambda inp: inp.lower()):
        """Delete a tag.
        example:
        tagdelete test"""
        #  Check if a tag exists
        query = """SELECT * FROM tag WHERE guild_id = $1 AND name = $2"""
        tag = await self.bot.db.fetch_row(query, ctx.guild.id, name)

        if tag is None:
            await ctx.message.delete(delay=6.0)
            message = await ctx.send("Tag with that name does not exist!")
            return await message.delete(delay=6.0)

        # Check if the author is the creator of the tag
        if tag.get("creator") != ctx.author.id:
            if not ctx.author.guild_permissions.administrator:
                return await ctx.send("You don't have permission to do that.")

        delete_query = """DELETE FROM tag WHERE guild_id = $1 AND name = $2"""
        await self.bot.db.execute(delete_query, ctx.guild.id, name)
        await ctx.send("You have successfully deleted your tag.")

    @commands.command()
    async def tagedit(self, ctx, name: lambda inp: inp.lower(), *, text: str):
        """Edit a tag
        example:
        - tagedit test this tag is edited"""
        query = """SELECT * FROM tag WHERE guild_id = $1 AND name = $2"""
        tag = await self.bot.db.fetch_row(query, ctx.guild.id, name)

        if tag is None:
            await ctx.message.delete(delay=6.0)
            message = await ctx.send("Could not find a tag with that name.")
            return await message.delete(delay=6.0)

        if tag.get("creator") != ctx.author.id:
            if not ctx.author.guild_permissions.administrator:
                return await ctx.send("You don't have permission to do that.")

        update_query = (
            """ UPDATE tag SET description = $3 WHERE guild_id = $1 AND name = $2"""
        )
        await self.bot.db.execute(update_query, ctx.guild.id, name, text)
        await ctx.send("You have successfully edited your tag.")

    @commands.command()
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def tagsearch(self, ctx, *, term: str):
        """Search for a tag given a search term. PostgreSQL syntax must be used for the search.
        example:
        - tagsearch xyz
        - tagsearch %abc%"""
        query = """SELECT name FROM tag WHERE guild_id = $1 AND name LIKE $2"""
        records = await self.bot.db.fetch(query, ctx.guild.id, term)

        if not records:
            await ctx.message.delete(delay=6.0)
            message = await ctx.send("No tags found that has the term in it's name.")
            return await message.delete(delay=6.0)

        rec = ""
        for i in range(len(records)):
            rec += records[i].get("name") + "\n"

        await ctx.send(
            f"**{len(records)} tags found with search term on this server.**```\n{rec}\n```"
        )

    @commands.command()
    async def tagrename(
        self, ctx, name: lambda inp: inp.lower(), *, new_name: lambda inp: inp.lower()
    ):
        """Rename a tag.
        example:
        - tagrename test 'two words'
        - tagrename test2 two"""
        new_name = await commands.clean_content().convert(ctx=ctx, argument=new_name)
        query = """SELECT * FROM tag WHERE guild_id = $1 AND name = $2"""
        tag = await self.bot.db.fetch_row(query, ctx.guild.id, name)

        if tag is None:
            await ctx.message.delete(delay=6.0)
            message = await ctx.send("Could not find a tag with that name.")
            return await message.delete(delay=6.0)

        if tag.get("creator") != ctx.author.id:
            if not ctx.author.guild_permissions.administrator:
                return await ctx.send("You don't have permission to do that.")

        check_query = """ SELECT name FROM tag WHERE guild_id = $1"""
        data = await self.bot.db.fetch(check_query, ctx.guild.id, new_name, name)

        for i in range(len(data)):
            if data[i].get("name") == new_name.lower():
                return await ctx.send("A tag with that name already exists.")

        update_query = """ UPDATE tag SET name = $3 WHERE guild_id = $1 name = $2"""
        await self.bot.db.execute(update_query, ctx.guild.id, new_name, name)
        await ctx.send("You have successfully renamed your tag.")

    @commands.command()
    async def taglist(self, ctx, member: commands.MemberConverter = None):
        """List users existing tags.
        example:
        - taglist
        - taglist @NoobMaster"""
        member = member or ctx.author
        query = """SELECT name FROM tag WHERE guild_id = $1 AND creator = $2 ORDER BY name"""
        records = await self.bot.db.fetch(query, ctx.guild.id, member.id)
        if not records:
            return await ctx.send("No tags found.")

        await ctx.send(
            f"**{len(records)} tags by {'you' if member == ctx.author else str(member)} found on this server.**"
        )

        pager = commands.Paginator()

        for record in records:
            pager.add_line(line=record["name"])

        for page in pager.pages:
            await ctx.send(page)

    @commands.command()
    @commands.cooldown(1, 3600 * 24, commands.BucketType.user)
    async def tagall(self, ctx: commands.Context):
        """List all existing tags alphabetically ordered and sends them in DMs."""
        records = await self.bot.db.fetch(
            """SELECT name FROM tag WHERE guild_id = $1 ORDER BY name""", ctx.guild.id
        )

        if not records:
            return await ctx.send("This server doesn't have any tags.")

        try:
            await ctx.author.send(f"***{len(records)} tags found on this server.***")
        except discord.Forbidden:
            ctx.command.reset_cooldown(ctx)
            return await ctx.send("Could not dm you...", delete_after=10)

        pager = commands.Paginator()

        for record in records:
            pager.add_line(line=record["name"])

        for page in pager.pages:
            await asyncio.sleep(1)
            await ctx.author.send(page)

        await ctx.send("Tags sent in DMs.")
