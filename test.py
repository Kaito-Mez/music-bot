import sys
import os
from pathlib import Path
from io import BytesIO
sys.path.append(os.path.join(os.path.dirname(__file__), 'ytdlp'))
from ytdlp import ytdownloader
searchterm = "https://youtu.be/1KqSd5WH6II?si=2GVlL8u2gBA9f0_8"
is_link = False
buffer = BytesIO()
if "https://www.youtube.com/watch?v=" in searchterm or "https://youtu.be/" in searchterm:
    is_link = True
    
ytdownloader.download(searchterm, is_link, buffer)
Path("test.mp4").write_bytes(buffer.getvalue())
#print(yt)