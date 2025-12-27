"""
设置界面
"""
import webbrowser

from tinui import BasicTinUI, TinUIXml
from tinui.theme.tinuilight import TinUILight
from tinui.theme.tinuidark import TinUIDark

import data


class SettingView(BasicTinUI):

    def __init__(self, master=None, theme=TinUILight):
        super().__init__(master)
        self.ui = theme(self)
        self.uixml = TinUIXml(self.ui)
        self.init_ui()
    
    def init_ui(self):
        self.uixml.funcs['open_github'] = self.open_github
        self.uixml.funcs['open_gitee'] = self.open_gitee
        with open("./assets/settingui.xml", "r", encoding="utf-8") as f:
            xml = f.read().replace("%VERSION%", data.version)
        self.uixml.loadxml(xml)
    
    def open_github(self, _):
        ...
    
    def open_gitee(self, _):
        ...
