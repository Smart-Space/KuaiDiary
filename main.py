"""
KuaiDiary
开包即用的纯文本日记软件
Author: Smart-Space<<smart-space@qq.com>>
License: MIT
Copyright (c) 2025 Smart-Space
"""
import os
import socket
import threading
os.chdir(os.path.dirname(os.path.abspath(__file__)))

import data
from ui.mainwindow import MainWindow
from core.files import init_work_dir
from core.settings import init_settings
from core.image_db import image_db

def activate_existing_instance():
    """向已运行的实例发送激活信号"""
    try:
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.settimeout(0.1)
        client.connect(('127.0.0.1', data.SERVER_PORT))
        client.send(b'activate')
        client.close()
        return True
    except Exception:
        return False

if activate_existing_instance():
    exit(0)

def start_server():
    """启动服务器监听激活信号"""
    def handle_client(client_socket):
        try:
            client_socket.settimeout(1)
            msg = client_socket.recv(1024)
            if msg == b'activate':
                mainwindow.after(0, bring_to_front)
        except Exception:
            pass
        finally:
            client_socket.close()

    def bring_to_front():
        mainwindow.deiconify()
        mainwindow.attributes('-topmost', True)
        mainwindow.update()
        mainwindow.attributes('-topmost', False)
        mainwindow.focus_force()

    try:
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind(('127.0.0.1', data.SERVER_PORT))
        server.listen(3)
        data.SERVER_SOCKET = server
        while True:
            client_socket, _ = server.accept()
            handle_client(client_socket)
    except Exception:
        pass

init_settings()
mainwindow = MainWindow()
init_work_dir()
image_db.init_db()
threading.Thread(target=start_server, daemon=True).start()
mainwindow.init_ui()

mainwindow.mainloop()
