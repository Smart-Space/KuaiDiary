"""
当天日志编辑器
"""
from tkinter import Text
import datetime

from tinui import BasicTinUI, ExpandPanel, VerticalPanel, HorizonPanel, show_error
from tinui.theme.tinuilight import TinUILight
# from tinui.theme.tinuidark import TinUIDark

from control.editor import editorabel
from control.today_diary import reg_textbox, load_context, save_context
from core.files import export_month, export_month_to_file


class TodayView(BasicTinUI):

    def __init__(self, master=None, theme=TinUILight):
        super().__init__(master)
        self.ui = theme(self)
        self.init_ui()
    
    def init_ui(self):
        self.root = ExpandPanel(self, padding=(4,4,4,4), bg='#F9F9F9', bd=17)

        vp = VerticalPanel(self, spacing=5)
        self.root.set_child(vp)

        hp = HorizonPanel(self, spacing=5, padding=(0,2,0,0))
        vp.add_child(hp, 30)
        hp.add_child(self.ui.add_title((0,0), text=datetime.date.today().strftime('%Y-%m-%d'), anchor='w'), weight=1)
        hp.add_child(self.ui.add_button2((0,0), text='导出本月', command=self.save_this_month, anchor='w')[-1])
        self.clip_button = self.ui.add_toolbutton((0,0), icon='\uE8C8', text='', font=('{Segoe Fluent Icons}', 14), bg='#F9F9F9', line='#F9F9F9', command=self.save_this_month_clipboard, anchor='w')[-1]
        hp.add_child(self.clip_button)

        ep = ExpandPanel(self)
        vp.add_child(ep, weight=1)
        textbox = self.ui.add_textbox((0,0), scrollbar=True)
        ep.set_child(textbox[-1])
        self.textbox:Text = textbox[0]
        editorabel(self.textbox)
        reg_textbox(self.textbox)
        load_context()

        self.bind("<Configure>", self.on_resize)
    
    def on_resize(self, event):
        self.root.update_layout(event.x, event.y, event.width-1, event.height-1)
    
    def save_log(self):
        save_context()
    
    def save_this_month(self, _):
        self.save_log()
        month = datetime.date.today().strftime('%Y-%m')
        content = export_month(month)
        if not content:
            show_error(self.master, '无法导出', '本月没有日志。')
            return
        export_month_to_file(month, content)
    
    def save_this_month_clipboard(self, _):
        self.save_log()
        month = datetime.date.today().strftime('%Y-%m')
        content = export_month(month)
        if not content:
            show_error(self.master, '无法导出', '本月没有日志。')
            return
        self.clipboard_clear()
        self.itemconfig(self.clip_button+'icon', text='\uE73E')
        self.clipboard_append(content)
        self.after(1000, lambda: self.itemconfig(self.clip_button+'icon', text='\uE8C8'))
