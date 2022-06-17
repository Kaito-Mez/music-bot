from discord.errors import ClientException, Forbidden
from disc_gui import discordBook
from queue_manager import ServerManager
import discord
import asyncio
import time
import os

class MusicBot(discord.Client):

    def __init__(self, intents):
        self.directory = os.path.dirname(__file__)
        self.servers = []

        super().__init__(intents = intents)


    async def _setup_guild(self, guild):

        channels = await guild.fetch_channels()
        channel_id = None
        has_channel = False

        name = "8-track-fm"
        topic = "<:8TrackFM:941526015602225192> Join a call and send messages or links in this channel to queue music. Supported platforms: Youtube, Spotify (Link Only), Souncloud (Link Only)"
        for channel in channels:
            if channel.name == name:
                has_channel = True
                channel_id = channel.id
                break
            elif channel.name == "8trackfm941526015602225192-8-track-fm":
                await channel.delete()
        if not has_channel:
            #if bot doesnt have perms to make a channel
            try:
                channel_id = await guild.create_text_channel(name=name, topic=topic)
                channel_id = channel_id.id
                has_channel = True
            except Forbidden:
                print(guild.name, "couldnt create chanenl")
        

        if has_channel:
            def is_not_music_message(message):
                return message.author != client.user
            channel = client.get_channel(channel_id)
            await channel.purge(check = is_not_music_message)
            book = discordBook(self, False, self.directory+"/data/screen.json")

            print(f"sending to {guild.name}")
            found = False
            
            music_message = None

            async for message in channel.history(limit=100):
                if not found:
                    if not is_not_music_message(message):
                        music_message = await channel.fetch_message(message.id)
                        found = True

            if music_message:
                print("attaching")
                await book.send_book(channel, music_message)

            else:
                print("creating")
                await book.send_book(channel)

            
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

    def get_server_from_id(self, id):
        for server in self.servers:
            if server.id == id:
                return server
        return None

    def get_server_from_message(self, channel_id):
        for server in self.servers:
            if channel_id == server.channel:
                return server
        return False

    async def on_message(self, message):
        print("MESSAGE RECEIVED")

        async def add_song(server, message):
            server.add(message.content, message.author)
            if not server.is_playing():
                await self.handle_play_pause(server, message.author)

        if message.author == client.user:
            return

        server = self.get_server_from_message(message.channel.id)
        if server:
            if message.channel.id == server.get_channel_id():
                await asyncio.sleep(0.5)
                await message.delete()
                if server.vc:
                    if server.is_member_in_call(message.author):
                        await add_song(server, message)

                else:
                    if server.is_member_connected(message.author):
                        await add_song(server, message)
                


        
    




    async def handle_play_pause(self, server, member):

        if server.vc:
            if server.is_member_in_call(member):
                if server.is_playing():
                    await server.pause_audio()
                elif server.is_paused():
                    await server.resume_audio()
                else:
                    await server.play_audio()
                    
        if not server.vc:
            if server.is_member_connected(member):
                await server.join_channel(member.voice.channel.id)







    


    async def on_ready(self):
        for guild in client.guilds:
            await self._setup_guild(guild)
        
        print("Bot Online!")
        print("Name: {}".format(self.user.name))
        print("ID: {}".format(self.user.id))
        print("Version: {}".format(discord.__version__))
        print(discord.opus.is_loaded())

    async def on_raw_reaction_add(self, payload:discord.RawReactionActionEvent):
        member = payload.member
        emoji = payload.emoji
        message_id = payload.message_id
        channel_id = payload.channel_id
        if client.user == member:
            return

        server = self.get_server_from_message(channel_id)
        if server:
            book = server.book
            result = await book.handle_react(emoji, member, message_id)
            
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
            server.remove_song(server.current)

        elif result == 7:
            await server.stop_audio()

        print("React result ", result)

    #connect ui with bot
    '''
    async def on_reaction_add(self, reaction, member):
        if client.user == member:
            return

        msg = reaction.message
        server = self.get_server_from_message(msg)
        if server:
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
            server.remove_song(server.current)

        elif result == 7:
            await server.stop_audio()

        print("React result ", result)
    '''

    async def on_voice_state_update(self, member, before, after):
        if before.channel:
            server = self.get_server_from_id(before.channel.guild.id)
            if server:
                if server.is_bot_alone():
                    await server.stop_audio()




def get_token():
    with open("data/discordToken.txt", "r") as f:
        token = f.readline()
        return token


if __name__ == "__main__":
    intents = discord.Intents.all()
    
    client = MusicBot(intents=intents)
    client.run(get_token())

#Stop Button
#