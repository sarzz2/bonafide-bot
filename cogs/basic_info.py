import datetime
import time

from discord.ext import commands
import discord


def setup(bot: commands.Bot):
    bot.add_cog(BasicInfo(bot=bot))


class BasicInfo(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.remove_command("help")

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

    @commands.command()
    async def ping(self, ctx):
        """Get the bot ping"""
        before = time.monotonic()
        message = await ctx.send("Pong!")
        ping = (time.monotonic() - before) * 1000
        await message.edit(content=f"Pong!  `{int(ping)}ms`")

    @commands.command()
    async def info(self, ctx):
        """Get the info about the server"""
        embed = discord.Embed(
            timestamp=datetime.datetime.utcnow(), colour=discord.Colour.blurple()
        )
        embed.set_author(name="BonaFide", icon_url=self.bot.user.avatar_url)
        embed.add_field(name="Guilds", value=f"{len(self.bot.guilds)}")
        embed.add_field(name="Users", value=f"{len(self.bot.users)}")
        embed.add_field(name="Owner", value="<@576760984576983060>")
        await ctx.send(embed=embed)

    @commands.command()
    async def emotes(self, ctx):
        """Get all the emotes of the server"""
        emoji = ""
        for emojis in ctx.guild.emojis:
            emoji += str(emojis)

        embed = discord.Embed(description=emoji)
        await ctx.send(embed=embed)

    @commands.command(aliases=["support", "patreon"])
    async def donate(self, ctx):
        embed = discord.Embed(
            title="Support",
            url="https://patreon.com/bonafided",
            timestamp=datetime.datetime.utcnow(),
            colour=discord.Colour.gold(),
        )
        embed.add_field(
            name="Join the patreon.",
            value="https://patreon.com/bonafided",
            inline=False,
        )
        embed.set_thumbnail(
            url="https://cdn.discordapp.com/attachments/852867509765799956/862672668187820032/af0941ba06185e9846af909ba9350baf.png"
        )
        embed.set_footer(text="Support the bot")
        await ctx.send(embed=embed)
