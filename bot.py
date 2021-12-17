from disc_gui import discordBook
from queue_manager import QueueManager
import discord
import asyncio

class MusicBot(discord.Client):

    def __init__(self):

        self.vc = None
        self.connected = False
        self.channel = None
        self.queue = QueueManager()
        self.ui = discordBook(self, False, "data/screen.json")
        super().__init__()

    async def on_message(self, message):
        
        if message.author == client.user:
            return

        
        #add new song from message
        self.queue.add(message.content)
        #result = self.executor.submit(self.download, message.content)

    def handle_after(self):
        print("doing after")
        if self.queue.advance:
            client.loop.run_until_complete(self.play_audio)
            #asyncio.run_coroutine_threadsafe(self.play_audio, client.loop)
        
        else:
            asyncio.run_coroutine_threadsafe(self.leave_channel, client.loop)
    
    async def play_audio(self):    
        def my_after(vc):
            fut = asyncio.run_coroutine_threadsafe(vc.disconnect, client.loop)
            try:
                fut.result()
            except:
                pass
        
        #self.vc.play(discord.FFmpegPCMAudio(self.queue.get_file()), after = lambda _:my_after(self.vc))
        if self.connected:
            if self.queue.current == None:
                if self.queue.is_downloading:
                    while self.queue.is_downloading:
                        print("awaiting download")
                        asyncio.sleep(0.5)
                        print("playing")
                    self.vc.play(discord.FFmpegPCMAudio(self.queue.get_file()), after = lambda _:self.handle_after())
            else:
                print("playing 2")
                print("THINGS GO HERE")
                print(f"{self.vc}, {self.queue}, {self.queue.get_file()}")
                self.vc.play(discord.FFmpegPCMAudio(self.queue.get_file()), after = lambda _:self.handle_after())

    async def stop_audio(self):
        if self.connected:
            try:
                self.vc.stop()
                await self.leave_channel()
            except discord.errors.ClientException as e:
                print("stop audio failed", e)
            finally:
                self.queue.clear()

    async def handle_play_pause(self, member):
        if not self.connected:
            await self.join_channel(member.voice.channel.id)

        else:
            if self.vc.is_playing():
                await self.pause_audio()
            elif self.vc.is_paused():
                await self.resume_audio()
            else:
                await self.play_audio()

    async def resume_audio(self):
        if self.connected:
            try:
                self.vc.resume()
            except discord.errors.ClientException as e:
                print("resume audio failed", e)

    async def pause_audio(self):
        if self.connected:
            try:
                self.vc.pause()
                
            except discord.errors.ClientException as e:
                print("pause audio failed", e)

    async def join_channel(self, channel):

        try:
            print(channel)
            self.vc = await self.get_channel(channel).connect(reconnect = True)
            self.connected = True
            print(f"vc = {self.vc}")
        except discord.errors.ClientException as e:
            self.vc = None
            self.connected = False
            print(e)
    
    async def leave_channel(self):
        try:
            await self.vc.disconnect()
            self.connected = False
        except discord.errors.ClientException as e:
            print("Leave_channel_broke", e)

    async def on_ready(self):
        for channel in self.get_all_channels():
            if channel.name == "music":
                self.channel = channel
                await self.ui.send_book(self.channel)

        #await self.do()

        
        print("Bot Online!")
        print("Name: {}".format(self.user.name))
        print("ID: {}".format(self.user.id))
        print("Version: {}".format(discord.__version__))
        print(discord.opus.is_loaded())


    async def on_reaction_add(self, reaction, member):
        result = await self.ui.handle_react(reaction, member)
        if result == -1:
            return
        
        elif result == 2:
            await self.handle_play_pause(member)

        elif result == 4:
            await self.stop_audio()

        print(result)






if __name__ == "__main__":
    client = MusicBot()
    client.run("Mjk4NDE3Mzk5NDY2Njg4NTEz.WOIw3A.1-4w2uZ7Ri3gxjVVzJcXlah2-6E")