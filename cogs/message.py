import datetime

from discord.ext import commands
import discord
from discord.ext.commands import has_permissions


def setup(bot: commands.Bot):
    bot.add_cog(Message(bot=bot))


class Message(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def server_log_channel(self, guild_id):
        """Get the server logs channel for the current guild"""

        query = """SELECT server_log FROM guild WHERE guild_id = $1"""
        data = await self.bot.db.fetch_row(query, guild_id)
        return self.bot.get_channel(data.get("server_log"))

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        # Ignore messages sent by bot
        if message.author.bot:
            return

        # Check if message cogs is enabled
        query = (
            """ SELECT * FROM cog_check WHERE guild_id = $1 AND cog_name = 'message'"""
        )
        data = await self.bot.db.fetch_row(query, message.guild.id)
        if data.get("enabled") is False:
            return

        embed = discord.Embed(
            title=f"Message deleted by{message.author.mention} in {message.channel.mention}",
            description=message.content,
            colour=discord.Colour.red(),
            timestamp=datetime.datetime.utcnow(),
        )
        embed.set_author(name=message.author, icon_url=message.author.avatar_url)
        x = await self.server_log_channel(message.guild.id)
        channel = self.bot.get_channel(x.id)
        await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_message_edit(self, message_before, message_after):
        # Ignore messages sent by bot
        if message_before.author.bot:
            return

        # Check if message cogs is enabled
        query = (
            """ SELECT * FROM cog_check WHERE guild_id = $1 AND cog_name = 'message'"""
        )
        data = await self.bot.db.fetch_row(query, message_before.guild.id)
        if data.get("enabled") is False:
            return

        embed = discord.Embed(
            title="Jump to message",
            url=message_after.jump_url,
            colour=discord.Colour.blurple(),
            timestamp=datetime.datetime.utcnow(),
        )
        embed.set_author(
            name=message_before.author, icon_url=message_before.author.avatar_url
        )
        embed.add_field(
            name="Message edited by",
            value=f"{message_before.author.mention} in {message_after.channel.mention}",
            inline=False,
        )

        embed.add_field(name="Before", value=message_before.content, inline=False)
        embed.add_field(name="After", value=message_after.content, inline=False)

        x = await self.server_log_channel(message_after.guild.id)
        channel = self.bot.get_channel(x.id)

        await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_reaction_remove(self, reaction, user):
        # Check if stats cogs is enabled
        query = (
            """ SELECT * FROM cog_check WHERE guild_id = $1 AND cog_name = 'message'"""
        )
        data = await self.bot.db.fetch_row(query, user.guild.id)
        if data.get("enabled") is False:
            return

        if reaction.message.author.bot:
            return
        x = await self.server_log_channel(user.guild.id)
        channel = self.bot.get_channel(x.id)
        embed = discord.Embed(
            title="Jump to message",
            url=reaction.message.jump_url,
            colour=discord.Colour.orange(),
            timestamp=datetime.datetime.utcnow(),
        )
        embed.set_author(
            name=reaction.message.author, icon_url=reaction.message.author.avatar_url
        )
        embed.add_field(
            name=f"Reaction {reaction} removed by",
            value=f"{reaction.message.author.mention} in {reaction.message.channel.mention}",
            inline=False,
        )
        await channel.send(embed=embed)

    @commands.command()
    @has_permissions(manage_messages=True)
    async def purge(self, ctx, limit: int, user: discord.Member = None):
        """Purge the number of messages specified in the channel. Can not purge more than 100 at once.
        example:
        - purge 100"""
        if limit > 100:
            await ctx.message.delete(delay=5.0)
            message = await ctx.channel.send(
                "You can not delete more than 100 messages."
            )
            return await message.delete(delay=5.0)

        if discord.Member is not None:
            await ctx.message.channel.purge(
                limit=limit + 1, check=lambda x: (x.author.id == user.id)
            )

        await ctx.channel.purge(limit=limit + 1)
