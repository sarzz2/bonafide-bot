from utils.time_converter import convert_time_to_seconds
from discord.ext import commands
import asyncio
import random
import datetime
import discord


def setup(bot: commands.Bot):
    bot.add_cog(Giveaway(bot=bot))


class Giveaway(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_check(self, ctx):
        """Check if the category/cog is enabled"""
        if ctx.author.guild_permissions.administrator:
            return True
        query = (
            """ SELECT * FROM cog_check WHERE guild_id = $1 AND cog_name = 'giveaway'"""
        )
        data = await self.bot.db.fetch_row(query, ctx.guild.id)
        if data.get("enabled") is True:
            return True
        else:
            return False

    @commands.command()
    async def giveaway(self, ctx, time, winners, description):
        """Setup a giveaway
        example:
        - giveaway 1d 3 nitro giveaway"""
        try:
            time = convert_time_to_seconds(time)
        except ValueError:
            return await ctx.send("**Invalid time value.**")

        embed = discord.Embed(
            title="🎉 __**Giveaway**__ 🎉",
            description=f"**Prize: {description}**",
            timestamp=datetime.datetime.utcnow(),
            color=discord.Colour.gold(),
        )
        embed.set_footer(
            text=f"This giveaway ends in {time}. React with 🎉 to enter. {winners} winners."
        )
        embed = await ctx.send(embed=embed)
        await embed.add_reaction("🎉")

        await asyncio.sleep(time)

        message = await ctx.fetch_message(embed.id)
        users = await message.reactions[0].users().flatten()
        users.pop(users.index(ctx.guild.me))

        if len(users) == 0:
            await ctx.send("No winner was decided.")
            return
        for i in range(len(winners)):
            winner = random.choice(users)
            await ctx.send(f"**Congratulations {winner.mention}! You Won!**")

    @commands.command()
    async def reroll(self, ctx, message):
        try:
            *_, channel_id, msg_id = message.split("/")

            try:
                channel = self.bot.get_channel(int(channel_id))
                message = await channel.fetch_message(int(msg_id))
            except:
                return await ctx.send(
                    "**Please provide the message ID/link for a valid giveaway.**"
                )
        except:
            try:
                message = await ctx.channel.fetch_message(message)
            except:
                return await ctx.send(
                    "**Please provide the message ID/link for a valid giveaway.**"
                )

        users = await message.reactions[0].users().flatten()
        users.pop(users.index(ctx.guild.me))

        if len(users) == 0:
            await ctx.send("No winner was decided.")
            return

        winner = random.choice(users)
        await ctx.send(f"**Congratulations {winner.mention}! You Won!**")
