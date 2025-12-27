"""
日记信息核心
"""
import datetime

class Diary:
    def __init__(self, date:datetime.date):
        self.date = date
        self.contents = ""
        self.existence = False

    def update_contents(self, contents):
        self.contents = contents
        self.existence = True
    
    def get_contents(self):
        return self.contents

