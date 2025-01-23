import auth as authorisation
from django.utils.text import slugify
from spotipy import Spotify
from spotipy.oauth2 import SpotifyClientCredentials
from sclib import SoundcloudAPI
from concurrent.futures.thread import ThreadPoolExecutor
import os
import sys
import ytdownloader
from models.song import Song
import discord
import asyncio
import time
import subprocess
from subprocess import PIPE
from io import BytesIO 
from random import shuffle

class ServerManager():

    def __init__(self, id, channel, book, client):
        self.directory = os.path.dirname(__file__)
        self.closing = False
        self.disengage = False
        self.rewind = False
        self.current = None
        self.queue = []
        self.index = 0
        self.executor = ThreadPoolExecutor(thread_name_prefix="ServerManagerExecutor")
        auth = authorisation.get_spotify_auth()
        self.spotify = Spotify(auth_manager=SpotifyClientCredentials(client_id=auth[0], client_secret=auth[1]))
        self.soundcloud = SoundcloudAPI()

        self.channel = channel
        self.id = id
        self.book = book
        self.vc = None
        self.client = client

    async def join_channel(self, channel):

        try:
            self.vc = await self.client.get_channel(channel).connect(reconnect = True)
            if self.vc:
                self.vc.play(discord.FFmpegPCMAudio("./data/sounds/bootup.mp3"))
        except discord.errors.ClientException as e:
            self.vc = None
            self.connected = False
            print(e)

    async def disconnect(self):
        if self.vc:
            await self.vc.disconnect()
            self.vc = None

    async def leave_channel(self):
        if self.vc:
            try:
                await asyncio.sleep(2)
                self.vc.play(discord.FFmpegPCMAudio("./data/sounds/exit.mp3"), after= lambda _:asyncio.run_coroutine_threadsafe(self.disconnect(), self.client.loop))
                await asyncio.sleep(3)
            except discord.errors.ClientException as e:
                print("Leave_channel_broke", e)

    async def play_audio(self):

        if self.vc:
            self.vc.stop()
            if self.current:
                print("awaiting download")
                while self.current.is_downloaded == False:
                    await asyncio.sleep(0.5)
                try:
                    self.vc.play(discord.FFmpegPCMAudio("./data/sounds/start.mp3"), after= lambda _:self.vc.play(discord.FFmpegPCMAudio(self.get_file()), after = lambda _:self.handle_after()))
                except discord.errors.ClientException as e:
                    pass

    async def stop_audio(self):
        if self.vc:
            try:
                self.closing = True
                self.vc.stop()
                await self.leave_channel()
            except discord.errors.ClientException as e:
                print("stop audio failed", e)
            finally:
                await asyncio.sleep(1)
                self.clear()
                await self.reset_player_info()

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

            if len(self.queue) > 0:
                self.index = 0
                self.current = self.queue[self.index]
                
                asyncio.run_coroutine_threadsafe(self.update_player_info(), self.client.loop)
                
            if self.is_paused() or self.is_playing():
                try:
                    self.vc.stop()
                except discord.errors.ClientException as e:
                    print("start ", e)
            else:
                self.handle_after()

    async def to_end(self):
        if self.vc:
            self.disengage = True

            if len(self.queue) > 0:
                self.index = len(self.queue) - 1
                self.current = self.queue[self.index]
                
                asyncio.run_coroutine_threadsafe(self.update_player_info(), self.client.loop)

            if self.is_paused() or self.is_playing():
                try:
                    self.vc.stop()
                except discord.errors.ClientException as e:
                    print("start ", e)
            else:
                self.handle_after()

    def is_playing(self):
        if self.vc:
            return self.vc.is_playing()

        return False

    def is_paused(self):
        if self.vc:
            return self.vc.is_paused()

    def handle_after(self):
        if not self.closing:
            if not self.disengage:
                if self.rewind:
                    self.previous()
                    self.rewind = False

                else:
                    self.advance()
                
            self.client.on_song_end()
            self.disengage = False
            self.vc.play(discord.FFmpegPCMAudio("./data/sounds/end.mp3"), after= lambda _:asyncio.run_coroutine_threadsafe(self.play_audio(), self.client.loop))
        self.closing = False

    def is_member_in_call(self, member):
        if member.voice and self.vc:
            if member.voice.channel == self.vc.channel:
                return True

        return False

    def is_member_connected(self, member):
        if member.voice:
            if member.voice.channel in self.client.get_guild(self.id).voice_channels:
                return True
        return False

    def is_bot_alone(self):
        if self.vc:
            if len(self.vc.channel.voice_states) == 1:
                
                print("BOT IS ALONE ")
                return True

        return False

    async def reset_player_info(self, update=True):
        self.book.remove_page(1)
        self.book.pages_from_json("./data/screen.json")
        if update:
            await self.book.update_page()

    async def update_player_info(self):
        queue_vis = []
        for i in self.queue:
            queue_vis.append(i.title)
        print("UPDATE CALLED", queue_vis)
        fields = [self.get_embed_data()]
        if self.current:
            print("AVATAR", self.current.requestor_avatar)
            self.book.modify_page(1, False, fields = fields, thumbnail = {"url":self.current.thumbnail}, 
                                title = self.current.title, url=self.current.url,
                                description = self.current.duration, 
                                footer = {"text":self.current.requestor_name, "icon_url": self.current.requestor_avatar})
        else:
            await self.reset_player_info(False)
            self.book.modify_page(1, False, fields = fields)
        await self.book.update_page()

    def display_song(self, test_index, num_to_display):

        queue_length = len(self.queue)
        current_index = self.index

        cutoff = int(num_to_display/2)


        if current_index < cutoff:
            if test_index < num_to_display:
                return True
            return False

        elif current_index >= queue_length-cutoff:
            if test_index >= queue_length-num_to_display:
                return True
            return False
        
        else:
            if test_index > current_index - cutoff and test_index <= current_index + cutoff:
                return True
            return False
            
    def get_embed_data(self):
        dic = {"name":"Queue:", "inline":True}
        value = ""
        num = 10

        for song in self.queue:
            test_ind = self.queue.index(song)
            if self.display_song(test_ind, num):
                if song == self.current:
                    value += "***"
                
                value += str(self.queue.index(song)+1)
                value += ". "
                value += song.title

                if song == self.current:
                    value += "***"
                
                value += "\n"

        dic["value"] = value
        return dic

    def remove_song(self, song):
        self.index -= 1
        if song:
            song.is_cancelled = True
            self.queue.remove(song)

        if song == self.current:
            self.current = None
            self.disengage = True

        self.vc.stop()
        path = song.get_filepath()
        if path:
            while os.path.isfile(path):
                try:
                    os.remove(song.get_filepath())
                except OSError as e:
                    pass
                time.sleep(0.1)

        if len(self.queue) == 0:
            asyncio.run_coroutine_threadsafe(self.reset_player_info(), self.client.loop)
        else:
            asyncio.run_coroutine_threadsafe(self.update_player_info(), self.client.loop)

    def get_downloads(self, max_num):
        l = []

        for index, song in enumerate(self.queue):
            if not song.is_downloaded and not song.downloading:
                if self.display_song(index, max_num):
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
    #calls download which call pytube
    def download_all(self):
        for song in self.get_downloads(10):
            song.downloading = True
            future = self.executor.submit(self._download, song.title, song)
            future.add_done_callback(song.populate)
    # song model section
    def add(self, searchterm:str, requestor):
        if "open.spotify.com/playlist/" in searchterm:
            playlist = self.spotify.playlist(searchterm)
            songs = playlist['tracks']['items']
            searchterms = []
            for songdata in songs:
                searchterms.append(songdata["track"]["external_urls"]["spotify"])

            shuffle(searchterms)

            for term in searchterms:
                song = Song(term, requestor)
                self.queue.append(song)        

                if self.current == None:
                    self.current = song
                    self.index = len(self.queue) - 1
                    self.client.on_song_end()

        else:    
            song = Song(searchterm, requestor)

            self.queue.append(song)

            if self.current == None:
                self.current = song
                self.index = len(self.queue) - 1
                self.client.on_song_end()

        asyncio.run_coroutine_threadsafe(self.update_player_info(), self.client.loop)

    def clear(self):
        for song in self.queue:
            song.empty()

        self.queue = []
            
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
        loop = True
        if len(self.queue) == 0 or self.index >= len(self.queue) - 1:
            self.index = len(self.queue) 
            self.current = None
            asyncio.run_coroutine_threadsafe(self.update_player_info(), self.client.loop)
            return False

            """
            elif self.index >= len(self.queue) - 1:
                self.index = 0
                self.current = self.queue[self.index]
                asyncio.run_coroutine_threadsafe(self.update_player_info(), self.client.loop)
                return True
            """
        else:
            self.index += 1
            self.current = self.queue[self.index]
            asyncio.run_coroutine_threadsafe(self.update_player_info(), self.client.loop)
            return True

    def get_file(self):
        if self.current:
            return f"./sound/{self.current.filename}"

    def _download(self, searchterm, song):
        data = []
        if "spotify.com" in searchterm:
            data = self._download_sp(searchterm, song)

        elif "soundcloud.com" in searchterm:
            data = self._download_sc(searchterm, song)
        #calls pytube
        else:
            data = self._download_yt(searchterm, song)

        asyncio.run_coroutine_threadsafe(self.update_player_info(), self.client.loop)

        return data

        

    def remove_song_duplicates(self, filename):
        count = 1
        indexes = []
        for i, song in enumerate(self.queue):
            if song.filename == filename:
                count += 1
                indexes.append(i)        

        if count > 1:
            indexes.reverse()
            for j in indexes:
                self.queue.pop(j)

    def process_normalize(self, process, input):
        process.communicate(input=input)

    def normalize_stream(self, buffer, path, song):


        with open("./data/volume.txt", "r") as f:
            target_level = int(f.readline())

        cmd = ["ffmpeg", "-hide_banner", "-loglevel", "warning", "-i", "pipe:0", "-vn",
        "-ar", "44100", "-filter:a", f"loudnorm=I={target_level}", "-c:a", "mp3", "-y", f"{path}"]

        process = subprocess.Popen(cmd, stdin=PIPE)
        #os.close(process.stdout)
        self.executor.submit(self.process_normalize, process, buffer.getvalue())
        while process.poll() is None:
            if not song.is_cancelled:
                time.sleep(1)
            else:
                print("CANCELLED")
                process.terminate()
                print("removing", song.title)
                os.remove(path)
        
        print("finished processing")

    def _download_sp(self, url, song):
        print("SPOTIFY")
        searchterm = ""
        track = self.spotify.track(url)
        searchterm += track["name"]
        for i in track["artists"]:
            searchterm += " "
            searchterm += i["name"]

        return self._download_yt(searchterm, song)
        
    #pytube location
    def _download_yt(self, searchterm, song):
        print("YOUTUBE")
        # adds local path for yt-dlp functionality
        sys.path.append(os.path.join(os.path.dirname(__file__), 'ytdlp'))
        is_link = False
        if "https://www.youtube.com/watch?v=" in searchterm or "https://youtu.be/" in searchterm:
            is_link = True #yt = pytube.YouTube(searchterm, use_oauth=True)
        yt = ytdownloader.download(searchterm, is_link)
        '''
        else:
            search = pytube.Search(searchterm)
            url = search.results[0].watch_url
            yt = pytube.YouTube(url, use_oauth=True)
        '''
        
        filename = slugify(yt["title"])+".mp3"
        path = "./sound/"+filename
        buffer = BytesIO()
        
        if yt["duration"] > 10800:
            self.remove_song(song)
        
        if not os.path.isfile(path):
            print("File not found")
            if not song.is_cancelled:
                print("streaming to buffer")
                '''itags = [251, 140, 139]
                stream = None
                for i in itags:
                    if not stream:
                        stream = yt.streams.get_by_itag(i)
                    else:
                        break

                stream.stream_to_buffer(buffer)'''
                # output download of song to stdout then to buffer
                ytdownloader.download(yt["url"], is_link, buffer)
            if not song.is_cancelled:
                print("normalizing audio")
                self.executor.submit(self.normalize_stream, buffer, path, song)

        else:
            self.remove_song_duplicates(filename)

        return {"filename":filename, "thumbnail":yt["thumbnail"], 
            "title":yt["title"], "duration":yt["duration"], "url":yt["url"]}

    def _download_sc(self, url, song):
        track = self.soundcloud.resolve(url)

        filename = f'{track.artist} {track.title}'
        filename = slugify(filename)
        filename += ".mp3"
        title = f'{track.artist} {track.title}'

        buffer = BytesIO()
        path = "./sound/"+filename
        '''
        if track.duration > 10800:
            print("song TOO LONG !!!!")
            self.remove_song(song)'''
        if not os.path.isfile(path):
            if not song.is_cancelled:
                track.write_mp3_to(buffer)
            if not song.is_cancelled:
                self.executor.submit(self.normalize_stream, buffer, path, song)
        else:
            self.remove_song_duplicates(filename)

        return {"filename":filename, "thumbnail":track.artwork_url, 
            "title":title, "duration":int(track.duration/1000), "url":track.permalink_url}