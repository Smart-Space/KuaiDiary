"""
全局搜索视图
"""
from tkinter import Entry
import datetime
from typing import List
from tinui import BasicTinUI, ExpandPanel, VerticalPanel, HorizonPanel, show_error
from tinui.theme.tinuilight import TinUILight

import data
from control.search import search_engine, FileResult


class SearchView(BasicTinUI):

    def __init__(self, master=None, theme=TinUILight):
        super().__init__(master)
        self.set_scale(data.factory)
        self.ui = theme(self)
        self.theme = data.settings['theme']
        self.init_ui()
    
    def init_ui(self):
        all_bg = '#F9F9F9' if data.settings['theme'] == 'light' else '#272727'
        self.root = ExpandPanel(self, padding=(4,4,4,4), bg=all_bg, bd=17)

        vp = VerticalPanel(self, spacing=5)
        self.root.set_child(vp)

        hp = HorizonPanel(self, spacing=5)
        vp.add_child(hp, 40)
        hp.add_child(self.ui.add_back((0,0)), weight=1)
        entrys = self.ui.add_entry((0,0), width=400, call='\uF78B', command=self.on_search, anchor='w')
        self.entry:Entry = entrys[0]
        hp.add_child(entrys[-1])
        hp.add_child(self.ui.add_button2((0,0), text='', icon='\uE895', command=self.force_refresh, anchor='w')[-1])
        hp.add_child(self.ui.add_back((0,0)), weight=1)

        self.bind("<Configure>", self.on_resize)
    
    def on_resize(self, event):
        self.root.update_layout(event.x, event.y, event.width-1, event.height-1)
    
    def on_search(self, text):
        results:List[FileResult] = search_engine.search(text)
        for r in results:
            print(f"{r.month}-{r.day} ({len(r.matches)} matches)")
            for m in r.matches:
                print(f"  ...{m.snippet}...")
        # TODO 显示结果
    
    def force_refresh(self, _):
        search_engine.ensure_index(force=True)
