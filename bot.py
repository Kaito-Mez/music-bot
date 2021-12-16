from asyncio.coroutines import coroutine
from concurrent.futures.thread import ThreadPoolExecutor
from discord.opus import load_opus
from spotipy import Spotify
from spotipy.oauth2 import SpotifyClientCredentials
from sclib import SoundcloudAPI, Track
from disc_gui import discordBook
import discord
import pytube
import asyncio

class MusicBot(discord.Client):

    def __init__(self):
        self.executor = ThreadPoolExecutor()

        self.ui = discordBook(self, False, "data/screen.json")
        auth = self._get_spotify_auth()
        self.spotify = Spotify(auth_manager=SpotifyClientCredentials(client_id=auth[0], client_secret=auth[1]))
        self.soundcloud = SoundcloudAPI(client_id=self._get_soundcloud_auth())
        super().__init__()

    async def on_message(self, message):

        if message.author == client.user:
            return
        #add new song from message
        #result = self.executor.submit(self.download, message.content)


    async def do(self):        
        def my_after(vc):
            fut = asyncio.run_coroutine_threadsafe(vc.disconnect(), client.loop)
            try:
                fut.result()
            except:
                pass

        try:
            vc = await self.get_channel(738231254905782317).connect(reconnect = True)
            vc.play(discord.FFmpegPCMAudio("sound/Korn - Twist.webm"), after = lambda _:my_after(vc))
        except discord.errors.ClientException as e:
            print("PLAYER FAILURE")
            print(e)

    async def on_ready(self):
        ch = self.get_channel(738233500301394001)

        #await self.do()

        
        await self.ui.send_book(ch)
        print("Bot Online!")
        print("Name: {}".format(self.user.name))
        print("ID: {}".format(self.user.id))
        print("Version: {}".format(discord.__version__))
        print(discord.opus.is_loaded())


    async def on_reaction_add(self, reaction, user):
        result = await self.ui.handle_react(reaction, user)
        if result == -1:
            return
        
        else:
            print(result)

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


    def download(self, searchterm):
        print(searchterm)
        data = []
        if "spotify.com" in searchterm:
            data = self.download_sp(searchterm)

        elif "soundcloud.com" in searchterm:
            data = self.download_sc(searchterm)
        
        else:
            data = self.download_yt(searchterm)

        return data

        

    def download_sp(self, url):
        print("SPOTIFY")
        searchterm = ""
        track = self.spotify.track(url)
        searchterm += track["name"]
        for i in track["artists"]:
            searchterm += " "
            searchterm += i["name"]

        return self.download_yt(searchterm)
        

    def download_yt(self, searchterm):
        print("YOUTUBE")
        search = pytube.Search(searchterm)
        url = search.results[0].watch_url
        yt = pytube.YouTube(url)
        print(yt.title)
        yt.streams.get_by_itag(251).download("sound", yt.title+".webm")
        
        return [yt.title, yt.thumbnail_url]

    def download_sc(self, url):
        print("SOUNDCLOUD")
        track = self.soundcloud.resolve(url)

        filename = f'{track.artist} {track.title}.mp3'

        with open("sound/" + filename, 'wb+') as fp:
            track.write_mp3_to(fp)
        
        return [filename, track.artwork_url]




if __name__ == "__main__":
    client = MusicBot()
    client.run("Mjk4NDE3Mzk5NDY2Njg4NTEz.WOIw3A.1-4w2uZ7Ri3gxjVVzJcXlah2-6E")