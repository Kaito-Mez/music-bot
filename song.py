import os
import datetime
import time

class Song:
    '''Container for a song. Created when a song is requested and fully populated upon song download'''

    
    directory = ""
    '''Path to the stored file'''

    title = ""
    '''Title of the song'''

    requestor_avatar = ""
    '''URL of the avatar of the discord user who requested the song'''

    filename = ""
    '''Filename of the stored file'''

    thumbnail = ""
    '''URL of the thumbnail of the song/video'''

    url = ""
    '''URL to the song/video'''

    duration = 0
    '''Duration of the song in seconds'''

    downloading = False
    '''Whether the file is currently being downloaded'''

    is_downloaded = False
    '''Whether the file has been downloaded and the metadata populated'''

    is_cancelled = False
    '''Whether the download for this video has been calculated'''

    def __init__(self, searchterm, requestor):
        self.directory = os.path.dirname(__file__)
        self.title = searchterm
        if requestor.nick:
            self.requestor_name = requestor.nick
        else:
            self.requestor_name = requestor.name
        self.requestor_avatar = str(requestor.avatar.url)
        self.filename = ""
        self.thumbnail = ""
        self.url = ""
        self.duration = 0
        self.is_downloaded = False
        self.downloading = False
        self.is_cancelled = False

    def populate(self, future):
        '''Populates the metadata once the download future has completed'''
        result = future.result()
        self.filename = result["filename"]
        self.thumbnail = result["thumbnail"]
        self.title = result["title"]
        self.duration = result["duration"]
        self.url = result["url"]

        self.duration = str(datetime.timedelta(seconds=self.duration))
        self.is_downloaded = True
        self.downloading = False
        print(f"Populating: {self.title}, {self.filename}, {self.thumbnail}, {self.duration}")
        return

    def empty(self):
        '''Deletes the local file once it is no longer needed'''
        self.is_cancelled = True
        if self.get_filepath():
            while os.path.isfile(self.get_filepath()):
                try:
                    os.remove(self.get_filepath())
                except OSError:
                    print("Couldnt be deleted")
                    time.sleep(0.2)

    def get_filepath(self) -> str:
        '''Returns filepath'''
        if self.is_downloaded:
            return "./sound/"+self.filename
        
        else:
            return None
