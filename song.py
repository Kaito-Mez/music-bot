import os

class Song:
    def __init__(self, searchterm) -> None:
        self.title = searchterm
        self.filename = ""
        self.thumbnail = ""
        self.is_downloaded = False
        self.downloading = False
    

    def populate(self, future):
        result = future.result()
        self.filename = result[0]
        self.thumbnail = result[1]
        self.title = result[2]
        self.is_downloaded = True
        self.downloading = False
        print(f"Populating: {self.title}, {self.filename}, {self.thumbnail}")
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
