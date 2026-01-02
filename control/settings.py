"""
设置中需要执行的操作
"""
import shutil
import os
import platform


def copy_to(source_path, target_path):
    """
    将source_path复制到target_path
    """
    for item in os.listdir(source_path):
        src_path = os.path.join(source_path, item)
        dst_path = os.path.join(target_path, item)
        if os.path.isdir(src_path):
            shutil.move(src_path, dst_path)
        # else:
        #     shutil.copy2(src_path, dst_path)

def open_folder(path):
    """
    打开文件夹
    """
    path = os.path.abspath(path)
    if platform.system() == "Windows":
        os.startfile(path)
    elif platform.system() == "Darwin":
        os.system("open %s" % path)
    else:
        os.system("xdg-open %s" % path)
