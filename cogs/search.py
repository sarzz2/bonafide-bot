from discord.ext import commands
from googlesearch import search
from dotenv import load_dotenv
import requests
import os

load_dotenv()
google_api_key = os.getenv("google-api-key")


def setup(bot: commands.Bot):
    bot.add_cog(Search(bot=bot))


class Search(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_check(self, ctx):
        """Check if the category/cog is enabled"""

        if ctx.author.guild_permissions.administrator:
            return True
        query = (
            """ SELECT * FROM cog_check WHERE guild_id = $1 AND cog_name = 'search'"""
        )
        data = await self.bot.db.fetch_row(query, ctx.guild.id)
        if data.get("enabled") is True:
            return True
        else:
            return False

    @commands.command()
    @commands.cooldown(1, 10)
    async def google(self, ctx, *, query):
        """Search for something on google
        example:
        - google who is elon musk?"""
        for j in search(query, tld="com", num=1, stop=1, pause=1):
            await ctx.send(j)

    @commands.command()
    @commands.cooldown(1, 5)
    async def youtube(self, ctx, *, query):
        """Search for a video on youtube
        example:
        - youtube spaceX"""
        url = f"https://www.googleapis.com/youtube/v3/search?part=snippet&q={query}&type=video&maxResults=1&key={google_api_key}"
        response = requests.get(url)
        try:
            await ctx.send(
                f"https://www.youtube.com/watch?v={response.json()['items'][0]['id']['videoId']}"
            )
        except IndexError:
            await ctx.send("**No results for given query found.**")
