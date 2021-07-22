from discord.ext import commands
import datetime
import discord

from utils.graph import plot


def setup(bot: commands.Bot):
    bot.add_cog(Stats(bot=bot))


class Stats(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_check(self, ctx):
        """Check if the category/cog is enabled"""
        # check admin
        if ctx.author.guild_permissions.administrator:
            return True

        query = """ SELECT * FROM cog_check WHERE guild_id = $1 AND cog_name = 'basic_info'"""
        data = await self.bot.db.fetch_row(query, ctx.guild.id)

        # check if cog is enabled
        if data.get("enabled"):
            return True
        # if cog is not enabled then check whether author's role is allowed to run the cog's commands
        else:
            query = """SELECT * FROM role_check WHERE guild_id = $1 AND cog_name = 'basic_info' AND role_id = $2"""

            for i in range(len(ctx.author.roles)):
                data = await self.bot.db.fetch_row(
                    query, ctx.guild.id, ctx.author.roles[i].id
                )
                if data is None:
                    continue
                elif data.get("enabled"):
                    return True

            return False

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        # Check if stats cogs is enabled
        query = (
            """ SELECT * FROM cog_check WHERE guild_id = $1 AND cog_name = 'stats'"""
        )
        data = await self.bot.db.fetch_row(query, message.guild.id)
        if data.get("enabled") is False:
            return

        query = """SELECT created_at FROM stats WHERE guild_id = $1 AND user_id = $2 AND created_at = $3"""
        data = await self.bot.db.fetch_row(
            query, message.guild.id, message.author.id, datetime.datetime.today()
        )
        if data is None:
            query = """INSERT INTO stats (guild_id, user_id, message_count, created_at) VALUES($1,$2, $3, $4)"""
            await self.bot.db.execute(
                query, message.guild.id, message.author.id, 1, datetime.datetime.today()
            )
        else:
            query = """UPDATE stats SET message_count = message_count + 1 WHERE guild_id = $1 AND user_id = $2 AND
            created_at = $3 """
            await self.bot.db.execute(
                query, message.guild.id, message.author.id, datetime.datetime.today()
            )

    @commands.Cog.listener()
    async def on_member_join(self, member):
        # Check if stats cogs is enabled
        query = (
            """ SELECT * FROM cog_check WHERE guild_id = $1 AND cog_name = 'stats'"""
        )
        data = await self.bot.db.fetch_row(query, member.guild.id)
        if data.get("enabled") is False:
            return

        query = """SELECT created_at FROM stats_server WHERE guild_id = $1 AND created_at = $2"""
        data = await self.bot.db.fetch_row(
            query, member.guild.id, datetime.datetime.today()
        )

        if data is None:
            query = """INSERT INTO stats_server (guild_id, member_count, created_at) VALUES ($1, $2, $3)"""
            await self.bot.db.execute(
                query, member.guild.id, 1, datetime.datetime.today()
            )

        query = """UPDATE stats_server SET member_count = member_count + 1 WHERE guild_id = $1 AND created_at = $2"""
        await self.bot.db.execute(query, member.guild.id, datetime.datetime.today())

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        # Check if stats cogs is enabled
        query = (
            """ SELECT * FROM cog_check WHERE guild_id = $1 AND cog_name = 'stats'"""
        )
        data = await self.bot.db.fetch_row(query, member.guild.id)
        if data.get("enabled") is False:
            return

        query = """SELECT created_at FROM stats_server WHERE guild_id = $1 AND created_at = $2"""
        data = await self.bot.db.fetch_row(
            query, member.guild.id, datetime.datetime.today()
        )

        if data is None:
            query = """INSERT INTO stats_server (guild_id, member_count, created_at) VALUES ($1, $2, $3)"""
            await self.bot.db.execute(
                query, member.guild.id, -1, datetime.datetime.today()
            )

        query = """UPDATE stats_server SET member_count = member_count - 1 WHERE guild_id = $1 AND created_at = $2"""
        await self.bot.db.execute(query, member.guild.id, datetime.datetime.today())

    @commands.command()
    @commands.cooldown(1, 10)
    async def stat(self, ctx, member: discord.Member = None):
        """Check the stats for the member"""
        if member is None:
            member = ctx.author

        # get the total message of user
        query = """SELECT SUM(message_count) FROM stats WHERE guild_id = $1 AND user_id = $2 """
        message_sum = await self.bot.db.fetch_row(query, ctx.guild.id, member.id)

        # get last 30 days of message
        query = """SELECT * FROM stats WHERE guild_id = $1 AND user_id = $2 AND created_at > (CURRENT_DATE - INTERVAL
        '30 days') ORDER BY created_at ASC """
        data = await self.bot.db.fetch(query, member.guild.id, member.id)

        dates = []
        message = []
        for i in range(len(data)):
            dates.append(data[i].get("created_at"))
            message.append(data[i].get("message_count"))

        # plot the graph
        plot(dates, message)
        file = discord.File("./foo.png", filename="foo.png")

        embed = discord.Embed(
            description=f"Message stats for {member.mention} for last 30 days.\n\n"
            f" Change with the ``lookback`` command.",
            timestamp=datetime.datetime.utcnow(),
            colour=discord.Colour.blurple(),
        )
        embed.set_author(name=member.display_name, icon_url=member.avatar_url)
        embed.add_field(
            name=f"Total Messages: {message_sum.get('sum')}",
            value="\u200b",
            inline=False,
        )
        embed.set_image(url="attachment://foo.png")

        await ctx.send(file=file, embed=embed)

    @commands.command(aliases=["memstat"])
    @commands.cooldown(1, 10)
    async def memstats(self, ctx):
        """Get message stats for entire server for all time, last 30 days, last 7 days and last 24 hours"""

        # Get the total messages for the server
        query = """SELECT SUM(message_count) FROM stats WHERE guild_id = $1"""
        message_sum = await self.bot.db.fetch_row(query, ctx.guild.id)

        # Get the messages for last 30 days of the server
        query = """SELECT SUM(message_count) FROM stats WHERE guild_id = $1 AND created_at > current_timestamp -
        interval '30 day'"""
        message_sum_30 = await self.bot.db.fetch_row(query, ctx.guild.id)

        # Get the messages for last 7 days of the server
        query = """SELECT SUM(message_count) FROM stats WHERE guild_id = $1 AND created_at > current_timestamp -
        interval '7 day'"""
        message_sum_7 = await self.bot.db.fetch_row(query, ctx.guild.id)

        # Get the messages for last 24 hours of the server
        query = """SELECT SUM(message_count) FROM stats WHERE guild_id = $1 AND created_at > current_timestamp -
        interval '1 day'"""
        message_sum_1 = await self.bot.db.fetch_row(query, ctx.guild.id)

        query = """SELECT created_at,SUM(message_count) FROM stats WHERE guild_id= $1 GROUP BY created_at ORDER BY
        created_at ASC"""
        data = await self.bot.db.fetch(query, ctx.guild.id)

        dates = []
        message = []
        for i in range(len(data)):
            dates.append(data[i].get("created_at"))
            message.append(data[i].get("sum"))

        # plot the graph
        plot(dates, message)
        file = discord.File("./foo.png", filename="foo.png")

        embed = discord.Embed(
            title=f"Message stats for {ctx.guild.name}\n",
            timestamp=datetime.datetime.utcnow(),
            colour=discord.Colour.blurple(),
        )
        embed.add_field(
            name=f"Total Messages: {message_sum.get('sum')}",
            value="\u200b",
            inline=False,
        )
        embed.add_field(
            name=f"Messages for last 30 days: {message_sum_30.get('sum')}",
            value="\u200b",
            inline=False,
        )
        embed.add_field(
            name=f"Messages for last 7 days: {message_sum_7.get('sum')}",
            value="\u200b",
            inline=False,
        )
        embed.add_field(
            name=f"Messages for last 24 hours: {message_sum_1.get('sum')}",
            value="\u200b",
            inline=False,
        )
        embed.set_image(url="attachment://foo.png")
        await ctx.send(file=file, embed=embed)

    @commands.command(aliases=["guildstats", "guildstat", "serverstats"])
    @commands.cooldown(1, 10)
    async def serverstat(self, ctx):
        # Get the member change for last 30 days of the server
        query = """SELECT SUM(member_count) FROM stats_server WHERE guild_id = $1 AND created_at > current_timestamp -
               interval '30 day' """
        mem_30 = await self.bot.db.fetch_row(query, ctx.guild.id)

        # Get the member for last 7 days of the server
        query = """SELECT SUM(member_count) FROM stats_server WHERE guild_id = $1 AND created_at > current_timestamp -
               interval '7 day' """
        mem_7 = await self.bot.db.fetch_row(query, ctx.guild.id)

        # Get the messages for last 24 hours of the server
        query = """SELECT SUM(member_count) FROM stats_server WHERE guild_id = $1 AND created_at > current_timestamp -
               interval '1 day' """
        mem_1 = await self.bot.db.fetch_row(query, ctx.guild.id)

        query = """SELECT created_at,SUM(member_count) FROM stats_server WHERE guild_id= $1 GROUP BY created_at ORDER BY
               created_at ASC; """
        data = await self.bot.db.fetch(query, ctx.guild.id)

        dates = []
        message = []
        for i in range(len(data)):
            dates.append(data[i].get("created_at"))
            message.append(data[i].get("sum"))

        # plot the graph
        plot(dates, message)
        file = discord.File("./foo.png", filename="foo.png")

        embed = discord.Embed(
            title=f"Server stats for {ctx.guild.name}\n",
            timestamp=datetime.datetime.utcnow(),
            colour=discord.Colour.blurple(),
        )
        embed.add_field(
            name=f"Total Members: {len([i for i in ctx.guild.members if not i.bot])}\n"
            f"Total Bots: {len([i for i in ctx.guild.members if i.bot])}\n",
            value="\u200b",
            inline=False,
        )
        embed.add_field(
            name=f"Member change for last 30 days: {mem_30.get('sum')}",
            value="\u200b",
            inline=False,
        )
        embed.add_field(
            name=f"Member change for last 7 days: {mem_7.get('sum')}",
            value="\u200b",
            inline=False,
        )
        embed.add_field(
            name=f"Member change for last 24 hours: {mem_1.get('sum')}",
            value="\u200b",
            inline=False,
        )
        embed.set_image(url="attachment://foo.png")
        await ctx.send(file=file, embed=embed)
