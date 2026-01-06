"""
KuaiDiary
开包即用的纯文本日记软件
Author: Smart-Space<<smart-space@qq.com>>
License: MIT
Copyright (c) 2025 Smart-Space
"""


from ui.mainwindow import MainWindow
from core.files import init_work_dir
from core.settings import init_settings

init_settings()
mainwindow = MainWindow()
init_work_dir()
mainwindow.init_ui()

mainwindow.mainloop()