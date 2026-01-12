"""
自定义导出
"""
from tkinter import Entry, Text
from tkinter.filedialog import askdirectory
import datetime

from tinui import BasicTinUI, VerticalPanel, HorizonPanel, ExpandPanel, show_warning, show_error, show_info
from tinui.theme.tinuilight import TinUILight

import data
from core.files import exist_diary, export_from_to


class ExportView(BasicTinUI):

    def __init__(self, master=None, theme=TinUILight):
        super().__init__(master)
        y, m, d = datetime.datetime.now().strftime('%Y-%m-%d').split('-')
        self.start = [y, m, d]
        self.end = [y, m, d]
        self.sep_year = False
        self.sep_month = False
        self.diarys:list[datetime.date] = [] # 存在的日期对象
        self.ui = theme(self)
        self.init_ui()
        self.theme = data.settings['theme']
    
    def init_ui(self):
        all_bg = '#F9F9F9' if data.settings['theme'] == 'light' else '#272727'
        self.root = ExpandPanel(self)

        vp = VerticalPanel(self, spacing=5, bg=all_bg, bd=17, padding=(4,4,4,4))
        self.root.set_child(vp)

        hp1 = HorizonPanel(self, spacing=5)
        vp.add_child(hp1, 60)
        hp1.add_child(self.ui.add_back((0,0)), weight=1)
        hp1.add_child(self.ui.add_paragraph((0,0), text='开始年份', anchor='center'))
        sy_entry = self.ui.add_entry((0,0), width=60, anchor='center')
        hp1.add_child(sy_entry[-1], 100)
        self.sy_entry:Entry = sy_entry[0]
        self.sy_entry.insert(0, self.start[0])
        hp1.add_child(self.ui.add_paragraph((0,0), text='月份', anchor='center'))
        sm_entry = self.ui.add_entry((0,0), width=60, anchor='center')
        hp1.add_child(sm_entry[-1], 100)
        self.sm_entry:Entry = sm_entry[0]
        self.sm_entry.insert(0, self.start[1])
        hp1.add_child(self.ui.add_paragraph((0,0), text='日期', anchor='center'))
        sd_entry = self.ui.add_entry((0,0), width=60, anchor='w')
        hp1.add_child(sd_entry[-1], 100)
        self.sd_entry:Entry = sd_entry[0]
        self.sd_entry.insert(0, self.start[2])
        hp1.add_child(self.ui.add_back((0,0)), weight=1)

        hp2 = HorizonPanel(self, spacing=5)
        vp.add_child(hp2, 60)
        hp2.add_child(self.ui.add_back((0,0)), weight=1)
        hp2.add_child(self.ui.add_paragraph((0,0),text='结束年份', anchor='center'))
        ey_entry = self.ui.add_entry((0,0), width=60, anchor='center')
        hp2.add_child(ey_entry[-1], 100)
        self.ey_entry = ey_entry[0]
        self.ey_entry.insert(0, self.end[0])
        hp2.add_child(self.ui.add_paragraph((0,0), text='月份', anchor='center'))
        em_entry = self.ui.add_entry((0,0), width=60, anchor='center')
        hp2.add_child(em_entry[-1], 100)
        self.em_entry = em_entry[0]
        self.em_entry.insert(0, self.end[1])
        hp2.add_child(self.ui.add_paragraph((0,0), text='日期', anchor='center'))
        ed_entry = self.ui.add_entry((0,0), width=60, anchor='w')
        hp2.add_child(ed_entry[-1], 100)
        self.ed_entry = ed_entry[0]
        self.ed_entry.insert(0, self.end[2])
        hp2.add_child(self.ui.add_back((0,0)), weight=1)

        hp3 = HorizonPanel(self, spacing=5)
        vp.add_child(hp3, 60)
        hp3.add_child(self.ui.add_back((0,0)), weight=1)
        hp3.add_child(self.ui.add_checkbutton((0,0), text='分年导出', command=self.set_sep_year, anchor='e')[-1], 100)
        hp3.add_child(self.ui.add_checkbutton((0,0), text='分月内容', command=self.set_sep_month, anchor='center')[-1], 100)
        hp3.add_child(self.ui.add_button2((0,0), text='仅分析', command=self.analyze, anchor='center')[-1], 70)
        hp3.add_child(self.ui.add_button2((0,0), text='分析并导出', command=self.export, anchor='w')[-1], 100)
        hp3.add_child(self.ui.add_back((0,0)), weight=1)

        ep = ExpandPanel(self)
        vp.add_child(ep, weight=1)
        textbox = self.ui.add_textbox((0,0), scrollbar=True)
        ep.set_child(textbox[-1])
        self.textbox:Text = textbox[0]
        self.textbox.config(state='disabled')

        self.bind("<Configure>", self.on_resize)
    
    def on_resize(self, event):
        self.root.update_layout(event.x, event.y, event.width, event.height)
    
    def set_sep_year(self, value):
        self.start = None # 重置开始日期
        self.sep_year = value
    
    def set_sep_month(self, value):
        self.start = None # 重置开始日期
        self.sep_month = value
    
    def _log(self, text):
        self.textbox.insert('end', text + '\n')
    
    def analyze(self, _):
        start = [self.sy_entry.get(), self.sm_entry.get(), self.sd_entry.get()]
        end = [self.ey_entry.get(), self.em_entry.get(), self.ed_entry.get()]
        if not all(start) or not all(end):
            show_warning(self, '日期格式错误', '请输入完整的开始日期和结束日期')
            return
        if not all(map(lambda x: x.isdigit(), start)) or not all(map(lambda x: x.isdigit(), end)):
            show_error(self, '日期格式错误', '请输入数字的年份、月份、日期')
            return
        try:
            start_date = datetime.date(*map(int, start))
        except ValueError:
            show_error(self, '日期格式错误', '请输入正确的开始日期')
            return
        try:
            end_date = datetime.date(*map(int, end))
        except ValueError:
            show_error(self, '日期格式错误', '请输入正确的结束日期')
            return
        if start_date > end_date:
            show_error(self, '日期错误', '开始日期不能大于结束日期')
            return
        elif start_date == end_date:
            show_warning(self, '日期错误', '开始日期和结束日期相同')
            return
        if self.start == start and self.end == end:
            # 日期未修改，无需分析
            return True
        self.start = start
        self.end = end
        self.textbox.config(state='normal')
        self.textbox.delete('1.0', 'end')
        self._log('开始日期：' + '-'.join(self.start))
        self._log('结束日期：' + '-'.join(self.end))
        self._log('分年导出：' + str(self.sep_year))
        self._log('分月内容：' + str(self.sep_month))
        current_date = start_date
        cnt = 0
        self.diarys.clear()
        while current_date <= end_date:
            if exist_diary(current_date):
                self.diarys.append(current_date)
                cnt += 1
            current_date += datetime.timedelta(days=1)
        self._log('共导出日记：' + str(cnt))
        self.textbox.config(state='disabled')
        return True
    
    def export(self, _):
        if not self.analyze(None):
            return
        if not self.diarys or len(self.diarys) == 0:
            show_info(self, '提示', '没有可导出的内容')
            return
        output_dir = askdirectory(title='选择导出目录')
        if not output_dir:
            return
        self.textbox.config(state='normal')
        self._log('开始导出')
        export_from_to(self.diarys, output_dir, self.sep_year, self.sep_month)
        self._log('导出完成')
        self.textbox.config(state='disabled')
