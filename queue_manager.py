from django.utils.text import slugify
from spotipy import Spotify
from spotipy.oauth2 import SpotifyClientCredentials
from sclib import SoundcloudAPI, Track
from concurrent.futures.thread import ThreadPoolExecutor
import os
import pytube
from song import Song
import discord
import asyncio
import time
import ffmpeg_normalize

class ServerManager():

    def __init__(self, id, channel, book, client):
        self.disengage = False
        self.rewind = False
        self.current = None
        self.queue = []
        self.index = 0
        self.executor = ThreadPoolExecutor()
        auth = self._get_spotify_auth()
        self.spotify = Spotify(auth_manager=SpotifyClientCredentials(client_id=auth[0], client_secret=auth[1]))
        self.soundcloud = SoundcloudAPI(client_id=self._get_soundcloud_auth())

        
        self.channel = channel
        self.id = id
        self.book = book
        self.vc = None
        self.client = client

    async def join_channel(self, channel):

        try:
            print(channel)
            self.vc = await self.client.get_channel(channel).connect(reconnect = True)
        except discord.errors.ClientException as e:
            self.vc = None
            self.connected = False
            print(e)

    async def leave_channel(self):
        if self.vc:
            try:
                print("Innas")
                await asyncio.sleep(5)
                self.vc.play(discord.FFmpegPCMAudio("data/sounds/exit.webm"), after= lambda _:asyncio.run_coroutine_threadsafe(self.vc.disconnect(), self.client.loop))
                await asyncio.sleep(3)
            except discord.errors.ClientException as e:
                print("Leave_channel_broke", e)

    async def play_audio(self):

        if self.vc:
            if self.current:
                while self.current.is_downloaded == False:
                    await asyncio.sleep(0.5)
                    print("awaiting download")
                await self.update_player_info()
                self.vc.play(discord.FFmpegPCMAudio("data/sounds/start.webm"), after= lambda _:self.vc.play(discord.FFmpegPCMAudio(self.get_file()), after = lambda _:self.handle_after()))
            


    async def stop_audio(self):
        if self.vc:
            try:
                self.vc.stop()
                await self.leave_channel()
                self.vc = None
            except discord.errors.ClientException as e:
                print("stop audio failed", e)
            finally:
                await asyncio.sleep(1)
                self.clear()

    async def resume_audio(self):
        if self.vc:
            try:
                self.vc.resume()
            except discord.errors.ClientException as e:
                print("resume audio failed", e)

    async def pause_audio(self):
        if self.vc:
            try:
                self.vc.pause()
                
            except discord.errors.ClientException as e:
                print("pause audio failed", e)


    async def next_audio(self):
        if self.vc:
            if self.is_paused() or self.is_playing():
                self.vc.stop()
            else:    
                self.handle_after()


    async def previous_audio(self):
        if self.vc:
            self.rewind = True
            if self.is_paused() or self.is_playing():
                try:
                    self.vc.stop()
                except discord.errors.ClientException as e:
                    print("prevy", e)
            else:
                self.handle_after()

    async def to_start(self):
        if self.vc:
            self.disengage = True
            if self.is_paused or self.is_playing():
                try:
                    self.vc.stop()
                except discord.errors.ClientException as e:
                    print("start ", e)
            
            else:
                self.handle_after()
            if len(self.queue) > 0:
                self.index = 0
                self.current = self.queue[self.index]

    async def to_end(self):
        if self.vc:
            self.disengage = True
            if self.is_paused or self.is_playing():
                try:
                    self.vc.stop()
                except discord.errors.ClientException as e:
                    print("start ", e)
            else:
                self.handle_after()

            if len(self.queue) > 0:
                self.index = len(self.queue) - 1
                self.current = self.queue[self.index]

    def is_playing(self):
        if self.vc:
            return self.vc.is_playing()

        return False

    def is_paused(self):
        if self.vc:
            return self.vc.is_paused()

    def handle_after(self):
        
        self.client.on_song_end()
        if not self.disengage:
            if self.rewind:
                self.previous()
                self.rewind = False

            else:
                if self.advance():
                    print(f"ADVANCE TRUE {self.current}")
            
        self.disengage = False
        self.vc.play(discord.FFmpegPCMAudio("data/sounds/end.webm"), after= lambda _:asyncio.run_coroutine_threadsafe(self.play_audio(), self.client.loop))




    def is_member_in_call(self, member):
        if member.voice.channel != None and self.vc:
            if member.voice.channel == self.vc.channel:
                return True

        return False

    def is_member_connected(self, member):
        if member.voice.channel != None:
            if member.voice.channel in self.client.get_guild(self.id).voice_channels:
                return True
        return False






    async def update_player_info(self):
        fields = [self.get_embed_data()]

        self.book.modify_page(1, False, fields = fields, thumbnail = {"url":self.current.thumbnail}, title = {"title":self.current.title}, description = {"description":self.current.duration})
        await self.book.update_page()

    def get_embed_data(self):
        dic = {"name":"Queue:", "inline":True}
        value = ""

        for song in self.queue:
            if song == self.current:
                value += "***"

            value += song.title

            if song == self.current:
                value += "***"
            
            value += "\n"

        dic["value"] = value

        return dic





















    def _get_spotify_auth(self):
        data = []
        with open("data/spotifyToken.txt", "r") as f:
            data.append(f.readline())

        with open("data/spotifySecret.txt", "r") as f:
            data.append(f.readline())

        return data

    def _get_soundcloud_auth(self):
        with open("data/soundcloudToken.txt", "r") as f:
            data = f.readline()
        return data


    def get_downloads(self):
        l = []
        for song in self.queue:
            if not song.is_downloaded and not song.downloading:
                l.append(song)
        return l


    def get_message_id(self):
        return self.book.message.id

    def get_channel_id(self):
        return self.channel

    def is_same_channel(self, channel_id):
        return channel_id == self.channel

    def is_same_message(self, message_id):
        return message_id == self.get_message_id()

    def download_all(self):
        for song in self.get_downloads():
            song.downloading = True
            future = self.executor.submit(self._download, song.title)
            future.add_done_callback(song.populate)


    
    def _on_download(self, future):
        print("Second")
        self.queue.append(future.result())
        if len(self.queue) == 1:
            self.current = self.queue[0]


    def add(self, searchterm:str):
        song = Song(searchterm)
        self.queue.append(song)
        if self.current == None:
            self.current = song
            self.index = len(self.queue) - 1
            self.client.on_song_end()

        asyncio.run_coroutine_threadsafe(self.update_player_info(), self.client.loop)

    def clear(self):
        print("triggered")
        for song in self.queue:
            song.empty()
            self.queue.remove(song)
            
        self.__init__(self.id, self.channel, self.book, self.client)
        
        asyncio.run_coroutine_threadsafe(self.update_player_info(), self.client.loop)

    def previous(self):
        if len(self.queue) == 0:
            return False

        if self.index > 0:
            self.index -= 1
            self.current = self.queue[self.index]
        else:
            self.index = 0
            self.current = self.queue[self.index]
        
        asyncio.run_coroutine_threadsafe(self.update_player_info(), self.client.loop)
        return True

    def advance(self):
        if self.index >= len(self.queue) - 1 or len(self.queue) == 0:
            self.index = len(self.queue) 
            self.current = None
            asyncio.run_coroutine_threadsafe(self.update_player_info(), self.client.loop)
            return False

        else:
            print("INDEX BEFORE INCREMENT " + str(self.index))
            self.index += 1
            self.current = self.queue[self.index]
            asyncio.run_coroutine_threadsafe(self.update_player_info(), self.client.loop)
            return True

    def get_file(self):
        return f"sound/{self.current.filename}"

    





    





    def _download(self, searchterm):
        print(searchterm)
        data = []
        if "spotify.com" in searchterm:
            data = self._download_sp(searchterm)

        elif "soundcloud.com" in searchterm:
            data = self._download_sc(searchterm)
        
        else:
            data = self._download_yt(searchterm)

        asyncio.run_coroutine_threadsafe(self.update_player_info(), self.client.loop)

        return data

        







    def normalize_mp3(self, path):
        with open("data/volume.txt", "r") as f:
            target_level = int(f.readline())
        norm = ffmpeg_normalize.FFmpegNormalize(audio_codec="mp3", target_level=target_level)
        norm.add_media_file(path, path)
        norm.run_normalization()

    def _download_sp(self, url):
        print("SPOTIFY")
        searchterm = ""
        track = self.spotify.track(url)
        searchterm += track["name"]
        for i in track["artists"]:
            searchterm += " "
            searchterm += i["name"]

        return self._download_yt(searchterm)
        

    def _download_yt(self, searchterm):
        print("YOUTUBE")
        print(f"SEARCHTERM:{searchterm}")
        if "https://www.youtube.com/watch?v=" in searchterm or "https://youtu.be/" in searchterm:
            yt = pytube.YouTube(searchterm)
        
        else:
            search = pytube.Search(searchterm)
            url = search.results[0].watch_url
            print(f"URL: {url}")
            yt = pytube.YouTube(url)


        print(yt.title)
        filename = slugify(yt.title)
        filename
        yt.streams.get_by_itag(251).download("sound", filename+".webm")

        path = "sound/"+filename
        os.system(f"ffmpeg -hide_banner -loglevel error -i \"{path}.webm\" -vn -ab 128k -ar 48000 -y \"{path}.mp3\"")
        os.remove(path+".webm")

        self.normalize_mp3(path+".mp3")

        return [filename+".mp3", yt.thumbnail_url, yt.title, yt.length]

    def _download_sc(self, url):
        print("SOUNDCLOUD")
        track = self.soundcloud.resolve(url)

        filename = f'{track.artist} {track.title}'
        filename = slugify(filename)
        filename += ".mp3"
        title = f'{track.artist} {track.title}'

        with open("sound/" + filename, 'wb+') as fp:
            track.write_mp3_to(fp)
        
        self.normalize_mp3("sound/"+filename)

        return [filename, track.artwork_url, title, track.duration]
