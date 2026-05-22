"""
日记全局搜索引擎
"""
import pickle
import sqlite3
import threading
import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import Iterable, List, Optional

import data
from core.diary import Diary


@dataclass
class MatchInfo:
    """单条匹配的上下文片段"""
    snippet: str            # 前后文片段（换行替换为 ↵）


@dataclass
class FileResult:
    """单个文件的搜索结果"""
    month: str              # "2026-03"
    day: str                # "01"
    matches: List[MatchInfo]
    total_hits: int         # 总匹配数


class DiarySearchEngine:
    """
    全局文本搜索引擎
    流程:
      1. 首次调用时扫描 datas/ 下所有日记文件
      2. 并发提取纯文本，构建 SQLite 索引（文件表 + FTS5 全文表）
      3. 搜索时先用 simple 的 MATCH 语法筛候选，再做文本匹配
      4. 增量更新：仅重新解析 mtime 变化的文件
    """

    INDEX_FILE = '.search_index.db'

    def _load_simple_extension(self, conn: sqlite3.Connection):
        """加载 simple 扩展，让 FTS5 可以使用 tokenize='simple'。"""
        dll_path = Path(__file__).resolve().parent.parent / "libsimple-windows-x64" / "simple.dll"
        conn.enable_load_extension(True)
        try:
            try:
                conn.load_extension(str(dll_path), "sqlite3_simple_init")
            except TypeError:
                conn.load_extension(str(dll_path))
        finally:
            conn.enable_load_extension(False)

    def __init__(self, data_dir:str='datas', max_workers:int=4):
        self.data_dir = Path(data_dir)
        self.max_workers = max_workers

        self._conn: sqlite3.Connection | None = None
        self._db_dir: str | None = None
        self._lock = threading.Lock()          # 保护数据库读写
        self._build_lock = threading.Lock()    # 防止并发重复构建
        self._loaded = False

    def _extract_text(self, filepath: Path) -> str:
        """
        提取日记文本
        """
        # 纯文本
        if filepath.suffix != '.mdf':
            return filepath.read_text(encoding='utf-8', errors='ignore')

        # MDF 格式
        with open(filepath, 'rb') as f:
            data = pickle.load(f)
        return self._extract_text_from_data(data)

    def _extract_text_from_data(self, data:List) -> str:
        """从 MDF 数据结构中提取纯文本"""
        parts = []
        for item in data:
            if not isinstance(item, (list, tuple)) or len(item) < 2:
                continue
            if item[0] == 'text':
                parts.append(str(item[1]))
        return ''.join(parts)
    
    def _ensure_conn(self) -> sqlite3.Connection:
        """确保数据库连接可用"""
        db_path = self.data_dir / self.INDEX_FILE
        if self._conn and self._db_dir == str(self.data_dir):
            return self._conn
        db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._load_simple_extension(self._conn)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA synchronous=NORMAL")
        self._conn.execute("PRAGMA temp_store=MEMORY")
        self._conn.execute("PRAGMA wal_autocheckpoint=100") # 每100条提交一次 WAL
        self._conn.execute("PRAGMA journal_size_limit=1048576") # 1MB
        self._conn.execute(
            "CREATE TABLE IF NOT EXISTS files (rel_path TEXT PRIMARY KEY, mtime REAL NOT NULL, text TEXT NOT NULL)"
        )
        self._conn.execute(
            "CREATE VIRTUAL TABLE IF NOT EXISTS files_fts USING fts5(rel_path UNINDEXED, mtime UNINDEXED, text, tokenize='simple', content='files', content_rowid='rowid')"
        )
        self._conn.commit()
        self._db_dir = str(self.data_dir)
        return self._conn

    def _load_index(self):
        """从磁盘加载索引"""
        self._ensure_conn()
        self._loaded = True
        return (self.data_dir / self.INDEX_FILE).exists()

    def _save_index(self):
        """持久化索引到磁盘"""
        with self._lock:
            if not self._conn:
                return
            self._conn.commit()

    def _build_match_query(self, keyword: str) -> str:
        """把用户输入包装成适合 FTS5 simple 的短语查询。"""
        normalized = keyword.strip().replace('"', '""').replace("\x00", "")
        return f'"{normalized}"'

    def _update_file_index(self, rel_path: str, mtime: float, text: str):
        conn = self._ensure_conn()
    
        # 1. 查找旧记录的 rowid
        rowid_row = conn.execute(
            "SELECT rowid FROM files WHERE rel_path = ?", (rel_path,)
        ).fetchone()
        
        if rowid_row is not None:
            rowid = rowid_row[0]
            # 2. 先删 FTS5 中的旧索引
            conn.execute("DELETE FROM files_fts WHERE rowid = ?", (rowid,))
            # 3. 更新 files 主表
            conn.execute(
                "UPDATE files SET mtime=?, text=? WHERE rowid=?",
                (mtime, text, rowid),
            )
            # 4. 再插 FTS5 新索引
            conn.execute(
                "INSERT INTO files_fts(rowid, rel_path, mtime, text) VALUES (?, ?, ?, ?)",
                (rowid, rel_path, mtime, text),
            )
        else:
            # 5. 新文件：插入 files 主表
            conn.execute(
                "INSERT INTO files (rel_path, mtime, text) VALUES (?, ?, ?)",
                (rel_path, mtime, text),
            )
            # 6. 获取新 rowid 并插入 FTS5
            rowid = conn.execute(
                "SELECT rowid FROM files WHERE rel_path = ?", (rel_path,)
            ).fetchone()[0]
            conn.execute(
                "INSERT INTO files_fts(rowid, rel_path, mtime, text) VALUES (?, ?, ?, ?)",
                (rowid, rel_path, mtime, text),
            )

    def _remove_file_index(self, rel_path: str):
        conn = self._ensure_conn()
        rowid_row = conn.execute(
            "SELECT rowid FROM files WHERE rel_path = ?", (rel_path,)
        ).fetchone()
        if rowid_row is not None:
            # 先删 FTS5 索引，再删主表
            conn.execute("DELETE FROM files_fts WHERE rowid = ?", (rowid_row[0],))
            conn.execute("DELETE FROM files WHERE rowid = ?", (rowid_row[0],))

    def _iter_all_files(self) -> Iterable[tuple[str, float]]:
        ignore_prefixes = {
            self.INDEX_FILE,
            f"{self.INDEX_FILE}-wal",
            f"{self.INDEX_FILE}-shm",
        }
        for p in self.data_dir.rglob('*'):
            if not p.is_file():
                continue
            if p.name in ignore_prefixes:
                continue
            rel = str(p.relative_to(self.data_dir))
            yield rel, p.stat().st_mtime

    def ensure_index(self, force:bool=False):
        """
        确保索引为最新。
        - 只重新解析 mtime 变化的文件
        - 多线程加速首次构建
        - force=True: 强制重建全部索引
        """
        if not self._loaded:
            self._load_index()

        with self._build_lock:
            # 扫描当前所有文件
            current = dict(self._iter_all_files())
            conn = self._ensure_conn()
            rows = conn.execute("SELECT rel_path, mtime FROM files").fetchall()
            existing = {rel: mtime for rel, mtime in rows}
            fts_count = conn.execute("SELECT COUNT(*) FROM files_fts").fetchone()[0]

            if force or fts_count != len(existing):
                stale = set(current.keys())
            else:
                stale = {
                    rel for rel, mt in current.items()
                    if rel not in existing or existing[rel] < mt
                }
            removed = set(existing.keys()) - set(current.keys())

            if not stale and not removed:
                return

            with self._lock:
                for rel_path in removed:
                    self._remove_file_index(rel_path)

            def _extract(rel_path: str) -> Optional[tuple[str, float, str]]:
                fp = self.data_dir / rel_path
                try:
                    text = self._extract_text(fp)
                    return rel_path, current[rel_path], text
                except Exception:
                    return None

            with ThreadPoolExecutor(self.max_workers) as pool:
                for result in pool.map(_extract, stale):
                    if not result:
                        continue
                    rel_path, mtime, text = result
                    with self._lock:
                        self._update_file_index(rel_path, mtime, text)

            with self._lock:
                conn.commit()

    def invalidate_file(self, diary:Diary):
        """
        标记单个文件索引为过期。
        在日记编辑保存后调用，下次搜索自动重建该文件索引。
        """
        rel_path = f"{diary.date.strftime('%Y-%m')}/{diary.date.strftime('%d')}"
        if diary.format:
            rel_path += '.mdf'
        with self._lock:
            self._remove_file_index(rel_path)
            if self._conn:
                self._conn.commit()
    
    def modify_file(self, diary:Diary):
        """
        直接修改内存索引中某个文件的文本。
        在日记编辑保存后调用，立即更新该文件索引，无需等待下次搜索。
        """
        rel_path = f"{diary.date.strftime('%Y-%m')}/{diary.date.strftime('%d')}"
        if diary.format:
            rel_path += '.mdf'
            text = self._extract_text_from_data(diary.get_contents())
        else:
            text = diary.get_contents()
        with self._lock:
            self._update_file_index(rel_path, time.time(), text)
            if self._conn:
                self._conn.commit()

    def _fetch_texts(self, rel_paths: List[str]) -> dict[str, str]:
        conn = self._ensure_conn()
        if not rel_paths:
            return {}
        texts: dict[str, str] = {}
        chunk_size = 500
        with self._lock:
            for i in range(0, len(rel_paths), chunk_size):
                chunk = rel_paths[i:i + chunk_size]
                placeholders = ",".join(["?"] * len(chunk))
                sql = f"SELECT rel_path, text FROM files WHERE rel_path IN ({placeholders})"
                rows = conn.execute(sql, chunk).fetchall()
                for rel_path, text in rows:
                    texts[rel_path] = text
        return texts

    def _find_candidates(self, match_query: str) -> List[str]:
        conn = self._ensure_conn()
        with self._lock:
            if not match_query:
                rows = conn.execute("SELECT rel_path FROM files").fetchall()
                return [rel_path for (rel_path,) in rows]
            rows = conn.execute(
                "SELECT rel_path FROM files_fts WHERE files_fts MATCH ?",
                (match_query,),
            ).fetchall()
            return [rel_path for (rel_path,) in rows]

    def search(
        self,
        keyword:str,
        context_chars:int = 20,
        max_per_file:int = 10,
        ignore_case:bool = True,
    ) -> List[FileResult]:
        """
        全局文本搜索。

        Args:
            keyword:        搜索关键词
            context_chars:  匹配位置前后各取的字符数
            max_per_file:   每个文件最多返回的匹配数（0=不限）
            ignore_case:    忽略大小写

        Returns:
            按日期排序的 FileResult 列表
        """
        if not keyword or not keyword.strip():
            return []

        self.ensure_index()

        query_text = keyword.strip()
        query = query_text.casefold() if ignore_case else query_text
        query_len = len(query_text)

        match_query = self._build_match_query(query)
        candidates = self._find_candidates(match_query)
        texts = self._fetch_texts(candidates)

        results: List[FileResult] = []

        for rel_path, text in texts.items():
            search_text = text.casefold() if ignore_case else text

            hit_positions: List[int] = []
            start = 0
            while True:
                pos = search_text.find(query, start)
                if pos < 0:
                    break
                hit_positions.append(pos)
                start = pos + query_len

            if not hit_positions:
                continue

            # 解析路径
            p = Path(rel_path)
            month = p.parent.name
            day = p.stem

            matches: List[MatchInfo] = []

            shown = hit_positions[:max_per_file] if max_per_file > 0 else hit_positions

            for pos in shown:
                cs = max(0, pos - context_chars)
                ce = min(len(text), pos + query_len + context_chars)

                # 换行符可视化，保持单行便于展示
                snippet = text[cs:ce].replace('\n', '↵')

                matches.append(MatchInfo(snippet=snippet))

            results.append(FileResult(
                month=month,
                day=day,
                matches=matches,
                total_hits=len(hit_positions),
            ))

        # 按月份+日期排序
        results.sort(key=lambda r: (r.month, r.day), reverse=not data.settings['reverse_sort'])
        return results

search_engine = DiarySearchEngine()
