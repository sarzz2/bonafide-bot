from discord.ext import commands
import datetime
import discord
from discord.ext.commands import has_permissions


def setup(bot: commands.Bot):
    bot.add_cog(UserInfo(bot=bot))


class UserInfo(commands.Cog):
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

    @commands.command()
    async def whois(self, ctx, member: discord.Member = None):
        """Get the user details.
        example:
        - whois
        - whois @NoobMaster"""
        if member is None:
            member = ctx.author

        x = ""
        for i in member.roles:
            if i.name == "@everyone":
                pass
            else:
                x += f"<@&{i.id}> "
            if len(x) > 1000:
                break

        perms_string = ""
        for perm, true_false in member.top_role.permissions:
            if true_false is True:
                perms_string += f"`{perm.title().replace('_', ' ')}`, "

        embed = discord.Embed(timestamp=datetime.datetime.utcnow(), colour=member.color)
        embed.set_author(name=member.display_name, icon_url=member.avatar_url)
        embed.set_thumbnail(url=member.avatar_url)
        embed.add_field(
            name="Joined:", value=member.joined_at.strftime("%d %b %Y, %a, %-I:%M %p")
        )
        embed.add_field(
            name="Created at:",
            value=member.created_at.strftime("%d %b %Y, %a, %-I:%M %p"),
        )
        if len(x) > 0:
            embed.add_field(
                name=f"Roles[{len(member.roles) -1}]", value=x, inline=False
            )
        else:
            embed.add_field(
                name=f"Roles[{len(member.roles) -1}]", value="No Roles", inline=False
            )

        embed.add_field(name="Key Permissions", value=perms_string, inline=False)
        return await ctx.send(embed=embed)

    @commands.command()
    async def av(self, ctx, member: discord.Member = None):
        """Get the user's avatar
         example:
        - av
        - av @NoobMaster"""
        if member is None:
            member = ctx.author

        embed = discord.Embed(timestamp=datetime.datetime.utcnow(), colour=member.color)
        embed.set_author(name=member.display_name, icon_url=member.avatar_url)
        embed.set_image(url=member.avatar_url)
        return await ctx.send(embed=embed)

    @commands.command(aliases=["changenick"])
    @has_permissions(kick_members=True)
    async def setnick(self, ctx, user: discord.Member, *, nick: str):
        """Change user's nickname
        example:
        - setnick @plasticnoobs xyz"""
        nick = await commands.clean_content().convert(ctx=ctx, argument=nick)
        if len(nick) > 32:
            return await ctx.send("**Nick length can not be more than 32 chars.**")

        await user.edit(nick=nick)
        await ctx.send(f"**{user.display_name} Nickname updated to {nick}.**")
