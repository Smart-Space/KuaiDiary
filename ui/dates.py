"""
以往日期选择与日志修改
"""
from tkinter import Text, TclError
import tkinter.font as tkfont

from tinui import BasicTinUI, ExpandPanel, VerticalPanel, HorizonPanel, show_error
from tinui.theme.tinuilight import TinUILight

import data
from control.dates_diary import reg_ui, load_one_diary, save_one_diary
from control.editor import editorabel
from core.files import export_month, export_month_to_file


class DatesView(BasicTinUI):

    FONT_TAGS = ('fmt_font_bold', 'fmt_font_italic', 'fmt_font_bold_italic')
    TAG_UNDERLINE = 'fmt_underline'
    TAG_STRIKETHROUGH = 'fmt_strikethrough'

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

        self.vp = vp = VerticalPanel(self, spacing=5, bg=all_bg, bd=17, padding=(4,4,4,4))
        hp.add_child(vp, weight=1)
        hp2 = HorizonPanel(self, spacing=5, padding=(0,2,0,0))
        vp.add_child(hp2, 30)
        self.title = self.ui.add_title((0, 0), text='过往日记修改', anchor='w')
        hp2.add_child(self.title, weight=1)
        mdf_checks = self.ui.add_checkbutton((0,0), text='富格式', command=self.mdf_state_changed, anchor='w')
        self.mdf_check = mdf_checks[-1]
        self.mdf_check_funcs = mdf_checks[-2]
        hp2.add_child(self.mdf_check)
        self.tog_button_text, _, _, self.tog_button_func, tog_button = self.ui.add_togglebutton((0,0), text='\uE72E', font='{Segoe Fluent Icons} 14', command=self.switch_editable, anchor='w')
        hp2.add_child(tog_button)
        hp2.add_child(self.ui.add_button2((0,0), text='导出该月', command=self.save_selected_month, anchor='w')[-1])
        self.clip_button = self.ui.add_toolbutton((0,0), icon='\uE8C8', text='', font=('{Segoe Fluent Icons}', 14), bg=all_bg, line=all_bg, command=self.save_this_month_clipboard, anchor='w')[-1]
        hp2.add_child(self.clip_button)

        barbutton_text = (
            ('', '\uE8DD', self.format_bold),
            ('', '\uE8DB', self.format_italic),
            ('', '\uE8DC', self.format_underline),
            ('', '\uEDE0', self.format_strikethrough),
        )
        self.barbutton = self.ui.add_barbutton((0,-50), content=barbutton_text, anchor='w')[-1]

        ep2 = ExpandPanel(self)
        vp.add_child(ep2, weight=1)
        textbox = self.ui.add_textbox((0,0), scrollbar=True)
        ep2.set_child(textbox[-1])
        self.textbox:Text = textbox[0]
        editorabel(self.textbox)
        self.init_text_tags()
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
                nowday = load_one_diary(diary)
                if nowday.format:
                    self.mdf_check_funcs.on()
                else:
                    self.mdf_check_funcs.off()
                self.tog_button_func.off()
    
    def save_log(self):
        if self.diary:
            save_one_diary(self.format)
    
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

    def init_text_tags(self):
        base_font = tkfont.Font(font=self.textbox.cget('font'))
        font_conf = base_font.actual()
        font_conf.update(weight='bold', slant='roman')
        self.bold_font = tkfont.Font(**font_conf)
        font_conf.update(weight='normal', slant='italic')
        self.italic_font = tkfont.Font(**font_conf)
        font_conf.update(weight='bold', slant='italic')
        self.bold_italic_font = tkfont.Font(**font_conf)
        self.textbox.tag_configure('fmt_font_bold', font=self.bold_font)
        self.textbox.tag_configure('fmt_font_italic', font=self.italic_font)
        self.textbox.tag_configure('fmt_font_bold_italic', font=self.bold_italic_font)
        self.textbox.tag_configure(self.TAG_UNDERLINE, underline=1)
        self.textbox.tag_configure(self.TAG_STRIKETHROUGH, overstrike=1)

    def _selection_range(self):
        try:
            return self.textbox.index('sel.first'), self.textbox.index('sel.last')
        except TclError:
            return None, None

    def _selection_all_match(self, start, end, checker):
        idx = start
        while self.textbox.compare(idx, '<', end):
            if not checker(idx):
                return False
            idx = self.textbox.index(f'{idx}+1c')
        return True

    def _font_flags_at(self, index):
        tags = self.textbox.tag_names(index)
        if 'fmt_font_bold_italic' in tags:
            return True, True
        if 'fmt_font_bold' in tags:
            return True, False
        if 'fmt_font_italic' in tags:
            return False, True
        return False, False

    def _apply_font_flags(self, start, end, bold, italic):
        for tag in self.FONT_TAGS:
            self.textbox.tag_remove(tag, start, end)
        if bold and italic:
            self.textbox.tag_add('fmt_font_bold_italic', start, end)
        elif bold:
            self.textbox.tag_add('fmt_font_bold', start, end)
        elif italic:
            self.textbox.tag_add('fmt_font_italic', start, end)

    def _toggle_font_flag(self, flag):
        start, end = self._selection_range()
        if not start or not end:
            return
        should_enable = not self._selection_all_match(
            start,
            end,
            lambda idx: self._font_flags_at(idx)[0] if flag == 'bold' else self._font_flags_at(idx)[1]
        )
        idx = start
        while self.textbox.compare(idx, '<', end):
            next_idx = self.textbox.index(f'{idx}+1c')
            bold, italic = self._font_flags_at(idx)
            if flag == 'bold':
                bold = should_enable
            else:
                italic = should_enable
            self._apply_font_flags(idx, next_idx, bold, italic)
            idx = next_idx

    def _toggle_simple_tag(self, tag_name):
        start, end = self._selection_range()
        if not start or not end:
            return
        has_all = self._selection_all_match(start, end, lambda idx: tag_name in self.textbox.tag_names(idx))
        if has_all:
            self.textbox.tag_remove(tag_name, start, end)
        else:
            self.textbox.tag_add(tag_name, start, end)

    def format_bold(self, _):
        self._toggle_font_flag('bold')
        self.textbox.edit_modified(True)

    def format_italic(self, _):
        self._toggle_font_flag('italic')
        self.textbox.edit_modified(True)

    def format_underline(self, _):
        self._toggle_simple_tag(self.TAG_UNDERLINE)
        self.textbox.edit_modified(True)

    def format_strikethrough(self, _):
        self._toggle_simple_tag(self.TAG_STRIKETHROUGH)
        self.textbox.edit_modified(True)
    
    first_mdf_change = True
    def mdf_state_changed(self, tag):
        self.format = tag
        if tag:
            self.vp.add_child(self.barbutton, 30, index=1)
        else:
            if self.first_mdf_change:
                self.first_mdf_change = False
                return
            self.vp.pop_child(1)
            self._BasicTinUI__auto_anchor(self.barbutton, (0,-50))
        self.event_generate("<Configure>", x=0, y=0, width=self.winfo_width(), height=self.winfo_height())
