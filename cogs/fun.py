import datetime
import os
import random

import aiohttp
import requests
from akinator.async_aki import Akinator
from discord.ext import commands
import discord
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("rapid-api-key")


def setup(bot: commands.Bot):
    bot.add_cog(Fun(bot=bot))


class Fun(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_check(self, ctx):
        """Check if the category/cog is enabled"""
        # check admin
        if ctx.author.guild_permissions.administrator:
            return True

        query = """ SELECT * FROM cog_check WHERE guild_id = $1 AND cog_name = 'fun'"""
        data = await self.bot.db.fetch_row(query, ctx.guild.id)

        # check if cog is enabled
        if data.get("enabled"):
            return True
        # if cog is not enabled then check whether author's role is allowed to run the cog's commands
        else:
            query = """SELECT * FROM role_check WHERE guild_id = $1 AND cog_name = 'fun' AND role_id = $2"""

            for i in range(len(ctx.author.roles)):
                data = await self.bot.db.fetch_row(
                    query, ctx.guild.id, ctx.author.roles[i].id
                )
                if data is None:
                    continue
                elif data.get("enabled"):
                    return True

            return False

    @commands.command(name="akinator", aliases=["aki"])
    async def akinator_game(self, ctx):
        aki = Akinator()
        first = await ctx.send("Processing...")
        q = await aki.start_game()

        game_embed = discord.Embed(
            title=f"{str(ctx.author.display_name)}'s game of Akinator",
            description=q,
            url=r"https://en.akinator.com/",
            color=discord.Color.blurple(),
        )
        game_embed.set_footer(
            text="Wait for the bot to add reactions before you give your response."
        )

        option_map = {
            "✅": "y",
            "❌": "n",
            "🤷‍♂️": "probably yes",
            "😕": "probably no",
            "⁉️": "idk",
        }

        game_embed.add_field(
            name="✅ -> YES, ❌-> NO, 🤷‍♂️-> PROBABLY YES, 😕-> PROBABLY NO, ⁉️->IDK,🔚-> force end game,"
            "◀️-> previous question",
            value="\u200b",
            inline=False,
        )

        def option_check(
            reaction, user
        ):  # a check function which takes the user's response
            return user == ctx.author and reaction.emoji in [
                "◀️",
                "✅",
                "❌",
                "🤷‍♂️",
                "😕",
                "⁉️",
                "🔚",
            ]

        count = 0
        while (
            aki.progression <= 80
        ):  # this is aki's certainty level on an answer, per say. 80 seems to be good
            if count == 0:
                await first.delete()  # deleting the message which said "Processing.."
                count += 1

            game_message = await ctx.send(embed=game_embed)

            for emoji in ["◀️", "✅", "❌", "🤷‍♂️", "😕", "⁉️", "🔚"]:
                await game_message.add_reaction(emoji)

            option, _ = await self.bot.wait_for(
                "reaction_add", check=option_check
            )  # taking user's response
            if option.emoji == "🔚":
                return await ctx.send("Game ended.")
            async with ctx.channel.typing():
                if option.emoji == "◀️":  # to go back to previous question
                    try:
                        q = await aki.back()
                    except:  # excepting trying-to-go-beyond-first-question error
                        pass
                    # editing embed for next question
                    game_embed = discord.Embed(
                        title=f"{str(ctx.author.display_name)}'s game of Akinator",
                        description=q,
                        url=r"https://en.akinator.com/",
                        color=discord.Color.blurple(),
                    )
                    game_embed.set_footer(
                        text="Wait for the bot to add reactions before you give your response."
                    )
                    continue
                else:
                    q = await aki.answer(option_map[option.emoji])
                    # editing embed for next question
                    game_embed = discord.Embed(
                        title=f"{str(ctx.author.display_name)}'s game of Akinator",
                        description=q,
                        url=r"https://en.akinator.com/",
                        color=discord.Color.blurple(),
                    )
                    game_embed.set_footer(
                        text="Wait for the bot to add reactions before you give your response."
                    )

                    continue

        await aki.win()

        result_embed = discord.Embed(
            title="My guess....", colour=discord.Color.dark_blue()
        )
        result_embed.add_field(
            name=f"My first guess is **{aki.first_guess['name']}**",
            value=aki.first_guess["description"],
            inline=False,
        )
        result_embed.set_footer(text="Was I right? Add the reaction accordingly.")
        result_embed.set_image(url=aki.first_guess["absolute_picture_path"])
        result_message = await ctx.send(embed=result_embed)
        for emoji in ["✅", "❌"]:
            await result_message.add_reaction(emoji)

        option, _ = await self.bot.wait_for(
            "reaction_add", check=option_check, timeout=15
        )
        if option.emoji == "✅":
            final_embed = discord.Embed(
                title="I'm a genius", color=discord.Color.green()
            )
        elif option.emoji == "❌":
            final_embed = discord.Embed(
                title="Oof", description="Maybe try again?", color=discord.Color.red()
            )

        return await ctx.send(embed=final_embed)

    @commands.command()
    async def urban(self, ctx, term):
        """Return the definition and example from the urban dictionary
        example:
        - urban @everyone"""
        url = "https://mashape-community-urban-dictionary.p.rapidapi.com/define"

        querystring = {"term": term}

        headers = {
            "x-rapidapi-key": api_key,
            "x-rapidapi-host": "mashape-community-urban-dictionary.p.rapidapi.com",
        }

        response = requests.request("GET", url, headers=headers, params=querystring)
        try:
            definition = response.json()["list"][0]["definition"]
            example = response.json()["list"][0]["example"]
            permalink = response.json()["list"][0]["permalink"]
            thumbs_up = response.json()["list"][0]["thumbs_up"]
            thumbs_down = response.json()["list"][0]["thumbs_down"]
        except IndexError:
            return await ctx.send("**No results for given query found.**")

        embed = discord.Embed(
            title=f"Definition of {term}",
            description=definition,
            timestamp=datetime.datetime.utcnow(),
            url=permalink,
            colour=discord.Colour.blurple(),
        )
        embed.add_field(name="**Example**", value=example)
        embed.add_field(name="👍", value=thumbs_up, inline=False)
        embed.add_field(name="👎", value=thumbs_down)
        embed.set_thumbnail(
            url="https://cdn.discordapp.com/attachments/852867509765799956/854316233696083968/297387706245_85899a44216ce1604c93_512.png"
        )

        return await ctx.send(embed=embed)

    @commands.command()
    @commands.cooldown(1, 5)
    async def dadjoke(self, ctx):
        """Get a random dad joke"""
        url = "https://dad-jokes.p.rapidapi.com/random/joke"

        headers = {
            "x-rapidapi-key": api_key,
            "x-rapidapi-host": "dad-jokes.p.rapidapi.com",
        }

        response = requests.request("GET", url, headers=headers)

        embed = discord.Embed(
            title="Dad Joke",
            timestamp=datetime.datetime.utcnow(),
            colour=discord.Colour.blurple(),
        )
        embed.add_field(
            name=response.json()["body"][0]["setup"],
            value=response.json()["body"][0]["punchline"],
        )
        await ctx.send(embed=embed)

    @commands.command()
    async def roast(self, ctx, user: discord.Member):
        """Roast a member
        example:
        - raost @PlasticNoob"""
        url = f"https://insult.mattbas.org/api/insult.json?who={user}"
        response = requests.get(url)
        await ctx.send(response.json()["insult"])

    @commands.command()
    @commands.cooldown(1, 10)
    async def meme(self, ctx):
        """Get a random meme from the internet"""
        embed = discord.Embed(timestamp=datetime.datetime.utcnow())
        subs = ["dankmemes", "memes", "meme", "AdviceAnimals"]
        sort = ["hot", "top"]
        async with aiohttp.ClientSession() as cs:
            async with cs.get(
                f"https://www.reddit.com/r/{random.choice(subs)}/new.json?sort={random.choice(sort)}"
            ) as r:
                res = await r.json()
                embed.set_image(
                    url=res["data"]["children"][random.randint(0, 25)]["data"]["url"]
                )
                await ctx.send(embed=embed)

    @commands.command(name="8ball")
    @commands.cooldown(1, 5)
    async def _8ball(self, ctx, *, question):
        """Let the magic 8ball predict!
        example:
        - 8ball will I find love?"""
        responses = [
            "It is certain",
            "It is decidedly so",
            "Without a doubt",
            "Yes, definitely",
            "You may rely on it",
            "As I see it, yes",
            "Most likely",
            "Outlook good",
            "Yes",
            "Signs point to yes",
            "Reply hazy try again",
            "Ask again later",
            "Better not tell you now",
            "Cannot predict now",
            "Concentrate and ask again",
            "Don't count on it",
            "My reply is no",
            "My sources say no",
            "Outlook not so good",
            "Very doubtful",
        ]
        response = random.choice(responses)
        embed = discord.Embed(
            title="The Magic 8 Ball has Spoken!",
            timestamp=datetime.datetime.utcnow(),
            colour=discord.Colour.blurple(),
        )
        embed.add_field(name="Question: ", value=f"{question}", inline=True)
        embed.add_field(name="Answer: ", value=f"{response}", inline=False)
        embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)
        await ctx.send(embed=embed)

    @commands.command()
    @commands.cooldown(1, 5)
    async def showerthought(self, ctx):
        """Get a shower thought"""
        embed = discord.Embed(timestamp=datetime.datetime.utcnow())
        sort = ["hot", "top", "new", "rising"]
        async with aiohttp.ClientSession() as cs:
            async with cs.get(
                f"https://www.reddit.com/r/Showerthoughts/new.json?sort={random.choice(sort)}"
            ) as r:
                res = await r.json()
                embed.add_field(
                    name=f"{res['data']['children'][random.randint(0, 25)]['data']['title']}",
                    value="\u200b",
                )
                await ctx.send(embed=embed)

    @commands.command(aliases=["randomcolour"])
    @commands.cooldown(1, 5)
    async def randomcolor(self, ctx):
        """Get a random color HEX and RGB value"""
        color = "%06x" % random.randint(0, 0xFFFFFF)
        RGB = tuple(int(color[i : i + 2], 16) for i in (0, 2, 4))  # noqaE402
        embed = discord.Embed(
            timestamp=datetime.datetime.utcnow(), colour=int(color, 16)
        )
        embed.add_field(name="HEX", value=f"#{color}")
        embed.add_field(name="RGB", value=f"{RGB}")
        await ctx.send(embed=embed)

    @commands.command(aliases=["colour"])
    @commands.cooldown(1, 5)
    async def color(self, ctx, value: str):
        """Get a color by it's HEX or RGB value
        example:
        - color 1371b8"""
        if "," in value:
            try:
                r, g, b = value.split(",")
            except ValueError:
                return await ctx.send("**Invalid RGB value**")
            if int(r) < 256 and int(g) < 256 and int(b) < 256:
                hex = "%02x%02x%02x" % (int(r), int(g), int(b))
                embed = discord.Embed(
                    timestamp=datetime.datetime.utcnow(),
                    colour=discord.Colour.from_rgb(int(r), int(g), int(b)),
                )
                embed.add_field(name="RGB", value=value)
                embed.add_field(name="HEX", value=hex)
                return await ctx.send(embed=embed)

            else:
                return await ctx.send("**Invalid color value.**")
        elif len(value) == 6:
            try:
                embed = discord.Embed(
                    timestamp=datetime.datetime.utcnow(), colour=int(value, 16)
                )
            except ValueError:
                return await ctx.send("**Invalid HEX value**")
            RGB = tuple(int(value[i : i + 2], 16) for i in (0, 2, 4))  # noqaE402
            embed.add_field(name="HEX", value=value)
            embed.add_field(name="RGB", value=str(RGB))
            await ctx.send(embed=embed)
        else:
            return await ctx.send("**Invalid HEX value**")
