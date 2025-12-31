"""
当天日记
"""
from tkinter import Text

from core.files import load_today_diary, save_today_diary, delete_today_diary
from core.diary import Diary

text:Text = None
today:Diary = None

def reg_textbox(textbox:Text):
    global text
    text = textbox

def load_context():
    global today
    today = load_today_diary()
    text.delete("1.0", "end")
    text.insert("end", today.get_contents())
    text.edit_reset()
    text.edit_modified(False)

def save_context():
    if not text.edit_modified():
        return
    context = text.get('1.0', 'end')[:-1] # 去掉文本框末尾换行
    if context:
        today.update_contents(context)
        save_today_diary(today)
    else:
        delete_today_diary()
    text.edit_modified(False)
