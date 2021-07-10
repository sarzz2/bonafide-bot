from discord.ext.commands.errors import UserNotFound
from discord.ext.commands import has_permissions
from discord.ext import commands, tasks
import datetime
import discord

from utils.time_converter import convert_time_to_seconds
from utils.paginators import EmbedReactionPaginator
from database.mod_logs import ModLogs
from database.roles import Roles


def setup(bot: commands.Bot):
    bot.add_cog(Moderation(bot=bot))


class Moderation(commands.Cog):
    def __init__(self, bot):
        self.auto_unmute.start()
        self.auto_unpunish.start()
        self.bot = bot

    async def mod_log_channel(self, guild_id):
        """Get the mod logs channel for the current guild"""

        query = """SELECT mod_log FROM guild WHERE guild_id=$1"""
        data = await self.bot.db.fetch_row(query, guild_id)
        return self.bot.get_channel(data.get("mod_log"))

    # Mod logs channel embed
    async def mod_log_embed(self, type, member, reason, author):
        query = """SELECT case_no FROM mod_logs WHERE guild_id = $1 ORDER BY case_no DESC LIMIT 1;"""
        x = await self.bot.db.fetch(query, author.guild.id)

        if not x:
            case_no = 1
        else:
            case_no = x[-1].get("case_no") + 1
        modlog_embed = discord.Embed(
            title=f"Case {case_no} | {type}",
            timestamp=datetime.datetime.utcnow(),
            colour=discord.Colour.red(),
        )
        modlog_embed.add_field(name="User", value=member)
        modlog_embed.add_field(name="Moderator", value=author.mention)
        modlog_embed.add_field(name="Reason", value=reason)
        return modlog_embed

    async def post_mod_log_to_db(
        self, type, member, reason, author, message_id, duration=None
    ):
        query = """SELECT case_no FROM mod_logs WHERE guild_id = $1 ORDER BY case_no DESC LIMIT 1;"""
        x = await self.bot.db.fetch(query, author.guild.id)

        if not x:
            case_no = 1
        else:
            case_no = x[-1].get("case_no") + 1
        x = ModLogs(
            bot=self.bot,
            guild_id=author.guild.id,
            user_id=member,
            moderator=author.id,
            reason=reason,
            type=type,
            case_no=case_no,
            message_id=message_id,
            duration=duration,
        )
        await x.post()

    @commands.command()
    @has_permissions(ban_members=True)
    async def ban(self, ctx, member: discord.User, *, reason=None):
        """Bans the specified member from the guild"""
        # If the user tries to ban himself
        if member == ctx.message.author:
            return await ctx.channel.send("You cannot ban yourself")

        message = f"You have been banned from {ctx.guild.name} for {reason}"
        # Ban the member
        await ctx.guild.ban(member, reason=reason)

        # Send the log in mod logs channel
        embed = await self.mod_log_embed(
            "BAN", member.mention, reason, ctx.message.author
        )
        x = await self.mod_log_channel(ctx.guild.id)
        await x.send(embed=embed)

        # Save the log in DB
        await self.post_mod_log_to_db(
            "BAN", member.mention, reason, ctx.message.author, x.last_message_id
        )

        # Try to DM the member if fails returns the message stating so
        try:
            await member.send(message)
        except:
            return await ctx.channel.send(
                embed=discord.Embed(
                    title=f"{member.mention} is banned! I couldn't DM them."
                )
            )

        return await ctx.channel.send(
            embed=discord.Embed(title=f"{member.mention} is banned!")
        )

    @commands.command()
    @has_permissions(ban_members=True)
    async def bansave(self, ctx, member: discord.User, *, reason=None):
        """Bans the specified member from the guild"""
        # If the user tries to ban himself
        if member == ctx.message.author:
            return await ctx.channel.send("You cannot ban yourself")

        message = f"You have been banned from {ctx.guild.name} for {reason}"
        # Ban the member
        await ctx.guild.ban(member, reason=reason, delete_message_days=0)

        # Send the log in mod logs channel
        embed = await self.mod_log_embed(
            "BAN", member.mention, reason, ctx.message.author
        )
        x = await self.mod_log_channel(ctx.guild.id)
        await x.send(embed=embed)

        # Save the log in DB
        await self.post_mod_log_to_db(
            "BAN", member.mention, reason, ctx.message.author, x.last_message_id
        )

        # Try to DM the member if fails returns the message stating so
        try:
            await member.send(message)
        except:
            return await ctx.channel.send(
                embed=discord.Embed(
                    title=f"{member.mention} is banned! I couldn't DM them."
                )
            )

        return await ctx.channel.send(
            embed=discord.Embed(title=f"{member.mention} is banned!")
        )

    @commands.command()
    @has_permissions(ban_members=True)
    async def unban(self, ctx, member: discord.User, *, reason=None):
        """Unbans the member from the guild"""
        # Check if member is banned or not
        if member in ctx.guild.members:
            return await ctx.channel.send(
                embed=discord.Embed(title=f"{member.mention}is already unbanned")
            )

        message = discord.Embed(
            title=f"{member.mention} has been unbanned",
            timestamp=datetime.datetime.utcnow(),
        )
        # Unbans the user
        await ctx.guild.unban(member, reason=reason)

        # Send the log in mod logs channel
        embed = await self.mod_log_embed(
            "UNBAN", member.mention, reason, ctx.message.author
        )
        x = await self.mod_log_channel(ctx.guild.id)
        await x.send(embed=embed)

        # Save the log in DB
        await self.post_mod_log_to_db(
            "UNBAN", member.mention, reason, ctx.message.author, x.last_message_id
        )
        await ctx.channel.send(embed=message)

    @commands.command()
    @has_permissions(kick_members=True)
    async def kick(self, ctx, member: discord.User, *, reason=None):
        """Kick the member from the guild"""
        if member == ctx.message.author:
            return await ctx.channel.send("You cannot kick yourself")

        # Kick the user from the guild return error if user not found
        try:
            await ctx.guild.kick(member, reason=reason)
        except UserNotFound:
            return await ctx.channel.send(
                embed=discord.Embed(title=f"{member.mention} not Found!")
            )

        message = f"You have been kicked from {ctx.guild.name} for {reason}"

        # Send the log in mod logs channel
        embed = await self.mod_log_embed(
            "KICK", member.mention, reason, ctx.message.author
        )

        x = await self.mod_log_channel(ctx.guild.id)
        await x.send(embed=embed)

        # Save the log in DB
        await self.post_mod_log_to_db(
            "KICK", member.mention, reason, ctx.message.author, x.last_message_id
        )
        # DM the user, returns error if couldn't DM
        try:
            await member.send(message)
        except:
            return await ctx.channel.send(
                embed=discord.Embed(
                    title=f"{member.name} is kicked! I couldn't DM them."
                )
            )

        return await ctx.channel.send(
            embed=discord.Embed(
                title=f"{member} has been kicked", timestamp=datetime.datetime.utcnow()
            )
        )

    @commands.command()
    @has_permissions(kick_members=True)
    async def mute(
        self,
        ctx,
        member: discord.Member,
        time=None,
        *,
        reason=None,
    ):
        """Adds the muted rule to the specified member in the guild"""
        # If user tries to mute himself
        if member == ctx.message.author:
            return await ctx.channel.send("You cannot mute yourself")

        # Convert m/h/d to seconds
        try:
            time = convert_time_to_seconds(time)
        except ValueError:
            return await ctx.send("**Invalid time value**")

        # Get the role from the guild
        guild = ctx.guild
        muted_role = discord.utils.get(guild.roles, name="Muted")
        # Create a muted role if it doesn't exist
        if not muted_role:
            muted_role = await guild.create_role(name="Muted")
            # Set permission for the role
            for channel in guild.channels:
                await channel.set_permissions(
                    muted_role,
                    speak=False,
                    manage_channels=False,
                    send_messages=False,
                    read_message_history=True,
                    read_messages=True,
                    connect=False,
                )
        # Check to see if member is already muted
        if muted_role in member.roles:
            return await ctx.channel.send(
                embed=discord.Embed(
                    title=f"{member} is already muted!",
                    timestamp=datetime.datetime.utcnow(),
                )
            )

        persistent_role = Roles(
            bot=self.bot,
            guild_id=ctx.guild.id,
            user_id=member.id,
            roles=muted_role.id,
        )

        # Add the muted role
        await member.add_roles(muted_role)
        # Post to db for persistent role
        await persistent_role.post()

        # Send the message to user if fails, returns string stating so
        try:
            await member.send(
                f"You have been muted from: {ctx.guild.name} for {reason}"
            )
            channel_embed = discord.Embed(
                title=f"{member} has been muted!", timestamp=datetime.datetime.utcnow()
            )
        except:
            channel_embed = discord.Embed(
                title=f"{member.name} is muted! I couldn't DM them."
            )

        mod_log_embed = await self.mod_log_embed(
            "MUTE", member.mention, reason, ctx.message.author
        )
        # Add duration field to the log
        mod_log_embed.add_field(name="Duration:", value=f"{time}", inline=False)
        # Send the log
        x = await self.mod_log_channel(ctx.guild.id)
        await x.send(embed=mod_log_embed)

        await ctx.channel.send(embed=channel_embed)

        # Save the log to the DB
        if time is not None:
            duration = datetime.datetime.utcnow() + datetime.timedelta(seconds=time)
        else:
            duration = None
        await self.post_mod_log_to_db(
            "MUTE",
            member.id,
            reason,
            ctx.message.author,
            x.last_message_id,
            duration,
        )

    @tasks.loop(seconds=10)
    async def auto_unmute(self):
        query = """SELECT * FROM mod_logs WHERE type='MUTE'"""
        data = await self.bot.db.fetch(query)

        for i in range(len(data)):
            if data[i].get("action"):
                if data[i].get("duration") is None:
                    pass
                elif data[i].get("duration") <= datetime.datetime.utcnow():
                    guild = self.bot.get_guild(data[i].get("guild_id"))
                    muted_role = discord.utils.get(guild.roles, name="Muted")

                    member = guild.get_member(data[i].get("user_id"))
                    query = """UPDATE mod_logs SET action = false WHERE guild_id=$1 AND user_id=$2 AND type='MUTE'"""
                    await self.bot.db.execute(query, guild.id, member.id)
                    # Delete the role from db once time is over and remove the role
                    if muted_role in member.roles:
                        persistent_role = Roles(
                            bot=self.bot,
                            guild_id=guild.id,
                            user_id=member.id,
                            roles=muted_role.id,
                        )
                        await persistent_role.delete()
                        await member.remove_roles(muted_role)

                        moderator = guild.get_member(data[i].get("moderator"))
                        reason = "Auto"
                        unmute_embed = await self.mod_log_embed(
                            "UNMUTE", member, reason, moderator
                        )

                        # Send the auto unmute log
                        x = await self.mod_log_channel(guild.id)
                        await x.send(embed=unmute_embed)

                        # Save the log to the DB
                        await self.post_mod_log_to_db(
                            "UNMUTE", member.id, reason, moderator, x.last_message_id
                        )

    @commands.command()
    @has_permissions(kick_members=True)
    async def unmute(self, ctx, member: discord.Member, *, reason=None):
        """Removes the muted role from the user in the guild"""
        muted_role = discord.utils.get(ctx.guild.roles, name="Muted")

        # Check to see if the user is muted
        if muted_role in member.roles:
            persistent_role = Roles(
                bot=self.bot,
                guild_id=ctx.guild.id,
                user_id=member.id,
                roles=muted_role.id,
            )

            # Remove the role from user
            await member.remove_roles(muted_role)
            # Delete the role from database
            await persistent_role.delete()

            # Send the log
            unmute_embed = await self.mod_log_embed(
                "UNMUTE", member.mention, reason, ctx.message.author
            )
            x = await self.mod_log_channel(ctx.guild.id)
            await x.send(embed=unmute_embed)

            # Save the log to DB
            await self.post_mod_log_to_db(
                "UNMUTE", member.mention, reason, ctx.message.author, x.last_message_id
            )
            return await ctx.channel.send(
                embed=discord.Embed(
                    title=f"{member} has been unmuted!",
                    timestamp=datetime.datetime.utcnow(),
                )
            )

        return await ctx.channel.send(
            embed=discord.Embed(
                title=f"{member} is not muted!", timestamp=datetime.datetime.utcnow()
            )
        )

    @commands.command()
    @has_permissions(kick_members=True)
    async def punish(
        self,
        ctx,
        member: discord.Member,
        time: int = None,
        *,
        reason=None,
    ):
        """Adds the punished role to the user in the guild so he can't add reactions/embed/send files."""
        # If user tries to punish himself
        if member == ctx.message.author:
            return await ctx.channel.send("You cannot punish yourself")

        try:
            time = convert_time_to_seconds(time)
        except ValueError:
            return await ctx.send("**Invalid time value**")

        # Get the punished role
        guild = ctx.guild
        punished_role = discord.utils.get(guild.roles, name="Punished")

        # Create a punished role if it doesn't exist
        if not punished_role:
            punished_role = await guild.create_role(name="Punished")
            #  Set permission for the role
            for channel in guild.channels:
                await channel.set_permissions(
                    punished_role,
                    send_messages=True,
                    read_message_history=True,
                    read_messages=True,
                    embed_links=False,
                    attach_files=False,
                    add_reactions=False,
                )

        # Check if the user is already punished
        if punished_role in member.roles:
            return await ctx.channel.send(
                embed=discord.Embed(title=f"{member} is already punished!")
            )

        persistent_role = Roles(
            bot=self.bot,
            guild_id=ctx.guild.id,
            user_id=member.id,
            roles=punished_role.id,
        )

        # Add the role to user
        await member.add_roles(punished_role)
        # Post to db for persistent role
        await persistent_role.post()

        # Send the DM to user, if fails return saying so
        try:
            await member.send(
                f"You have been punished in: {ctx.guild.name} for {reason}"
            )
            channel_embed = discord.Embed(
                title=f"{member} has been Punished!",
                timestamp=datetime.datetime.utcnow(),
            )
        except:
            channel_embed = discord.Embed(
                title=f"{member} is Punished! I couldn't DM them.",
                timestamp=datetime.datetime.utcnow(),
            )

        embed = await self.mod_log_embed(
            "PUNISH", member.mention, reason, ctx.message.author
        )
        embed.add_field(name="Duration:", value=f"{time}", inline=False)

        x = await self.mod_log_channel(ctx.guild.id)
        await x.send(embed=embed)

        if time is not None:
            duration = datetime.datetime.utcnow() + datetime.timedelta(seconds=time)
        else:
            duration = ""

        # Save the log to the DB
        await self.post_mod_log_to_db(
            "PUNISH",
            member.mention,
            reason,
            ctx.message.author,
            x.last_message_id,
            duration,
        )
        await ctx.channel.send(embed=channel_embed)

    @tasks.loop(seconds=10)
    async def auto_unpunish(self):
        query = """SELECT * FROM mod_logs WHERE type='PUNISH'"""
        data = await self.bot.db.fetch(query)

        for i in range(len(data)):
            if data[i].get("action"):
                if data[i].get("duration") is None:
                    pass
                elif data[i].get("duration") <= datetime.datetime.utcnow():

                    guild = self.bot.get_guild(data[i].get("guild_id"))
                    muted_role = discord.utils.get(guild.roles, name="Punished")

                    member = guild.get_member(data[i].get("user_id"))

                    query = """UPDATE mod_logs SET action=false WHERE guild_id=$1 AND user_id=$2 AND type='PUNISH'"""
                    await self.bot.db.execute(query, guild.id, member.id)
                    # Delete the role from db once time is over and remove the role
                    if muted_role in member.roles:
                        persistent_role = Roles(
                            bot=self.bot,
                            guild_id=guild.id,
                            user_id=member.id,
                            roles=muted_role.id,
                        )
                        await persistent_role.delete()
                        await member.remove_roles(muted_role)

                        moderator = guild.get_member(data[i].get("moderator"))
                        reason = "Auto"
                        unmute_embed = await self.mod_log_embed(
                            "UNPUNISH", member, reason, moderator
                        )

                        # Send the auto unpunish log
                        x = await self.mod_log_channel(guild.id)
                        await x.send(embed=unmute_embed)

                        # Save the log to the DB
                        await self.post_mod_log_to_db(
                            "UNPUNISH", member.id, reason, moderator, x.last_message_id
                        )

    @commands.command()
    @has_permissions(kick_members=True)
    async def unpunish(self, ctx, member: discord.Member, *, reason=None):
        """Remove the punished role from user in the guild"""
        punished_role = discord.utils.get(ctx.guild.roles, name="Punished")

        # Remove the role if user has it
        if punished_role in member.roles:
            persistent_role = Roles(
                bot=self.bot,
                guild_id=ctx.guild.id,
                user_id=member.id,
                roles=punished_role.id,
            )
            await persistent_role.delete()

            await member.remove_roles(punished_role)

            # Send the log in mod logs channel
            embed = await self.mod_log_embed(
                "UNPUNISH", member.mention, reason, ctx.message.author
            )

            x = await self.mod_log_channel(ctx.guild.id)
            await x.send(embed=embed)

            # Store the log in DB
            await self.post_mod_log_to_db(
                "UNPUNISH",
                member.mention,
                reason,
                ctx.message.author,
                x.last_message_id,
            )

            return await ctx.channel.send(
                embed=discord.Embed(
                    title=f"{member} has been UNPUNISHED!",
                    timestamp=datetime.datetime.utcnow(),
                )
            )

        return await ctx.channel.send(
            embed=discord.Embed(
                title=f"{member} is not Punished!", timestamp=datetime.datetime.utcnow()
            )
        )

    @commands.command()
    @has_permissions(kick_members=True)
    async def warn(self, ctx, member: discord.Member, *, reason):
        """Log a warning and DM the user in the guild for violating rules"""
        # Send the warning to the user, if fails return error saying so
        try:
            await member.send(
                f"**You have been warned in: {ctx.guild.name} for {reason}**"
            )
            channel_embed = discord.Embed(
                title=f"{member} has been Warned!",
                timestamp=datetime.datetime.utcnow(),
            )
        except:
            channel_embed = discord.Embed(
                title=f"{member} is Warned! I couldn't DM them.",
                timestamp=datetime.datetime.utcnow(),
            )

        # Send the log
        embed = await self.mod_log_embed(
            "WARN", member.mention, reason, ctx.message.author
        )
        await ctx.channel.send(embed=channel_embed)
        x = await self.mod_log_channel(ctx.guild.id)

        await x.send(embed=embed)

        # Save the log to DB
        await self.post_mod_log_to_db(
            "WARN", member.mention, reason, ctx.message.author, x.last_message_id
        )

    @commands.command()
    @has_permissions(kick_members=True)
    async def delwarn(self, ctx, case_id: int):
        """Delete a warning for the user."""
        query = """SELECT * FROM mod_logs WHERE guild_id = $1 AND case_no= $2"""
        data = await self.bot.db.fetch_row(query, ctx.guild.id, case_id)

        if data is None:
            return await ctx.send(f"Case with ID {case_id} does not exist")
        if data.get("type") == "WARN":
            query = """DELETE FROM mod_logs WHERE  guild_id = $1 AND case_no= $2"""
            await self.bot.db.execute(query, ctx.guild.id, case_id)
            return await ctx.send(
                f"Warning for Case no {case_id} deleted successfully!"
            )

        return await ctx.send("Not a valid warn log")

    @commands.command()
    @has_permissions(kick_members=True)
    async def modlogs(self, ctx, member: discord.Member, filter: str = None):
        """Show all the logs for a user in the guild"""
        # Filters the unmutes and unpunish logs else shows all
        if filter == "infractions":
            query = """
            SELECT * FROM mod_logs WHERE guild_id = $1 and user_id = $2 and type = any('{MUTE,BAN,PUNISH,KICK}')
            """
            data = await self.bot.db.fetch(
                query, member.guild.id, member.mention, filter
            )
            embed = discord.Embed(
                title=f"{filter} Modlogs for *{member}* ({member.id})",
                timestamp=datetime.datetime.utcnow(),
            )

        else:
            query = "SELECT * FROM mod_logs WHERE guild_id = $1 and user_id = $2"
            data = await self.bot.db.fetch(query, member.guild.id, member.mention)
            embed = discord.Embed(
                title=f"All Modlogs for *{member}* ({member.id})",
                timestamp=datetime.datetime.utcnow(),
                colour=discord.Colour.blurple(),
            )
            embed.add_field(name="\u200b", value=f"***Total {len(data)} logs found.***")
            embed.set_author(name=member.display_name, icon_url=member.avatar_url)

        x = ""
        # Make and send the embed
        for i in range(len(data)):
            x += f"**Case** {data[i].get('case_no')}\n**Type:** {data[i].get('type')} \n **Moderator:** {data[i].get('moderator')} \n **Reason:** {data[i].get('reason')} \n **Date:** {data[i].get('created_at')}\n\n"

        # If no logs found in DB
        if not data:
            return await ctx.channel.send(
                embed=discord.Embed(
                    title=f"No modlogs found for *{member}*",
                    timestamp=datetime.datetime.utcnow(),
                )
            )

        else:
            pag = EmbedReactionPaginator.paginate(
                x,
                bot=self.bot,
                embed=embed,
                page_size=504,
                prefix="",
                suffix="",
                owner=ctx.author,
            )

            await pag.send_to(ctx.channel)

    @commands.command()
    @has_permissions(kick_members=True)
    async def reason(self, ctx, case: int, *, reason):
        """Update the reason for an infraction"""
        query = "SELECT * FROM mod_logs WHERE guild_id = $1 AND case_no = $2;"
        data = await self.bot.db.fetch_row(query, ctx.guild.id, case)
        # Return error if case number not found
        if not data:
            return await ctx.channel.send(
                embed=discord.Embed(
                    title=f"Case {case} not found!",
                    timestamp=datetime.datetime.utcnow(),
                    colour=discord.Colour.darker_grey(),
                )
            )
        # Update the reason in database for the case_no
        query2 = """UPDATE mod_logs SET reason=$1 WHERE case_no = $2, guild_id = $3"""
        await self.bot.db.execute(query2, reason, case, ctx.guild.id)

        # Edit the embed in the log channel
        mod_log_channel_id = await self.mod_log_channel(ctx.guild.id)
        msg = await mod_log_channel_id.fetch_message(data.get("message_id"))

        modlog_embed = discord.Embed(
            title=f"Case {data.get('case_no')} | {data.get('type')}",
            timestamp=datetime.datetime.utcnow(),
            colour=discord.Colour.red(),
        )
        modlog_embed.add_field(name="User", value=f"{data.get('user_id')}")
        modlog_embed.add_field(name="Moderator", value=f"{data.get('moderator')}")
        modlog_embed.add_field(name="Reason", value=f"{reason}")
        if data.get("duration") is not None:
            modlog_embed.add_field(name="Duration", value=data.get("duration"))
        await msg.edit(embed=modlog_embed)
        return await ctx.channel.send(
            embed=discord.Embed(
                title=f"Case {case} updated!",
                timestamp=datetime.datetime.utcnow(),
                colour=discord.Colour.blurple(),
            )
        )

    @commands.command()
    @has_permissions(kick_members=True)
    async def moderations(self, ctx, member: discord.Member = None):
        """Shows all the mod actions taken by a user(staff)"""
        # If no argument provided then return moderation for author
        if member is None:
            member = ctx.author
        query = "SELECT * FROM mod_logs WHERE guild_id = $1 AND moderator = $2"
        data = await self.bot.db.fetch(query, member.guild.id, member.mention)
        # Return if no mod actions found for the user
        if not data:
            return await ctx.channel.send(
                embed=discord.Embed(
                    title=f"No mod action found for {member.display_name}",
                    timestamp=datetime.datetime.utcnow(),
                    colour=discord.Colour.blurple(),
                )
            )
        embed = discord.Embed(
            title=f"Moderation for *{member.display_name}*",
            timestamp=datetime.datetime.utcnow(),
        )
        embed.add_field(
            name="\u200b", value=f"***Total {len(data)} moderations found.***"
        )
        embed.set_author(name=member, icon_url=member.avatar_url)
        x = ""
        for i in range(len(data)):
            x += (
                f"**Case** {data[i].get('case_no')} \n"
                f"**Type:** {data[i].get('type')}\n"
                f"**User:** {data[i].get('user_id')}\n"
                f"**Reason:** {data[i].get('reason')} \n"
                f"**Time:** {data[i].get('created_at')}\n\n"
            )

        pag = EmbedReactionPaginator.paginate(
            x,
            bot=self.bot,
            embed=embed,
            page_size=504,
            prefix="",
            suffix="",
            owner=ctx.author,
        )

        await pag.send_to(ctx.channel)
