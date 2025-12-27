"""
文件管理核心
"""
import os
import datetime

import data
from data import work_dir, setting_dir
from core.diary import Diary

def init_work_dir():
    """
    初始化工作目录
    """
    if not os.path.exists(work_dir):
        os.makedirs(work_dir)
    else:
        # 遍历各个子文件夹，获取文件夹名，在获取其下所有文件名
        months:dict = {}
        now_month = datetime.date.today().strftime("%Y-%m")
        now_day = datetime.date.today().strftime("%d")
        for file_name in os.listdir(work_dir):
            file_path = os.path.join(work_dir, file_name)
            if os.path.isdir(file_path):
                files = []
                for file in os.listdir(file_path):
                    files.append(file)
                months[file_name] = files
        # data.months为months的倒叙，从新到旧
        data.months = dict(sorted(months.items(), reverse=True))
        if now_month in data.months and now_day in data.months[now_month]:
            data.months[now_month].remove(now_day)
    if not os.path.exists(setting_dir):
        os.makedirs(setting_dir)

def save_today_diary(diary:Diary):
    """
    保存当天日记
    """
    month = diary.date.strftime("%Y-%m")
    month_dir = os.path.join(work_dir, month)
    if not os.path.exists(month_dir):
        os.makedirs(month_dir)
    file_name = diary.date.strftime("%d")
    file_path = os.path.join(month_dir, file_name)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(diary.contents)

def delete_today_diary():
    """
    删除当天日记
    """
    month = datetime.date.today().strftime("%Y-%m")
    month_dir = os.path.join(work_dir, month)
    if not os.path.exists(month_dir):
        return
    file_name = datetime.date.today().strftime("%d")
    file_path = os.path.join(month_dir, file_name)
    if not os.path.exists(file_path):
        return
    os.remove(file_path)
    # 判断当月文件夹是否为空
    if len(os.listdir(month_dir)) == 0:
        os.rmdir(month_dir)

def save_diary(diary:Diary):
    """
    保存过往日记
    """
    month_dir = diary.date.strftime("%Y-%m")
    file_name = diary.date.strftime("%d")
    file_path = os.path.join(work_dir, month_dir, file_name)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(diary.contents)

def load_today_diary() -> Diary:
    """
    读取当天日记
    """
    month = datetime.date.today().strftime("%Y-%m")
    month_dir = os.path.join(work_dir, month)
    if not os.path.exists(month_dir):
        return Diary(datetime.date.today())
    file_name = datetime.date.today().strftime("%d")
    file_path = os.path.join(month_dir, file_name)
    if not os.path.exists(file_path):
        return Diary(datetime.date.today())
    with open(file_path, "r", encoding="utf-8") as f:
        contents = f.read()
    diary = Diary(datetime.date.today())
    diary.update_contents(contents)
    return diary

def load_diary(date:datetime.date) -> Diary:
    """
    读取过往日记
    """
    month_dir = date.strftime("%Y-%m")
    file_name = date.strftime("%d")
    file_path = os.path.join(work_dir, month_dir, file_name)
    with open(file_path, "r", encoding="utf-8") as f:
        contents = f.read()
    diary = Diary(date)
    diary.update_contents(contents)
    return diary
