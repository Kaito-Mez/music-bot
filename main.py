
#good for downloading but requires exact url
from sclib import SoundcloudAPI, Track, Playlist

#doesnt work for anything
from pysoundcloud import Client


client = Client("0QQbTpZ8EsXI2Oz2cY45hz88oskRPlNY")



result = client.search("XYconstant her eyes ekae remix")
print(result)
api = SoundcloudAPI(client_id="0QQbTpZ8EsXI2Oz2cY45hz88oskRPlNY")  # never pass a Soundcloud client ID that did not come from this library

track = api.resolve('https://soundcloud.com/ninjaerx/the-prodigy-voodoo-people')

assert type(track) is Track

filename = f'./{track.artist} - {track.title}.mp3'

with open(filename, 'wb+') as fp:
    track.write_mp3_to(fp)