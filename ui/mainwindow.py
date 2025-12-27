"""
KuaiDiary主窗口
"""
from tkinter import Tk

from tinui import BasicTinUI, ExpandPanel, VerticalPanel, HorizonPanel
from tinui.theme.tinuilight import TinUILight
from tinui.theme.tinuidark import TinUIDark

from ui.today import TodayView
from ui.dates import DatesView
from ui.setting import SettingView

class MainWindow(Tk):

    def __init__(self, theme=TinUILight):
        super().__init__()
        self.title("KuaiDiary")
        self.iconbitmap('./logo.ico')
        self.geometry("800x600")
        self.minsize(800, 600)
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.theme = theme
        self.now_view:BasicTinUI = None
        # self.init_ui()
    
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

        self.now_view = self.today_view = TodayView(self.child[0], self.theme)
        self.dates_view = DatesView(self.child[0], self.theme)
        self.setting_view = SettingView(self.child[0], self.theme)
        self.now_view.pack(fill="both", expand=True)
    
    def on_resize(self, event):
        self.root.update_layout(event.x, event.y, event.width, event.height)

    def change_view(self, tag):
        if isinstance(tag, bool):
            self.ui_.event_generate("<Configure>", x=0, y=0, width=self.winfo_width(), height=self.winfo_height())
            return
        if not self.now_view:
            return # UI初始化时会触发，但界面还没初始化
        if tag == '今日':
            self.now_view.pack_forget()
            self.now_view = self.today_view
        elif tag == '往昔':
            self.now_view.pack_forget()
            self.now_view = self.dates_view
        elif tag == '设置':
            self.now_view.pack_forget()
            self.now_view = self.setting_view
        self.now_view.pack(fill="both", expand=True)
    
    def on_close(self): # 保存日志并退出
        """
        保存策略
        当天日记，如果不为空，则保存，为空则删除
        过往日记，在树状图选择后，上一次编辑保存，这里只更新当前编辑的过往日记
        """
        self.today_view.save_log()
        self.dates_view.save_log()
        self.destroy()
