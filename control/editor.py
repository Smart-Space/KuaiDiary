"""
编辑器化
"""
from tkinter import Text
import tkinter.font as tkfont

import data

def editorabel(text:Text):
    if data.settings['theme'] == 'light':
        ibg = '#000000'
    else:
        ibg = '#E0E0E0'
    font = tkfont.Font(font=text.cget("font"))
    font_size = font.measure("    ")
    text.config(tabs=font_size, undo=True, maxundo=100, autoseparators=False, wrap="word", spacing1=4, spacing3=4,
                insertbackground=ibg, insertwidth=1)
    text.bind("<Control-z>", __editor_undo)
    text.bind("<Control-y>", __editor_redo)
    text.bind("<Key>", __editor_input)

def __editor_undo(e):
    try:
        e.widget.edit_undo()
    except:
        pass
    return "break"

def __editor_redo(e):
    try:
        e.widget.edit_redo()
    except:
        pass
    return "break"

last_keycode = None
sep_keycodes = (229, 32, 13)
def __editor_input(e):
    global last_keycode
    if e.keycode in sep_keycodes and e.keycode != last_keycode:
        e.widget.edit_separator()
    last_keycode = e.keycode
