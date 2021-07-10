import datetime

import discord
from discord.ext import commands, tasks
from utils.time_converter import convert_time_to_seconds


def setup(bot: commands.Bot):
    bot.add_cog(RemindMe(bot=bot))


class RemindMe(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.reminder.start()

    async def cog_check(self, ctx):
        """Check if the category/cog is enabled"""
        if ctx.author.guild_permissions.administrator:
            return True
        query = (
            """ SELECT * FROM cog_check WHERE guild_id = $1 AND cog_name = 'remind_me'"""
        )
        data = await self.bot.db.fetch_row(query, ctx.guild.id)
        if data.get("enabled") is True:
            return True
        else:
            return False

    @commands.command()
    @commands.cooldown(1, 10)
    async def remindme(self, ctx, time, *, desc):
        """Add a reminder
        example:
        - remindme 10s reminder
        - remindme 5d long reminder"""
        try:
            time = convert_time_to_seconds(time)
        except ValueError:
            return await ctx.send("**Invalid time value**")

        query = """INSERT INTO remindme (guild_id, user_id, description, reminder_time) VALUES($1, $2, $3, $4)"""
        await self.bot.db.execute(
            query,
            ctx.guild.id,
            ctx.author.id,
            desc,
            datetime.datetime.utcnow() + datetime.timedelta(seconds=time),
        )
        embed = discord.Embed(
            title=f"I'll remind you to {desc} at {(datetime.datetime.utcnow() + datetime.timedelta(seconds=time)).strftime('%d/%m/%Y, %H:%M:%S')}.",
            colour=discord.Colour.orange(),
        )
        await ctx.send(embed=embed)

    @tasks.loop(seconds=20)
    async def reminder(self):
        query = """SELECT * FROM remindme"""
        data = await self.bot.db.fetch(query)

        for i in range(len(data)):
            if data[i].get("reminder_time") <= datetime.datetime.utcnow():
                user_id = data[i].get("user_id")
                guild_id = data[i].get("guild_id")
                description = data[i].get("description")

                user = self.bot.get_user(user_id)
                await user.send(f"**Reminder:**  {description}")
                query = """DELETE FROM remindme WHERE guild_id = $1 AND user_id = $2 AND description = $3"""
                await self.bot.db.execute(query, guild_id, user_id, description)
