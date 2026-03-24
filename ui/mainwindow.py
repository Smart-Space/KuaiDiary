"""
KuaiDiary主窗口
"""
from tkinter import Tk

from tinui import BasicTinUI, ExpandPanel, HorizonPanel

from ui.today import TodayView
from ui.dates import DatesView
from ui.export import ExportView
from ui.setting import SettingView
import data
from core.settings import save_settings
from core.image_db import image_db

class MainWindow(Tk):

    def __init__(self):
        super().__init__()
        self.title("KuaiDiary")
        self.iconbitmap('./logo.ico')
        self.geometry("800x600")
        self.minsize(800, 600)
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.now_view:BasicTinUI = None
        
        window_action = data.settings.get('window_action', 0)
        if window_action == 1:
            self.state('zoomed')
        elif window_action == 2:
            sc_width = self.winfo_screenwidth()
            sc_height = self.winfo_screenheight()
            w, h = 800, 600
            x = (sc_width - w) // 2
            y = (sc_height - h) // 2
            self.geometry(f"{w}x{h}+{x}+{y}")
        elif window_action == 3:
            x, y, w, h = data.settings['window_action_pos']
            self.geometry(f"{w}x{h}+{x}+{y}")
        self.update()
    
    def init_ui(self):
        self.theme = data.UITheme
        self.ui_ = BasicTinUI(self)
        self.ui_.pack(fill="both", expand=True)
        self.ui = self.theme(self.ui_)

        self.root = ExpandPanel(self.ui_, padding=(5,5,5,5))
        
        hp1 = HorizonPanel(self.ui_, spacing=2)
        self.root.set_child(hp1)
        nav_content = (
            ('./assets/today.png','今日'),
            ('./assets/dates.png','往昔'),
            ('./assets/export.png','导出'),
            ('./assets/setting.png','设置')
        )
        self.nav = self.ui.add_navigation((0,0), maxwidth=100, content=nav_content, command=self.change_view)
        hp1.add_child(self.nav[-1])

        ep = ExpandPanel(self.ui_)
        self.child = self.ui_.add_ui((0,0), content=False)
        ep.set_child(self.child[-1])
        hp1.add_child(ep, weight=1)

        self.ui_.bind("<Configure>", self.on_resize)

        self.now_view = self.today_view = TodayView(self.child[0], self.theme)
        self.dates_view = DatesView(self.child[0], self.theme)
        self.export_view = ExportView(self.child[0], self.theme)
        self.setting_view = SettingView(self.child[0], self.theme)
        self.now_view.pack(fill="both", expand=True)

        self.after(100, self.today_view.load_diary)
    
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
        
        self.destroy()
