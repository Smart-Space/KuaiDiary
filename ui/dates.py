"""
以往日期选择与日志修改
"""
from tkinter import Text
from tkinter.colorchooser import askcolor
from tinui import BasicTinUI, ExpandPanel, VerticalPanel, HorizonPanel, show_error
from tinui.theme.tinuilight import TinUILight

import data
from control.dates_diary import reg_ui, load_one_diary, save_one_diary
from control.editor import RichTextEditor, editorabel
from core.files import export_month, export_month_to_file


class DatesView(BasicTinUI):

    def __init__(self, master=None, theme=TinUILight):
        super().__init__(master)
        self.diary:str = None
        self.ui = theme(self)
        self.theme = data.settings['theme']
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

        ep2 = ExpandPanel(self)
        vp.add_child(ep2, weight=1)
        textbox = self.ui.add_textbox((0,0), scrollbar=True)
        ep2.set_child(textbox[-1])
        self.textbox:Text = textbox[0]
        format_colors = RichTextEditor.get_format_colors(self.theme)
        self.rich_editor = RichTextEditor(self.textbox, self.theme, format_colors, self.master)
        self.rich_editor.init_text_tags()
        editorabel(self.textbox)
        reg_ui(self.textbox)

        barbutton_text = (
            ('', '\uE8DD', self.rich_editor.format_bold),
            ('', '\uE8DB', self.rich_editor.format_italic),
            ('', '\uE8DC', self.rich_editor.format_underline),
            ('', '\uEDE0', self.rich_editor.format_strikethrough),
            ('', '\uE7E6', self.rich_editor.format_highlight),
            ('', '\uE71B', self.rich_editor.format_link),
            '',
            ('', '\uE91B', self.rich_editor.format_insert_image),
            ('', '\uE9AA', self.rich_editor.format_quote),
            ('', '\uE8E4', self.rich_editor.format_align_left),
            ('', '\uE8E3', self.rich_editor.format_align_center),
            ('', '\uE8E2', self.rich_editor.format_align_right),
        )
        barbuttons, self.barbutton = self.ui.add_barbutton((0,-50), content=barbutton_text, anchor='w')[-2:]
        flyoutui,_,self.flyout_hide,_ = self.ui.add_flyout(barbuttons[4][-1], width=120, height=120, bind='<Button-3>', anchor='s')
        flyoutui.add_button((5,5), text='    ', bg='#FFE600', activebg='#FFE600', linew=0, command=lambda _: self.higlight_default_other_color('#FFE600'))
        flyoutui.add_button((45,5), text='    ', bg='#D87700', activebg='#D87700', linew=0, command=lambda _: self.higlight_default_other_color('#D87700'))
        flyoutui.add_button((85,5), text='    ', bg='#ff0000', activebg='#ff0000', linew=0, command=lambda _: self.higlight_default_other_color('#ff0000'))
        flyoutui.add_button((5,45), text='    ', bg='#008000', activebg='#008000', linew=0, command=lambda _: self.higlight_default_other_color('#008000'))
        flyoutui.add_button((45,45), text='    ', bg='#0000ff', activebg='#0000ff', linew=0, command=lambda _: self.higlight_default_other_color('#0000ff'))
        flyoutui.add_button((85,45), text='    ', bg='#4b0082', activebg='#4b0082', linew=0, command=lambda _: self.higlight_default_other_color('#4b0082'))
        flyoutui.add_button((5,85), text='    ', bg='#ee82ee', activebg='#ee82ee', linew=0, command=lambda _: self.higlight_default_other_color('#ee82ee'))
        flyoutui.add_button((45,85), text='🚫', linew=0, command=self.format_remove_color)
        flyoutui.add_button((83,85), text='🎨', linew=0, command=self.highlight_other_color)

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
    
    def _link_tag_config(self, val, url):
        self.rich_editor._link_tag_config(val, url)

    def insert_image_by_name(self, image_name, index):
        self.rich_editor.insert_image_by_name(image_name, index)

    def format_bold(self, event):
        return self.rich_editor.format_bold(event)

    def format_italic(self, event):
        return self.rich_editor.format_italic(event)

    def format_underline(self, event):
        return self.rich_editor.format_underline(event)

    def mdf_state_changed(self, tag):
        if self.format == tag:
            return
        self.format = tag
        if tag:
            self.vp.add_child(self.barbutton, 30, index=1)
            self.textbox_kr_quote_id = self.textbox.bind('<KeyRelease>', self.rich_editor._sync_quote_for_current_line, True)
        else:
            self.vp.pop_child(1)
            self._BasicTinUI__auto_anchor(self.barbutton, (0,-50))
            self.textbox.unbind('<KeyRelease>', self.textbox_kr_quote_id)
        self.event_generate("<Configure>", x=0, y=0, width=self.winfo_width(), height=self.winfo_height())

    def higlight_default_other_color(self, color):
        self.flyout_hide(None)
        self.rich_editor.format_other_color(color)
        self.textbox.tag_raise('sel')

    def highlight_other_color(self, _):
        self.flyout_hide(None)
        color = askcolor(parent=self.master, title='选择高亮颜色')[1]
        if color:
            self.rich_editor.format_other_color(color)
        self.textbox.tag_raise('sel')
    
    def format_remove_color(self, _):
        self.flyout_hide(None)
        self.rich_editor.format_remove_color(None)
