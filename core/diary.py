"""
日记信息核心
"""
import datetime

class Diary:
    def __init__(self, date:datetime.date):
        self.date = date
        self.contents = ""
        self.existence = False
        self.format = False

    def update_contents(self, contents, format_flag=None):
        self.contents = contents
        self.existence = True
        if format_flag is not None:
            self.format = format_flag

    def get_contents(self):
        return self.contents

