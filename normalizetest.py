
import pytube
from sclib import SoundcloudAPI, Track
import subprocess
from subprocess import PIPE
from io import BytesIO
import time


def _get_soundcloud_auth():
    with open("data/soundcloudToken.txt", "r") as f:
        data = f.readline()
    return data

client_id=_get_soundcloud_auth()

soundcloud = SoundcloudAPI()

track = soundcloud.resolve('https://soundcloud.com/monstercat/unlike-pluto-everything-black')


search = pytube.Search("cyber grind")
url = search.results[0].watch_url
print(f"URL: {url}")
yt = pytube.YouTube(url)


t1 = time.time()

buffer = BytesIO()
#yt.streams.get_by_itag(251).stream_to_buffer(buffer)
track.write_mp3_to(buffer)



filename = "data/sounds/test.mp3"




cmd = ["ffmpeg", "-hide_banner", "-i", "pipe:0", 
"-vn", "-ab", "128k", "-ar", "48000", "-f", "mp3", "pipe:1", 
"|", "ffmpeg", "-hide_banner", "-i", "pipe:0", "-filter:a", 
"loudnorm=I=-36", "-c:a", "mp3", "-y", f"{filename}z.mp3"]

cmd = ["ffmpeg", "-hide_banner", "-i", "pipe:0", 
"-vn", "-ab", "128k", "-ar", "48000", "-f", "mp3",
 "-y", f"{filename}.mp3"]



cmd = ["ffmpeg", "-hide_banner", "-i", "pipe:0", "-vn",
"-ar", "44100", "-filter:a", f"loudnorm=I=-30", "-c:a", "mp3", "-y", f"{filename}"]




t2 = time.time()
pipe = subprocess.Popen(cmd, stdin=PIPE)
pipe.communicate(input=buffer.getvalue())
#pipe.wait()

print("TIME = ", t2-t1)