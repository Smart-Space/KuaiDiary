"""
以往日期选择与日志修改
"""
from tkinter import Text

from tinui import BasicTinUI, ExpandPanel, VerticalPanel, HorizonPanel, show_error
from tinui.theme.tinuilight import TinUILight

import data
from control.dates_diary import reg_ui, load_one_diary, save_one_diary
from control.editor import editorabel
from core.files import export_month, export_month_to_file


class DatesView(BasicTinUI):

    def __init__(self, master=None, theme=TinUILight):
        super().__init__(master)
        self.diary:str = None
        self.ui = theme(self)
        self.init_data()
        self.init_ui()
        self.theme = data.settings['theme']
    
    def init_data(self): # 获取以往日记信息
        if not data.months:
            self.data = ('尚无日记~',)
        else:
            self.data = []
            for k, v in data.months.items():
                if v:
                    self.data.append((k, v))
                else:
                    self.data.append(k)
    
    def init_ui(self):
        all_bg = '#F9F9F9' if data.settings['theme'] == 'light' else '#272727'
        self.root = ExpandPanel(self)

        hp = HorizonPanel(self, spacing=5)
        self.root.set_child(hp)

        ep = ExpandPanel(self)
        hp.add_child(ep, 120)
        treev = self.ui.add_treeview((0,0), content=self.data, command=self.on_select)
        ep.set_child(treev[-1])
        self.tvitems = treev[0]
        self.tv:BasicTinUI = treev[2]
        tvfuncs = treev[-2]
        tvfuncs.close_all()

        vp = VerticalPanel(self, spacing=5, bg=all_bg, bd=17, padding=(4,4,4,4))
        hp.add_child(vp, weight=1)
        hp2 = HorizonPanel(self, spacing=5, padding=(0,2,0,0))
        vp.add_child(hp2, 30)
        self.title = self.ui.add_title((0, 0), text='过往日记修改', anchor='w')
        hp2.add_child(self.title, weight=1)
        self.tog_button_text, _, _, self.tog_button_func, tog_button = self.ui.add_togglebutton((0,0), text='\uE72E', font='{Segoe Fluent Icons} 14', command=self.switch_editable, anchor='w')
        hp2.add_child(tog_button)
        hp2.add_child(self.ui.add_button2((0,0), text='导出该月', command=self.save_selected_month, anchor='w')[-1])
        self.clip_button = self.ui.add_toolbutton((0,0), icon='\uE8C8', text='', font=('{Segoe Fluent Icons}', 14), bg=all_bg, line=all_bg, command=self.save_this_month_clipboard, anchor='w')[-1]
        hp2.add_child(self.clip_button)

        ep2 = ExpandPanel(self)
        vp.add_child(ep2, weight=1)
        textbox = self.ui.add_textbox((0,0), scrollbar=True)
        ep2.set_child(textbox[-1])
        self.textbox:Text = textbox[0]
        editorabel(self.textbox)
        reg_ui(self.textbox)

        self.bind("<Configure>", self.on_resize)
        self.tog_button_func.off()

    def on_resize(self, event):
        self.root.update_layout(event.x, event.y, event.width-1, event.height-1)
    
    def on_select(self, d):
        self.tree_val = d
        if len(d) == 2:
            monthi, datei = d
            month = self.tv.itemcget(self.tvitems[monthi][0], 'text')
            date = self.tv.itemcget(self.tvitems[datei][0], 'text')
            diary = f"{month}-{date}"
            if diary != self.diary:
                if self.diary:
                    save_one_diary()
                self.diary = diary
                self.itemconfig(self.title, text=self.diary)
                load_one_diary(diary)
                self.tog_button_func.off()
    
    def save_log(self):
        if self.diary:
            save_one_diary()
    
    def save_selected_month(self, _):
        self.save_log()
        if self.diary:
            month = '-'.join(self.diary.split('-')[:2])
            content = export_month(month)
            if not content:
                show_error(self.master, '无法导出', '该月没有日志。', theme=self.theme)
                return
            export_month_to_file(month, content)
        else:
            show_error(self.master, "无法导出", "请先选择日期，详见左上方年-月-日标题。", theme=self.theme)
    
    def save_this_month_clipboard(self, _):
        self.save_log()
        if self.diary:
            month = '-'.join(self.diary.split('-')[:2])
            content = export_month(month)
            if not content:
                show_error(self.master, '无法导出', '该月没有日志。', theme=self.theme)
                return
            self.clipboard_clear()
            self.itemconfig(self.clip_button+'icon', text='\uE73E')
            self.clipboard_append(content)
            self.after(1000, lambda: self.itemconfig(self.clip_button+'icon', text='\uE8C8'))
        else:
            show_error(self.master, "无法导出", "请先选择日期，详见左上方年-月-日标题。", theme=self.theme)
    
    def switch_editable(self, state):
        if not self.diary:
            return
        if state:
            self.itemconfig(self.tog_button_text, text='\uE785')
            self.textbox.config(state='normal')
        else:
            self.itemconfig(self.tog_button_text, text='\uE72E')
            self.textbox.config(state='disabled')
