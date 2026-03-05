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
    if text:
        text.config(state="normal")
        text.delete("1.0", "end")
        text.insert("1.0", nowday.get_contents())
        text.edit_reset()
        text.edit_modified(False)
    return nowday

def save_one_diary(format:bool=False):
    if (not text or not text.edit_modified() or not nowday) and format == nowday.format:
        return
    context = text.get("1.0", "end-1c")
    nowday.update_contents(context)
    nowday.format = format
    save_diary(nowday)
    text.edit_modified(False)
