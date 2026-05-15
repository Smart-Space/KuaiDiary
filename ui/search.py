"""
全局搜索视图
"""
from tkinter import Entry
from typing import List
from tinui import BasicTinUI, ExpandPanel, VerticalPanel, HorizonPanel, CardPanel
from tinui.theme.tinuilight import TinUILight

import data
from control.search import search_engine, FileResult


class SearchView(BasicTinUI):

    def __init__(self, master=None, theme=TinUILight):
        super().__init__(master)
        self.set_scale(data.factory)
        self.ui = theme(self)
        self.Theme = theme
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

        ep = ExpandPanel(self, bg=self['background'], padding=(10,10,10,10))
        self.card_ui, self.card_rescroll, _, card_ui = self.ui.add_ui((0,0), scrollbar=True, region="man", content=False)
        ep.set_child(card_ui)
        vp.add_child(ep, weight=1)
        self.card_ui_theme = self.Theme(self.card_ui)
        self.card = CardPanel(self.card_ui, bg=self['background'], card_width=300, v_spacing=10, h_spacing=10)

        self.card_ui.bind("<Configure>", self.on_card_resize)
        self.bind("<Configure>", self.on_resize)
    
    def on_resize(self, event):
        self.root.update_layout(event.x, event.y, event.width-1, event.height-1)
    
    def on_card_resize(self, event):
        self.card.update_layout(event.x, event.y, event.width-1, event.height-1)
        self.card_rescroll()
    
    def on_search(self, text):
        results:List[FileResult] = search_engine.search(text, ignore_case=not data.settings['case_sensitive'])
        self.card.clear_children()
        for r in results:
            for i, m in enumerate(r.matches):
                vp = VerticalPanel(self.card_ui, spacing=5, bg=self.root.bg, padding=(5,5,5,5))
                hp = HorizonPanel(self.card_ui, spacing=5, bg=self.root.bg)
                vp.add_child(hp, 20)
                hp.add_child(self.card_ui_theme.add_label((0,0), text=f"{r.month}-{r.day} ({i+1}/{r.total_hits})", anchor='center')[-1])
                hp.add_child(self.card_ui_theme.add_button2((0,0), text='', icon='\uE72D', command=lambda _, path=(r.month,r.day):self.open_dairy(path), anchor='w')[-1], 20)
                vp.add_child(self.card_ui_theme.add_paragraph((0,0), text=f"...{m.snippet}...", width=self.scale_value(280)), 80)
                self.card.add_child(vp)
        self.card_ui.event_generate("<Configure>", x=0, y=0, width=self.card_ui.winfo_width(), height=self.card_ui.winfo_height())

    def open_dairy(self, path):
        data.req_open_dairy = path
        data.root.event_generate("<<OpenDiary>>")

    def force_refresh(self, _):
        search_engine.ensure_index(force=True)
