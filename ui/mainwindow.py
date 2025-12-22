"""
KuaiDiary主窗口
"""
from tkinter import Tk

from tinui import BasicTinUI, ExpandPanel, VerticalPanel, HorizonPanel
from tinui.theme.tinuilight import TinUILight
from tinui.theme.tinuidark import TinUIDark

class MainWindow(Tk):

    def __init__(self, theme=TinUILight):
        super().__init__()
        self.title("KuaiDiary")
        self.geometry("800x600")
        self.minsize(800, 600)
        self.theme = theme
        self.init_ui()
    
    def init_ui(self):
        self.ui_ = BasicTinUI(self)
        self.ui_.pack(fill="both", expand=True)
        self.ui = self.theme(self.ui_)

        self.root = ExpandPanel(self.ui_, padding=(5,5,5,5))
        
        hp1 = HorizonPanel(self.ui_)
        self.root.set_child(hp1)
        self.nav = self.ui.add_navigation((0,0), maxwidth=100, content=(('\uE929','今日'),('\uE787','往昔'),('\uE713','设置')), command=self.change_view)
        hp1.add_child(self.nav[-1])

        ep = ExpandPanel(self.ui_)
        self.child = self.ui_.add_ui((0,0), content=False)
        ep.set_child(self.child[-1])
        hp1.add_child(ep, weight=1)

        self.ui_.bind("<Configure>", self.on_resize)
    
    def on_resize(self, event):
        self.root.update_layout(event.x, event.y, event.width, event.height)

    def change_view(self, tag):
        if isinstance(tag, bool):
            self.ui_.event_generate("<Configure>", x=0, y=0, width=self.winfo_width(), height=self.winfo_height())
