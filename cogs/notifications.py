from discord.ext import commands


def setup(bot: commands.Bot):
    bot.add_cog(Notifcation(bot=bot))


class Notifcation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # @tasks.loop(seconds=60)
    # async def yt():
    #     youtube = build('youtube', 'v3', developerKey='Enter your key here')
    #     req = youtube.playlistItems().list(
    #         playlistId='The Playlist id of the channel you want to post video i.e. the id of video playlist of the channel',
    #         part='snippet',
    #         maxResults=1
    #     )
    #     res = req.execute()
    #     vedioid = res['items'][0]['snippet']['resourceId']['videoId']
    #     link = "https://www.youtube.com/watch?v=" + vedioid
    #     ch = await client.fetch_channel("channel")
    #
    #     async for message in ch.history(
    #             limit=1):  # looping through the channel to get  the latest message i can do this using last message also but I prefer using channel.history
    #         if str(link) != str(message.content):
    #             ch2 = await client.fetch_channel("")
    #
    #             await ch2.send(f'@everyone,**User** just posted a vedio!Go and check it out!\n{link}')
    #
    #             await ch.send(link2)  # this is important as after posting the video the link must also be posted to the check channel so that the bot do not send other link
    #         else:
    #             pass
