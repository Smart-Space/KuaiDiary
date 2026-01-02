"""
KuaiDiary数据
"""
from tkinter import Tk

version:str = "0.3.0" # 版本号

root:Tk = None # 主窗口

work_dir:str = "./datas" # 工作目录
months:dict = {} # 存放月份数据 {年-月:[日期,...]}，需要有序字典，从python3.7开始默认字典有序

setting_dir:str = "./settings" # 设置目录
settings:dict = {
    "storage_path": "./datas", # 数据存储路径
    "format_content": "\n{year}-{month}-{day}\n{content}\n", # 内容格式
    "format_sep": "==========", # 分隔线格式
}
