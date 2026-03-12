"""
编辑器化
"""
from tkinter import Text, TclError
import tkinter.font as tkfont
from webbrowser import open as open_url

import data
from tinui import ask_string, show_question

def editorabel(text:Text):
    if data.settings['theme'] == 'light':
        ibg = '#000000'
    else:
        ibg = '#E0E0E0'
    font = tkfont.Font(font=text.cget("font"))
    font_size = font.measure("    ")
    text.config(tabs=font_size, undo=True, maxundo=100, autoseparators=False, wrap="char", spacing1=4, spacing3=4,
                insertbackground=ibg, insertwidth=1)
    text.bind("<Control-z>", __editor_undo)
    text.bind("<Control-y>", __editor_redo)
    text.bind("<Key>", __editor_input)
    text.bind("<Control-b>", text.master.format_bold)
    text.bind("<Control-i>", text.master.format_italic)
    text.bind("<Control-u>", text.master.format_underline)

def __editor_undo(e):
    try:
        e.widget.edit_undo()
    except:
        pass
    return "break"

def __editor_redo(e):
    try:
        e.widget.edit_redo()
    except:
        pass
    return "break"

last_keycode = None
sep_keycodes = (229, 32, 13)
def __editor_input(e):
    global last_keycode
    if e.keycode in sep_keycodes and e.keycode != last_keycode:
        e.widget.edit_separator()
    last_keycode = e.keycode


class RichTextEditor:
    """富文本编辑器"""

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
    TAG_HIGHLIGHTPREFIX = 'fmt_highlight|'

    @staticmethod
    def get_format_colors(theme):
        """获取格式颜色配置"""
        if theme == 'light':
            return {
                'markbg': '#FFE600',
                'quotefg': '#888888',
                'linkfg': '#003e92'
            }
        else:
            return {
                'markbg': '#D87700',
                'quotefg': '#BBBBBB',
                'linkfg': '#99ebff'
            }

    def __init__(self, textbox, theme, format_colors, master=None):
        """初始化富文本编辑器"""
        self.textbox = textbox
        self.theme = theme
        self.format_colors = format_colors
        self.master = master

    def init_text_tags(self):
        """初始化文本标签"""
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
        """获取选区范围"""
        try:
            return self.textbox.index('sel.first'), self.textbox.index('sel.last')
        except TclError:
            return None, None

    def _selection_all_match(self, start, end, checker):
        """检查选区匹配"""
        idx = start
        while self.textbox.compare(idx, '<', end):
            if not checker(idx):
                return False
            idx = self.textbox.index(f'{idx}+1c')
        return True

    def _font_flags_at(self, index):
        """获取字体标志"""
        tags = self.textbox.tag_names(index)
        if 'fmt_font_bold_italic' in tags:
            return True, True
        if 'fmt_font_bold' in tags:
            return True, False
        if 'fmt_font_italic' in tags:
            return False, True
        return False, False

    def _apply_font_flags(self, start, end, bold, italic):
        """应用字体标志"""
        for tag in self.FONT_TAGS:
            self.textbox.tag_remove(tag, start, end)
        if bold and italic:
            self.textbox.tag_add('fmt_font_bold_italic', start, end)
        elif bold:
            self.textbox.tag_add('fmt_font_bold', start, end)
        elif italic:
            self.textbox.tag_add('fmt_font_italic', start, end)

    def _toggle_font_flag(self, flag):
        """切换字体标志"""
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
        """切换简单标签"""
        start, end = self._selection_range()
        if not start or not end:
            return
        has_all = self._selection_all_match(start, end, lambda idx: tag_name in self.textbox.tag_names(idx))
        if has_all:
            self.textbox.tag_remove(tag_name, start, end)
        else:
            self.textbox.tag_add(tag_name, start, end)
        self.textbox.edit_modified(True)

    def _line_range(self, index):
        """获取行范围"""
        line_start = self.textbox.index(f'{index} linestart')
        line_end = self.textbox.index(f'{index} lineend +1c')
        return line_start, line_end

    def _line_has_quote(self, index):
        """检查是否有引用"""
        probe = self.textbox.index(f'{index} lineend')
        return self.TAG_QUOTE in self.textbox.tag_names(probe)

    def _sync_quote_for_current_line(self, _):
        """同步引用标签"""
        insert = self.textbox.index('insert')
        if not insert.endswith('.1'):
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
        """获取对齐标签"""
        probe = self.textbox.index(f'{index} lineend')
        tags = self.textbox.tag_names(probe)
        for tag in self.ALIGN_TAGS:
            if tag in tags:
                return tag
        return None

    def _format_align(self, target_tag):
        """格式化对齐"""
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

    def open_url(self, url):
        if data.settings['ask_url']:
            if not show_question(self.master, '打开链接', f'是否要打开链接：\n{url}', theme=self.theme):
                return
        open_url(url)

    def _link_tag_config(self, tag_name, url):
        """配置链接标签"""
        self.textbox.tag_configure(tag_name, foreground=self.format_colors['linkfg'], underline=1)
        self.textbox.tag_bind(tag_name, '<Control-Button-1>', lambda _: self.open_url(url))

    def format_bold(self, event=None):
        """格式化粗体"""
        if self.textbox.cget('state') == 'disabled':
            return
        self._toggle_font_flag('bold')

    def format_italic(self, event=None):
        """格式化斜体"""
        if self.textbox.cget('state') == 'disabled':
            return "break"
        self._toggle_font_flag('italic')
        return "break"

    def format_underline(self, event=None):
        """格式化下划线"""
        if self.textbox.cget('state') == 'disabled':
            return
        self._toggle_simple_tag(self.TAG_UNDERLINE)

    def format_strikethrough(self, event=None):
        """格式化删除线"""
        if self.textbox.cget('state') == 'disabled':
            return
        self._toggle_simple_tag(self.TAG_STRIKETHROUGH)

    def format_highlight(self, event=None):
        """格式化高亮"""
        if self.textbox.cget('state') == 'disabled':
            return
        self._toggle_simple_tag(self.TAG_HIGHLIGHT)
    
    def format_other_color(self, color):
        """格式化其他颜色"""
        if self.textbox.cget('state') == 'disabled':
            return
        start, end = self._selection_range()
        if not start:
            return
        for tag in self.textbox.tag_names(start):
            if tag.startswith(self.TAG_HIGHLIGHTPREFIX):
                self.textbox.tag_remove(tag, start, end)
        tag_name = f'{self.TAG_HIGHLIGHT}|{color}'
        self.textbox.tag_configure(tag_name, background=color)
        self._toggle_simple_tag(tag_name)
    
    def format_remove_color(self, event=None):
        """移除颜色格式"""
        if self.textbox.cget('state') == 'disabled':
            return
        start, end = self._selection_range()
        if not start:
            return
        for tag in self.textbox.tag_names(start):
            if tag.startswith(self.TAG_HIGHLIGHTPREFIX):
                self.textbox.tag_remove(tag, start, end)

    def format_quote(self, event=None):
        """格式化引用"""
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

    def format_align_left(self, event=None):
        """格式化左对齐"""
        if self.textbox.cget('state') == 'disabled':
            return
        self._format_align(self.TAG_ALIGN_LEFT)

    def format_align_center(self, event=None):
        """格式化居中对齐"""
        if self.textbox.cget('state') == 'disabled':
            return
        self._format_align(self.TAG_ALIGN_CENTER)

    def format_align_right(self, event=None):
        """格式化右对齐"""
        if self.textbox.cget('state') == 'disabled':
            return
        self._format_align(self.TAG_ALIGN_RIGHT)

    def format_link(self, event=None):
        """格式化链接"""
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
