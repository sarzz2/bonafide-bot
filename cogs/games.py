import asyncio
import datetime
import html
import random

import aiohttp
import discord
from discord.ext import commands


def setup(bot: commands.Bot):
    bot.add_cog(Games(bot=bot))


class Games(commands.Cog):
    hilo_cooldown = commands.CooldownMapping.from_cooldown(
        1.0, 14400.0, commands.BucketType.user
    )
    daily_cooldown = commands.CooldownMapping.from_cooldown(
        1.0, 86400.0, commands.BucketType.user
    )
    bj_cooldown = commands.CooldownMapping.from_cooldown(
        1.0, 60.0, commands.BucketType.user
    )
    quiz_cooldown = commands.CooldownMapping.from_cooldown(
        1.0, 14400.0, commands.BucketType.user
    )

    def __init__(self, bot):
        self.bot = bot
        self.rr = {}
        self.members = {}
        self.amount = {}
        self.rrauthor = {}
        self.ttt_games = {}

    async def cog_check(self, ctx):
        """Check if the category/cog is enabled"""
        # check admin
        if ctx.author.guild_permissions.administrator:
            return True

        query = (
            """ SELECT * FROM cog_check WHERE guild_id = $1 AND cog_name = 'games'"""
        )
        data = await self.bot.db.fetch_row(query, ctx.guild.id)

        # check if cog is enabled
        if data.get("enabled"):
            return True
        # if cog is not enabled then check whether author's role is allowed to run the cog's commands
        else:
            query = """SELECT * FROM role_check WHERE guild_id = $1 AND cog_name = 'games' AND role_id = $2"""

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
    async def hilo(self, ctx):
        """Play a game of high low to win some coins"""
        bucket = self.hilo_cooldown.get_bucket(ctx.message)
        retry_after = bucket.update_rate_limit()
        if retry_after:
            return await ctx.send(f"You are on cooldown. Try again in {retry_after}")

        number = random.randint(1, 100)
        embed = discord.Embed(
            title=f"The number selected is {number}",
            timestamp=datetime.datetime.utcnow(),
            colour=discord.Colour.blurple(),
        )
        embed.add_field(
            name="Will the next number be higher or lower?",
            value="\u200b",
            inline=False,
        )
        embed.set_footer(text="Randomly selects a number from 1-100")
        embed.set_thumbnail(
            url="https://cdn.discordapp.com/attachments/852867509765799956/854950687191072798/maxresdefault.png"
        )
        msg = await ctx.send(embed=embed)
        for emoji in ["⬆", "⬇"]:
            await msg.add_reaction(emoji)
        number2 = random.randint(1, 100)

        def option_check(
            reaction, user
        ):  # a check function which takes the user's response
            return user == ctx.author and reaction.emoji in ["⬆", "⬇"]

        option, _ = await self.bot.wait_for(
            "reaction_add", check=option_check, timeout=30
        )
        query = """ UPDATE bonafidecoin SET wallet = wallet + 50 WHERE guild_id = $1 AND user_id = $2"""
        if option.emoji == "⬆":
            if number2 > number or number2 == number:
                await self.bot.db.execute(query, ctx.guild.id, ctx.author.id)
                return await ctx.send(
                    f"The number was {number2}. **Congratulations! You won <:coin:853891390537465858> 50.**"
                )
            else:
                return await ctx.send(
                    f"The number was {number2}. **You lost.** Better luck next time!"
                )
        elif option.emoji == "⬇":
            if number2 < number:
                await self.bot.db.execute(query, ctx.guild.id, ctx.author.id)
                return await ctx.send(
                    f"The number was {number2}. **Congratulations! You won <:coin:853891390537465858> 50.**"
                )
            else:
                return await ctx.send(
                    f"The number was {number2}. **You lost.** Better luck next time!"
                )

    @commands.command()
    @commands.cooldown(1, 5)
    async def coinflip(self, ctx):
        """Can't decide on what to do? Flip a coin."""
        first = await ctx.send("Flipping...")
        embed = discord.Embed(
            title="CoinFlip",
            description=random.choice(["Heads", "Tails"]),
            timestamp=datetime.datetime.utcnow(),
            colour=discord.Colour.orange(),
        )
        await asyncio.sleep(1)
        await first.delete()
        await ctx.send(embed=embed)

    @commands.command()
    async def daily(self, ctx):
        bucket = self.daily_cooldown.get_bucket(ctx.message)
        retry_after = bucket.update_rate_limit()
        if retry_after:
            return await ctx.send(
                f"You are on cooldown. Try again in {int(retry_after / 3600)} hrs."
            )

        query = """ UPDATE bonafidecoin SET wallet = wallet + 500 WHERE guild_id = $1 AND user_id = $2"""
        await self.bot.db.execute(query, ctx.guild.id, ctx.author.id)
        await ctx.send(
            "**You have been awarded your daily <:coin:853891390537465858> 500.**"
        )

    @commands.command(aliases=["blackjack"])
    async def bj(self, ctx, amount: int):
        """Play a game of blackjack
        example:
        - bj 100"""
        bucket = self.bj_cooldown.get_bucket(ctx.message)
        retry_after = bucket.update_rate_limit()
        if retry_after:
            return await ctx.send(f"You are on cooldown. Try again in {retry_after}")
        if amount < 50:
            return await ctx.send("**Minimum amount to enter is 50.**")
        query = """SELECT * FROM bonafidecoin WHERE guild_id = $1 AND user_id = $2"""
        data = await self.bot.db.fetch_row(query, ctx.guild.id, ctx.author.id)
        if amount > data.get("wallet"):
            return await ctx.send(
                "**You don't have enough coins in wallet to start a game of blackjack.**"
            )
        lost_query = """UPDATE bonafidecoin SET wallet = wallet - $3 WHERE guild_id = $1 AND user_id = $2"""
        # The type of suit
        suits = ["Spades", "Hearts", "Clubs", "Diamonds"]
        # The suit value
        suits_values = {"Spades": "♠", "Hearts": "❤", "Clubs": "♣", "Diamonds": "♦"}
        # The type of card
        cards = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]
        # The card value
        cards_values = {
            "A": 11,
            "2": 2,
            "3": 3,
            "4": 4,
            "5": 5,
            "6": 6,
            "7": 7,
            "8": 8,
            "9": 9,
            "10": 10,
            "J": 10,
            "Q": 10,
            "K": 10,
        }

        # Cards for both dealer and player
        player_cards = []
        dealer_cards = []

        # Scores for both dealer and player
        player_score = 0
        dealer_score = 0
        deck = []
        # Making the deck
        for i in range(6):
            for suit in suits:
                # Loop for every type of card in a suit
                for card in cards:
                    # Adding card to the deck
                    deck.append((suits_values[suit], card, cards_values[card]))

        while len(player_cards) < 2:
            player_card = random.choice(deck)
            player_cards.append(player_card)
            deck.remove(player_card)
            player_score += player_card[2]
            if len(player_cards) == 2:
                if player_cards[0][2] == 11 and player_cards[1][2] == 11:
                    x = list(player_cards[0])
                    x[2] = 1
                    player_cards[0] = tuple(x)
                    player_score -= 10

            dealer_card = random.choice(deck)
            dealer_cards.append(player_card)
            deck.remove(dealer_card)
            dealer_score += dealer_card[2]
            if len(dealer_cards) == 2:
                if dealer_cards[0][2] == 11 and dealer_cards[1][2] == 11:
                    x = list(dealer_cards[0])
                    x[2] = 1
                    dealer_cards[0] = tuple(x)
                    dealer_score -= 10

        embed = discord.Embed(
            title=f"New game of blackjack started with <:coin:853891390537465858> {amount}",
            description="Press 👋 to hit, 2️⃣ to double down, ✋ to stand.",
            timestamp=datetime.datetime.utcnow(),
            colour=discord.Colour.blurple(),
        )
        embed.add_field(
            name="Your hand", value=f"{player_cards}\n Score: {player_score}"
        )
        embed.add_field(
            name="Dealer's hand", value=f"{dealer_cards[0]} {dealer_cards[0][2]}"
        )
        embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)
        embed.set_thumbnail(
            url="https://cdn.discordapp.com/attachments/852867509765799956/855872437166014496/apps.png"
        )
        msg = await ctx.send(embed=embed)
        for emoji in ["👋", "✋", "2️⃣"]:
            await msg.add_reaction(emoji)

        # a check function which takes the user's response
        def option_check(reaction, user):
            return (
                user == ctx.author
                and reaction.emoji in ["👋", "2️⃣", "✋"]
                and reaction.message.id == msg.id
            )

        option, _ = await self.bot.wait_for(
            "reaction_add", check=option_check, timeout=60
        )
        while True:
            if option.emoji == "2️⃣":
                amount *= 2
                embed = discord.Embed(
                    title=f"Blackjack | <:coin:853891390537465858> {amount}",
                    description="Press 👋 to hit, ✋ to stand.",
                    timestamp=datetime.datetime.utcnow(),
                    colour=discord.Colour.blurple(),
                )
                embed.add_field(
                    name="Your hand", value=f"{player_cards} \nScore: {player_score}"
                )
                embed.add_field(
                    name="Dealer's hand",
                    value=f"{dealer_cards[0]}\n Score: {dealer_cards[0][2]}",
                )
                embed.set_author(
                    name=ctx.author.display_name, icon_url=ctx.author.avatar_url
                )
                embed.set_thumbnail(
                    url="https://cdn.discordapp.com/attachments/852867509765799956/855872437166014496/apps.png"
                )
                msg = await ctx.send(embed=embed)

                for emoji in ["👋", "✋"]:
                    await msg.add_reaction(emoji)
                option, _ = await self.bot.wait_for("reaction_add", check=option_check)

                continue
            if option.emoji == "✋":
                break
            elif option.emoji == "👋":
                player_card = random.choice(deck)
                player_cards.append(player_card)
                deck.remove(player_card)
                player_score += player_card[2]
                a = 0
                for i in range(len(player_cards)):
                    if player_cards[i][2] == 11:
                        a += 1
                    if a == 2:
                        x = list(player_cards[i])
                        x[2] = 1
                        player_cards[i] = tuple(x)
                        player_score -= 10
                        break

                embed = discord.Embed(
                    title=f"Blackjack | <:coin:853891390537465858> {amount}",
                    description="Press 👋 to hit, ✋ to stand.",
                    timestamp=datetime.datetime.utcnow(),
                    colour=discord.Colour.blurple(),
                )
                embed.add_field(
                    name="Your hand", value=f"{player_cards} \nScore: {player_score}"
                )
                embed.add_field(
                    name="Dealer's hand",
                    value=f"{dealer_cards[0]}\n Score: {dealer_cards[0][2]}",
                )
                embed.set_author(
                    name=ctx.author.display_name, icon_url=ctx.author.avatar_url
                )
                embed.set_thumbnail(
                    url="https://cdn.discordapp.com/attachments/852867509765799956/855872437166014496/apps.png"
                )
                msg = await ctx.send(embed=embed)

                if player_score > 21:
                    await self.bot.db.execute(
                        lost_query, ctx.guild.id, ctx.author.id, amount
                    )
                    return await ctx.send(
                        embed=discord.Embed(
                            title=" BUST! You lost!",
                            timestamp=datetime.datetime.utcnow(),
                            colour=discord.Colour.red(),
                        )
                    )
                for emoji in ["👋", "✋"]:
                    await msg.add_reaction(emoji)
                option, _ = await self.bot.wait_for("reaction_add", check=option_check)

                continue

        while dealer_score < 17:
            dealer_card = random.choice(deck)
            dealer_cards.append(dealer_card)
            deck.remove(dealer_card)
            dealer_score += dealer_card[2]
            a = 0
            for i in range(len(dealer_card)):
                if dealer_cards[i][2] == 11:
                    a += 1
                if a == 2:
                    x = list(dealer_cards[i])
                    x[2] = 1
                    dealer_cards[i] = tuple(x)
                    dealer_score -= 10
                    break
        embed = discord.Embed(
            title=f"Blackjack | <:coin:853891390537465858> {amount}",
            description="Press 👋 to hit, ✋ to stand.",
            timestamp=datetime.datetime.utcnow(),
            colour=discord.Colour.blurple(),
        )
        embed.add_field(
            name="Your hand", value=f"{player_cards}\nScore: {player_score}"
        )
        embed.add_field(
            name="Dealer's hand", value=f"{dealer_cards}\nScore: {dealer_score}"
        )
        embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)
        embed.set_thumbnail(
            url="https://cdn.discordapp.com/attachments/852867509765799956/855872437166014496/apps.png"
        )
        await ctx.send(embed=embed)

        query = """UPDATE bonafidecoin SET wallet = wallet + $3 WHERE guild_id = $1 AND user_id = $2"""
        if dealer_score == player_score:
            return await ctx.send(
                embed=discord.Embed(
                    title="Game Tied!",
                    timestamp=datetime.datetime.utcnow(),
                    colour=discord.Colour.darker_grey(),
                )
            )

        elif player_score == 21:
            await self.bot.db.execute(query, ctx.guild.id, ctx.author.id, amount)
            return await ctx.send(
                embed=discord.Embed(
                    title="BLACKJACK! You Won!",
                    timestamp=datetime.datetime.utcnow(),
                    colour=discord.Colour.green(),
                )
            )

        elif player_score > 21:
            await self.bot.db.execute(lost_query, ctx.guild.id, ctx.author.id, amount)
            return await ctx.send(
                embed=discord.Embed(
                    title="BUST! You Lost!",
                    timestamp=datetime.datetime.utcnow(),
                    colour=discord.Colour.red(),
                )
            )

        elif dealer_score > 21:
            await self.bot.db.execute(query, ctx.guild.id, ctx.author.id, amount)
            return await ctx.send(
                embed=discord.Embed(
                    title="Dealer's Bust! You Won!",
                    timestamp=datetime.datetime.utcnow(),
                    colour=discord.Colour.green(),
                )
            )

        elif dealer_score > player_score:
            await self.bot.db.execute(lost_query, ctx.guild.id, ctx.author.id, amount)
            return await ctx.send(
                embed=discord.Embed(
                    title="Dealer's score is higher. You Lost!",
                    timestamp=datetime.datetime.utcnow(),
                    colour=discord.Colour.red(),
                )
            )

        elif dealer_score < player_score:
            await self.bot.db.execute(query, ctx.guild.id, ctx.author.id, amount)
            return await ctx.send(
                embed=discord.Embed(
                    title="Dealer's score is lower. You Won!",
                    timestamp=datetime.datetime.utcnow(),
                    colour=discord.Colour.green(),
                )
            )

    @commands.command()
    async def quiz(self, ctx, difficulty: str = None):
        """Answer a trivia question and stand a chance to win bonafide coins. You don't lose anything on incorrect answer.
        Difficulty:
        Easy - 100
        Medium - 250
        Hard - 500
        example:
        - quiz
        - quiz hard"""
        bucket = self.hilo_cooldown.get_bucket(ctx.message)
        retry_after = bucket.update_rate_limit()
        if retry_after:
            return await ctx.send(
                f"**You are on cooldown. Try again in {retry_after}**"
            )

        if difficulty is None:
            difficulty = random.choice(["easy", "medium", "hard"])
        url = f"https://opentdb.com/api.php?amount=1&difficulty={difficulty}&type=multiple"
        async with aiohttp.ClientSession() as cs:
            async with cs.get(url) as res:
                response = await res.json()
                category = response["results"][0]["category"]
                question = response["results"][0]["question"]
                correct_answer = response["results"][0]["correct_answer"]
                incorrect_answers = response["results"][0]["incorrect_answers"]

        one = "1️⃣"
        two = "2️⃣"
        three = "3️⃣"
        four = "4️⃣"

        choices = [correct_answer]
        for i in incorrect_answers:
            choices.append(i)

        random.shuffle(choices)
        answer_choices = choices.copy()

        x = ""
        choices[0] = one + " " + choices[0]
        choices[1] = two + " " + choices[1]
        choices[2] = three + " " + choices[2]
        choices[3] = four + " " + choices[3]
        x += "\n".join(choices)

        embed = discord.Embed(
            title=f"Quiz| {difficulty} | {category}",
            timestamp=datetime.datetime.utcnow(),
            colour=discord.Colour.blurple(),
        )
        embed.add_field(name="Question", value=html.unescape(question))
        embed.add_field(name="Options", value=f"{x}", inline=False)
        embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)
        embed.set_footer(text="Answer this question in 15 seconds!")
        msg = await ctx.send(embed=embed)

        def option_check(reaction, user):
            return user == ctx.author and reaction.emoji in ["1️⃣", "2️⃣", "3️⃣", "4️⃣"]

        for emoji in ["1️⃣", "2️⃣", "3️⃣", "4️⃣"]:
            await msg.add_reaction(emoji)
        try:
            option, _ = await self.bot.wait_for(
                "reaction_add", check=option_check, timeout=15
            )
        except asyncio.TimeoutError:
            return await ctx.send("**Timeout!**")

        if difficulty.lower() == "easy":
            win = 100
        elif difficulty.lower() == "medium":
            win = 250
        else:
            win = 500

        query = """UPDATE bonafidecoin SET wallet = wallet + $3 WHERE guild_id = $1 AND user_id = $2"""
        if option.emoji == "1️⃣":
            if correct_answer == answer_choices[0]:
                await self.bot.db.execute(query, ctx.guild.id, ctx.author.id, win)
                return await ctx.send(
                    f"**Correct Answer! You Won <:coin:853891390537465858>{win}**"
                )
            else:
                return await ctx.send("**Wrong Answer! You lost!**")
        elif option.emoji == "2️⃣":
            if correct_answer == answer_choices[1]:
                await self.bot.db.execute(query, ctx.guild.id, ctx.author.id, win)
                return await ctx.send(
                    f"**Correct Answer! You Won <:coin:853891390537465858>{win}**"
                )
            else:
                return await ctx.send("**Wrong Answer! You lost!**")
        elif option.emoji == "3️⃣":
            if correct_answer == answer_choices[2]:
                await self.bot.db.execute(query, ctx.guild.id, ctx.author.id, win)
                return await ctx.send(
                    f"**Correct Answer! You Won <:coin:853891390537465858>{win}**"
                )
            else:
                return await ctx.send("**Wrong Answer! You lost!**")
        elif option.emoji == "4️⃣":
            if correct_answer == answer_choices[3]:
                await self.bot.db.execute(query, ctx.guild.id, ctx.author.id, win)
                return await ctx.send(
                    f"**Correct Answer! You Won <:coin:853891390537465858>{win}**"
                )
            else:
                return await ctx.send("**Wrong Answer! You lost!**")

    @commands.command(aliases=["russianroulette"])
    async def rr(self, ctx, amount: int):
        """Start a new game or russian roulette. One game of roulette at a time.
        example:
        - rr 100
        - russianroulette 100"""
        # Check if the game exists
        if self.rr.get(ctx.guild.id) is True:
            return await ctx.send(
                f"**A game is already started with a bet of {self.amount}.**"
            )
        if amount < 100:
            return await ctx.send(
                "**Minimum amount to start a russian roulette round is 100.**"
            )

        # Check if the user starting the game has enough coins in wallet
        query = """SELECT * FROM bonafidecoin WHERE guild_id = $1 AND user_id = $2"""
        data = await self.bot.db.fetch_row(query, ctx.guild.id, ctx.author.id)

        if data is None:
            return await ctx.send("**Not Enough coins in wallet to start a game.**")
        if data.get("wallet") < amount:
            return await ctx.send("**Not Enough coins in wallet to start a game.**")

        # Update the wallet
        query = """UPDATE bonafidecoin SET wallet = wallet - $3 WHERE guild_id = $1 AND user_id = $2"""
        await self.bot.db.execute(query, ctx.guild.id, ctx.author.id, amount)

        # Update the dicts
        self.rr.update({ctx.guild.id: True})
        self.rrauthor.update({ctx.guild.id: ctx.author.id})
        self.amount.update({ctx.guild.id: amount})
        self.members.update({ctx.guild.id: [ctx.author.id]})

        embed = discord.Embed(
            title=f"New game of russian roulette started with bet of {amount}.",
            description=f"**Type .joinrr {amount} to join.\nType startrr to start the game.(Only the creator of the "
            f"game can start)**",
            timestamp=datetime.datetime.utcnow(),
            colour=discord.Colour.blurple(),
        )
        embed.set_footer(text="Minimum 3 members required to start.")
        await ctx.send(embed=embed)
        # await asyncio.sleep(60)
        # if len(self.members.get(ctx.guild.id)) > 0:
        #     return await ctx.invoke(self.bot.get_command("startrr"))
        # else:
        #     query = """UPDATE bonafidecoin SET wallet = wallet + $3 WHERE guild_id = $1 AND user_id = $2"""
        #     await self.bot.db.execute(query, ctx.guild.id, ctx.author.id, amount)
        #     return await ctx.send("**Timeout!**")

    @commands.command()
    async def joinrr(self, ctx, amount: int):
        """Join the current game of russian roulette.
        example:
        - joinrr 100"""
        # Check if the game exists
        if self.rr.get(ctx.guild.id) is None:
            return await ctx.send("**No game started. Use rr amount to start.**")
        # Check if user is already in a game
        if ctx.author.id in self.members.get(ctx.guild.id):
            return await ctx.send("**Already in a game.**")
        # check for the game bet
        if amount != self.amount.get(ctx.guild.id):
            return await ctx.send(
                f"**Current game's bet is {self.amount.get(ctx.guild.id)}**"
            )

        query = """SELECT * FROM bonafidecoin WHERE guild_id = $1 AND user_id = $2"""
        data = await self.bot.db.fetch_row(query, ctx.guild.id, ctx.author.id)

        if data.get("wallet") < amount:
            return await ctx.send("**Not Enough coins in wallet to start a game.**")

        query = """UPDATE bonafidecoin SET wallet = wallet - $3 WHERE guild_id = $1 AND user_id = $2"""
        await self.bot.db.execute(query, ctx.guild.id, ctx.author.id, amount)

        self.members.update(
            {ctx.guild.id: self.members.get(ctx.guild.id) + [ctx.author.id]}
        )
        await ctx.send(f"**Joined the game with {self.amount.get(ctx.guild.id)}**")

    @commands.command()
    async def startrr(self, ctx):
        """Start the current game of russian roulette. Only the author/creator of the game can start."""
        if ctx.author.id != self.rrauthor.get(ctx.guild.id):
            return

        if self.rr.get(ctx.guild.id) is None:
            return await ctx.send("**No game started. Use rr amount to start.**")

        if len(self.members.get(ctx.guild.id)) < 3:
            return await ctx.send("**Not enough members.**")

        place = 1
        while len(self.members.get(ctx.guild.id)) > 1:
            await asyncio.sleep(5)
            mem = random.choice(self.members.get(ctx.guild.id))
            await ctx.send(f"Bye! <@{mem}>")
            await ctx.send(f"**<@{mem}> was the {place}(st/nd/rd/th) to die!**")
            try:
                await mem.send(f"**You were the {place}(st/nd/rd/th) to die.**")
            except:
                pass
            self.members.get(ctx.guild.id).remove(mem)
            place += 1

        query = """UPDATE bonafidecoin SET wallet = wallet + $3 WHERE guild_id = $1 AND user_id = $2"""
        await self.bot.db.execute(
            query, ctx.guild.id, ctx.author.id, self.amount.get(ctx.guild.id) * 2
        )
        await ctx.send(
            f"**Congratulations! <@{self.members.get(ctx.guild.id)[0]}> You Won! {self.amount.get(ctx.guild.id) * 2}**"
        )

        del self.rr[ctx.guild.id]
        del self.amount[ctx.guild.id]
        del self.rrauthor[ctx.guild.id]
        del self.members[ctx.guild.id]

    @commands.command(aliases=["rps"])
    @commands.cooldown(1, 5)
    async def rockpaperscissor(self, ctx, choice: str):
        """Play a game of rock paper scissor with the bot. Valid options: rock, paper, scissor.
        example:
        - rps rock
        - rps paper
        - rockpaperscissor paper
        """
        valid = ["rock", "paper", "scissor"]
        if choice.lower() not in valid:
            return await ctx.send(
                "**Not a valid choice. Choose rock, paper or scissor.**"
            )

        bot_choices = ["rock", "paper", "scissor"]
        bot_choice = random.choice(bot_choices)
        if bot_choice == choice:
            return await ctx.send(f"**The bot chose {bot_choice}. TIE.**")
        elif bot_choice == "rock" and choice == "paper":
            return await ctx.send(f"**The bot chose:rock: {bot_choice}. You Win.**")
        elif bot_choice == "rock" and choice == "scissor":
            return await ctx.send(f"**The bot chose :rock: {bot_choice}. You Lose.**")
        elif bot_choice == "paper" and choice == "rock":
            return await ctx.send(
                f"**The bot chose :page_with_curl: {bot_choice}. You Lose.**"
            )
        elif bot_choice == "paper" and choice == "scissor":
            return await ctx.send(
                f"**The bot chose :page_with_curl: {bot_choice}. You Win.**"
            )
        elif bot_choice == "scissor" and choice == "rock":
            return await ctx.send(
                f"**The bot chose :scissors: {bot_choice}. You Win.**"
            )
        elif bot_choice == "scissor" and choice == "paper":
            return await ctx.send(
                f"**The bot chose :scissors: {bot_choice}. You Lose.**"
            )
