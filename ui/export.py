"""
自定义导出
"""
from tkinter import Text
from tkinter.filedialog import askdirectory
import datetime

from tinui import BasicTinUI, VerticalPanel, HorizonPanel, ExpandPanel, show_warning, show_error, show_info
from tinui.theme.tinuilight import TinUILight
from tinuipicker.datepicker import TinUIDatePicker, pickerdark, pickerlight

import data
from core.files import exist_diary, export_from_to


class ExportView(BasicTinUI):

    def __init__(self, master=None, theme=TinUILight):
        super().__init__(master)
        self.start = None
        self.end = None
        self.temp_start = datetime.date.today()
        self.temp_end = datetime.date.today()
        self.sep_year = False
        self.sep_month = False
        self.diarys:list[datetime.date] = [] # 存在的日期对象
        self.ui = theme(self)
        self.init_ui()
        self.theme = data.settings['theme']
    
    def init_ui(self):
        all_bg = '#F9F9F9' if data.settings['theme'] == 'light' else '#272727'
        picker_colors = pickerlight if data.settings['theme'] == 'light' else pickerdark
        self.root = ExpandPanel(self)

        vp = VerticalPanel(self, spacing=5, bg=all_bg, bd=17, padding=(4,4,4,4))
        self.root.set_child(vp)

        hp1 = HorizonPanel(self, spacing=5)
        vp.add_child(hp1, 60)
        hp1.add_child(self.ui.add_back((0,0)), weight=1)
        hp1.add_child(self.ui.add_paragraph((0,0), text='开始日期', anchor='center'))
        self.start_datepicker = TinUIDatePicker(self, (0,0), font=('Segoe UI', 12), now=self.temp_start, command=self.set_start_date, anchor='w', **picker_colors)
        hp1.add_child(self.start_datepicker.uid)
        hp1.add_child(self.ui.add_back((0,0)), 20)
        hp1.add_child(self.ui.add_paragraph((0,0),text='结束年份', anchor='center'))
        self.end_datepicker = TinUIDatePicker(self, (0,0), font=('Segoe UI', 12), now=self.temp_end, command=self.set_end_date, anchor='w', **picker_colors)
        hp1.add_child(self.end_datepicker.uid)
        hp1.add_child(self.ui.add_back((0,0)), weight=1)

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
    
    def set_start_date(self, date):
        self.temp_start = datetime.date.fromisoformat(date)
    
    def set_end_date(self, date):
        self.temp_end = datetime.date.fromisoformat(date)
    
    def set_sep_year(self, value):
        self.start = None # 重置开始日期
        self.sep_year = value
    
    def set_sep_month(self, value):
        self.start = None # 重置开始日期
        self.sep_month = value
    
    def _log(self, text):
        self.textbox.insert('end', text + '\n')
    
    def analyze(self, _):
        if data.months.__len__() == 0:
            show_warning(self, '无日记内容', '空空如也，快写下你的第一篇日记吧~', theme=self.theme)
            return

        start_date = self.temp_start
        end_date = self.temp_end
        if start_date > end_date:
            show_error(self, '日期错误', '开始日期不能大于结束日期', theme=self.theme)
            return
        elif start_date == end_date:
            show_warning(self, '日期错误', '开始日期和结束日期相同', theme=self.theme)
            return
        if self.start == start_date and self.end == end_date:
            # 日期未修改，无需分析
            return True
        self.start = start_date
        self.end = end_date
        self.textbox.config(state='normal')
        self.textbox.delete('1.0', 'end')
        self._log('开始日期：' + str(self.start))
        self._log('结束日期：' + str(self.end))
        self._log('分年导出：' + str(self.sep_year))
        self._log('分月内容：' + str(self.sep_month))
        
        current_date = start_date
        cnt = 0
        self.diarys.clear()
        last_year_month_str = next(reversed(data.months.items()))[0].split('-')
        last_year_month = datetime.date(int(last_year_month_str[0]), int(last_year_month_str[1]), 1)
        if last_year_month > start_date:
            current_date = last_year_month
        least_year_month_str = next(iter(data.months.items()))[0].split('-')
        least_year_month = datetime.date(int(least_year_month_str[0]), int(least_year_month_str[1]), 1) + datetime.timedelta(days=30)
        if least_year_month < end_date:
            end_date = least_year_month
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
            show_info(self, '提示', '没有可导出的内容', theme=self.theme)
            return
        output_dir = askdirectory(title='选择导出目录')
        if not output_dir:
            return
        self.textbox.config(state='normal')
        self._log('开始导出')
        export_from_to(self.diarys, output_dir, self.sep_year, self.sep_month)
        self._log('导出完成')
        self.textbox.config(state='disabled')
