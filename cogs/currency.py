import random

from discord.ext.commands import has_permissions
from discord.ext import commands
import datetime
import discord
from database.currency import BonfideCoin


def setup(bot: commands.Bot):
    bot.add_cog(Currency(bot=bot))


class Currency(commands.Cog):
    message_cooldown = commands.CooldownMapping.from_cooldown(
        1.0, 21600.0, commands.BucketType.user
    )

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

    async def add_to_db(self, guild_id, user_id):
        x = BonfideCoin(bot=self.bot)
        await x.post(guild_id=guild_id, user_id=user_id, wallet=0, bank=0)

    # user basic commands
    @commands.command(aliases=["bal"])
    async def balance(self, ctx, member: discord.Member = None):
        """Check the balance of a member
        example:
        - balance
        - balance @PlasticFood"""
        if member is None:
            member = ctx.author
        data = await BonfideCoin(self.bot).get(member.guild.id, member.id)
        # If user doesn't exist in db add to db
        if data is None:
            await self.add_to_db(member.guild.id, member.id)

        # Get the updated data and send
        data = await BonfideCoin(self.bot).get(member.guild.id, member.id)
        embed = discord.Embed(
            timestamp=datetime.datetime.utcnow(), colour=discord.Colour.orange()
        )
        embed.set_author(name=member.display_name, icon_url=member.avatar_url)
        embed.add_field(
            name="<:coin:853891390537465858> In Wallet",
            value=f"{data.get('wallet')}",
            inline=False,
        )
        embed.add_field(
            name="<:coin:853891390537465858> In BonaFide Bank",
            value=f"{data.get('bank')}",
            inline=False,
        )
        embed.add_field(
            name="<:coin:853891390537465858> Total",
            value=f"{int(data.get('bank')) + int(data.get('wallet'))}",
            inline=False,
        )
        return await ctx.send(embed=embed)

    @commands.command(aliases=["dep"])
    async def deposit(self, ctx, amount: int):
        """Deposit the specified coins in wallet to the bank
        example:
        - deposit 1000"""
        data = await BonfideCoin(self.bot).get(ctx.guild.id, ctx.author.id)
        if data is None:
            await self.add_to_db(ctx.guild.id, ctx.author.id)

        data = await BonfideCoin(self.bot).get(ctx.guild.id, ctx.author.id)

        # check if money being deposited is equal to or less than wallet
        if 0 < data.get("wallet") >= amount:
            query = """UPDATE bonafidecoin SET bank = $3 + bank, wallet = wallet - $3 WHERE guild_id = $1 AND user_id
            = $2"""
            await self.bot.db.execute(query, ctx.guild.id, ctx.author.id, amount)
            return await ctx.send(
                f"Successfully deposited <:coin:853891390537465858> **{amount}**."
            )
        return await ctx.send("You don't have sufficient balance to deposit.")

    @commands.command()
    async def withdraw(self, ctx, amount: int):
        """Withdraw the coins from bank to wallet to use
        example:
        - withdraw 456"""
        data = await BonfideCoin(self.bot).get(ctx.guild.id, ctx.author.id)
        if data is None:
            await self.add_to_db(ctx.guild.id, ctx.author.id)

        data = await BonfideCoin(self.bot).get(ctx.guild.id, ctx.author.id)
        if amount <= data.get("bank"):
            query = """UPDATE bonafidecoin SET bank = bank - $3, wallet = wallet + $3 WHERE guild_id = $1 AND user_id
            = $2 """
            await self.bot.db.execute(query, ctx.guild.id, ctx.author.id, amount)
            return await ctx.send(
                f"Successfully withdrawn <:coin:853891390537465858> **{amount}**."
            )

        return await ctx.send("You don't have sufficient balance to withdraw.")

    @commands.command()
    async def give(self, ctx, amount: int, member: discord.Member):
        """User gives the coins to other user
        example:
        - give 1000 @PlasticFood"""
        if member.id == ctx.author.id:
            return await ctx.send("Can not give to yourself.")
        # Get the author details
        author = await BonfideCoin(self.bot).get(ctx.guild.id, ctx.author.id)
        if author is None:
            await self.add_to_db(ctx.guild.id, ctx.author.id)
        # Get the member details
        mem = await BonfideCoin(self.bot).get(ctx.guild.id, member.id)
        if mem is None:
            await self.add_to_db(ctx.guild.id, member.id)

        # Check if user has enough coin in wallet to give and update there db
        if author.get("wallet") >= amount > 0:
            query = """UPDATE bonafidecoin SET  wallet = wallet - $3 WHERE guild_id = $1 AND user_id = $2 """
            await self.bot.db.execute(query, ctx.guild.id, ctx.author.id, amount)
            query = """UPDATE bonafidecoin SET  wallet = wallet + $3 WHERE guild_id = $1 AND user_id = $2 """
            await self.bot.db.execute(query, ctx.guild.id, member.id, amount)
            return await ctx.send(
                f"Successfully sent <:coin:853891390537465858> {amount} coins to <@{member.id}>"
            )

    @commands.command()
    async def rob(self, ctx, member: discord.Member):
        """Rob the member who has more than 300 coins in wallet. Can be used once every 6 hrs and user can be fined,
        if caught.
        example:
        - rob @plasticFood"""
        if member.id == ctx.author.id:
            return await ctx.send("Can not rob yourself.")

        data = await BonfideCoin(self.bot).get(member.guild.id, member.id)
        if data is None:
            return await ctx.send("User doesn't have enough coins to rob!")

        # Rob user every 6 hrs only
        bucket = self.message_cooldown.get_bucket(ctx.message)
        retry_after = bucket.update_rate_limit()
        if retry_after:
            return await ctx.send(
                f" You are on cool down! Try again after {retry_after}!"
            )

        wallet = data.get("wallet")

        if wallet < 300:
            return await ctx.send(" User doesn't have enough coins to rob!")

        random_bit = random.getrandbits(1)
        random_boolean = bool(random_bit)

        if random_boolean:
            amount = random.randint(25, round(wallet / 1.5))
            # Update the author wallet
            query = """ UPDATE bonafidecoin SET wallet = wallet + $3 WHERE guild_id = $1 AND user_id = $2 """
            await self.bot.db.execute(query, ctx.guild.id, ctx.author.id, amount)

            # Ping the robbed user to update him
            await ctx.send(
                f"Successfully robbed <:coin:853891390537465858> {amount} from <@{member.id}>"
            )
            # Update the member (robbed) wallet
            query = """ UPDATE bonafidecoin SET wallet = wallet - $3 WHERE guild_id = $1 AND user_id = $2 """
            await self.bot.db.execute(query, ctx.guild.id, member.id, amount)
        else:
            fine = random.randint(50, 1000)
            await ctx.send(f"You got caught! You have been fined {fine} coin!")
            query = """ UPDATE bonafidecoin SET wallet = wallet - $3 WHERE guild_id = $1 AND user_id = $2 """
            await self.bot.db.execute(query, ctx.guild.id, ctx.author.id, fine)

    # admin
    @commands.command()
    @has_permissions(administrator=True)
    async def addcoin(self, ctx, amount: int, member: discord.Member):
        """Add coins to user
        example:
        - addcoin 456 @Noobmaster"""
        data = await BonfideCoin(self.bot).get(ctx.guild.id, member.id)
        if data is None:
            await self.add_to_db(ctx.guild.id, member.id)

        if amount > 10000 or amount < 0:
            return await ctx.send("You can not add more than 10000 or less than 0.")
        query = """ UPDATE bonafidecoin SET wallet = wallet + $3 WHERE guild_id = $1 AND user_id = $2"""
        await self.bot.db.execute(query, member.guild.id, member.id, amount)
        await ctx.send(
            f"Successfully added <:coin:853891390537465858> {amount} to <@{member.id}>"
        )

    @commands.command()
    @has_permissions(administrator=True)
    async def removecoin(self, ctx, amount: int, member: discord.Member):
        """Remove coins from user
        example:
        - removecoin 456 @NoobMaster"""
        data = await BonfideCoin(self.bot).get(ctx.guild.id, member.id)
        if data is None:
            await self.add_to_db(ctx.guild.id, member.id)

        if amount > 10000 or amount < 0:
            return await ctx.send("You can not remove more than 10000 or less than 0.")
        query = """ UPDATE bonafidecoin SET wallet = wallet - $3 WHERE guild_id = $1 AND user_id = $2"""
        await self.bot.db.execute(query, member.guild.id, member.id, amount)
        await ctx.send(
            f"Successfully removed <:coin:853891390537465858> {amount} from <@{member.id}>"
        )
