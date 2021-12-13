import discord
import disc_gui

class MusicBot(discord.Client):

    def __init__(self):
        
        super().__init__()

    async def on_ready(self):


        print("Bot Online!")
        print("Name: {}".format(self.user.name))
        print("ID: {}".format(self.user.id))
        print("Version: {}".format(discord.__version__))
        print(discord.opus.is_loaded())s



if __name__ == "__main__":
    client = MusicBot()
    client.run("Mjk4NDE3Mzk5NDY2Njg4NTEz.WOIw3A.1-4w2uZ7Ri3gxjVVzJcXlah2-6E")