"""
以往日期选择与日志修改
"""
from tkinter import Text

from tinui import BasicTinUI, ExpandPanel, VerticalPanel, HorizonPanel
from tinui.theme.tinuilight import TinUILight
from tinui.theme.tinuidark import TinUIDark

import data
from control.dates_diary import reg_ui, load_one_diary, save_one_diary
from control.editor import editorabel


class DatesView(BasicTinUI):

    def __init__(self, master=None, theme=TinUILight):
        super().__init__(master)
        self.diary:str = None
        self.ui = theme(self)
        self.init_data()
        self.init_ui()
    
    def init_data(self): # 获取以往日记信息
        if not data.months:
            self.data = ('尚无日记~',)
        else:
            self.data = []
            for k, v in data.months.items():
                self.data.append((k, v))
    
    def init_ui(self):
        self.root = ExpandPanel(self)

        hp = HorizonPanel(self, spacing=5)
        self.root.set_child(hp)

        ep = ExpandPanel(self)
        hp.add_child(ep, 120)
        treev = self.ui.add_treeview((0,0), content=self.data, command=self.on_select)
        ep.set_child(treev[-1])
        self.tvitems = treev[0]
        self.tv:BasicTinUI = treev[-2]

        vp = VerticalPanel(self, spacing=10, bg='#F9F9F9', bd=17, padding=(4,4,4,4))
        hp.add_child(vp, weight=1)
        hp2 = HorizonPanel(self, spacing=5)
        vp.add_child(hp2, 30)
        self.title = self.ui.add_title((0, 0), text='过往日记修改', anchor='w')
        hp2.add_child(self.title, weight=1)
        # hp2.add_child(self.ui.add_button2((0,0), text='保存', anchor='w')[-1], 50)

        ep2 = ExpandPanel(self)
        vp.add_child(ep2, weight=1)
        textbox = self.ui.add_textbox((0,0), scrollbar=True)
        ep2.set_child(textbox[-1])
        self.textbox:Text = textbox[0]
        editorabel(self.textbox)
        reg_ui(self.textbox)

        self.bind("<Configure>", self.on_resize)

    def on_resize(self, event):
        self.root.update_layout(event.x, event.y, event.width-1, event.height-1)
    
    def on_select(self, d):
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
    
    def save_log(self):
        if self.diary:
            save_one_diary()