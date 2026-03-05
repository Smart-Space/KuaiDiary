"""
当天日记
"""
from tkinter import Text

from core.files import load_today_diary, save_today_diary, delete_today_diary
from core.diary import Diary

text:Text|None = None
today:Diary|None = None

def reg_textbox(textbox:Text):
    global text
    text = textbox

def load_context():
    global today
    today = load_today_diary()
    text.delete("1.0", "end")
    if not today.format:
        text.insert("end", today.get_contents())
    else:
        tag_stack = []
        for attr, val, index in today.get_contents():
            if attr == "text":
                text.insert(index, val)
            elif attr == "tagon":
                tag_stack.append((val, index))
            elif attr == "tagoff":
                if tag_stack and tag_stack[-1][0] == val:
                    start_index = tag_stack.pop()[1]
                    text.tag_add(val, start_index, index)
    text.edit_reset()
    text.edit_modified(False)
    return today

def get_format_context() -> str:
    context = text.dump("1.0", "end-1c", image=True, tag=True, text=True) # 去掉文本框末尾换行
    return context

def save_context(format:bool=False):
    if (not text or not text.edit_modified()) and format == today.format:
        return
    if not format:
        context = text.get('1.0', 'end-1c') # 去掉文本框末尾换行
    else:
        context = get_format_context()
    if not today:
        return
    if context:
        today.update_contents(context)
        today.format = format
        save_today_diary(today)
    else:
        delete_today_diary()
    text.edit_modified(False)
