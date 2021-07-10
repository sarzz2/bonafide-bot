from discord.ext import commands
import datetime
import discord


def setup(bot: commands.Bot):
    bot.add_cog(BasicSetup(bot=bot))


class BasicSetup(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_check(self, ctx):
        if ctx.author.guild_permissions.administrator:
            return True

    @commands.command()
    async def setup(self, ctx):
        """Add logs channel to the server"""
        query = """ SELECT server_log, mod_log FROM guild WHERE guild_id = $1"""
        data = await self.bot.db.fetch_row(query, ctx.guild.id)
        if data.get("server_log") is not None:
            return await ctx.channel.send(
                f"<#{data.get('server_log')}> and <#{data.get('mod_log')}> exists in LOGS"
                f" category. Delete the channels to do setup again or use update command to "
                f"update the channel id."
            )
        category = ctx.guild.categories

        if "LOGS" in str(category):
            await ctx.channel.send(
                "Category LOG exists. Skipping creating the category."
            )
            logs = discord.utils.get(ctx.guild.categories, name="LOGS")

        else:
            logs = await ctx.guild.create_category_channel(
                "LOGS",
                overwrites={
                    ctx.guild.default_role: discord.PermissionOverwrite(
                        view_channel=False,
                        read_messages=False,
                        send_messages=False,
                    )
                },
            )

        server_log = await ctx.guild.create_text_channel(
            "server-logs", category=logs, sync_permissions=True
        )
        mod_log = await ctx.guild.create_text_channel(
            "mod-logs", category=logs, sync_permissions=True
        )

        await ctx.channel.send("**Setup Complete**")
        query = (
            """UPDATE guild SET server_log = $2, mod_log = $3 WHERE guild_id = $1 """
        )
        await self.bot.db.execute(
            query, ctx.guild.id, int(server_log.id), int(mod_log.id)
        )

    @commands.command()
    async def update(self, ctx, to_update, channel):
        """Update the server log or mod log channel
        example:
        - update server-logs #channel-name
        - update mod-logs #channel-name"""
        char = ["<", ">", "#"]
        for i in char:
            channel = channel.replace(i, "")
        if to_update == "server-logs":
            query = """ UPDATE guild  SET server_log = $2 WHERE guild_id = $1"""
            await self.bot.db.execute(query, ctx.guild.id, int(channel))
        elif to_update == "mod-logs":
            query = """ UPDATE guild  SET mod_log = $2 WHERE guild_id = $1"""
            await self.bot.db.execute(query, ctx.guild.id, int(channel))

        return await ctx.channel.send(f"{to_update} has been updated to <#{channel}>")

    @commands.command()
    async def prefix(self, ctx, p):
        """Update prefix for the server
        example:
        - prefix ?"""
        if len(p) > 5:
            return await ctx.channel.send("Length of prefix can not be more than 5")

        query = """UPDATE guild SET prefix = $2 WHERE guild_id = $1"""
        await self.bot.db.execute(query, ctx.guild.id, p)
        return await ctx.channel.send(
            embed=discord.Embed(
                title=f"Prefix for bot updated to {p}",
                timestamp=datetime.datetime.utcnow(),
            )
        )

    @commands.command()
    async def ignorechannel(self, ctx, channel: discord.TextChannel):
        """Add channel to the ignored list for xp gain"""
        query = """SELECT ignored_channel FROM guild WHERE guild_id = $1"""
        ignored_channel = await self.bot.db.fetch_row(query, ctx.guild.id)
        if ignored_channel.get("ignored_channel") is None:
            pass
        elif channel.id in ignored_channel.get("ignored_channel"):
            return await ctx.send(
                f"**<#{channel.id}> is already in ignored channel list.**"
            )

        query = """ UPDATE guild SET ignored_channel = ignored_channel || $2 WHERE guild_id = $1"""
        await self.bot.db.execute(query, ctx.guild.id, [channel.id])
        return await ctx.send(f"**<#{channel.id}> added to ignored list for xp.**")

    @commands.command()
    async def unignorechannel(self, ctx, channel: discord.TextChannel):
        """Remove channel from the ignored list for the xp gain"""
        query = """ SELECT ignored_channel FROM guild WHERE guild_id = $1"""
        ignored_channel = await self.bot.db.fetch_row(query, ctx.guild.id)
        if ignored_channel.get("ignored_channel") is None:
            pass
        elif channel.id not in ignored_channel.get("ignored_channel"):
            return await ctx.send(
                f"**<#{channel.id}> is not in ignored channel list.**"
            )

        query = """UPDATE guild SET ignored_channel = array_remove(ignored_channel, $2) WHERE guild_id = $1"""
        await self.bot.db.execute(query, ctx.guild.id, channel.id)
        return await ctx.send(
            f"**<#{channel.id}> has been removed from ignored list for xp.**"
        )

    # TODO set this and perms
    # @commands.command()
    # async def toggle(self, ctx, type: str, cmd):
    #
    #     if cmd in self.bot.commands:
    #         if type.lower() == "disable":
    #             query = (
    #                 """ SELECT * FROM command WHERE guild_id = $1 AND command = $2"""
    #             )
    #             data = await self.bot.db.fetch_row(query, ctx.guild.id, cmd)
    #             # If command is in db then it is disabled
    #             if data:
    #                 query = """ INSERT INTO command (guild_id, cmd, enabled) VALUES ($1, $2, $3)"""
    #                 await self.bot.db.execute(query, ctx.guild.id, cmd, True)
    #                 return await ctx.send(
    #                     f"Command {cmd} has been disabled for everyone except admin privileges."
    #                 )
    #             else:
    #                 return await ctx.send(f"Command {cmd} is already disabled")
    #
    #         else:
    #             query = (
    #                 """ SELECT * FROM command WHERE guild_id = $1 AND command = $2"""
    #             )
    #             data = await self.bot.db.fetch_row(query, ctx.guild.id, cmd)
    #             # if command is not there in db then it's enabled
    #             if not data:
    #                 query = """ INSERT INTO command (guild_id, cmd, enabled) VALUES ($1, $2, $3)"""
    #                 await self.bot.db.execute(query, ctx.guild.id, cmd, True)
    #                 return await ctx.send(
    #                     f"Command {cmd} has been enabled for everyone."
    #                 )
    #             else:
    #                 return await ctx.send(f"Command {cmd} is already enabled")
    #
    #     else:
    #         await ctx.send(
    #             f"Command {cmd} not found. Type .help for list of all commands."
    #         )
