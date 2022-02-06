from discord.errors import ClientException, Forbidden
from disc_gui import discordBook
from queue_manager import ServerManager
import discord
import asyncio
import time

class MusicBot(discord.Client):

    def __init__(self):
        self.servers = []

        super().__init__()


    async def _setup_guild(self, guild):

        channels = await guild.fetch_channels()
        channel_id = None
        has_channel = False
        for channel in channels:
            if channel.name == "music-test":
                has_channel = True
                channel_id = channel.id
                break
        if not has_channel:
            try:
                channel_id = await guild.create_text_channel(name="music-test", topic="You want to play league of legends 😵😵")
                channel_id = channel_id.id
                has_channel = True
            except Forbidden:
                print(guild.name, "couldnt create chanenl")
        

        #if bot doesnt have perms to make a channel
        if has_channel:
            await client.get_channel(channel_id).purge()
            book = discordBook(self, False, "data/screen.json")
            
            print(f"sending to {guild.name}")
            await book.send_book(client.get_channel(channel_id))

            
            server = ServerManager(guild.id, channel_id, book, self)

            self.servers.append(server)


    async def on_guild_join(self, guild):
        print("Guild Joined ", guild.name)
        await self._setup_guild(guild)


    def on_song_end(self):
        t = time.time()
        #for server in self.servers:
        #   server.pause_audio()

        for server in self.servers:
            server.download_all()

        t2 = time.time()
        print(f"Glitch time ~{t2-t}s")
        
        #for server in self.servers:
        #   server.resume_audio()


    def get_server_from_message(self, message):
        for server in self.servers:
            if message.channel.id == server.channel:
                return server
        return False

    async def on_message(self, message):
        
        if message.author == client.user:
            return

        server = self.get_server_from_message(message)
        if server:
            if message.channel.id == server.get_channel_id():
                server.add(message.content)
                await asyncio.sleep(0.5)
                await message.delete()
                if not server.is_playing():
                    await self.handle_play_pause(server, message.author)
                


        
    




    async def handle_play_pause(self, server, member):

        if not server.vc:
            if server.is_member_connected(member):
                await server.join_channel(member.voice.channel.id)
            else:
                return

        if server.vc:
            if server.is_member_in_call(member):
                if server.vc.is_playing():
                    await server.pause_audio()
                elif server.vc.is_paused():
                    await server.resume_audio()
                else:
                    await server.play_audio()










    


    async def on_ready(self):
        for guild in client.guilds:
            await self._setup_guild(guild)
        
        print("Bot Online!")
        print("Name: {}".format(self.user.name))
        print("ID: {}".format(self.user.id))
        print("Version: {}".format(discord.__version__))
        print(discord.opus.is_loaded())

    
    def _get_server_from_message(self, id):
        for server in self.servers:
            if server.get_message_id() == id:
                return server
        return False

    #connect ui with bot
    async def on_reaction_add(self, reaction, member):
        if client.user == member:
            return

        id = reaction.message.id
        server = self._get_server_from_message(id)
        if server:
            print("made it")
            book = server.book
            result = await book.handle_react(reaction, member)
            
        else:
            result = -1


        if result == -1:
            return
        
        elif result == 1:
            await server.to_start()

        elif result == 2:
            await server.previous_audio()

        elif result == 3:
            await self.handle_play_pause(server, member)
        
        elif result == 4:
            await server.next_audio()

        elif result == 5:
            await server.to_end()
            
        elif result == 6:
            await server.stop_audio()

        print(result)






def get_token():
    with open("data/DiscordToken.txt", "r") as f:
        token = f.readline()
        return token


if __name__ == "__main__":
    client = MusicBot()
    client.run(get_token())

#Stop Button
#