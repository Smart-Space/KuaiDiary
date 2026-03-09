"""
以往日期选择与日志修改
"""
from tkinter import Text, TclError
import tkinter.font as tkfont
from webbrowser import open as open_url

from tinui import BasicTinUI, ExpandPanel, VerticalPanel, HorizonPanel, show_error, ask_string
from tinui.theme.tinuilight import TinUILight

import data
from control.dates_diary import reg_ui, load_one_diary, save_one_diary
from control.editor import editorabel
from core.files import export_month, export_month_to_file


class DatesView(BasicTinUI):

    FONT_TAGS = ('fmt_font_bold', 'fmt_font_italic', 'fmt_font_bold_italic')
    TAG_UNDERLINE = 'fmt_underline'
    TAG_STRIKETHROUGH = 'fmt_strikethrough'
    TAG_HIGHLIGHT = 'fmt_highlight'
    TAG_QUOTE = 'fmt_quote'
    TAG_ALIGN_LEFT = 'fmt_align_left'
    TAG_ALIGN_CENTER = 'fmt_align_center'
    TAG_ALIGN_RIGHT = 'fmt_align_right'
    ALIGN_TAGS = (TAG_ALIGN_LEFT, TAG_ALIGN_CENTER, TAG_ALIGN_RIGHT)
    TAG_LINKPREFIX = 'fmt_link|'

    def __init__(self, master=None, theme=TinUILight):
        super().__init__(master)
        self.diary:str = None
        self.ui = theme(self)
        self.theme = data.settings['theme']
        if self.theme == 'light':
            self.format_colors = {
                'markbg': '#FFE600',
                'quotefg': '#888888',
                'linkfg': '#003e92'
            }
        else:
            self.format_colors = {
                'markbg': '#D87700',
                'quotefg': '#BBBBBB',
                'linkfg': '#99ebff'
            }
        self.format = False
        self.init_data()
        self.init_ui()
    
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
            ('', '\uE7E6', self.format_highlight),
            ('', '\uE71B', self.format_link),
            '',
            ('', '\uE9AA', self.format_quote),
            ('', '\uE8E4', self.format_align_left),
            ('', '\uE8E3', self.format_align_center),
            ('', '\uE8E2', self.format_align_right),
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
        self.textbox_kr_quote_id = None
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
                    save_one_diary(self.format)
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
        self.textbox.tag_configure(self.TAG_HIGHLIGHT, background=self.format_colors['markbg'])
        self.textbox.tag_configure(self.TAG_QUOTE, lmargin1=20, lmargin2=20, foreground=self.format_colors['quotefg'])
        self.textbox.tag_configure(self.TAG_ALIGN_LEFT, justify='left')
        self.textbox.tag_configure(self.TAG_ALIGN_CENTER, justify='center')
        self.textbox.tag_configure(self.TAG_ALIGN_RIGHT, justify='right')
        self.textbox.tag_raise('sel')

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
        if self.textbox.cget('state') == 'disabled':
            return
        self._toggle_font_flag('bold')

    def format_italic(self, _):
        if self.textbox.cget('state') == 'disabled':
            return "break"
        self._toggle_font_flag('italic')
        return "break"

    def format_underline(self, _):
        if self.textbox.cget('state') == 'disabled':
            return
        self._toggle_simple_tag(self.TAG_UNDERLINE)

    def format_strikethrough(self, _):
        if self.textbox.cget('state') == 'disabled':
            return
        self._toggle_simple_tag(self.TAG_STRIKETHROUGH)
    
    def format_highlight(self, _):
        if self.textbox.cget('state') == 'disabled':
            return
        self._toggle_simple_tag(self.TAG_HIGHLIGHT)
    
    def _line_range(self, index):
        line_start = self.textbox.index(f'{index} linestart')
        line_end = self.textbox.index(f'{index} lineend +1c')
        return line_start, line_end

    def _line_has_quote(self, index):
        # 用 lineend 位置判断该行是否是 quote 行（空行时也可判断）
        probe = self.textbox.index(f'{index} lineend')
        return self.TAG_QUOTE in self.textbox.tag_names(probe)

    def _sync_quote_for_current_line(self, _):
        insert = self.textbox.index('insert')
        if not insert.endswith('.1'):
            # 不是行首，不处理
            return
        line_start, line_end = self._line_range(insert)
        if self._line_has_quote(insert):
            self.textbox.tag_add(self.TAG_QUOTE, line_start, line_end)
        align_tag = self._line_align_tag(insert)
        if align_tag:
            for tag in self.ALIGN_TAGS:
                self.textbox.tag_remove(tag, line_start, line_end)
            self.textbox.tag_add(align_tag, line_start, line_end)

    def _line_align_tag(self, index):
        probe = self.textbox.index(f'{index} lineend')
        tags = self.textbox.tag_names(probe)
        for tag in self.ALIGN_TAGS:
            if tag in tags:
                return tag
        return None

    def _format_align(self, target_tag):
        start, end = self._selection_range()
        if not start:
            start = self.textbox.index('insert')
            line_start = self.textbox.index(f'{start} linestart')
            line_end = self.textbox.index(f'{start} lineend +1c')
        else:
            line_start = self.textbox.index(f'{start} linestart')
            line_end = self.textbox.index(f'{end} lineend +1c')
        if target_tag in self.textbox.tag_names(start):
            self.textbox.tag_remove(target_tag, line_start, line_end)
        else:
            for tag in self.ALIGN_TAGS:
                self.textbox.tag_remove(tag, line_start, line_end)
            self.textbox.tag_add(target_tag, line_start, line_end)
        self.textbox.edit_modified(True)
    
    def format_quote(self, _):
        if self.textbox.cget('state') == 'disabled':
            return
        start, end = self._selection_range()
        if not start:
            start = self.textbox.index('insert')
            line_start = self.textbox.index(f'{start} linestart')
            line_end = self.textbox.index(f'{start} lineend +1c')
        else:
            line_start = self.textbox.index(f'{start} linestart')
            line_end = self.textbox.index(f'{end} lineend +1c')
        if self.TAG_QUOTE in self.textbox.tag_names(start):
            self.textbox.tag_remove(self.TAG_QUOTE, line_start, line_end)
        else:
            self.textbox.tag_add(self.TAG_QUOTE, line_start, line_end)
        self.textbox.edit_modified(True)

    def format_align_left(self, _):
        if self.textbox.cget('state') == 'disabled':
            return
        self._format_align(self.TAG_ALIGN_LEFT)

    def format_align_center(self, _):
        if self.textbox.cget('state') == 'disabled':
            return
        self._format_align(self.TAG_ALIGN_CENTER)

    def format_align_right(self, _):
        if self.textbox.cget('state') == 'disabled':
            return
        self._format_align(self.TAG_ALIGN_RIGHT)
    
    def _link_tag_config(self, tag_name, url):
        self.textbox.tag_configure(tag_name, foreground=self.format_colors['linkfg'], underline=1)
        self.textbox.tag_bind(tag_name, '<Control-Button-1>', lambda _: open_url(url))

    def format_link(self, _):
        if self.textbox.cget('state') == 'disabled':
            return
        start, end = self._selection_range()
        if not start or not end:
            return
        context = self.textbox.get(start, end)
        original_url = ''
        for tag in self.textbox.tag_names(start):
            if tag.startswith(self.TAG_LINKPREFIX):
                original_url = tag[len(self.TAG_LINKPREFIX):]
                break
        url = ask_string(self.master, '输入链接', f'请输入 {context} 的链接地址：', text=original_url, theme=self.theme)
        if url is None:
            return
        elif url == '':
            for tag in self.textbox.tag_names(start):
                if tag.startswith(self.TAG_LINKPREFIX):
                    self.textbox.tag_remove(tag, start, end)
                    self.textbox.edit_modified(True)
                    return
            return
        tag_name = self.TAG_LINKPREFIX + url
        self._link_tag_config(tag_name, url)
        self._toggle_simple_tag(tag_name)
    
    def mdf_state_changed(self, tag):
        if self.format == tag:
            return
        self.format = tag
        if tag:
            self.vp.add_child(self.barbutton, 30, index=1)
            self.textbox_kr_quote_id = self.textbox.bind('<KeyRelease>', self._sync_quote_for_current_line, True)
        else:
            self.vp.pop_child(1)
            self._BasicTinUI__auto_anchor(self.barbutton, (0,-50))
            self.textbox.unbind('<KeyRelease>', self.textbox_kr_quote_id)
        self.event_generate("<Configure>", x=0, y=0, width=self.winfo_width(), height=self.winfo_height())
