"""
当天日志编辑器
"""
from tkinter import Text, TclError
import datetime
import tkinter.font as tkfont

from tinui import BasicTinUI, ExpandPanel, VerticalPanel, HorizonPanel, show_error
from tinui.theme.tinuilight import TinUILight

from control.editor import editorabel
from control.today_diary import reg_textbox, load_context, save_context
from core.files import export_month, export_month_to_file
import data


class TodayView(BasicTinUI):

    FONT_TAGS = ('fmt_font_bold', 'fmt_font_italic', 'fmt_font_bold_italic')
    TAG_UNDERLINE = 'fmt_underline'
    TAG_STRIKETHROUGH = 'fmt_strikethrough'
    TAG_HIGHLIGHT = 'fmt_highlight'

    def __init__(self, master=None, theme=TinUILight):
        super().__init__(master)
        self.ui = theme(self)
        self.init_ui()
        self.theme = data.settings['theme']
    
    def init_ui(self):
        all_bg = '#F9F9F9' if data.settings['theme'] == 'light' else '#272727'
        self.root = ExpandPanel(self, padding=(4,4,4,4), bg=all_bg, bd=17)

        self.vp = vp = VerticalPanel(self, spacing=5)
        self.root.set_child(vp)

        hp = HorizonPanel(self, spacing=5, padding=(0,2,0,0))
        vp.add_child(hp, 30)
        hp.add_child(self.ui.add_title((0,0), text=datetime.date.today().strftime('%Y-%m-%d'), anchor='w'), weight=1)
        mdf_checks = self.ui.add_checkbutton((0,0), text='富格式', command=self.mdf_state_changed, anchor='w')
        self.mdf_check = mdf_checks[-1]
        self.mdf_check_funcs = mdf_checks[-2]
        hp.add_child(self.mdf_check)
        hp.add_child(self.ui.add_button2((0,0), text='导出本月', command=self.save_this_month, anchor='w')[-1])
        self.clip_button = self.ui.add_toolbutton((0,0), icon='\uE8C8', text='', font=('{Segoe Fluent Icons}', 14), bg=all_bg, line=all_bg, command=self.save_this_month_clipboard, anchor='w')[-1]
        hp.add_child(self.clip_button)

        barbutton_text = (
            ('', '\uE8DD', self.format_bold),
            ('', '\uE8DB', self.format_italic),
            ('', '\uE8DC', self.format_underline),
            ('', '\uEDE0', self.format_strikethrough),
            ('', '\uE7E6', self.format_highlight),
        )
        self.barbutton = self.ui.add_barbutton((0,-50), content=barbutton_text, anchor='w')[-1]

        ep = ExpandPanel(self)
        vp.add_child(ep, weight=1)
        textbox = self.ui.add_textbox((0,0), scrollbar=True)
        ep.set_child(textbox[-1])
        self.textbox:Text = textbox[0]
        editorabel(self.textbox)
        self.init_text_tags()
        reg_textbox(self.textbox)
        today = load_context()

        if today.format:
            self.mdf_check_funcs.on()
        else:
            self.mdf_check_funcs.off()

        self.bind("<Configure>", self.on_resize)
    
    def on_resize(self, event):
        self.root.update_layout(event.x, event.y, event.width-1, event.height-1)
    
    def save_log(self):
        save_context(self.format)
    
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
    
    def save_this_month(self, _):
        self.save_log()
        month = datetime.date.today().strftime('%Y-%m')
        content = export_month(month)
        if not content:
            show_error(self.master, '无法导出', '本月没有日志。', theme=self.theme)
            return
        export_month_to_file(month, content)
    
    def save_this_month_clipboard(self, _):
        self.save_log()
        month = datetime.date.today().strftime('%Y-%m')
        content = export_month(month)
        if not content:
            show_error(self.master, '无法导出', '本月没有日志。', theme=self.theme)
            return
        self.clipboard_clear()
        self.itemconfig(self.clip_button+'icon', text='\uE73E')
        self.clipboard_append(content)
        self.after(1000, lambda: self.itemconfig(self.clip_button+'icon', text='\uE8C8'))

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
        self.textbox.tag_configure(self.TAG_HIGHLIGHT, background="#FFE600" if data.settings['theme'] == 'light' else "#D87700")

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
        self.textbox.edit_modified(True)

    def _toggle_simple_tag(self, tag_name):
        start, end = self._selection_range()
        if not start or not end:
            return
        has_all = self._selection_all_match(start, end, lambda idx: tag_name in self.textbox.tag_names(idx))
        if has_all:
            self.textbox.tag_remove(tag_name, start, end)
        else:
            self.textbox.tag_add(tag_name, start, end)
        self.textbox.edit_modified(True)

    def format_bold(self, _):
        self._toggle_font_flag('bold')
    
    def format_italic(self, _):
        self._toggle_font_flag('italic')
    
    def format_underline(self, _):
        self._toggle_simple_tag(self.TAG_UNDERLINE)
    
    def format_strikethrough(self, _):
        self._toggle_simple_tag(self.TAG_STRIKETHROUGH)
    
    def format_highlight(self, _):
        self._toggle_simple_tag(self.TAG_HIGHLIGHT)
