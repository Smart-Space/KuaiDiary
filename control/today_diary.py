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
    if text:
        text.delete("1.0", "end")
        text.insert("end", today.get_contents())
        text.edit_reset()
        text.edit_modified(False)
    return today

def save_context(format:bool=False):
    if (not text or not text.edit_modified()) and format == today.format:
        return
    context = text.get('1.0', 'end-1c') # 去掉文本框末尾换行
    if not today:
        return
    if context:
        today.update_contents(context)
        today.format = format
        save_today_diary(today)
    else:
        delete_today_diary()
    text.edit_modified(False)
