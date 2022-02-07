import os
import datetime

class Song:
    def __init__(self, searchterm) -> None:
        self.title = searchterm
        self.filename = ""
        self.thumbnail = ""
        self.url = ""
        self.duration = 0
        self.is_downloaded = False
        self.downloading = False

    

    def populate(self, future):
        result = future.result()
        self.filename = result["filename"]
        self.thumbnail = result["thumbnail"]
        self.title = result["title"]
        self.duration = result["duration"]
        self.url = result["url"]

        self.duration = str(datetime.timedelta(seconds=self.duration))
        #brokey
        '''
        #splits second into hours and minutes and makes self.duration a string in either H/MM/SS, MM/SS, or SS format(eg 8:09:01)
        if self.duration < 60:
            #branch for SS format
            self.duration = f"{(str(int(self.duration % 60))).zfill(2)}"
        elif self.duration < 3600:
            #branch for MM/SS format
            self.duration = f"{(str(int(self.duration / 60))).zfill(2)}:{(str(int(self.duration % 60))).zfill(2)}"
        else:
            #branch for H/MM/SS format, would break if 10 hours but I'm assuming you don't allow 10 hour queues anyway 
            self.duration = f"{(int(self.duration / 3600))}:{(str(int((self.duration % 3600) / 60))).zfill(2)}:{(str(int((self.duration % 60) / 60))).zfill(2)}"
        '''
        self.is_downloaded = True
        self.downloading = False
        print(f"Populating: {self.title}, {self.filename}, {self.thumbnail}, {self.duration}")
        return

    def empty(self):
        try:
            os.remove(self.get_filepath())
        except OSError:
            print("Couldnt be deleted")
            
        self.__init__(self.title)

    def get_filepath(self) -> str:
        if self.is_downloaded:
            return "sound/"+self.filename
        
        else:
            return None
