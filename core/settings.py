"""
设置文件核心
"""
import json
import os

from tinui.theme.tinuilight import TinUILight
from tinui.theme.tinuidark import TinUIDark

import data
from data import setting_dir

def load_settings() -> dict:
    """
    加载设置文件
    """
    if not os.path.exists(setting_dir):
        os.makedirs(setting_dir)
    settings_file = os.path.join(setting_dir, "settings.json")
    if not os.path.exists(settings_file):
        return {}
    with open(settings_file, "r", encoding="utf-8") as f:
        return json.load(f)

def init_settings() -> None:
    """
    初始化设置文件
    """
    settings = load_settings()
    if settings:
        data.settings.update(settings)
    data.work_dir = data.settings.get("storage_path", "./datas")
    data.UITheme = TinUILight if data.settings.get("theme", "light") == "light" else TinUIDark

def save_settings() -> None:
    """
    保存设置文件
    """
    settings_file = os.path.join(setting_dir, "settings.json")
    with open(settings_file, "w", encoding="utf-8") as f:
        json.dump(data.settings, f, ensure_ascii=False, indent=4)
