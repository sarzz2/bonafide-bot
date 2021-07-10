from discord.ext import commands
import discord
import random

from database.levelling import Level


def setup(bot: commands.Bot):
    bot.add_cog(Levelling(bot=bot))


class Levelling(commands.Cog):
    message_cooldown = commands.CooldownMapping.from_cooldown(
        1.0, 60.0, commands.BucketType.member
    )

    def __init__(self, bot):
        self.bot = bot

    async def cog_check(self, ctx):
        """Check if the category/cog is enabled"""
        query = """ SELECT * FROM cog_check WHERE guild_id = $1 AND cog_name = 'levelling'"""
        data = await self.bot.db.fetch_row(query, ctx.guild.id)
        if data.get("enabled") is True:
            return True
        else:
            return False

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        # Check if levelling cogs is enabled
        query = (
            """ SELECT * FROM cog_check WHERE guild_id = $1 AND cog_name = 'filter'"""
        )
        data = await self.bot.db.fetch_row(query, message.guild.id)
        if data.get("enabled") is False:
            return

        # Check if message is sent in ignored channel
        query = """ SELECT ignored_channel FROM guild WHERE guild_id = $1"""
        ignored_channel = await self.bot.db.fetch_row(query, message.guild.id)
        if ignored_channel.get("ignored_channel") is None:
            pass
        elif message.channel.id in (ignored_channel.get("ignored_channel")):
            return

        # check if user is in db if not add the user
        check = """ SELECT * FROM level WHERE user_id = $1 AND guild_id = $2"""
        data = await self.bot.db.fetch_row(check, message.author.id, message.guild.id)
        if data is None:
            await Level(
                bot=self.bot,
                guild_id=message.guild.id,
                user=message.author.id,
                total_xp=random.randint(5, 20),
                current_xp=random.randint(5, 20),
                required_xp=100,
                lvl=0,
            ).post()

        # Update xp every min only
        bucket = self.message_cooldown.get_bucket(message)
        retry_after = bucket.update_rate_limit()
        if retry_after:
            return

        # update the xp
        x = random.randint(5, 25)
        query = """UPDATE level SET total_xp = total_xp + $3, current_xp = current_xp +$4 WHERE user_id = $1 AND
        guild_id = $2 """
        await self.bot.db.execute(query, message.author.id, message.guild.id, x, x)

        # check and update the level
        query = """ SELECT * FROM level WHERE user_id = $1 AND guild_id = $2"""
        data = await self.bot.db.fetch_row(query, message.author.id, message.guild.id)
        lvl = data.get("lvl")
        current_xp = data.get("current_xp")
        required_xp = data.get("required_xp")
        if current_xp > required_xp:
            current_xp -= required_xp
            req = 5 * (lvl ^ 2) + (50 * lvl) + 100 - current_xp
            query = """UPDATE level SET lvl = lvl + 1, current_xp = $3, required_xp = $4  WHERE user_id = $1 AND
            guild_id = $2 """
            await self.bot.db.execute(
                query, message.author.id, message.guild.id, current_xp, req
            )

    @commands.command()
    async def rank(self, ctx, member: discord.Member = None):
        """Check the rank of another member or yourself
        example:
        - rank @Noobmaster
        - rank"""
        if member is None:
            member = ctx.author
        query = """ WITH ordered_users AS (
                    SELECT
                    user_id,guild_id,lvl,total_xp,current_xp,required_xp,
                    ROW_NUMBER() OVER (ORDER BY level.total_xp DESC) AS i
                    FROM level
                    WHERE guild_id = $2)
                    SELECT i,lvl,total_xp,current_xp,required_xp FROM ordered_users WHERE ordered_users.user_id = $1;"""
        data = await self.bot.db.fetch_row(query, member.id, member.guild.id)
        if data is None:
            return await ctx.send(f"{member} is not ranked yet!")
        # TODO format rank output properly
        return await ctx.send(
            f"Rank:{data.get('i')}\n Level:{data.get('lvl')}\n Exp: {data.get('total_xp')}"
        )

    # @commands.command()
    async def givexp(self, ctx, xp: int, member: discord.Member):
        get = """SELECT lvl,total_xp,current_xp, required_xp FROM level WHERE user_id = $1 AND guild_id = $2"""
        data = await self.bot.db.fetch_row(get, member.id, member.guild.id)
        if data is None:
            pass
        lvl = data.get("lvl")
        current_xp = int(data.get("current_xp") + xp)
        total_xp = int(data.get("total_xp"))
        required_xp = int(data.get("required_xp"))

        for i in range(total_xp):
            req = 5 * (lvl ^ 2) + (50 * lvl) + 100 - current_xp
            if current_xp > required_xp:
                print(current_xp, req)
                current_xp -= req
                lvl += 1
            else:
                break
        print(lvl)
        # query = """UPDATE level SET total_xp = $3, current_xp = $4, required_xp = $5, lvl = $6 WHERE user_id = $1 AND
        #                guild_id = $2 """
        # await self.bot.db.execute(query, member.id, member.guild.id, total_xp + xp, current_xp, required_xp, lvl)
