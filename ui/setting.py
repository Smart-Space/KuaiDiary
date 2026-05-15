"""
设置界面
"""
import webbrowser
from tkinter import Text, Entry
from tkinter.filedialog import askdirectory
from tkinter.font import families

from tinui import BasicTinUI, TinUIXml, show_info, ask_choice
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
        self.uixml = TinUIXml(self.ui)
        self.init_ui()
        bbox = [*self.bbox('all')]
        bbox[0] -= 5
        bbox[1] -= 5
        bbox[2] += 5
        bbox[3] += 5
        self.config(scrollregion=bbox)
        self.bind('<MouseWheel>', self.on_mousewheel)
        self.theme = data.settings['theme']
    
    def on_mousewheel(self, event):
        self.yview_scroll(int(-1*(event.delta/120)), "units")
    
    def init_ui(self):
        if data.settings['theme'] == 'light':
            rbg = '#F5F5F5'
            rfg = '#1B1B1B'
            ibg = '#000000'
        else:
            rbg = "#2A2A2A"
            rfg = '#F5F5F5'
            ibg = '#E0E0E0'
        self.uixml.funcs.update({
            'open_github': self.open_github,
            'open_gitee': self.open_gitee,
            'apply_export_setting': self.apply_export_setting,
            'about_export_setting': self.about_export_setting,
            'select_storage_path': self.select_storage_path,
            'open_storage_path': self.open_storage_path,
            'about_storage_path': self.about_storage_path,
            'select_img_path': self.select_img_path,
            'open_img_path': self.open_img_path,
            'about_img_path': self.about_img_path,
            'change_theme': self.change_theme,
            'change_window_action': self.change_window_action,
            'toggle_ask_url': None,
            'select_font': self.select_font,
            'change_font_size': None,
            'toggle_case_sensitive': None,
            'toggle_reverse_sort': None
        })
        with open("./assets/settingui.xml", "r", encoding="utf-8") as f:
            xml = f.read().replace("%VERSION%", data.version)
        self.uixml.loadxml(xml)

        # windows
        self.theme_radiobox = self.uixml.tags['theme_radiobox'][-2]
        if data.settings['theme'] == 'light':
            self.theme_radiobox.select(0)
        else:
            self.theme_radiobox.select(1)
        self.win_segmentbutton = self.uixml.tags['win_segmentbutton'][-2]
        self.win_segmentbutton.select(data.settings['window_action'])

        self.font_demo = self.uixml.tags['font_demo']
        self.itemconfig(self.font_demo, font=(data.settings['font_family'], 12))
        self.font_size = self.uixml.tags['font_size']
        self.itemconfig(self.font_size, text=f"字体大小 {data.settings['font_size']}pt")
        index = data.settings['font_size'] - 10
        font_scale = self.uixml.tags['font_scale'][-2]
        font_scale.select(index)
        self.uixml.funcs['change_font_size'] = self.change_font_size

        ask_url_checkbutton = self.uixml.tags['ask_url_checkbutton'][-2]
        if data.settings['ask_url']:
            ask_url_checkbutton.on()
        self.uixml.funcs['toggle_ask_url'] = self.toggle_ask_url
        
        # storage
        self.st_entry:Entry = self.uixml.tags['st_entry'][0]
        st_entry_func = self.uixml.tags['st_entry'][1]
        st_entry_func.disable(fg=rfg, bg=rbg)
        self.st_entry.config(state="normal", readonlybackground=rbg)
        self.st_entry.insert(0, data.work_dir)
        self.st_entry.config(state="readonly")

        self.img_entry:Entry = self.uixml.tags['img_entry'][0]
        img_entry_func = self.uixml.tags['img_entry'][1]
        img_entry_func.disable(fg=rfg, bg=rbg)
        self.img_entry.config(state="normal", readonlybackground=rbg)
        self.img_entry.insert(0, data.img_dir)
        self.img_entry.config(state="readonly")

        # format
        self.fm_text:Text = self.uixml.tags['fm_textbox'][0]
        self.fm_entry:Entry = self.uixml.tags['fm_entry'][0]
        self.fm_string = self.uixml.tags['fm_string']
        self.fm_text.config(insertwidth=1, insertbackground=ibg)
        self.fm_text.insert(1.0, data.settings.get("format_content", ""))
        self.fm_entry.insert(0, data.settings.get("format_sep", ""))
        self.preview_export_format()

        # search
        case_sensitive_checkbutton = self.uixml.tags['case_sensitive_checkbutton'][-2]
        if data.settings['case_sensitive']:
            case_sensitive_checkbutton.on()
        self.reverse_sort_checkbutton = self.uixml.tags['reverse_sort_checkbutton'][-2]
        if data.settings['reverse_sort']:
            self.reverse_sort_checkbutton.on()
        self.uixml.funcs['toggle_case_sensitive'] = self.toggle_case_sensitive
        self.uixml.funcs['toggle_reverse_sort'] = self.toggle_reverse_sort
    
    def open_github(self, _):
        webbrowser.open("https://github.com/Smart-Space/KuaiDiary")
    
    def open_gitee(self, _):
        webbrowser.open("https://gitee.com/captorking/KuaiDiary")
    
    def about_export_setting(self, _):
        show_info(self.master, "导出设置说明", "导出内容为每篇日记导出的文本格式，有如下特殊转义文本：\n" \
        "· {year} 年 {month} 月 {day} 日\n" \
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
        _content = content.replace("{year}", "2026").replace("{month}", "01").replace("{day}", "01").replace("{-month}", "1").replace("{-day}", "1").replace("{content}", "日记内容")
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
        self.itemconfig(self.font_size, text=f"字体大小 {size}pt")
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
    
    def toggle_case_sensitive(self, tag):
        data.settings['case_sensitive'] = tag
        save_settings()
    
    def toggle_reverse_sort(self, tag):
        data.settings['reverse_sort'] = tag
        save_settings()
