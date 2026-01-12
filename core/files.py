"""
文件管理核心
"""
import os
import datetime
from tkinter.filedialog import asksaveasfilename

import data
from core.diary import Diary

def init_work_dir():
    """
    初始化工作目录
    """
    if not os.path.exists(data.work_dir):
        os.makedirs(data.work_dir)
    else:
        # 遍历各个子文件夹，获取文件夹名，在获取其下所有文件名
        months:dict = {}
        now_month = datetime.date.today().strftime("%Y-%m")
        now_day = datetime.date.today().strftime("%d")
        for file_name in os.listdir(data.work_dir):
            file_path = os.path.join(data.work_dir, file_name)
            if os.path.isdir(file_path):
                files = []
                for file in os.listdir(file_path):
                    files.append(file)
                months[file_name] = files
        # data.months为months的倒叙，从新到旧
        data.months = dict(sorted(months.items(), reverse=True))
        if now_month in data.months and now_day in data.months[now_month]:
            data.months[now_month].remove(now_day)

def save_today_diary(diary:Diary):
    """
    保存当天日记
    """
    month = diary.date.strftime("%Y-%m")
    month_dir = os.path.join(data.work_dir, month)
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
    month_dir = os.path.join(data.work_dir, month)
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
    file_path = os.path.join(data.work_dir, month_dir, file_name)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(diary.contents)

def load_today_diary() -> Diary:
    """
    读取当天日记
    """
    month = datetime.date.today().strftime("%Y-%m")
    month_dir = os.path.join(data.work_dir, month)
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

def exist_diary(date:datetime.date) -> bool:
    """
    判断是否存在这天日记。由导出遍历功能调用
    """
    month_dir = date.strftime("%Y-%m")
    file_name = date.strftime("%d")
    file_path = os.path.join(data.work_dir, month_dir, file_name)
    return os.path.exists(file_path)

def load_diary(date:datetime.date) -> Diary:
    """
    读取过往日记
    """
    month_dir = date.strftime("%Y-%m")
    file_name = date.strftime("%d")
    file_path = os.path.join(data.work_dir, month_dir, file_name)
    with open(file_path, "r", encoding="utf-8") as f:
        contents = f.read()
    diary = Diary(date)
    diary.update_contents(contents)
    return diary

def export_month(month:str) -> str:
    """
    导出月份
    """
    format = data.settings.get("format_content", "\n{year}-{month}-{day}\n{content}\n")
    separator = data.settings.get("format_sep", "==========")
    month_dir = os.path.join(data.work_dir, month)
    if not os.path.exists(month_dir):
        return ""
    results = []
    files = os.listdir(month_dir)
    if len(files) == 0:
        return ""
    files.sort(key=lambda x: int(x))
    year, month = month.split("-")
    _month = month.lstrip("0")
    for file_name in files:
        _day = file_name.lstrip("0")
        file_path = os.path.join(month_dir, file_name)
        if os.path.isfile(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                contents = f.read()
            result = format.replace('{year}', year).replace('{month}', month).replace('{-month}', _month).replace('{day}', file_name).replace('{-day}', _day).replace('{content}', contents)
            results.append(result)
    return separator+separator.join(results)+separator

def export_month_to_file(month:str, content:str):
    file = asksaveasfilename(defaultextension=".txt", filetypes=[("Text File", "*.txt")], initialfile=f"{month}.txt", title=f"保存{month}月份日记")
    if not file:
        return
    with open(file, "w", encoding="utf-8") as f:
        f.write(content)
    
def export_from_to(all_days:list[datetime.date], dir:str, sepyear:bool=False, sepmonth:bool=False):
    """
    从起始到终点日期，在dir目录下导出
    sepyear分年，即每年一个文件
    sepmonth分月，即每月一个文件；如果分年，则每年一个子文件夹
    默认不分，命名为"start_end.txt"
    分年命名为"year.txt"
    分月命名为"year-month.txt"，如果此时分年，则为"year/year-month.txt"
    """
    format = data.settings.get("format_content", "\n{year}-{month}-{day}\n{content}\n")
    separator = data.settings.get("format_sep", "==========")
    # =====================
    # 单文件导出模式
    # =====================
    if not sepyear and not sepmonth:
        start = all_days[0].strftime("%Y-%m-%d")
        end = all_days[-1].strftime("%Y-%m-%d")
        filepath = os.path.join(dir, f"{start}_{end}.txt")
        with open(filepath, 'w', encoding='utf-8', buffering=1024*1024) as f:  # 1MB缓冲
            f.write(separator)
            for d in all_days:
                diary = load_diary(d)
                f.write(format.replace('{year}', str(d.year)).replace('{month}', str(d.month)).replace('{day}', str(d.day)).replace('{-month}', str(d.month).lstrip('0')).replace('{-day}', str(d.day).lstrip('0')).replace('{content}', diary.contents))
                f.write(separator)
        return
    # =====================
    # 分组导出模式
    # =====================
    current_file = None
    current_group = None
    created_dirs = set()  # 避免重复创建目录
    for d in all_days:
        year, month = d.year, d.month
        # 确定分组标识
        if sepyear and sepmonth:
            group = (year, month)
        elif sepyear:
            group = year
        else:
            # 仅sepmonth为True
            group = (year, month)
        # 动态切换文件
        if group != current_group:
            if current_file:
                current_file.close()
            # 生成路径
            if sepyear and sepmonth:
                subdir = os.path.join(dir, str(year))
                if subdir not in created_dirs:
                    os.makedirs(subdir, exist_ok=True)
                    created_dirs.add(subdir)
                filename = f"{year}-{month:02d}.txt"
                filepath = os.path.join(subdir, filename)
            elif sepyear:
                filename = f"{year}.txt"
                filepath = os.path.join(dir, filename)
            else:
                # 仅分月
                filename = f"{year}-{month:02d}.txt"
                filepath = os.path.join(dir, filename)
            current_file = open(filepath, 'w', encoding='utf-8', buffering=256*1024)  # 256KB缓冲
            current_group = group
            current_file.write(separator)
        # 流式写入日记
        diary = load_diary(d)
        current_file.write(format.replace('{year}', str(d.year)).replace('{month}', str(d.month)).replace('{day}', str(d.day)).replace('{-month}', str(d.month).lstrip('0')).replace('{-day}', str(d.day).lstrip('0')).replace('{content}', diary.contents))
        current_file.write(separator)
    if current_file:
        current_file.close()
