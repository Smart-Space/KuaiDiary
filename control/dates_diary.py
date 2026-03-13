"""
过往日记
"""
from tkinter import Text
import datetime
from collections import defaultdict

from core.files import save_diary, load_diary
from core.diary import Diary


text:Text|None = None
nowday:Diary|None = None
TAG_LINKPREFIX = 'fmt_link|'
TAG_HIGHLIGHT = 'fmt_highlight|'

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
        tag_map = defaultdict(list)
        for attr, val, index in nowday.get_contents():
            if attr == "text":
                text.insert(index, val)
            elif attr == "image":
                text.master.insert_image_by_name(val, index)
            elif attr == "tagon":
                tag_map[val].append(index)
                if val.startswith(TAG_HIGHLIGHT):
                    text.tag_configure(val, background=val[len(TAG_HIGHLIGHT):])
            elif attr == "tagoff":
                if tag_map[val]:
                    start_index = tag_map[val].pop()
                    if val.startswith(TAG_LINKPREFIX):
                        url = val[len(TAG_LINKPREFIX):]
                        text.master._link_tag_config(val, url)
                    text.tag_add(val, start_index, index)
        while tag_map:
            # 处理未关闭的标签
            val, indices = tag_map.popitem()
            for start_index in indices:
                text.tag_add(val, start_index, "end")
    text.config(state="disabled")
    text.edit_reset()
    text.edit_modified(False)
    text.tag_raise('sel')
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
