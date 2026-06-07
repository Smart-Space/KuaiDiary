"""
KuaiDiary数据
"""
import sys
if sys.platform == "win32":
    import ctypes
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
    factory = ctypes.windll.shcore.GetScaleFactorForDevice(0) / 100
else:
    factory = 1
import socket
from tkinter import Tk

from tinui.TinUIDialog import Dialog
Dialog.set_scale(factory)
from tinui.theme.tinuilight import TinUILight
from tinui.theme.tinuidark import TinUIDark

from control.editor import RichTextEditor

version:str = "2.9.0" # 版本号

root:Tk | None = None # 主窗口

work_dir:str = "./datas" # 工作目录
months:dict = {} # 存放月份数据 {年-月:[日期,...]}，需要有序字典，从python3.7开始默认字典有序
img_dir:str = "./st_imgs" # 图片目录

setting_dir:str = "./settings" # 设置目录
settings:dict = {
    "theme": "light", # 主题
    "window_action": 0, # ("无要求","最大化","居中","记住上次位置")
    "window_action_pos": (0, 0, 800, 600), # 窗口位置
    "ask_url": False, # 打开URL前是否询问
    "storage_path": "./datas", # 数据存储路径
    "img_path": "./st_imgs", # 图片存储路径
    "format_content": "\n{year}-{month}-{day} {weekday}\n{content}\n", # 内容格式
    "format_sep": "==========", # 分隔线格式
    "font_family": "Microsoft YaHei", # 字体
    "font_size": 12, # 字体大小
    "case_sensitive": False, # 搜索是否区分大小写
    "reverse_sort": False, # 是否逆时间顺序排序
    "show_weekday": False # 是否显示星期
}

today_editor:RichTextEditor | None = None # 今日编辑器实例
dates_editor:RichTextEditor | None = None # 日期列表编辑器实例

UITheme:TinUILight|TinUIDark|None = None

SERVER_SOCKET:socket.socket|None = None # 单实例通信服务器
SERVER_PORT:int = 21567 # 通信端口

req_open_dairy:tuple[str, str, int, str] | None = None # 请求打开的日记日期
