import datetime

import discord
from discord.ext import commands
from discord.utils import get


def setup(bot: commands.Bot):
    bot.add_cog(Poll(bot=bot))


class Poll(commands.Cog):
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

    @property
    def reactions(self):
        return {
            1: "1️⃣",
            2: "2️⃣",
            3: "3️⃣",
            4: "4️⃣",
            5: "5️⃣",
            6: "6️⃣",
            7: "7️⃣",
            8: "8️⃣",
            9: "9️⃣",
            10: "🔟",
        }

    def poll_check(self, message: discord.Message):
        try:
            embed = message.embeds[0]
        except:
            return False
        if (
            str(embed.footer.text).count("Poll by") == 1
            or str(embed.footer.text) == "Quick poll"
        ):
            return message.author == self.bot.user
        return False

    @commands.command()
    @commands.cooldown(1, 10)
    async def poll(self, ctx, desc: str, *choices):
        """Create a new poll. If there are more than one word in description or choices don't forget to use ".
        example:
        - poll "test poll" "choice one" "choice two"
        - poll test one two"""
        await ctx.message.delete()

        if len(choices) < 2:
            ctx.command.reset_cooldown(ctx)
            if len(choices) == 1:
                return await ctx.send("**Can't make a poll with only one choice.**")
            return await ctx.send(
                "**You have to enter two or more choices to make a poll.**"
            )

        if len(choices) > 10:
            ctx.command.reset_cooldown(ctx)
            return await ctx.send(
                "**You can't make a poll with more than 10 choices.**"
            )

        embed = discord.Embed(
            title=desc,
            description="\n".join(
                f"{str(self.reactions[i])}  {choice}"
                for i, choice in enumerate(choices, 1)
            ),
            timestamp=datetime.datetime.utcnow(),
            color=discord.colour.Color.blurple(),
        )
        embed.set_footer(text=f"Poll by {ctx.author}")
        msg = await ctx.send(embed=embed)
        for i in range(1, len(choices) + 1):
            await msg.add_reaction(self.reactions[i])

    @commands.command()
    async def quickpoll(self, ctx, *, description: str):
        """Make a quick poll with thumbs up and down reaction.
        example:
        - quickpoll this is a poll"""
        await ctx.message.delete()
        embed = discord.Embed(
            title=description,
            timestamp=datetime.datetime.utcnow(),
            colour=discord.Colour.random(),
        )
        embed.set_footer(text="Quick poll")
        msg = await ctx.send(embed=embed)

        for i in ["👍", "👎"]:
            await msg.add_reaction(i)

    @commands.command()
    async def results(self, ctx, message: str):
        try:
            *_, channel_id, msg_id = message.split("/")

            try:
                channel = self.bot.get_channel(int(channel_id))
                message = await channel.fetch_message(int(msg_id))
            except:
                return await ctx.send(
                    "**Please provide the message ID/link for a valid poll.**"
                )
        except:
            try:
                message = await ctx.channel.fetch_message(message)
            except:
                return await ctx.send(
                    "**Please provide the message ID/link for a valid poll.**"
                )

        if self.poll_check(message):
            poll_embed = message.embeds[0]
            reactions = message.reactions
            count = {}
            total = 0

            desc = poll_embed.title.split("1")[0]
            footer = poll_embed.footer.text

            embed = discord.Embed(
                title=desc,
                timestamp=datetime.datetime.utcnow(),
                colour=discord.Colour.random(),
            )
            embed.set_footer(text="Poll Results")

            # count for quick poll
            if footer == "Quick poll":
                quickpoll_reaction = ["👍", "👎"]
                for i in range(len(reactions)):
                    reaction = get(reactions, emoji=quickpoll_reaction[i])
                    total += reaction.count - 1
                    if str(reaction) == "👍":
                        count["👍"] = int(reaction.count - 1)
                    elif str(reaction) == "👎":
                        count["👎"] = int(reaction.count - 1)

            else:
                for i in range(len(reactions)):
                    reaction = get(reactions, emoji=self.reactions[i + 1])
                    if str(reaction) in list(self.reactions.values()):
                        count[str(self.reactions[i + 1])] = int(reaction.count - 1)
                        total += reaction.count - 1

            for key, value in count.items():
                if total == 0:
                    indicator = "░" * 20
                    embed.add_field(
                        name=f"{key}  {value}", value=f"{indicator} 0%", inline=False
                    )
                else:
                    indicator = "█" * int(((value / total) * 100) / 5) + "░" * int(
                        (((total - value) / total) * 100) / 5
                    )
                    embed.add_field(
                        name=f"{key}  {value}",
                        value=f"{indicator} {int(value / total * 100)}%",
                        inline=False,
                    )

            await ctx.send(embed=embed)
