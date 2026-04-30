"""
文件管理核心
"""
import os
import datetime
import pickle
from tkinter.filedialog import asksaveasfilename

import data
from core.diary import Diary

DIARY_FORMAT_SUFFIX = ".mdf"


def _month_str_from_date(date:datetime.date) -> str:
    return date.strftime("%Y-%m")


def _day_str_from_date(date:datetime.date) -> str:
    return date.strftime("%d")


def _month_dir_path(month:str) -> str:
    return os.path.join(data.work_dir, month)


def _strip_day_suffix(file_name:str) -> str:
    return os.path.splitext(file_name)[0]


def _diary_candidate_paths(month_dir:str, day:str) -> tuple[str, str]:
    plain_path = os.path.join(month_dir, day)
    return plain_path, plain_path + DIARY_FORMAT_SUFFIX


def _resolve_diary_file(month_dir:str, day:str) -> tuple[str|None, bool]:
    plain_path, formatted_path = _diary_candidate_paths(month_dir, day)
    if os.path.exists(formatted_path):
        return formatted_path, True
    if os.path.exists(plain_path):
        return plain_path, False
    return None, False


def _collect_days(month_dir:str) -> list[str]:
    if not os.path.isdir(month_dir):
        return []
    days = set()
    for file in os.listdir(month_dir):
        file_path = os.path.join(month_dir, file)
        if os.path.isfile(file_path):
            day = _strip_day_suffix(file)
            if day.isdigit():
                days.add(day)
    return sorted(days, key=lambda x: int(x))


def _save_diary_file(diary:Diary):
    month = _month_str_from_date(diary.date)
    day = _day_str_from_date(diary.date)
    month_dir = _month_dir_path(month)
    os.makedirs(month_dir, exist_ok=True)
    plain_path, formatted_path = _diary_candidate_paths(month_dir, day)
    target_path = formatted_path if diary.format else plain_path
    obsolete_path = formatted_path if not diary.format else plain_path
    if os.path.exists(obsolete_path) and obsolete_path != target_path:
        os.remove(obsolete_path)
    if isinstance(diary.contents, str):
        with open(target_path, "w", encoding="utf-8") as f:
            f.write(diary.contents)
    else:
        with open(target_path, "wb") as f:
            pickle.dump(diary.contents, f)

def init_work_dir():
    """
    初始化工作目录
    """
    if not os.path.exists(data.work_dir):
        os.makedirs(data.work_dir)
    if not os.path.exists(data.img_dir):
        os.makedirs(data.img_dir)
    months:dict[str, list[str]] = {}
    now_month = datetime.date.today().strftime("%Y-%m")
    now_day = datetime.date.today().strftime("%d")
    for file_name in os.listdir(data.work_dir):
        file_path = os.path.join(data.work_dir, file_name)
        if os.path.isdir(file_path):
            days = _collect_days(file_path)
            months[file_name] = days
    sorted_months = dict(sorted(months.items(), reverse=True))
    formatted_months:dict[str, list[str]] = {}
    for month, days in sorted_months.items():
        formatted_months[month] = sorted(days, key=lambda x: int(x))
    data.months = formatted_months
    if now_month in data.months and now_day in data.months[now_month]:
        data.months[now_month].remove(now_day)

def save_today_diary(diary:Diary):
    """
    保存当天日记
    """
    _save_diary_file(diary)

def delete_today_diary():
    """
    删除当天日记
    """
    month = datetime.date.today().strftime("%Y-%m")
    month_dir = os.path.join(data.work_dir, month)
    if not os.path.exists(month_dir):
        return
    file_name = datetime.date.today().strftime("%d")
    file_path, _ = _resolve_diary_file(month_dir, file_name)
    if not file_path:
        return
    os.remove(file_path)
    # 判断当月文件夹是否为空
    if len(os.listdir(month_dir)) == 0:
        os.rmdir(month_dir)

def save_diary(diary:Diary):
    """
    保存过往日记
    """
    _save_diary_file(diary)

def load_today_diary() -> Diary:
    """
    读取当天日记
    """
    month = datetime.date.today().strftime("%Y-%m")
    month_dir = os.path.join(data.work_dir, month)
    if not os.path.exists(month_dir):
        return Diary(datetime.date.today())
    file_name = datetime.date.today().strftime("%d")
    file_path, formatted = _resolve_diary_file(month_dir, file_name)
    if not file_path:
        return Diary(datetime.date.today())
    if not formatted:
        with open(file_path, "r", encoding="utf-8") as f:
            contents = f.read()
    else:
        with open(file_path, "rb") as f:
            contents = pickle.load(f)
    diary = Diary(datetime.date.today())
    diary.update_contents(contents, formatted)
    return diary

def exist_diary(date:datetime.date) -> bool:
    """
    判断是否存在这天日记。由导出遍历功能调用
    """
    month_dir = _month_dir_path(_month_str_from_date(date))
    day = _day_str_from_date(date)
    file_path, _ = _resolve_diary_file(month_dir, day)
    return file_path is not None

def load_diary(date:datetime.date) -> Diary:
    """
    读取过往日记
    """
    month = _month_str_from_date(date)
    month_dir = _month_dir_path(month)
    day = _day_str_from_date(date)
    file_path, formatted = _resolve_diary_file(month_dir, day)
    if not file_path:
        return Diary(date)
    if not formatted:
        with open(file_path, "r", encoding="utf-8") as f:
            contents = f.read()
    else:
        with open(file_path, "rb") as f:
            contents = pickle.load(f)
    diary = Diary(date)
    diary.update_contents(contents, formatted)
    return diary

TAG_LINKPREFIX = 'fmt_link|'
TAG_HIGHLIGHTPREFIX = 'fmt_highlight|'
def _load_mdf2md(file_path:str) -> str:
    with open(file_path, "rb") as f:
        contents = pickle.load(f)
    tokens = ['\n']
    quote_tag = False
    link_tag = False
    line_start = True

    def _append_text(text:str):
        nonlocal line_start
        if not text:
            return
        if not quote_tag:
            tokens.append(text)
            line_start = text.endswith("\n")
            return
        parts = text.split("\n")
        for i, part in enumerate(parts):
            if i > 0:
                tokens.append("\n")
                line_start = True
            if line_start:
                tokens.append("> ")
            if part:
                tokens.append(part)
            line_start = False
    for attr, val, _ in contents:
        if attr == "text":
            _append_text(val)
        elif attr == "image":
            image_path = os.path.abspath(os.path.join(data.img_dir, val)).replace('\\', '/')
            if quote_tag and line_start:
                tokens.append("> ")
            tokens.append(f"![{val}]({image_path})")
            line_start = False
        elif attr == "tagon" or attr == "tagoff":
            match val:
                case "fmt_font_bold":
                    tokens.append("**")
                case "fmt_font_italic":
                    tokens.append("*")
                case "fmt_font_bold_italic":
                    tokens.append("***")
                case "fmt_strikethrough":
                    tokens.append("~~")
                case "fmt_underline":
                    if attr == "tagon":
                        tokens.append("<u>")
                    else:
                        tokens.append("</u>")
                case "fmt_superscript":
                    if attr == "tagon":
                        tokens.append("<sup>")
                    else:
                        tokens.append("</sup>")
                case "fmt_subscript":
                    if attr == "tagon":
                        tokens.append("<sub>")
                    else:
                        tokens.append("</sub>")
                case "fmt_highlight":
                    tokens.append("==")
                case "fmt_quote":
                    if attr == "tagon":
                        quote_tag = True
                    else:
                        quote_tag = False
                case "fmt_align_left":
                    if attr == "tagon":
                        tokens.append('<div align="left">')
                    else:
                        tokens.append('</div>')
                case "fmt_align_center":
                    if attr == "tagon":
                        tokens.append('<div align="center">')
                    else:
                        tokens.append('</div>')
                case "fmt_align_right":
                    if attr == "tagon":
                        tokens.append('<div align="right">')
                    else:
                        tokens.append('</div>')
                case _ if val.startswith(TAG_LINKPREFIX):
                    if attr == "tagon":
                        if link_tag:
                            continue
                        link_tag = True
                        tokens.append('[')
                    else:
                        link_tag = False
                        url = val[len(TAG_LINKPREFIX):]
                        tokens.append(f']({url})')
                case _ if val.startswith(TAG_HIGHLIGHTPREFIX):
                    tokens.append("==")
    tokens.append('\n')
    return "".join(tokens)

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
    days = _collect_days(month_dir)
    if len(days) == 0:
        return ""
    year, month = month.split("-")
    _month = month.lstrip("0")
    for day in days:
        file_path, formatted = _resolve_diary_file(month_dir, day)
        if not file_path:
            continue
        _day = day.lstrip("0")
        if not formatted:
            with open(file_path, "r", encoding="utf-8") as f:
                contents = f.read()
        else:
            contents = _load_mdf2md(file_path)
        result = format.replace('{year}', year).replace('{month}', month).replace('{-month}', _month).replace('{day}', day).replace('{-day}', _day).replace('{content}', contents)
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
                if diary.format:
                    diary_contents = _load_mdf2md(os.path.join(_month_dir_path(_month_str_from_date(d)), _day_str_from_date(d) + DIARY_FORMAT_SUFFIX))
                    diary.contents = diary_contents
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
        if current_file:
            diary = load_diary(d)
            if diary.format:
                diary_contents = _load_mdf2md(os.path.join(_month_dir_path(_month_str_from_date(d)), _day_str_from_date(d) + DIARY_FORMAT_SUFFIX))
                diary.contents = diary_contents
            current_file.write(format.replace('{year}', str(d.year)).replace('{month}', str(d.month)).replace('{day}', str(d.day)).replace('{-month}', str(d.month).lstrip('0')).replace('{-day}', str(d.day).lstrip('0')).replace('{content}', diary.contents))
            current_file.write(separator)
    if current_file:
        current_file.close()
