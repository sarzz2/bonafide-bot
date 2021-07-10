from googleapiclient import discovery
from database.filter import Filter

import os

import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()


def setup(bot: commands.Bot):
    bot.add_cog(Filtering(bot=bot))


class Filtering(commands.Cog):
    API_KEY = os.getenv("google-api-key")

    def __init__(self, bot):
        self.bot = bot

    async def cog_check(self, ctx):
        if ctx.author.guild_permissions.administrator:
            return True

    @commands.Cog.listener()
    async def on_message(self, message):
        await self.bot.wait_until_ready()

        # Ignore messages sent by bot
        if message.author.bot:
            return

        # Check if filter cogs is enabled
        query = (
            """ SELECT * FROM cog_check WHERE guild_id = $1 AND cog_name = 'filter'"""
        )
        data = await self.bot.db.fetch_row(query, message.guild.id)
        if data.get("enabled") is False:
            return

        # # Ignore messages sent by staff
        if message.author.guild_permissions.kick_members:
            return

        # Ignore messages if sent in ignored channel list
        query = """SELECT * FROM guild WHERE guild_id = $1"""
        data = await self.bot.db.fetch_row(query, message.guild.id)

        # Delete invite links
        if data.get("invite_link") is True:
            if "discord.gg/" in message.content:
                await message.delete()
                return await message.channel.send(
                    f"**{message.author.mention} no invite links allowed**"
                )

        # If channel is NSFW profanity and blacklisted words are ignored
        if message.channel.is_nsfw():
            return

        if data.get("filter_ignored_channel") is None:
            pass
        elif message.channel.id in (data.get("filter_ignored_channel")):
            return

        # Check for blacklisted words
        query = """SELECT * FROM filter WHERE guild_id = $1"""
        keyword = await self.bot.db.fetch(query, message.guild.id)

        for i in range(len(keyword)):
            if keyword[i].get("keyword") in message.content:
                await message.delete()
                return await message.channel.send(
                    f"**{message.author.mention} Mind your language!**"
                )

        # Google NLP profanity check
        if data.get("profanity_check") is True:
            client = discovery.build(
                "commentanalyzer",
                "v1alpha1",
                developerKey=self.API_KEY,
                discoveryServiceUrl="https://commentanalyzer.googleapis.com/$discovery/rest?version=v1alpha1",
                static_discovery=False,
            )

            analyze_request = {
                "comment": {"text": message.content},
                "requestedAttributes": {"TOXICITY": {}},
            }

            response = client.comments().analyze(body=analyze_request).execute()
            x = response["attributeScores"]["TOXICITY"]["spanScores"][0]["score"][
                "value"
            ]

            if x > 0.8:
                await message.delete()
                return await message.channel.send(
                    f"**{message.author.mention} Mind your language!**"
                )

    @commands.Cog.listener()
    async def on_message_edit(self, message_before, message_after):
        await self.bot.wait_until_ready()

        # Ignore messages sent by bot
        if message_before.author.bot:
            return

        # Check if filter cogs is enabled
        query = (
            """ SELECT * FROM cog_check WHERE guild_id = $1 AND cog_name = 'filter'"""
        )
        data = await self.bot.db.fetch_row(query, message_before.guild.id)
        if data.get("enabled") is False:
            return

        # # Ignore messages sent by staff
        if message_before.author.guild_permissions.kick_members:
            return

        # Ignore messages if sent in ignored channel list
        query = """SELECT * FROM guild WHERE guild_id = $1"""
        data = await self.bot.db.fetch_row(query, message_before.guild.id)

        # If channel is NSFW profanity and blacklisted words are ignored
        if message_before.channel.is_nsfw():
            return

        if data.get("filter_ignored_channel") is None:
            pass
        elif message_before.channel.id in (data.get("filter_ignored_channel")):
            return

        # Check for blacklisted words
        query = """SELECT * FROM filter WHERE guild_id = $1"""
        keyword = await self.bot.db.fetch(query, message_before.guild.id)

        for i in range(len(keyword)):
            if keyword[i].get("keyword") in message_after.content:
                await message_after.delete()
                return await message_after.channel.send(
                    f"**{message_after.author.mention} Mind your language!**"
                )

        # Google NLP profanity check
        if data.get("profanity_check") is True:
            client = discovery.build(
                "commentanalyzer",
                "v1alpha1",
                developerKey=self.API_KEY,
                discoveryServiceUrl="https://commentanalyzer.googleapis.com/$discovery/rest?version=v1alpha1",
                static_discovery=False,
            )

            analyze_request = {
                "comment": {"text": message_after.content},
                "requestedAttributes": {"TOXICITY": {}},
            }

            response = client.comments().analyze(body=analyze_request).execute()
            x = response["attributeScores"]["TOXICITY"]["spanScores"][0]["score"][
                "value"
            ]

            if x > 0.8:
                await message_after.delete()
                return await message_after.channel.send(
                    f"**{message_after.author.mention} Mind your language!**"
                )

    @commands.command()
    async def blacklist(self, ctx, *, query: str):
        """Add a word to blacklist. Members with kick members permission bypass it. Enable profanity filter for blacklisting words like fuck, bitch etc.
        example:
        - blacklist xyz"""
        query = await commands.clean_content().convert(ctx=ctx, argument=query)
        query = query.lower()

        data = await Filter(self.bot).get(ctx.guild.id, query)
        if data is not None:
            return await ctx.send(f"**{query} is already in blacklisted list.**")
        await Filter(self.bot).post(ctx.guild.id, query)
        return await ctx.send(f"**{query} added to blacklisted words.**")

    @commands.command()
    async def whitelist(self, ctx, *, query):
        """Remove a word from blacklist.
        example:
        - whitelist xyz"""
        query = await commands.clean_content().convert(ctx=ctx, argument=query)
        query = query.lower()

        data = await Filter(self.bot).get(ctx.guild.id, query)
        if data is None:
            return await ctx.send(f"**{query} is not whitelisted.**")

        await Filter(self.bot).delete(ctx.guild.id, query)
        return await ctx.send(f"{query} removed to blacklisted words.")

    @commands.command()
    async def filterlist(self, ctx):
        query = """SELECT * FROM filter WHERE guild_id = $1"""
        data = await self.bot.db.fetch(query, ctx.guild.id)

        keyword = "```"
        for i in range(len(data)):
            keyword += data[i].get("keyword") + "\n"
        keyword += "```"
        return await ctx.send(keyword)

    @commands.command()
    async def addchannel(self, ctx, channel: discord.TextChannel):
        """Add a channel to ignored list for filtering. NSFW channel are ignored by default.
        example:
        - addchannel #general"""

        query = """SELECT filter_ignored_channel FROM guild WHERE guild_id = $1"""
        ignored_channel = await self.bot.db.fetch_row(query, ctx.guild.id)
        if ignored_channel.get("filter_ignored_channel") is None:
            pass
        elif channel.id in ignored_channel.get("filter_ignored_channel"):
            return await ctx.send(
                f"**<#{channel.id}> is already in ignored channel list.**"
            )

        query = """UPDATE guild SET filter_ignored_channel = filter_ignored_channel || $2 WHERE guild_id = $1"""
        await self.bot.db.execute(query, ctx.guild.id, [channel.id])
        return await ctx.send(
            f"**{channel.mention} added to ignored list for filter.**"
        )

    @commands.command()
    async def removechannel(self, ctx, channel: discord.TextChannel):
        """Remove a channel from ignored filter list
        example:
        - removechannel #general"""

        query = """SELECT filter_ignored_channel FROM guild WHERE guild_id = $1"""
        ignored_channel = await self.bot.db.fetch_row(query, ctx.guild.id)
        if ignored_channel.get("filter_ignored_channel") is None:
            pass
        elif channel.id not in ignored_channel.get("filter_ignored_channel"):
            return await ctx.send(
                f"**<#{channel.id}> is not in ignored channel list.**"
            )

        query = """UPDATE guild SET filter_ignored_channel = array_remove(filter_ignored_channel, $2) WHERE guild_id
        = $1 """
        await self.bot.db.execute(query, ctx.guild.id, channel.id)
        return await ctx.send(
            f"**{channel.mention} removed from ignored list for filter.**"
        )

    @commands.command()
    async def profanity(self, ctx, toggle: str):
        """Enable AI profanity check.
        example:
        - profanity true
        - profanity false"""

        if toggle.lower() == "true":
            query = """UPDATE guild SET profanity_check = true WHERE guild_id=$1"""
            await self.bot.db.execute(query, ctx.guild.id)
            await ctx.send("**Profanity check enabled.**")
        elif toggle.lower() == "false":
            query = """UPDATE guild SET profanity_check = false WHERE guild_id=$1"""
            await self.bot.db.execute(query, ctx.guild.id)
            await ctx.send("**Profanity check disabled.**")
        else:
            await ctx.send("**toggle value is either True or False**")

    @commands.command()
    async def invite_link(self, ctx, toggle):
        """Remove any discord invite links posted. Ignored channel will not trigger."""

        if toggle.lower() == "true":
            query = """UPDATE guild SET invite_link = true WHERE guild_id=$1"""
            await self.bot.db.execute(query, ctx.guild.id)
            await ctx.send("**Invite links will be deleted.**")
        elif toggle.lower() == "false":
            query = """UPDATE guild SET invite_link = false WHERE guild_id=$1"""
            await self.bot.db.execute(query, ctx.guild.id)
            await ctx.send("**Invite links will not be deleted.**")
        else:
            await ctx.send("**toggle value is either True or False**")
