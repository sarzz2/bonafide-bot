import discord
from discord.ext import commands

from datetime import datetime

import itertools


class HelpCommand(commands.HelpCommand):
    def embed_fy(self, **kwargs):
        return discord.Embed(
            timestamp=datetime.utcnow(), color=0x36393E, **kwargs
        ).set_footer(text="Called by: %s" % self.context.author)

    def command_desk(self, command: commands.Command, add_example=False):
        if command.help:
            _help, *example = command.help.split("\nexample:\n")
        else:
            _help, example = "No specified description.", None

        desk = "%s```dust\n%s```" % (
            _help,
            self.clean_prefix
            + command.qualified_name
            + " "
            + command.signature.translate(str.maketrans("[]", "{}")),
        )
        if add_example and example:
            desk += "**Example**```md\n%s```" % example[0]

        return desk

    @property
    def opening_note(self):
        return (
            """Use **`%shelp "command name"`** for more info on a command."""
            % self.clean_prefix
        )

    def subcommand_not_found(self, command, string):
        if isinstance(command, commands.Group) and len(command.all_commands) > 0:
            return 'Command "%s" has no subcommand named "%s".' % (
                command.qualified_name,
                string,
            )
        return 'Command "%s" has no subcommands.' % command.qualified_name

    @staticmethod
    def __get_cog(command: commands.Command):
        cog = command.cog
        return cog.qualified_name if cog else "No Category"

    async def send_bot_help(self, mapping):
        embed = self.embed_fy(title="General Help", description=self.opening_note)
        bot_commands = await self.filter_commands(
            self.context.bot.commands, sort=True, key=self.__get_cog
        )

        for category, cmds in itertools.groupby(bot_commands, key=self.__get_cog):
            embed.add_field(
                name=category,
                value="```ini\n[%s]```" % ", ".join(cmd.name for cmd in cmds),
                inline=False,
            )

        await self.context.send(embed=embed)

    async def send_cog_help(self, cog: commands.Cog):
        embed = self.embed_fy(title=cog.qualified_name, description=cog.description)
        for command in cog.get_commands():
            embed.add_field(
                name=" | ".join([command.name] + command.aliases),
                value=self.command_desk(command),
                inline=False,
            )

        return await self.context.send(embed=embed)

    async def send_group_help(self, group: commands.Group):
        embed = self.embed_fy(
            title=" | ".join([group.name] + group.aliases),
            description=self.command_desk(group),
        )
        for command in group.commands:
            embed.add_field(
                name=" | ".join([command.name] + command.aliases),
                value=self.command_desk(command),
                inline=False,
            )

        return await self.context.send(embed=embed)

    async def send_command_help(self, command: commands.Command):
        embed = self.embed_fy(
            title=" | ".join([command.name] + command.aliases),
            description=self.command_desk(command, add_example=True),
        )
        return await self.context.send(embed=embed)


class HelpCog(commands.Cog, name="Help"):
    def __init__(self, bot):
        self.bot = bot
        self._original_help_command = bot.help_command

        self.bot.help_command = HelpCommand()
        self.bot.help_command.cog = self

        self.bot.get_command("help").hidden = True

    def cog_unload(self):
        self.bot.help_command = self._original_help_command


def setup(bot):
    bot.add_cog(HelpCog(bot))
