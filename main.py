
#good for downloading but requires exact url
from requests import auth
from sclib import SoundcloudAPI, Track, Playlist

import pytube

import spotipy
from spotipy.oauth2 import SpotifyClientCredentials, SpotifyOAuth

scope = "user-library-read"

sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(client_id="b58cdb1e535c4e99aa44da51f8cd02ce", client_secret="bad3ee5be47545689e28d901be264a92"))

for i in sp.track("https://open.spotify.com/track/40QjbtQ2GJigjUgVNiDiqJ?si=b1d66878a5dc4638"):
    print(i)
    
for i in sp.track("https://open.spotify.com/track/40QjbtQ2GJigjUgVNiDiqJ?si=b1d66878a5dc4638")["artists"]:
    print(i["name"])
s = pytube.Search("run by i am the kid you know what i mean")
link = s.results[0].watch_url
yt = pytube.YouTube(link)
for i in yt.streams:
    #print(i)
    pass

#yt.streams.get_by_itag(251).download()
api = SoundcloudAPI(client_id="0QQbTpZ8EsXI2Oz2cY45hz88oskRPlNY")  # never pass a Soundcloud client ID that did not come from this library

track = api.resolve('https://soundcloud.com/ninjaerx/the-prodigy-voodoo-people')

assert type(track) is Track

filename = f'./{track.artist} - {track.title}.mp3'

with open(filename, 'wb+') as fp:
    track.write_mp3_to(fp)