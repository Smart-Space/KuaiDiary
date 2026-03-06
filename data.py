"""
KuaiDiary数据
"""
import socket
from tkinter import Tk

from tinui.theme.tinuilight import TinUILight
from tinui.theme.tinuidark import TinUIDark

version:str = "2.0.0" # 版本号

root:Tk | None = None # 主窗口

work_dir:str = "./datas" # 工作目录
months:dict = {} # 存放月份数据 {年-月:[日期,...]}，需要有序字典，从python3.7开始默认字典有序

setting_dir:str = "./settings" # 设置目录
settings:dict = {
    "theme": "light", # 主题
    "window_action": 0, # ("无要求","最大化","居中","记住上次位置")
    "window_action_pos": (0, 0, 800, 600), # 窗口位置
    "storage_path": "./datas", # 数据存储路径
    "format_content": "\n{year}-{month}-{day}\n{content}\n", # 内容格式
    "format_sep": "==========", # 分隔线格式
}

UITheme:TinUILight|TinUIDark|None = None

SERVER_SOCKET:socket.socket|None = None # 单实例通信服务器
SERVER_PORT:int = 21567 # 通信端口
