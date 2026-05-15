"""
KuaiDiary主窗口
"""
from datetime import date
from tkinter import Tk

from tinui import BasicTinUI, ExpandPanel, HorizonPanel

from ui.today import TodayView
from ui.dates import DatesView
from ui.export import ExportView
from ui.setting import SettingView
from ui.search import SearchView
import data
from core.settings import save_settings
from core.image_db import image_db
from control.search import search_engine

class MainWindow(Tk):

    def __init__(self):
        super().__init__()
        self.title("KuaiDiary")
        self.iconbitmap('./logo.ico')
        width = int(800 * data.factory)
        height = int(600 * data.factory)
        self.geometry(f"{width}x{height}")
        self.minsize(width, height)
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.now_view:BasicTinUI = None

        self.theme = data.UITheme
        self.ui_ = BasicTinUI(self)
        self.ui_.set_scale(data.factory)
        self.ui_.pack(fill="both", expand=True)
        self.ui = self.theme(self.ui_)
        
        window_action = data.settings.get('window_action', 0)
        if window_action == 1:
            self.state('zoomed')
        elif window_action == 2:
            sc_width = self.winfo_screenwidth()
            sc_height = self.winfo_screenheight()
            w, h = int(800 * data.factory), int(600 * data.factory)
            x = (sc_width - w) // 2
            y = (sc_height - h) // 2
            self.geometry(f"{w}x{h}+{x}+{y}")
        elif window_action == 3:
            x, y, w, h = data.settings['window_action_pos']
            self.geometry(f"{w}x{h}+{x}+{y}")
        self.update()

        self.ui_.add_image((self.ui_.winfo_width()//2, self.ui_.winfo_height()//2), imgfile='./assets/logo-small.png', anchor='center')
        self.ui_.update_idletasks()

        self.bind("<<OpenDiary>>", self.open_diary)
    
    def init_ui(self):
        self.root = ExpandPanel(self.ui_, padding=(5,5,5,5))
        
        hp1 = HorizonPanel(self.ui_, spacing=2)
        self.root.set_child(hp1)
        nav_content = (
            ('\uE929','今日'),
            ('\uE787','往昔'),
            ('\uEDE1','导出'),
            ('\uE721','搜索'),
            ('\uE713','设置')
        )
        self.nav = self.ui.add_navigation((0,0), maxwidth=100*data.factory, content=nav_content, command=self.change_view)
        hp1.add_child(self.nav[-1])

        ep = ExpandPanel(self.ui_)
        self.child = self.ui_.add_ui((0,0), content=False)
        ep.set_child(self.child[-1])
        hp1.add_child(ep, weight=1)

        self.ui_.bind("<Configure>", self.on_resize)

        self.now_view = self.today_view = TodayView(self.child[0], self.theme)
        self.dates_view = DatesView(self.child[0], self.theme)
        self.export_view = ExportView(self.child[0], self.theme)
        self.search_view = SearchView(self.child[0], self.theme)
        self.setting_view = SettingView(self.child[0], self.theme)
        self.now_view.pack(fill="both", expand=True)

        self.after(100, self.today_view.load_diary)

        self.ui_.event_generate("<Configure>", x=0, y=0, width=self.ui_.winfo_width(), height=self.ui_.winfo_height())
    
    def open_diary(self, _):
        diary_date = data.req_open_dairy
        if date.today().strftime("%Y-%m-%d") == f"{diary_date[0]}-{diary_date[1]}":
            self.nav[-2].navigate(0) # 今日
        else:
            self.nav[-2].navigate(1) # 往昔
            self.dates_view.select_to(diary_date[0], diary_date[1])
    
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
        elif tag == '导出':
            self.now_view.pack_forget()
            self.now_view = self.export_view
        elif tag == '搜索':
            self.now_view.pack_forget()
            self.now_view = self.search_view
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
        
        # 记住位置
        if data.settings['window_action'] == 3:
            data.settings['window_action_pos'] = (self.winfo_rootx(), self.winfo_rooty(), self.winfo_width(), self.winfo_height())
            save_settings()

        image_db.close_db()

        search_engine._save_index() # 保存搜索索引
        
        self.destroy()
