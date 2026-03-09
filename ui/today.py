"""
当天日志编辑器
"""
from tkinter import Text
import datetime
from tinui import BasicTinUI, ExpandPanel, VerticalPanel, HorizonPanel, show_error
from tinui.theme.tinuilight import TinUILight

from control.editor import RichTextEditor, editorabel
from control.today_diary import reg_textbox, load_context, save_context
from core.files import export_month, export_month_to_file
import data


class TodayView(BasicTinUI):

    def __init__(self, master=None, theme=TinUILight):
        super().__init__(master)
        self.ui = theme(self)
        self.theme = data.settings['theme']
        self.init_ui()
    
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

        ep = ExpandPanel(self)
        vp.add_child(ep, weight=1)
        textbox = self.ui.add_textbox((0,0), scrollbar=True)
        ep.set_child(textbox[-1])
        self.textbox:Text = textbox[0]
        format_colors = RichTextEditor.get_format_colors(self.theme)
        self.rich_editor = RichTextEditor(self.textbox, self.theme, format_colors, self.master)
        self.rich_editor.init_text_tags()
        editorabel(self.textbox)
        reg_textbox(self.textbox)
        today = load_context()

        barbutton_text = (
            ('', '\uE8DD', self.format_bold),
            ('', '\uE8DB', self.format_italic),
            ('', '\uE8DC', self.format_underline),
            ('', '\uEDE0', self.rich_editor.format_strikethrough),
            ('', '\uE7E6', self.rich_editor.format_highlight),
            ('', '\uE71B', self.rich_editor.format_link),
            '',
            ('', '\uE9AA', self.rich_editor.format_quote),
            ('', '\uE8E4', self.rich_editor.format_align_left),
            ('', '\uE8E3', self.rich_editor.format_align_center),
            ('', '\uE8E2', self.rich_editor.format_align_right),
        )
        self.barbutton = self.ui.add_barbutton((0,-50), content=barbutton_text, anchor='w')[-1]

        if today.format:
            self.mdf_check_funcs.on()
        else:
            self.mdf_check_funcs.off()

        self.bind("<Configure>", self.on_resize)
        self.textbox_kr_quote_id = None
    
    def on_resize(self, event):
        self.root.update_layout(event.x, event.y, event.width-1, event.height-1)
    
    def save_log(self):
        save_context(self.format)
    
    first_mdf_change = True
    def mdf_state_changed(self, tag):
        self.format = tag
        if tag:
            if self.first_mdf_change:
                self.first_mdf_change = False
            self.vp.add_child(self.barbutton, 30, index=1)
            self.textbox_kr_quote_id = self.textbox.bind('<KeyRelease>', self.rich_editor._sync_quote_for_current_line, True)
        else:
            if self.first_mdf_change:
                self.first_mdf_change = False
                return
            self.vp.pop_child(1)
            self._BasicTinUI__auto_anchor(self.barbutton, (0,-50))
            self.textbox.unbind('<KeyRelease>', self.textbox_kr_quote_id)
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
    
    def _link_tag_config(self, val, url):
        self.rich_editor._link_tag_config(val, url)

    def format_bold(self, event):
        return self.rich_editor.format_bold(event)

    def format_italic(self, event):
        return self.rich_editor.format_italic(event)

    def format_underline(self, event):
        return self.rich_editor.format_underline(event)
