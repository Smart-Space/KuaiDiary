"""
日记全局搜索引擎
"""
import pickle
import re
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


class _SimpleTokenizer:
    """使用 simple.dll 进行分词"""

    def __init__(self):
        self._local = threading.local()
        self._dll_path = (
            Path(__file__).resolve().parent.parent / "libsimple-windows-x64" / "simple.dll"
        )

    def _create_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(":memory:")
        conn.execute("PRAGMA temp_store=MEMORY")
        conn.enable_load_extension(True)
        try:
            try:
                conn.load_extension(str(self._dll_path), "sqlite3_simple_init")
            except TypeError:
                conn.load_extension(str(self._dll_path))
        finally:
            conn.enable_load_extension(False)
        conn.execute("CREATE VIRTUAL TABLE IF NOT EXISTS t USING fts5(content, tokenize='simple')")
        conn.execute("CREATE VIRTUAL TABLE IF NOT EXISTS t_vocab USING fts5vocab(t, 'row')")
        return conn

    def _get_conn(self) -> sqlite3.Connection:
        conn = getattr(self._local, "conn", None)
        if conn is None:
            conn = self._create_conn()
            self._local.conn = conn
        return conn

    def tokenize(self, text: str) -> List[str]:
        if not text:
            return []
        try:
            conn = self._get_conn()
            conn.execute("DELETE FROM t")
            conn.execute("INSERT INTO t(content) VALUES (?)", (text,))
            rows = conn.execute("SELECT term FROM t_vocab").fetchall()
            return [term for (term,) in rows if term]
        except Exception:
            return _fallback_tokenize(text)


def _fallback_tokenize(text: str) -> List[str]:
    parts = re.findall(r"[0-9A-Za-z]+|[\u4e00-\u9fff]", text)
    return parts


_simple_tokenizer = _SimpleTokenizer()

class DiarySearchEngine:
    """
    全局文本搜索引擎
    流程:
      1. 首次调用时扫描 datas/ 下所有日记文件
      2. 并发提取纯文本，构建 SQLite 索引（文本 + 分词映射）
      3. 搜索时先用分词索引筛候选，再做文本匹配
      4. 增量更新：仅重新解析 mtime 变化的文件
    """

    INDEX_FILE = '.search_index.db'

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
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA synchronous=NORMAL")
        self._conn.execute("PRAGMA temp_store=MEMORY")
        self._conn.execute(
            "CREATE TABLE IF NOT EXISTS files (rel_path TEXT PRIMARY KEY, mtime REAL NOT NULL, text TEXT NOT NULL)"
        )
        self._conn.execute(
            "CREATE TABLE IF NOT EXISTS tokens (token TEXT NOT NULL, rel_path TEXT NOT NULL, PRIMARY KEY (token, rel_path))"
        )
        self._conn.execute("CREATE INDEX IF NOT EXISTS idx_tokens_token ON tokens(token)")
        self._conn.execute("CREATE INDEX IF NOT EXISTS idx_tokens_rel_path ON tokens(rel_path)")
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

    def _tokenize_text(self, text: str) -> List[str]:
        """使用 simple 对文本分词"""
        normalized = text.casefold()
        tokens = [t.strip() for t in _simple_tokenizer.tokenize(normalized) if t.strip()]
        return tokens

    def _tokenize_query(self, keyword: str) -> List[str]:
        keyword_norm = keyword.casefold()
        tokens = set(self._tokenize_text(keyword_norm))
        if keyword_norm and keyword_norm not in tokens:
            tokens.add(keyword_norm)
        return sorted(tokens)

    def _update_file_index(self, rel_path: str, mtime: float, text: str):
        conn = self._ensure_conn()
        conn.execute("DELETE FROM tokens WHERE rel_path = ?", (rel_path,))
        conn.execute(
            "INSERT OR REPLACE INTO files (rel_path, mtime, text) VALUES (?, ?, ?)",
            (rel_path, mtime, text),
        )
        tokens = sorted(set(self._tokenize_text(text)))
        if tokens:
            conn.executemany(
                "INSERT OR IGNORE INTO tokens (token, rel_path) VALUES (?, ?)",
                [(token, rel_path) for token in tokens],
            )

    def _remove_file_index(self, rel_path: str):
        conn = self._ensure_conn()
        conn.execute("DELETE FROM tokens WHERE rel_path = ?", (rel_path,))
        conn.execute("DELETE FROM files WHERE rel_path = ?", (rel_path,))

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

            if force:
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

    def _find_candidates(self, tokens: List[str]) -> List[str]:
        conn = self._ensure_conn()
        with self._lock:
            if not tokens:
                rows = conn.execute("SELECT rel_path FROM files").fetchall()
                return [rel_path for (rel_path,) in rows]
            placeholders = ",".join(["?"] * len(tokens))
            sql = (
                f"SELECT rel_path FROM tokens WHERE token IN ({placeholders}) "
                "GROUP BY rel_path HAVING COUNT(DISTINCT token) = ?"
            )
            rows = conn.execute(sql, (*tokens, len(tokens))).fetchall()
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

        query = keyword.casefold() if ignore_case else keyword
        query_len = len(keyword)

        tokens = self._tokenize_query(keyword)
        candidates = self._find_candidates(tokens)
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
