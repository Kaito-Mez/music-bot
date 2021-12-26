from asyncio.tasks import sleep

from discord.errors import ClientException
from disc_gui import discordBook
from queue_manager import QueueManager
import discord
import asyncio
import time

class MusicBot(discord.Client):

    def __init__(self):

        self.vc = None
        self.connected = False
        self.channel = None
        self.queue = QueueManager()
        self.ui = discordBook(self, False, "data/screen.json")
        super().__init__()



    def _is_user_connected(self, member):
        if member.voice.channel != None:
            print("is User Connected", True)
            return True
        else:
            print("is User Connected", False)
            return False

    def _is_same_call(self, member):
        if member.voice.channel != None and self.connected:
            print("is User in same call", "Maybe")
            if member.voice.channel == self.vc.channel:
                print("is User in same call", True)
                return True

        print("is User in same call", False)
        return False

    async def on_message(self, message):
        
        if message.author == client.user:
            return

        def call(f):
            asyncio.run_coroutine_threadsafe(self.update_player_info(), client.loop)
        #add new song from message
        self.queue.add(message.content, call)
        #result = self.executor.submit(self.download, message.content)

    def handle_after(self):
        
        print(f"AFTER {self.queue.current}, {self.queue.list}")
        if self.queue.advance():
            print(f"ADVANCE TRUE {self.queue.current}")
            asyncio.run_coroutine_threadsafe(self.update_player_info(), client.loop)
            asyncio.run_coroutine_threadsafe(self.play_audio(), client.loop)
        
        else:
            print(f"ADVANCE False {self.queue.current}")
            asyncio.run_coroutine_threadsafe(self.leave_channel(), client.loop)
        
    
    async def play_audio(self):

        if self.connected:
            if self.queue.current == None:
                if self.queue.is_downloading:
                    while self.queue.is_downloading:
                        print("awaiting download")
                        asyncio.sleep(0.5)
                    self.vc.play(discord.FFmpegPCMAudio(self.queue.get_file()), after = lambda _:self.handle_after())
            else:
                print("playing 2")
                print(f"{self.vc}, {self.queue}, {self.queue.get_file()}")
                self.vc.stop()
                self.vc.play(discord.FFmpegPCMAudio(self.queue.get_file()), after = lambda _:self.handle_after())

    async def stop_audio(self):
        if self.connected:
            try:
                self.vc.stop()
                await self.leave_channel()
            except discord.errors.ClientException as e:
                print("stop audio failed", e)
            finally:
                time.sleep(1)
                self.queue.clear()

    async def handle_play_pause(self, member):

        if not self.connected:
            if self._is_user_connected(member):
                await self.join_channel(member.voice.channel.id)
            else:
                return

        if self.connected:
            if self._is_same_call(member):
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

    async def previous_audio(self):
        if self.connected:
            try:
                self.vc.stop()
                self.queue.previous()
                await self.play_audio()
            except discord.errors.ClientException as e:
                print("prevy", e)

    async def next_audio(self):
        if self.connected:
            self.vc.stop()
            self.handle_after()

    async def join_channel(self, channel):

        try:
            print(channel)
            self.vc = await self.get_channel(channel).connect(reconnect = True)
            self.connected = True
        except discord.errors.ClientException as e:
            self.vc = None
            self.connected = False
            print(e)
    
    async def leave_channel(self):
        print("YEAH RIGHT")
        if self.connected:
            try:
                
                print("Innas")
                time.sleep(1)
                self.vc.play(discord.FFmpegPCMAudio("data/sounds/exit.webm"), after= lambda _:asyncio.run_coroutine_threadsafe(self.vc.disconnect(), client.loop))
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
        
        elif result == 1:
            await self.previous_audio()

        elif result == 2:
            await self.handle_play_pause(member)
        
        elif result == 3:
            await self.next_audio()

        elif result == 4:
            await self.stop_audio()

        print(result)


    async def update_player_info(self):
        fields = [self.get_embed_data()]
        self.ui.modify_page(1, True, fields = fields, thumbnail = {"url":self.queue.current[1]})
        await self.ui.update_page()

    def get_embed_data(self):
        dic = {"name":"Queue:", "inline":True}
        value = ""

        for index, item in enumerate(self.queue.list):
            if index == self.queue.index:
                value += "***"
            
            #value += item[0].replace("webm", "").replace("mp3", "").replace("-", " ")

            value += item[2]

            if index == self.queue.index:
                value += "***"
            
            value += "\n"

        dic["value"] = value

        return dic




if __name__ == "__main__":
    client = MusicBot()
    client.run("Mjk4NDE3Mzk5NDY2Njg4NTEz.WOIw3A.1-4w2uZ7Ri3gxjVVzJcXlah2-6E")