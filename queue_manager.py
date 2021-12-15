class Queue_Manager():
    def __init__(self):
        self.current = None
        self.list = []
        self.index = 0
    def add(self, filename:str):
        self.list.append(filename)
        if self.list.length() == 1:
            self.current = self.list[self.index]
        
    def remove(self, filename:str):
        self.list.remove(filename)
    def backtrack(self):
        if self.index > 0:
            self.index -= 1
    def skip(self):
        if self.index == self.list.length() - 1 or self.list.length() == 0:
            self.current = None
            self.index = 0
        else:
            self.index += 1
            self.current = self.list[self.index]