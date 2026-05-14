"""
日记全局搜索引擎
"""
import pickle
import re
import threading
import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import List, Optional

from core.diary import Diary


@dataclass
class MatchInfo:
    """单条匹配的上下文片段"""
    snippet: str            # 前后文片段（换行替换为 ↵）
    highlight_start: int    # 关键词在 snippet 中的起始偏移
    highlight_end: int      # 关键词在 snippet 中的结束偏移


@dataclass
class FileResult:
    """单个文件的搜索结果"""
    rel_path: str           # "2026-03/01.mdf"
    month: str              # "2026-03"
    day: str                # "01"
    matches: List[MatchInfo]
    total_hits: int         # 总匹配数


# ─────────────────── 搜索引擎 ───────────────────

class DiarySearchEngine:
    """
    全局文本搜索引擎
    流程:
      1. 首次调用时扫描 datas/ 下所有 .mdf 文件
      2. 并发提取纯文本，构建内存索引并持久化为 pickle
      3. 后续搜索直接在内存文本中正则匹配
      4. 增量更新：仅重新解析 mtime 变化的文件
    """

    INDEX_FILE = '.search_cache.pkl'

    def __init__(self, data_dir:str='datas', max_workers:int=4):
        self.data_dir = Path(data_dir)
        self.max_workers = max_workers

        # 内存索引: { "2026-03/01.mdf": {"mtime": float, "text": str} }
        self._index: dict = {}
        self._lock = threading.Lock()          # 保护 _index 读写
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
    
    def _load_index(self):
        """从磁盘加载索引"""
        path = self.data_dir / self.INDEX_FILE
        have_file = False
        if path.exists():
            try:
                with open(path, 'rb') as f:
                    self._index = pickle.load(f)
                have_file = True
            except Exception:
                self._index = {}
        self._loaded = True
        return have_file

    def _save_index(self):
        """持久化索引到磁盘"""
        path = self.data_dir / self.INDEX_FILE
        path.parent.mkdir(parents=True, exist_ok=True)
        # 先写临时文件再原子重命名，防止写入中断导致损坏
        tmp = path.with_suffix('.tmp')
        with open(tmp, 'wb') as f:
            pickle.dump(self._index, f, protocol=pickle.HIGHEST_PROTOCOL)
        tmp.replace(path)

    def ensure_index(self, force:bool=False):
        """
        确保索引为最新。
        - 只重新解析 mtime 变化的文件
        - 多线程加速首次构建
        - force=True: 强制重建全部索引
        """
        if not self._loaded:
            if self._load_index() and not force:
                return

        with self._build_lock:
            # 扫描当前所有文件
            current: dict[str, float] = {}
            for p in self.data_dir.rglob('*'):
                if not p.is_file():
                    continue
                if p.name == self.INDEX_FILE or p.name.endswith('.tmp'):
                    continue
                rel = str(p.relative_to(self.data_dir))
                current[rel] = p.stat().st_mtime

            # 找出需要更新的文件
            if force:
                stale = set(current.keys())
            else:
                stale = {
                    rel for rel, mt in current.items()
                    if rel not in self._index
                    or self._index[rel]['mtime'] < mt
                }

            if not stale:
                return

            # 并发提取纯文本
            def _extract(rel_path:str) -> Optional[tuple]:
                fp = self.data_dir / rel_path
                try:
                    text = self._extract_text(fp)
                    return rel_path, {'mtime': current[rel_path], 'text': text}
                except Exception:
                    return None

            with ThreadPoolExecutor(self.max_workers) as pool:
                for result in pool.map(_extract, stale):
                    if result:
                        self._index[result[0]] = result[1]

            self._save_index()

    def invalidate_file(self, diary:Diary):
        """
        标记单个文件索引为过期。
        在日记编辑保存后调用，下次搜索自动重建该文件索引。
        """
        rel_path = f"{diary.date.strftime('%Y-%m')}/{diary.date.strftime('%d')}"
        if diary.format:
            rel_path += '.mdf'
        with self._lock:
            self._index.pop(rel_path, None)
    
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
            entry = self._index.get(rel_path)
            if entry:
                entry['text'] = text
                entry['mtime'] = time.time()

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

        flags = re.IGNORECASE if ignore_case else 0
        pattern = re.compile(re.escape(keyword), flags)

        # 取快照，避免长时间持锁
        with self._lock:
            snapshot = dict(self._index)

        results: List[FileResult] = []

        for rel_path, entry in snapshot.items():
            text = entry['text']
            hits = list(pattern.finditer(text))
            if not hits:
                continue

            # 解析路径
            p = Path(rel_path)
            month = p.parent.name
            day = p.stem

            shown = hits[:max_per_file] if max_per_file > 0 else hits
            matches: List[MatchInfo] = []

            for m in shown:
                cs = max(0, m.start() - context_chars)
                ce = min(len(text), m.end() + context_chars)

                # 换行符可视化，保持单行便于展示
                snippet = text[cs:ce].replace('\n', '↵')

                matches.append(MatchInfo(
                    snippet=snippet,
                    highlight_start=m.start() - cs,
                    highlight_end=m.end() - cs,
                ))

            results.append(FileResult(
                rel_path=rel_path,
                month=month,
                day=day,
                matches=matches,
                total_hits=len(hits),
            ))

        # 按月份+日期排序
        results.sort(key=lambda r: (r.month, r.day), reverse=True)
        return results

search_engine = DiarySearchEngine()
