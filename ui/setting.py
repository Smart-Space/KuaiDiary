"""
设置界面
"""
import webbrowser

from tinui import BasicTinUI, TinUIXml
from tinui.theme.tinuilight import TinUILight
# from tinui.theme.tinuidark import TinUIDark

import data


class SettingView(BasicTinUI):

    def __init__(self, master=None, theme=TinUILight):
        super().__init__(master)
        self.ui = theme(self)
        self.uixml = TinUIXml(self.ui)
        self.init_ui()
        bbox = [*self.bbox('all')]
        bbox[0] -= 5
        bbox[1] -= 5
        bbox[2] += 5
        bbox[3] += 5
        self.config(scrollregion=bbox)
        self.bind('<MouseWheel>', self.on_mousewheel)
    
    def on_mousewheel(self, event):
        self.yview_scroll(int(-1*(event.delta/120)), "units")
    
    def init_ui(self):
        self.uixml.funcs['open_github'] = self.open_github
        self.uixml.funcs['open_gitee'] = self.open_gitee
        with open("./assets/settingui.xml", "r", encoding="utf-8") as f:
            xml = f.read().replace("%VERSION%", data.version)
        self.uixml.loadxml(xml)
    
    def open_github(self, _):
        webbrowser.open("https://github.com/Smart-Space/KuaiDiary")
    
    def open_gitee(self, _):
        webbrowser.open("https://gitee.com/captorking/KuaiDiary")
