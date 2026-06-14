"""
设置界面
"""
import webbrowser
from tkinter import Text, Entry
from tkinter.filedialog import askdirectory
from tkinter.font import families

from tinui import BasicTinUI, show_info, ask_choice, ExpandPanel, HorizonPanel, VerticalPanel, PanelSash
from tinui.TinUI import TinUIXmlFunc
from tinui.theme.tinuilight import TinUILight

import data
from core.settings import save_settings
from core.image_db import image_db
from control.settings import open_folder, copy_to


class SettingView(BasicTinUI):

    def __init__(self, master=None, theme=TinUILight):
        super().__init__(master)
        self.set_scale(data.factory)
        self.ui = theme(self)
        self.init_ui()
        self.bind('<MouseWheel>', self.on_mousewheel)
        self.theme = data.settings['theme']
    
    def on_mousewheel(self, event):
        self.yview_scroll(int(-1*(event.delta/120)), "units")
    
    def init_ui(self):
        if data.settings['theme'] == 'light':
            rbg = '#F5F5F5'
            rfg = '#1B1B1B'
            ibg = '#000000'
            self.all_bg = '#F9F9F9'
            self.all_line = '#e5e5e5'
        else:
            rbg = "#2A2A2A"
            rfg = '#F5F5F5'
            ibg = '#E0E0E0'
            self.all_bg = '#272727'
            self.all_line = '#1d1d1d'

        self.root = ExpandPanel(self, padding=(4,4,4,4))
        vp = VerticalPanel(self, spacing=30)
        self.root.set_child(vp)

        # about
        about_panel = HorizonPanel(self, spacing=20, bg=self.all_bg, linew=1, line=self.all_line, padding=(10,10,10,10))
        vp.add_child(about_panel, 100)
        about_panel.add_child(self.ui.add_image((0,0), imgfile='./assets/logo.png', state='uniform', width=100, height=100, anchor='w'))
        about_vp = VerticalPanel(self, spacing=5)
        about_panel.add_child(about_vp, weight=1)
        about_vp.add_child(self.ui.add_title((0,0), text=f"快日记 | KuaiDiary {data.version}", anchor='w'), 50)
        about_vp.add_child(self.ui.add_paragraph((0,0), text='2025-present Smart-Space copyright', width=self.scale_value(300)), 50)
        about_panel.add_child(self.ui.add_link((0,0), text='GitHub', command=self.open_github, anchor='w')[-1], 70)
        about_panel.add_child(self.ui.add_link((0,0), text='Gitee', command=self.open_gitee, anchor='w')[-1], 70)

        # window
        window_panel = VerticalPanel(self, bg=self.all_bg, linew=1, line=self.all_line, padding=(10,10,10,10))
        vp.add_child(window_panel, 300)
        window_panel.add_child(self.ui.add_title((0,0), text="界面设置", size=2), 40)
        window_panel.add_child(PanelSash(window_panel, bg=self.all_line, draggable=False), 2)

        window_panel_hp1 = HorizonPanel(self, spacing=20, padding=(0,20,0,10))
        window_panel.add_child(window_panel_hp1, 60)
        window_panel_hp1.add_child(self.ui.add_paragraph((0,0), text='外观 (重启后生效)', anchor='w'), weight=1)
        self.theme_radiobox, theme_radiobox = self.ui.add_radiobox((0,0), content=('明亮', '暗黑'), command=self.change_theme, anchor='w')[-2:]
        if data.settings['theme'] == 'light':
            self.theme_radiobox.select(0)
        else:
            self.theme_radiobox.select(1)
        window_panel_hp1.add_child(theme_radiobox)
        window_panel.add_child(PanelSash(window_panel, bg=self.all_line, draggable=False), 2)

        window_panel_hp2 = HorizonPanel(self, spacing=20, padding=(0,20,0,10))
        window_panel.add_child(window_panel_hp2, 60)
        window_panel_hp2.add_child(self.ui.add_paragraph((0,0), text='窗口启动', anchor='w'), weight=1)
        self.win_segmentbutton, win_segmentbutton = self.ui.add_segmentbutton((0,0), content=('无要求','最大化','居中','上次位置'), command=self.change_window_action, anchor='w')[-2:]
        self.win_segmentbutton.select(data.settings['window_action'])
        window_panel_hp2.add_child(win_segmentbutton)
        window_panel.add_child(PanelSash(window_panel, bg=self.all_line, draggable=False), 2)

        window_panel_hp3 = HorizonPanel(self, spacing=20, padding=(0,20,0,10))
        window_panel.add_child(window_panel_hp3, 60)
        window_panel_hp3.add_child(self.ui.add_paragraph((0,0), text='编辑字体', anchor='w'))
        self.font_demo = self.ui.add_paragraph((0,0), text="abc甲乙丙", anchor='w')
        window_panel_hp3.add_child(self.font_demo, 100)
        self.itemconfig(self.font_demo, font=(data.settings['font_family'], 12))
        window_panel_hp3.add_child(self.ui.add_button2((0,0), text='选择字体', command=self.select_font, anchor='w')[-1])
        window_panel_hp3.add_child(PanelSash(window_panel_hp3, bg=self.all_line, draggable=False), 2)
        window_panel_hp3.add_child(self.ui.add_paragraph((0,0), text='字体大小', anchor='w'))
        self.font_size = self.ui.add_paragraph((0,0), text=f"{data.settings['font_size']}pt", anchor='w')
        window_panel_hp3.add_child(self.font_size, 50)
        index = data.settings['font_size'] - 10
        change_font_size_func = TinUIXmlFunc(None)
        font_scale, font_scale_uid = self.ui.add_scalebar((0,0), data=(10,11,12,13,14,15,16,17,18,19,20,21,22,23,24), command=change_font_size_func, anchor='w')[-2:]
        font_scale.select(index)
        change_font_size_func.function = self.change_font_size
        window_panel_hp3.add_child(font_scale_uid)
        window_panel.add_child(PanelSash(window_panel, bg=self.all_line, draggable=False), 2)

        window_panel_hp4 = HorizonPanel(self, spacing=20, padding=(0,20,0,10))
        window_panel.add_child(window_panel_hp4, 60)
        toggle_ask_url_func = TinUIXmlFunc(None)
        ask_url_checkbutton, as_url_checkbutton_uid = self.ui.add_checkbutton((0,0), text='打开URL前询问', command=toggle_ask_url_func, anchor='w')[-2:]
        if data.settings['ask_url']:
            ask_url_checkbutton.on()
        toggle_ask_url_func.function = self.toggle_ask_url
        window_panel_hp4.add_child(as_url_checkbutton_uid)
        toggle_show_weekday_func = TinUIXmlFunc(None)
        show_weekday_checkbutton, show_weekday_checkbutton_uid = self.ui.add_checkbutton((0,0), text='显示星期', command=toggle_show_weekday_func, anchor='w')[-2:]
        if data.settings['show_weekday']:
            show_weekday_checkbutton.on()
        toggle_show_weekday_func.function = self.toggle_show_weekday
        window_panel_hp4.add_child(show_weekday_checkbutton_uid)
        
        # storage
        storage_panel = VerticalPanel(self, bg=self.all_bg, linew=1, line=self.all_line, padding=(10,10,10,10))
        vp.add_child(storage_panel, 180)
        storage_panel.add_child(self.ui.add_title((0,0), text="存储设置", size=2), 40)
        storage_panel.add_child(PanelSash(storage_panel, bg=self.all_line, draggable=False), 2)

        storage_hp1 = HorizonPanel(self, spacing=20, padding=(0,20,0,10))
        storage_panel.add_child(storage_hp1, 60)
        storage_hp1.add_child(self.ui.add_paragraph((0,0), text='存储位置', anchor='w'))
        self.st_entry:Entry
        self.st_entry, st_entry_funcs, st_entry_uid = self.ui.add_entry((0,0), width=300, anchor='w')
        storage_hp1_ep = ExpandPanel(self)
        storage_hp1_ep.set_child(st_entry_uid)
        storage_hp1.add_child(storage_hp1_ep, weight=1)
        storage_hp1.add_child(self.ui.add_button2((0,0), icon='\ue712', text='', command=self.select_storage_path, anchor='w')[-1])
        storage_hp1.add_child(self.ui.add_button2((0,0), icon='\ue8da', text='', command=self.open_storage_path, anchor='w')[-1])
        storage_hp1.add_child(self.ui.add_button2((0,0), icon='\ue897', text='', command=self.about_storage_path, anchor='w')[-1])
        st_entry_funcs.disable(fg=rfg, bg=rbg)
        self.st_entry.config(state="normal", readonlybackground=rbg)
        self.st_entry.insert(0, data.work_dir)
        self.st_entry.config(state="readonly")

        storage_hp2 = HorizonPanel(self, spacing=20, padding=(0,20,0,10))
        storage_panel.add_child(storage_hp2, 60)
        storage_hp2.add_child(self.ui.add_paragraph((0,0), text='图片位置', anchor='w'))
        self.img_entry:Entry
        self.img_entry, img_entry_funcs, img_entry_uid = self.ui.add_entry((0,0), width=300, anchor='w')
        storage_hp2_ep = ExpandPanel(self)
        storage_hp2_ep.set_child(img_entry_uid)
        storage_hp2.add_child(storage_hp2_ep, weight=1)
        storage_hp2.add_child(self.ui.add_button2((0,0), icon='\ue712', text='', command=self.select_img_path, anchor='w')[-1])
        storage_hp2.add_child(self.ui.add_button2((0,0), icon='\ue8da', text='', command=self.open_img_path, anchor='w')[-1])
        storage_hp2.add_child(self.ui.add_button2((0,0), icon='\ue897', text='', command=self.about_img_path, anchor='w')[-1])
        img_entry_funcs.disable(fg=rfg, bg=rbg)
        self.img_entry.config(state="normal", readonlybackground=rbg)
        self.img_entry.insert(0, data.img_dir)
        self.img_entry.config(state="readonly")

        # format
        export_panel = VerticalPanel(self, bg=self.all_bg, linew=1, line=self.all_line, padding=(10,10,10,10))
        vp.add_child(export_panel, 400)
        export_hp_title = HorizonPanel(self, spacing=20, padding=(0,20,0,0))
        export_panel.add_child(export_hp_title, 40)
        export_hp_title.add_child(self.ui.add_title((0,0), text="导出设置", size=2), weight=1)
        export_hp_title.add_child(self.ui.add_button((0,0), text='应用更改', command=self.apply_export_setting)[-1])
        export_hp_title.add_child(self.ui.add_button2((0,0), icon='\ue897', text='', command=self.about_export_setting)[-1])
        export_panel.add_child(PanelSash(export_panel, bg=self.all_line, draggable=False), 2)

        export_hp1 = HorizonPanel(self, spacing=20, padding=(10,20,10,10))
        export_panel.add_child(export_hp1, 280)
        export_hp1.add_child(self.ui.add_paragraph((0,0), text='导出内容'))
        exprot_hp1_ep = ExpandPanel(self)
        export_hp1.add_child(exprot_hp1_ep, weight=1)
        self.fm_text:Text
        self.fm_text, _, fm_text_uid = self.ui.add_textbox((0,0), width=225, height=200, scrollbar=True, anchor='w')
        exprot_hp1_ep.set_child(fm_text_uid)
        self.fm_string = self.ui.add_paragraph((0,0), text='')
        export_hp1.add_child(self.fm_string, weight=1)
        export_panel.add_child(PanelSash(export_panel, bg=self.all_line, draggable=False), 2)

        export_hp2 = HorizonPanel(self, spacing=20, padding=(0,20,0,10))
        export_panel.add_child(export_hp2, 60)
        export_hp2.add_child(self.ui.add_paragraph((0,0), text='日记分隔', anchor='w'))
        self.fm_entry:Entry
        self.fm_entry, _, fm_entry_uid = self.ui.add_entry((0,0), width=self.scale_value(200), anchor='w')
        export_hp2.add_child(fm_entry_uid)

        self.fm_text.config(insertwidth=1, insertbackground=ibg)
        self.fm_text.insert(1.0, data.settings.get("format_content", ""))
        self.fm_entry.insert(0, data.settings.get("format_sep", ""))
        self.preview_export_format()

        # search
        search_panel = VerticalPanel(self, bg=self.all_bg, linew=1, line=self.all_line, padding=(10,10,10,10))
        vp.add_child(search_panel, 180)
        search_panel.add_child(self.ui.add_title((0,0), text="搜索设置", size=2), 40)
        search_panel.add_child(PanelSash(search_panel, bg=self.all_line, draggable=False), 2)

        search_hp1 = HorizonPanel(self, spacing=20, padding=(0,20,0,10))
        search_panel.add_child(search_hp1, 60)
        toggle_case_func = TinUIXmlFunc(None)
        case_checkbutton, case_checkbutton_uid = self.ui.add_checkbutton((0,0), text='区分大小写', command=toggle_case_func, anchor='w')[-2:]
        if data.settings['case_sensitive']:
            case_checkbutton.on()
        toggle_case_func.function = self.toggle_case_sensitive
        search_hp1.add_child(case_checkbutton_uid)

        search_hp2 = HorizonPanel(self, spacing=20, padding=(0,20,0,10))
        search_panel.add_child(search_hp2, 60)
        toggle_reverse_func = TinUIXmlFunc(None)
        reverse_checkbutton, reverse_checkbutton_uid = self.ui.add_checkbutton((0,0), text='逆时间顺序排序', command=toggle_reverse_func, anchor='w')[-2:]
        if data.settings['reverse_sort']:
            reverse_checkbutton.on()
        toggle_reverse_func.function = self.toggle_reverse_sort
        search_hp2.add_child(reverse_checkbutton_uid)

        self.bind("<Configure>", self.on_resize)
    
    def on_resize(self, event):
        self.root.update_layout(event.x, event.y, event.width-1, self.scale_value(2000))
        bbox = [*self.bbox('all')]
        bbox[0] -= 5
        bbox[1] -= 5
        bbox[2] += 5
        bbox[3] += 5
        self.config(scrollregion=bbox)
    
    def open_github(self, _):
        webbrowser.open("https://github.com/Smart-Space/KuaiDiary")
    
    def open_gitee(self, _):
        webbrowser.open("https://gitee.com/captorking/KuaiDiary")
    
    def about_export_setting(self, _):
        show_info(self.master, "导出设置说明", "导出内容为每篇日记导出的文本格式，有如下特殊转义文本：\n" \
        "· {year} 年 {month} 月 {day} 日 {weekday} 星期\n" \
        "· {-month}\t无补零月\n" \
        "· {-day}\t\t无补零日\n" \
        "· {content}\t日记内容\n\n" \
        "日记分隔为每篇日记的分隔符，且会出现在全部日记的首尾。\n\n" \
        "富格式会导出为markdown格式。", theme=self.theme)
    
    def apply_export_setting(self, _):
        content, sep = self.preview_export_format()
        data.settings["format_content"] = content
        data.settings["format_sep"] = sep
        save_settings()
    
    def preview_export_format(self):
        # 预览导出格式
        content = self.fm_text.get(1.0, "end-1c")
        sep = self.fm_entry.get()
        _content = content.replace("{year}", "2026").replace("{month}", "01").replace("{day}", "01").replace("{-month}", "1").replace("{-day}", "1").replace("{weekday}", "Monday").replace("{content}", "日记内容")
        self.itemconfig(self.fm_string, text=f"格式预览：\n{sep}{_content}{sep}")
        return content, sep

    def select_storage_path(self, _):
        new_path = askdirectory(initialdir=data.work_dir, title="选择存储目录")
        if not new_path:
            return
        data.settings["storage_path"] = new_path
        self.st_entry.config(state="normal")
        self.st_entry.delete(0, "end")
        self.st_entry.insert(0, new_path)
        self.st_entry.config(state="readonly")
        save_settings()
        # 迁移原目录下的所有文件
        copy_to(data.work_dir, new_path)
        # 更新文件目录
        data.work_dir = new_path
    
    def open_storage_path(self, _):
        open_folder(data.work_dir)
    
    def about_storage_path(self, _):
        show_info(self.master, "存储目录说明", "更改存储目录后，快日记会迁移所有日记。\n当日记较多时，请等待片刻。", theme=self.theme)
    
    def select_img_path(self, _):
        new_path = askdirectory(initialdir=data.img_dir, title="选择图片存储目录")
        if not new_path:
            return
        data.settings["img_path"] = new_path
        self.img_entry.config(state="normal")
        self.img_entry.delete(0, "end")
        self.img_entry.insert(0, new_path)
        self.img_entry.config(state="readonly")
        save_settings()
        # 迁移原目录下的所有文件
        copy_to(data.img_dir, new_path)
        # 更新文件目录
        data.img_dir = new_path
        image_db.reopen()
    
    def open_img_path(self, _):
        open_folder(data.img_dir)

    def about_img_path(self, _):
        show_info(self.master, "图片目录说明", "更改图片目录后，快日记会迁移所有图片。\n当图片较多时，请等待片刻。", theme=self.theme)

    def change_theme(self, t):
        if t == '明亮':
            data.settings['theme'] = 'light'
        else:
            data.settings['theme'] = 'dark'
        save_settings()
    
    def change_window_action(self, t):
        if t == '无要求':
            now = 0
        elif t == '最大化':
            now = 1
        elif t == '居中':
            now = 2
        elif t == '上次位置':
            now = 3
        if now != data.settings['window_action']:
            data.settings['window_action'] = now
            save_settings()
    
    def change_font_size(self, size):
        data.settings['font_size'] = size
        save_settings()
        self.itemconfig(self.font_size, text=f"{size}pt")
        data.today_editor.config_new_font_family(data.settings['font_family'], data.settings['font_size'])
        data.dates_editor.config_new_font_family(data.settings['font_family'], data.settings['font_size'])

    def select_font(self, _):
        all_fonts = sorted(list(families()))
        font = ask_choice(self.master, "选择字体", "请选择字体", all_fonts, theme=self.theme)
        if font:
            data.settings['font_family'] = font
            save_settings()
            self.itemconfig(self.font_demo, font=(data.settings['font_family'], 14))
            data.today_editor.config_new_font_family(font, data.settings['font_size'])
            data.dates_editor.config_new_font_family(font, data.settings['font_size'])

    def toggle_ask_url(self, tag):
        data.settings['ask_url'] = tag
        save_settings()
    
    def toggle_show_weekday(self, tag):
        data.settings['show_weekday'] = tag
        save_settings()
    
    def toggle_case_sensitive(self, tag):
        data.settings['case_sensitive'] = tag
        save_settings()
    
    def toggle_reverse_sort(self, tag):
        data.settings['reverse_sort'] = tag
        save_settings()
