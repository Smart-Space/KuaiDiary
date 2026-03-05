"""
过往日记
"""
from tkinter import Text
import datetime

from core.files import save_diary, load_diary
from core.diary import Diary


text:Text|None = None
nowday:Diary|None = None

def reg_ui(t:Text):
    global text
    text = t

def load_one_diary(date:str):
    global nowday
    nowday = load_diary(datetime.date.fromisoformat(date))
    text.config(state="normal")
    text.delete("1.0", "end")
    if not nowday.format:
        text.insert("1.0", nowday.get_contents())
    else:
        tag_stack = []
        for attr, val, index in nowday.get_contents():
            if attr == "text":
                text.insert(index, val)
            elif attr == "tagon":
                tag_stack.append((val, index))
            elif attr == "tagoff":
                if tag_stack and tag_stack[-1][0] == val:
                    start_index = tag_stack.pop()[1]
                    text.tag_add(val, start_index, index)
    text.config(state="disabled")
    text.edit_reset()
    text.edit_modified(False)
    return nowday

def get_format_context() -> str:
    context = text.dump("1.0", "end-1c", image=True, tag=True, text=True) # 去掉文本框末尾换行
    return context

def save_one_diary(format:bool=False):
    if (not text or not text.edit_modified() or not nowday) and format == nowday.format:
        return
    if not format:
        context = text.get("1.0", "end-1c")
    else:
        context = get_format_context()
    nowday.update_contents(context)
    nowday.format = format
    save_diary(nowday)
    text.edit_modified(False)
