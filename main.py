from utils.log_stream_handler import LogStreamHandler
from discord.ext.commands.errors import *

from database.database import DataBase
from database.guilds import Guild
from database import init_db
from discord.ext import commands

from dotenv import load_dotenv
from datetime import datetime

import logging
import asyncio
import discord
import os

cogs = []
for filename in os.listdir("cogs"):
    if filename.endswith(".py"):
        cogs.append(f"cogs.{filename[:-3]}")

logger = logging.getLogger("root")
logger.addHandler(LogStreamHandler())
logger.setLevel(logging.DEBUG)

logger.info("Connecting...")

load_dotenv()
TOKEN = os.getenv("TOKEN")
URI = os.getenv("URI")


class BonaFide(commands.AutoShardedBot):
    def __init__(self, **kwargs):
        super().__init__(
            command_prefix=self.get_prefix(),
            intents=kwargs.pop("intents", discord.Intents.all()),
            allowed_mentions=discord.AllowedMentions(everyone=False, roles=False),
            case_insensitive=True,
            **kwargs,
        )
        self.start_time = datetime.utcnow()

        self.__initial_connect = True
        self.__initial_ready = True

        self.blacklist = set()

    async def get_prefix(self, msg=None):
        guild_id = msg.guild.id
        query = """ SELECT prefix FROM guild WHERE guild_id = $1"""
        data = await self.db.fetch_row(query, guild_id)
        return data.get("prefix")

    async def on_connect(self):
        logger.info("Bot Connected")
        if self.__initial_connect:
            self.__initial_connect = False

            self.db = await DataBase.create_pool(
                bot=self,
                uri=URI,
                loop=self.loop,
            )
        await self.db.execute(init_db.guild)
        await self.db.execute(init_db.bonafidecoin)
        await self.db.execute(init_db.cog_check)
        await self.db.execute(init_db.filter)
        await self.db.execute(init_db.level)
        await self.db.execute(init_db.mod_logs)
        await self.db.execute(init_db.roles)
        await self.db.execute(init_db.shop)
        await self.db.execute(init_db.stats)
        await self.db.execute(init_db.stats_server)
        await self.db.execute(init_db.tags)
        await self.db.execute(init_db.user_inventory)
        await self.db.execute(init_db.role_check)

    async def on_ready(self):
        logger.info(f"Logged in as {self.user} (ID: {self.user.id})")
        logger.info(f"Sharded to {len(self.guilds)} guilds, {len(self.users)} users")

        if self.__initial_ready:
            self.__initial_ready = False

            self.load_extension("jishaku")
            for ext in cogs:
                self.load_extension(ext)
                logger.info(f"Loaded Extension: {ext}")

            logger.info("Loaded all Extensions")

    async def on_message(self, message):
        if message.author == self.user:
            return

        if message.guild:
            logger.info(
                f"{message.guild}: #{message.channel}: @{message.author}: {message.content}"
            )
            return await self.process_commands(message)
        else:
            logger.debug(f"{message.channel}: @{message.author}: {message.content}")

    async def on_guild_join(self, guild):
        # Check to see if guild id already exists
        query = """SELECT * FROM guild WHERE guild_id = $1"""
        data = await self.db.fetch_row(query, guild.id)

        if data is not None:
            logger.info(f"{guild.name}: {guild.id} rejoined")
        # If not log it and post to db
        else:
            logger.info(f"Joined {guild.name}: {guild.id}")
            x = Guild(self, guild.id, guild.name)
            await x.post()

            # basic_setup, help, moderation, perms, lock, roles, filter
            query = """INSERT INTO cog_check (guild_id, cog_name, enabled) VALUES($1, $2 ,$3)"""
            await self.db.execute(query, guild.id, "basic_info", True)
            await self.db.execute(query, guild.id, "currency", False)
            await self.db.execute(query, guild.id, "fun", False)
            await self.db.execute(query, guild.id, "games", False)
            await self.db.execute(query, guild.id, "giveaway", False)
            await self.db.execute(query, guild.id, "levelling", False)
            await self.db.execute(query, guild.id, "message", False)
            await self.db.execute(query, guild.id, "poll", False)
            await self.db.execute(query, guild.id, "remind_me", False)
            await self.db.execute(query, guild.id, "search", False)
            await self.db.execute(query, guild.id, "shop", False)
            await self.db.execute(query, guild.id, "stats", False)
            await self.db.execute(query, guild.id, "tags", False)
            await self.db.execute(query, guild.id, "user_info", True)

    async def on_member_join(self, member):
        query = "SELECT * FROM roles where user_id = $1 and guild_id = $2"
        data = await self.db.fetch(query, member.id, member.guild.id)
        if data is None:
            return
        else:
            for i in range(len(data)):
                role_id = data[i].get("roles")
                role = member.guild.get_role(role_id)
                await member.add_roles(role)

    async def process_commands(self, message):
        if message.author.bot:
            return
        ctx = await self.get_context(message=message)
        try:
            await self.invoke(ctx)
        except:
            pass

    # async def process_commands(self, message):
    #     if message.author.bot:
    #         return
    #     ctx = await self.get_context(message=message)
    #     query = """ SELECT * FROM commands WHERE guild_id = $1 AND cmd = $2 """
    #     data = await self.db.fetch_row(query, message.guild.id, ctx.command.name)
    #
    #     try:
    #         if not ctx.author.guild_permissions.administrator:
    #             if data.get("enabled") is True:
    #                 return await ctx.send("The command is not enabled")
    #         else:
    #             await self.invoke(ctx)
    #
    #     except:
    #         await self.invoke(ctx)

    async def on_command_error(self, ctx, exception):
        await self.wait_until_ready()

        error = getattr(exception, "original", exception)
        # This prevents any commands with local handlers being handled here in on_command_error.
        if hasattr(ctx.command, "on_error"):
            return

        # This prevents any cogs with an overwritten cog_command_error being handled here.
        cog = ctx.cog
        if cog:
            if cog._get_overridden_method(cog.cog_command_error) is not None:
                return

        ignored = (commands.CommandNotFound,)

        # Anything in ignored will return and prevent anything happening.
        if isinstance(error, ignored):
            return

        if isinstance(error, CheckFailure):
            return

        if isinstance(
            error,
            (
                BadUnionArgument,
                CommandOnCooldown,
                PrivateMessageOnly,
                NoPrivateMessage,
                ConversionError,
            ),
        ):
            return await ctx.send(str(error))

        elif isinstance(error, (MissingRequiredArgument, BadArgument)):
            return await (ctx.send_help(ctx.command))

        elif isinstance(error, BotMissingPermissions):
            return await ctx.send("I am missing these permissions to do this command:")

        elif isinstance(error, MissingPermissions):
            return await ctx.send(
                "You are missing these permissions to do this command:"
            )
        elif isinstance(error, (BotMissingAnyRole, BotMissingRole)):
            return await ctx.send("I am missing these roles to do this command:")
        elif isinstance(error, (MissingRole, MissingAnyRole)):
            return await ctx.send("You are missing these roles to do this command:")
        elif isinstance(error, UserNotFound):
            return await ctx.send("Can't find the specified user")
        elif isinstance(error, MemberNotFound):
            return await ctx.send("Cant find the member")
        elif isinstance(error, RoleNotFound):
            return await ctx.send(f"Role {error.argument} not found")

        else:
            logger.error(error)
            raise error

    @classmethod
    async def setup(cls, **kwargs):
        bot = cls()
        try:
            await bot.start(TOKEN, **kwargs)
        except KeyboardInterrupt:
            await bot.close()
        return bot


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(BonaFide.setup())
