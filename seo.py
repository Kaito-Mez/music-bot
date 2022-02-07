
from fileinput import filename
import pytube
from sclib import SoundcloudAPI, Track
import subprocess
from subprocess import PIPE
from io import BytesIO
import time




search = pytube.Search("cyber grind")
url = search.results[0].watch_url

print(search.results)

yt = pytube.YouTube(url)
yt.streams.get_by_itag(251).download(filename="test.webm")