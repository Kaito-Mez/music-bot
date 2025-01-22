import sys
import os
#sys.path.append(os.path.join(os.path.dirname(__file__), 'yt_dlp'))
from yt_dlp import YoutubeDL
from contextlib import redirect_stdout
from io import BytesIO


def download(searchterm, is_link, buffer = None):
    '''
    downloads 'video' to 'musicbot/sound/' as blank webm with highest
    available audio quality, returns dictionary of title, thumbnail url,
    duration in secs and vid url,
    '''
    current_directory = os.path.dirname(__file__)
    sys.path.append(current_directory)
    #obtains directory to download files to
    download_folder = os.path.join(current_directory, "../sound")
    download_folder = os.path.abspath(download_folder)
    #print(download_folder)

    options = {
        "verbose": False,
        "format": "bestaudio",
        "default_search": 'ytsearch1',
        "overwrites": True,
        "logtostderr": True,
        #outputs to stdout
        "outtmpl":"-"
        #"paths": {"home": download_folder}
    }
    
    #extract info only if buffer not passed
    if buffer is None:
        
        with YoutubeDL(options) as ydl:
            info = ydl.extract_info(searchterm, download=False)
        # if searchterm is not a link, extract_audio will return a json with list,
        if not is_link:
            info = info["entries"][0]
        #print(json.dumps(ydl.sanitize_info(info)))
        #print(info["title"], info["thumbnail"], info["webpage_url"], info["duration"])
        return {"title":info["title"], "thumbnail":info["thumbnail"],
                "duration": info["duration"], "url":info["webpage_url"]}
    #download only to buffer
    else:
        with redirect_stdout(buffer), YoutubeDL(options) as ydl:
            ydl.download(searchterm)