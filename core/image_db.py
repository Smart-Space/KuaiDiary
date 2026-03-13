"""
图片数据库核心
"""
import hashlib
import os
import shutil
import sqlite3

import data

DB_FILE_NAME = "image_index.db"


class ImageDB:
    """图片数据库"""

    def __init__(self):
        self._conn:sqlite3.Connection|None = None
        self._db_dir:str|None = None

    def init_db(self, force:bool=False):
        """
        初始化数据库连接
        """
        if self._conn and not force:
            return
        if self._conn:
            self._close_locked()
        os.makedirs(data.img_dir, exist_ok=True)
        db_path = os.path.join(data.img_dir, DB_FILE_NAME)
        self._conn = sqlite3.connect(db_path)
        self._conn.execute("CREATE TABLE IF NOT EXISTS images (hash TEXT PRIMARY KEY, name TEXT NOT NULL)")
        self._conn.commit()
        self._db_dir = data.img_dir

    def close_db(self):
        """
        关闭数据库连接
        """
        self._close_locked()

    def _close_locked(self):
        if not self._conn:
            return
        try:
            self._conn.commit()
        finally:
            self._conn.close()
            self._conn = None

    def reopen(self):
        """
        重新打开数据库
        """
        self.init_db(force=True)

    def _ensure_conn(self) -> sqlite3.Connection:
        if self._conn is None or self._db_dir != data.img_dir:
            self.init_db(force=True)
        if self._conn is None:
            raise RuntimeError("图片数据库初始化失败")
        return self._conn

    def _compute_image_hash(self, file_path:str) -> str|None:
        """
        计算图片哈希值
        """
        try:
            hasher = hashlib.sha256()
            with open(file_path, "rb") as f:
                while True:
                    chunk = f.read(1024 * 1024)
                    if not chunk:
                        break
                    hasher.update(chunk)
            return hasher.hexdigest()
        except Exception:
            return None

    def _build_image_name(self, file_path:str, hash_value:str) -> str:
        """
        构建图片名称
        """
        _, ext = os.path.splitext(file_path)
        ext = ext.lower() if ext else ".img"
        return f"{hash_value}{ext}"

    def ensure_image(self, file_path:str) -> str|None:
        """
        写入图片索引并返回名称
        """
        if not file_path:
            return None
        conn = self._ensure_conn()
        hash_value = self._compute_image_hash(file_path)
        if not hash_value:
            return None
        cursor = conn.execute("SELECT name FROM images WHERE hash = ?", (hash_value,))
        row = cursor.fetchone()
        if row:
            image_name = row[0]
            image_path = os.path.join(data.img_dir, image_name)
            if os.path.exists(image_path):
                return image_name
            conn.execute("DELETE FROM images WHERE hash = ?", (hash_value,))
            conn.commit()
        image_name = self._build_image_name(file_path, hash_value)
        image_path = os.path.join(data.img_dir, image_name)
        if os.path.abspath(file_path) != os.path.abspath(image_path):
            try:
                shutil.copy2(file_path, image_path)
            except Exception:
                return None
        try:
            conn.execute("INSERT OR REPLACE INTO images (hash, name) VALUES (?, ?)", (hash_value, image_name))
            conn.commit()
        except Exception:
            return None
        return image_name


image_db = ImageDB()
