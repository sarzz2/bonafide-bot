import discord
from discord.ext import commands


def setup(bot: commands.Bot):
    bot.add_cog(Lock(bot=bot))


class Lock(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_check(self, ctx):
        if ctx.author.guild_permissions.administrator:
            return True

    @commands.command()
    async def lockdown(self, ctx):
        """Lockdown the selected channel in the server. Tip: Add all the public channels in the list in case of a raid.
        Do not remove channel from the lockdown list during lockdown as those channels will not be unlocked on running endlockdown then."""
        query = """SELECT lockdown_channel FROM guild WHERE guild_id = $1"""
        lockdown_channel = await self.bot.db.fetch_row(query, ctx.guild.id)
        if lockdown_channel.get("lockdown_channel") is None:
            return await ctx.send("***No channels configured for lockdown***")
        for i in lockdown_channel.get("lockdown_channel"):
            channel = discord.utils.get(ctx.guild.channels, id=i)
            overwrite = channel.overwrites_for(ctx.guild.default_role)
            overwrite.send_messages = False
            await channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)
        await ctx.send(
            f"**{len(lockdown_channel.get('lockdown_channel'))} channels locked.**"
        )

    @commands.command()
    async def endlockdown(self, ctx):
        """Ends the lockdown."""
        query = """SELECT lockdown_channel FROM guild WHERE guild_id = $1"""
        lockdown_channel = await self.bot.db.fetch_row(query, ctx.guild.id)
        if lockdown_channel.get("lockdown_channel") is None:
            return await ctx.send("***No channels configured for lockdown***")
        for i in lockdown_channel.get("lockdown_channel"):
            channel = discord.utils.get(ctx.guild.channels, id=i)
            overwrite = channel.overwrites_for(ctx.guild.default_role)
            overwrite.send_messages = None
            await channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)
        await ctx.send(
            f"**Lockdown ended! {len(lockdown_channel.get('lockdown_channel'))} channels unlocked.**"
        )

    @commands.command()
    async def lock(self, ctx, channel: discord.TextChannel = None):
        """Locks a channel.
        example:
        - lock #general
        - lock
        """
        if channel is None:
            channel = ctx.channel
        overwrite = channel.overwrites_for(ctx.guild.default_role)
        overwrite.send_messages = False
        await channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)
        await ctx.send(f"**Channel <#{channel.id}> locked.**")

    @commands.command()
    async def unlock(self, ctx, channel: discord.TextChannel = None):
        """Unlocks the channel.
        example:
        - unlock #general
        - unlock general"""

        if channel is None:
            channel = ctx.channel
        overwrite = channel.overwrites_for(ctx.guild.default_role)
        overwrite.send_messages = None
        await channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)
        await ctx.send(f"**Channel <#{channel.id}> unlocked.**")

    @commands.command()
    async def add(self, ctx, channel: commands.Greedy[discord.TextChannel]):
        """Adds the channel to the lockdown list.
        example:
        - add #general#help"""
        if not channel:
            return await ctx.send("**Provide at least one channel.**")
        query = """SELECT lockdown_channel FROM guild WHERE guild_id = $1"""
        lockdown_channel = await self.bot.db.fetch_row(query, ctx.guild.id)
        if lockdown_channel.get("lockdown_channel") is None:
            pass
        query = """ UPDATE guild SET lockdown_channel = lockdown_channel || $2 WHERE guild_id = $1"""
        for i in channel:
            if i.id in lockdown_channel.get("lockdown_channel"):
                await ctx.send(f"**<#{i.id}> is already in lockdown channel list.**")
                continue
            await self.bot.db.execute(query, ctx.guild.id, [i.id])
            await ctx.send(f"**<#{i.id}> added to lockdown channel list.**")

    @commands.command()
    async def remove(self, ctx, channel: commands.Greedy[discord.TextChannel]):
        """Removes the channel to the lockdown list.
        example:
        - remove #general#help"""
        if not channel:
            return await ctx.send("**Provide at least one channel.**")
        query = """SELECT lockdown_channel FROM guild WHERE guild_id = $1"""
        lockdown_channel = await self.bot.db.fetch_row(query, ctx.guild.id)
        if lockdown_channel.get("lockdown_channel") is None:
            pass
        query = """ UPDATE guild SET lockdown_channel = lockdown_channel || $2 WHERE guild_id = $1"""

        for i in channel:
            if i.id not in lockdown_channel.get("lockdown_channel"):
                await ctx.send(f"**<#{i.id}> is not in lockdown channel list.**")
                continue
            await self.bot.db.execute(query, ctx.guild.id, [i.id])
            await ctx.send(f"**<#{i.id}> removed from lockdown channel list.**")

    @commands.command()
    async def listlockdownchannels(self, ctx):
        """List all the channels which would get locked on running lockdown."""
        query = """SELECT lockdown_channel FROM guild WHERE guild_id = $1"""
        data = await self.bot.db.fetch_row(query, ctx.guild.id)
        for i in data.get("lockdown_channel"):
            await ctx.send(f"<#{i}>")
