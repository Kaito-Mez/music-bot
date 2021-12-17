from spotipy import Spotify
from spotipy.oauth2 import SpotifyClientCredentials
from sclib import SoundcloudAPI, Track
from concurrent.futures.thread import ThreadPoolExecutor
import os
import pytube

class QueueManager():

    def __init__(self):
        self.current = None
        self.list = []
        self.index = 0
        self.is_downloading = False
        self.executor = ThreadPoolExecutor()
        auth = self._get_spotify_auth()
        self.spotify = Spotify(auth_manager=SpotifyClientCredentials(client_id=auth[0], client_secret=auth[1]))
        self.soundcloud = SoundcloudAPI(client_id=self._get_soundcloud_auth())

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

    
    
    def _on_download(self, future):
        print("Second")
        self.list.append(future.result())
        if len(self.list) == 1:
            self.current = self.list[0]
        self.is_downloading = False


    def add(self, searchterm:str):
        self.is_downloading = True
        future = self.executor.submit(self._download, searchterm)
        future.add_done_callback(self._on_download)
        print("First Hopefullty")

    def clear(self):
        print("triggered")
        self.__init__()
        for file in os.listdir("sound"):
            os.remove(f"sound/{file}")

    def previous(self):
        if self.index > 0:
            self.index -= 1
            self.current = self.list[self.index]
            return True
        
        return False

    def advance(self):
        if self.index == len(self.list) - 1 or len(self.list) == 0:
            return False

        else:
            self.index += 1
            self.current = self.list[self.index]
            return True

    def get_file(self):
        return f"sound/{self.current[0]}"

    def get_thumbnail(self):
        return self.current[1]    
    
    def _download(self, searchterm):
        print(searchterm)
        data = []
        if "spotify.com" in searchterm:
            data = self._download_sp(searchterm)

        elif "soundcloud.com" in searchterm:
            data = self._download_sc(searchterm)
        
        else:
            data = self._download_yt(searchterm)

        return data

        

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
        search = pytube.Search(searchterm)
        url = search.results[0].watch_url
        yt = pytube.YouTube(url)
        print(yt.title)
        filename = yt.title+".webm"
        yt.streams.get_by_itag(251).download("sound", filename)
        return [filename, yt.thumbnail_url]

    def _download_sc(self, url):
        print("SOUNDCLOUD")
        track = self.soundcloud.resolve(url)

        filename = f'{track.artist} {track.title}.mp3'

        with open("sound/" + filename, 'wb+') as fp:
            track.write_mp3_to(fp)
        
        return [filename, track.artwork_url]
