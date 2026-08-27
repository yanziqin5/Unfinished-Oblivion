"""
数据库管理 —— SQLite 本地存储。
"""
import sqlite3
import time
import os
import json
from dataclasses import dataclass, field
from threading import Lock

from utils.constants import DB_PATH, LIFE_BASE_SEC


# ================================================================
#  数据模型
# ================================================================
@dataclass
class Page:
    page_id: int = 0
    page_name: str = ""
    title: str = ""
    paper_type: str = "黄1"
    use_handwritten: bool = False
    is_sealed: bool = False
    is_always_light: bool = True
    avg_old_degree: float = 0.0
    revive_total: int = 0
    comment_count: int = 0
    word_count: int = 0
    epigraph: str = ""
    create_time: float = 0.0
    last_open_time: float = 0.0

    def to_dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items()}


@dataclass
class Word:
    word_id: int = 0
    page_id: int = 0
    content: str = ""
    x: float = 0.0
    y: float = 0.0
    font_size: int = 14
    life_total_sec: float = LIFE_BASE_SEC
    create_timestamp: float = 0.0
    revive_count: int = 0
    is_deleted: bool = False
    comment_id: int = 0
    dissolved_to_dot: bool = False
    dissolved_x: float = 0.0
    dissolved_y: float = 0.0
    order_index: int = 0

    def to_dict(self) -> dict:
        return {k: v for k, v in self.__dict__.items()}


@dataclass
class Comment:
    """AI 跨时空批注（文档规定字段）"""
    comment_id: int = 0
    page_id: int = 0
    content: str = ""
    x: float = 0.0
    y: float = 0.0
    rotate_angle: float = 0.0         # 旋转角度 ±12°
    base_alpha: float = 0.4            # 基准透明度（0.35~0.5 终身不变）
    font_size: int = 10
    font_path: str = ""                # 绑定手写字体路径
    unlock_type: int = 1               # 解锁类型：1普通浅层 / 2语义关键词 / 3深层尘封
    unlock_time: float = 0.0           # 首次写入时间戳
    keyword_match: str = ""            # 触发的关键词（空=随机/普通）
    hover_count: int = 0               # 用户悬停互动次数
    is_overwrite_dead: bool = False    # 是否被顶替淘汰（已删除标记）


# ================================================================
#  DB Manager
# ================================================================
class DB:
    """线程安全的 SQLite 管理器。"""

    def __init__(self, path: str | None = None):
        # 允许通过环境变量 DB_PATH 重定向数据库路径（测试隔离用）；缺省使用正式路径
        if path is None:
            path = os.environ.get("DB_PATH", str(DB_PATH))
        self._path = path
        self._lock = Lock()
        os.makedirs(os.path.dirname(path), exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._path)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._lock:
            conn = self._connect()
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS pages (
                    page_id     INTEGER PRIMARY KEY AUTOINCREMENT,
                    page_name   TEXT DEFAULT '',
                    title       TEXT DEFAULT '',
                    paper_type  TEXT DEFAULT '黄1',
                    use_handwritten INTEGER DEFAULT 0,
                    is_sealed   INTEGER DEFAULT 0,
                    is_always_light INTEGER DEFAULT 1,
                    avg_old_degree REAL DEFAULT 0.0,
                    revive_total INTEGER DEFAULT 0,
                    comment_count INTEGER DEFAULT 0,
                    epigraph   TEXT DEFAULT '',
                    create_time REAL DEFAULT 0,
                    last_open_time REAL DEFAULT 0
                );

                CREATE TABLE IF NOT EXISTS words (
                    word_id     INTEGER PRIMARY KEY AUTOINCREMENT,
                    page_id     INTEGER NOT NULL,
                    content     TEXT DEFAULT '',
                    x           REAL DEFAULT 0,
                    y           REAL DEFAULT 0,
                    font_size   INTEGER DEFAULT 14,
                    life_total_sec REAL DEFAULT 7200,
                    create_timestamp REAL DEFAULT 0,
                    revive_count INTEGER DEFAULT 0,
                    is_deleted  INTEGER DEFAULT 0,
                    comment_id  INTEGER DEFAULT 0,
                    dissolved_to_dot INTEGER DEFAULT 0,
                    dissolved_x REAL DEFAULT 0,
                    dissolved_y REAL DEFAULT 0,
                    FOREIGN KEY (page_id) REFERENCES pages(page_id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS comments (
                    comment_id  INTEGER PRIMARY KEY AUTOINCREMENT,
                    page_id     INTEGER NOT NULL,
                    content     TEXT DEFAULT '',
                    x           REAL DEFAULT 0,
                    y           REAL DEFAULT 0,
                    rotate_angle REAL DEFAULT 0,
                    base_alpha  REAL DEFAULT 0.4,
                    font_size   INTEGER DEFAULT 10,
                    font_path   TEXT DEFAULT '',
                    unlock_type INTEGER DEFAULT 1,
                    unlock_time REAL DEFAULT 0,
                    keyword_match TEXT DEFAULT '',
                    hover_count INTEGER DEFAULT 0,
                    is_overwrite_dead INTEGER DEFAULT 0,
                    FOREIGN KEY (page_id) REFERENCES pages(page_id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS settings (
                    key         TEXT PRIMARY KEY,
                    value       TEXT DEFAULT ''
                );

                CREATE INDEX IF NOT EXISTS idx_words_page ON words(page_id);
                CREATE INDEX IF NOT EXISTS idx_comments_page ON comments(page_id);
            """)
            conn.commit()
            conn.close()
        self._migrate()

    def _migrate(self):
        """给旧数据库添加缺失的列。"""
        with self._lock:
            conn = self._connect()
            # 检查并添加缺失的列
            existing = set(r[1] for r in conn.execute("PRAGMA table_info(pages)").fetchall())
            needed = {
                "title": "TEXT DEFAULT ''",
                "epigraph": "TEXT DEFAULT ''",
                "is_sealed": "INTEGER DEFAULT 0",
                "is_always_light": "INTEGER DEFAULT 1",
                "avg_old_degree": "REAL DEFAULT 0.0",
                "revive_total": "INTEGER DEFAULT 0",
                "comment_count": "INTEGER DEFAULT 0",
                "last_open_time": "REAL DEFAULT 0",
            }
            for col, col_type in needed.items():
                if col not in existing:
                    try:
                        conn.execute(f"ALTER TABLE pages ADD COLUMN {col} {col_type}")
                    except Exception:
                        pass

            existing_w = set(r[1] for r in conn.execute("PRAGMA table_info(words)").fetchall())
            needed_w = {
                "revive_count": "INTEGER DEFAULT 0",
                "is_deleted": "INTEGER DEFAULT 0",
                "comment_id": "INTEGER DEFAULT 0",
                "dissolved_to_dot": "INTEGER DEFAULT 0",
                "dissolved_x": "REAL DEFAULT 0",
                "dissolved_y": "REAL DEFAULT 0",
                "order_index": "INTEGER DEFAULT 0",
            }
            for col, col_type in needed_w.items():
                if col not in existing_w:
                    try:
                        conn.execute(f"ALTER TABLE words ADD COLUMN {col} {col_type}")
                    except Exception:
                        pass
            # 如果 order_index 是新添加的，用 word_id 初始化（保持原有顺序）
            if "order_index" not in existing_w:
                try:
                    conn.execute("UPDATE words SET order_index = word_id")
                    conn.commit()
                except Exception:
                    pass

            # 迁移 comments 表新增列（三层解锁体系+字段规范）
            existing_c = set(r[1] for r in conn.execute("PRAGMA table_info(comments)").fetchall())
            # 旧字段重命名映射
            rename_map = {"rotation": "rotate_angle", "alpha": "base_alpha"}
            for old, new in rename_map.items():
                if old in existing_c and new not in existing_c:
                    try:
                        conn.execute(f"ALTER TABLE comments RENAME COLUMN {old} TO {new}")
                    except Exception:
                        pass
            needed_c = {
                "font_path": "TEXT DEFAULT ''",
                "unlock_type": "INTEGER DEFAULT 1",
                "unlock_time": "REAL DEFAULT 0",
                "keyword_match": "TEXT DEFAULT ''",
                "hover_count": "INTEGER DEFAULT 0",
                "is_overwrite_dead": "INTEGER DEFAULT 0",
            }
            for col, col_type in needed_c.items():
                if col not in existing_c:
                    try:
                        conn.execute(f"ALTER TABLE comments ADD COLUMN {col} {col_type}")
                    except Exception:
                        pass

            conn.commit()
            conn.close()

    # ---- Pages ----
    def create_page(self, paper_type: str = "黄1", title: str = "",
                    epigraph: str = "", **kwargs) -> Page:
        now = time.time()
        with self._lock:
            conn = self._connect()
            cur = conn.execute(
                "INSERT INTO pages (paper_type, title, epigraph, create_time, last_open_time) "
                "VALUES (?, ?, ?, ?, ?)",
                (paper_type, title, epigraph, now, now),
            )
            pid = cur.lastrowid
            conn.commit()
            conn.close()
        return self.get_page(pid)

    def get_page(self, page_id: int) -> Page | None:
        with self._lock:
            conn = self._connect()
            row = conn.execute(
                "SELECT * FROM pages WHERE page_id = ?", (page_id,)
            ).fetchone()
            conn.close()
        if row:
            return Page(**dict(row))
        return None

    def update_page(self, page: Page):
        with self._lock:
            conn = self._connect()
            conn.execute(
                "UPDATE pages SET page_name=?, title=?, paper_type=?, use_handwritten=?, "
                "is_sealed=?, is_always_light=?, avg_old_degree=?, revive_total=?, "
                "comment_count=?, epigraph=?, create_time=?, last_open_time=? "
                "WHERE page_id=?",
                (
                    page.page_name, page.title, page.paper_type, int(page.use_handwritten),
                    int(page.is_sealed), int(page.is_always_light), page.avg_old_degree,
                    page.revive_total, page.comment_count, page.epigraph,
                    page.create_time, page.last_open_time, page.page_id,
                ),
            )
            conn.commit()
            conn.close()

    def list_pages(self, search: str = "") -> list[Page]:
        with self._lock:
            conn = self._connect()
            if search:
                q = f"%{search}%"
                rows = conn.execute(
                    "SELECT p.*, (SELECT COUNT(*) FROM words WHERE page_id=p.page_id AND is_deleted=0) as word_count "
                    "FROM pages p WHERE p.title LIKE ? "
                    "OR p.epigraph LIKE ? "
                    "OR p.page_id IN (SELECT DISTINCT page_id FROM words WHERE is_deleted=0 AND content LIKE ?) "
                    "ORDER BY p.last_open_time DESC",
                    (q, q, q),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT p.*, (SELECT COUNT(*) FROM words WHERE page_id=p.page_id AND is_deleted=0) as word_count "
                    "FROM pages p ORDER BY p.last_open_time DESC"
                ).fetchall()
            conn.close()
        return [Page(**dict(r)) for r in rows]

    def delete_page(self, page_id: int):
        with self._lock:
            conn = self._connect()
            conn.execute("DELETE FROM words WHERE page_id = ?", (page_id,))
            conn.execute("DELETE FROM comments WHERE page_id = ?", (page_id,))
            conn.execute("DELETE FROM pages WHERE page_id = ?", (page_id,))
            conn.commit()
            conn.close()

    def seal_page(self, page_id: int, sealed: bool = True):
        p = self.get_page(page_id)
        if p:
            p.is_sealed = sealed
            self.update_page(p)

    def unseal_page(self, page_id: int):
        """解封页面——将封存的页面重新激活，恢复文字消亡机制。"""
        self.seal_page(page_id, sealed=False)

    def rename_page(self, page_id: int, new_title: str):
        with self._lock:
            conn = self._connect()
            conn.execute(
                "UPDATE pages SET title=? WHERE page_id=?",
                (new_title, page_id),
            )
            conn.commit()
            conn.close()

    def delete_all_words_on_page(self, page_id: int):
        """删除页面所有文字（重置页面）。"""
        with self._lock:
            conn = self._connect()
            conn.execute("DELETE FROM words WHERE page_id=?", (page_id,))
            conn.execute("DELETE FROM comments WHERE page_id=?", (page_id,))
            conn.commit()
            conn.close()

    def init(self):
        """显式初始化（兼容 old-style 调用）。"""
        pass  # __init__ 中已初始化

    def get_dissolved_dots(self, page_id: int, limit: int = 500) -> list:
        """获取已消散文字的残影点（用于画布残影层）。"""
        with self._lock:
            conn = self._connect()
            rows = conn.execute(
                "SELECT content, dissolved_x, dissolved_y, revive_count "
                "FROM words WHERE page_id=? AND is_deleted=0 AND dissolved_to_dot=1 "
                "LIMIT ?",
                (page_id, limit),
            ).fetchall()
            conn.close()
            result = []
            for r in rows:
                dot = type("Dot", (), {
                    "content": r[0],
                    "dissolved_x": r[1] or 0,
                    "dissolved_y": r[2] or 0,
                    "revive_count": r[3] or 0,
                })()
                result.append(dot)
            return result

    def mark_word_dissolved(self, word_id: int, x: float, y: float):
        """自然死亡的文字：保留数据库记录并标记为已消散残影点（记录残影坐标）。

        注意：此处保持 is_deleted=0，仅置 dissolved_to_dot=1。残影层查询
        (get_dissolved_dots / total_lost_words) 均要求 is_deleted=0，且
        get_alive_words 按寿命过滤（寿命耗尽则 is_word_alive=False），故保留行
        不会让文字复活或重新计入正文，仅用于残影点绘制与"逝去字数"统计。
        """
        with self._lock:
            conn = self._connect()
            conn.execute(
                "UPDATE words SET is_deleted=0, dissolved_to_dot=1, dissolved_x=?, dissolved_y=? "
                "WHERE word_id=?",
                (x, y, word_id),
            )
            conn.commit()
            conn.close()

    def delete_all_pages(self):
        with self._lock:
            conn = self._connect()
            conn.execute("DELETE FROM words")
            conn.execute("DELETE FROM comments")
            conn.execute("DELETE FROM pages")
            # 同时清除首启标记，使"全部删除"等价于回到首次启动
            conn.execute("DELETE FROM settings WHERE key IN ('first_launch_done', 'guide_shown')")
            conn.commit()
            conn.close()

    def touch_page(self, page_id: int):
        """更新页面最后打开时间，供"最近打开"排序使用。"""
        with self._lock:
            conn = self._connect()
            conn.execute(
                "UPDATE pages SET last_open_time=? WHERE page_id=?",
                (time.time(), page_id),
            )
            conn.commit()
            conn.close()

    # ---- Words ----
    def add_word(self, word: Word) -> int:
        with self._lock:
            conn = self._connect()
            cur = conn.execute(
                "INSERT INTO words (page_id, content, x, y, font_size, life_total_sec, "
                "create_timestamp, revive_count, is_deleted, comment_id, "
                "dissolved_to_dot, dissolved_x, dissolved_y, order_index) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    word.page_id, word.content, word.x, word.y, word.font_size,
                    word.life_total_sec, word.create_timestamp, word.revive_count,
                    int(word.is_deleted), word.comment_id,
                    int(word.dissolved_to_dot), word.dissolved_x, word.dissolved_y,
                    word.order_index,
                ),
            )
            wid = cur.lastrowid
            conn.commit()
            conn.close()
        return wid

    def get_words(self, page_id: int) -> list[Word]:
        with self._lock:
            conn = self._connect()
            rows = conn.execute(
                "SELECT * FROM words WHERE page_id = ? ORDER BY order_index", (page_id,)
            ).fetchall()
            conn.close()
        return [Word(**dict(r)) for r in rows]

    def get_alive_words(self, page_id: int) -> list[Word]:
        """返回未消散的文字（alpha > 0）。"""
        from utils.helpers import is_word_alive
        all_words = self.get_words(page_id)
        return [w for w in all_words if not w.is_deleted and is_word_alive(
            w.create_timestamp, w.life_total_sec, w.revive_count)]

    def update_word(self, word: Word):
        with self._lock:
            conn = self._connect()
            conn.execute(
                "UPDATE words SET content=?, x=?, y=?, font_size=?, "
                "life_total_sec=?, revive_count=?, create_timestamp=?, "
                "is_deleted=?, dissolved_to_dot=?, dissolved_x=?, dissolved_y=? "
                "WHERE word_id=?",
                (
                    word.content, word.x, word.y, word.font_size,
                    word.life_total_sec, word.revive_count, word.create_timestamp,
                    int(word.is_deleted),
                    int(word.dissolved_to_dot), word.dissolved_x, word.dissolved_y,
                    word.word_id,
                ),
            )
            conn.commit()
            conn.close()

    def delete_word(self, word_id: int):
        with self._lock:
            conn = self._connect()
            conn.execute("UPDATE words SET is_deleted=1 WHERE word_id=?", (word_id,))
            conn.commit()
            conn.close()

    def update_word_position(self, word_id: int, x: float, y: float):
        """仅更新单字在纸面上的坐标（中间插入/删除后重排版用）。"""
        with self._lock:
            conn = self._connect()
            conn.execute("UPDATE words SET x=?, y=? WHERE word_id=?", (x, y, word_id))
            conn.commit()
            conn.close()

    def batch_update_word_positions(self, positions: list[tuple[int, float, float, int]]):
        """批量更新多个文字的坐标和顺序（优化重排版性能）。"""
        if not positions:
            return
        with self._lock:
            conn = self._connect()
            conn.executemany(
                "UPDATE words SET x=?, y=?, order_index=? WHERE word_id=?",
                [(x, y, order_idx, word_id) for word_id, x, y, order_idx in positions]
            )
            conn.commit()
            conn.close()

    def total_words_on_page(self, page_id: int) -> int:
        alive = self.get_alive_words(page_id)
        return sum(len(w.content) for w in alive if w.content != '\n')

    def total_revives_on_page(self, page_id: int) -> int:
        with self._lock:
            conn = self._connect()
            row = conn.execute(
                "SELECT SUM(revive_count) FROM words WHERE page_id=? AND is_deleted=0",
                (page_id,),
            ).fetchone()
            conn.close()
        return row[0] or 0

    def total_dissolved_words(self) -> int:
        with self._lock:
            conn = self._connect()
            row = conn.execute(
                "SELECT COUNT(*) FROM words WHERE dissolved_to_dot=1"
            ).fetchone()
            conn.close()
        return row[0] or 0

    def total_lost_words(self) -> int:
        """所有消散字数总和。"""
        with self._lock:
            conn = self._connect()
            row = conn.execute(
                "SELECT COALESCE(SUM(LENGTH(content)), 0) FROM words "
                "WHERE dissolved_to_dot=1 AND is_deleted=0"
            ).fetchone()
            conn.close()
        return row[0] or 0

    def wordcloud_weights(self, search: str = "") -> list[tuple[str, float]]:
        """
        归档馆“字迹云”的单字频率权重（方案①）。
        遍历所有未删除文字，逐字计数；不做长度过滤、不分词、不做 n-gram。
        search 非空时，仅统计内容命中检索的文字。
        返回 [(单字, 出现频次)]，按频次降序，最多 120 个。
        """
        with self._lock:
            conn = self._connect()
            if search:
                rows = conn.execute(
                    "SELECT content FROM words WHERE is_deleted=0 "
                    "AND content != '' AND content LIKE ?",
                    (f"%{search}%",),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT content FROM words WHERE is_deleted=0 AND content != ''"
                ).fetchall()
            conn.close()
        from collections import Counter
        freq: "Counter" = Counter()
        for (content,) in rows:
            for ch in content:
                if ch.isspace():
                    continue
                freq[ch] += 1
        if not freq:
            return []
        return [(ch, float(cnt)) for ch, cnt in freq.most_common(120)]

    # ---- Comments ----
    def add_comment(self, comment: Comment) -> int:
        now = time.time()
        with self._lock:
            conn = self._connect()
            cur = conn.execute(
                "INSERT INTO comments (page_id, content, x, y, rotate_angle, base_alpha, "
                "font_size, font_path, unlock_type, unlock_time, keyword_match, hover_count) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)",
                (
                    comment.page_id, comment.content, comment.x, comment.y,
                    comment.rotate_angle, comment.base_alpha, comment.font_size,
                    comment.font_path, comment.unlock_type, now, comment.keyword_match,
                ),
            )
            cid = cur.lastrowid
            conn.commit()
            conn.close()
        return cid

    def get_comments(self, page_id: int) -> list[Comment]:
        with self._lock:
            conn = self._connect()
            rows = conn.execute(
                "SELECT * FROM comments WHERE page_id = ? AND is_overwrite_dead = 0 "
                "ORDER BY comment_id",
                (page_id,),
            ).fetchall()
            conn.close()
        result = []
        for r in rows:
            d = dict(r)
            result.append(Comment(**{k: v for k, v in d.items()
                                     if k in Comment.__dataclass_fields__}))
        return result

    def count_comments_by_type(self, page_id: int, unlock_type: int) -> int:
        """统计某页指定解锁类型（2=语义 / 3=深层尘封）的批注数量。"""
        with self._lock:
            conn = self._connect()
            row = conn.execute(
                "SELECT COUNT(*) AS n FROM comments "
                "WHERE page_id = ? AND unlock_type = ? AND is_overwrite_dead = 0",
                (page_id, unlock_type),
            ).fetchone()
            conn.close()
        return int(row["n"]) if row else 0

    def update_comment(self, comment: Comment):
        """更新批注（is_overwrite_dead 标记等）。"""
        with self._lock:
            conn = self._connect()
            conn.execute(
                "UPDATE comments SET is_overwrite_dead=? WHERE comment_id=?",
                (int(comment.is_overwrite_dead), comment.comment_id),
            )
            conn.commit()
            conn.close()

    def mark_comment_dead(self, comment_id: int):
        """标记批注为被淘汰（逻辑删除，不物理删除）。"""
        with self._lock:
            conn = self._connect()
            conn.execute(
                "UPDATE comments SET is_overwrite_dead=1 WHERE comment_id=?",
                (comment_id,),
            )
            conn.commit()
            conn.close()

    def delete_comment(self, comment_id: int):
        """物理删除批注。"""
        with self._lock:
            conn = self._connect()
            conn.execute("DELETE FROM comments WHERE comment_id=?", (comment_id,))
            conn.commit()
            conn.close()

    def delete_page_comments(self, page_id: int):
        """物理删除某页全部批注（正文不足阈值时清理陈旧数据）。"""
        with self._lock:
            conn = self._connect()
            conn.execute("DELETE FROM comments WHERE page_id=?", (page_id,))
            conn.commit()
            conn.close()

    def page_ever_had_words(self, page_id: int) -> bool:
        """该页是否曾经落过字（含已自然消散、未物理删除的字）。

        用于区分空状态文案：
        - 自然消散的字 is_deleted=0、dissolved_to_dot=1 → 命中，呈现"曾写全散"专属文案；
        - 被用户主动物理删除的字 is_deleted=1 → 不命中，回落为"从未写过"通用引导。
        """
        with self._lock:
            conn = self._connect()
            n = conn.execute(
                "SELECT COUNT(*) FROM words WHERE page_id=? AND is_deleted=0",
                (page_id,),
            ).fetchone()[0]
            conn.close()
        return n > 0

    def increment_comment_hover(self, comment_id: int):
        """批注被悬停时，hover_count+1。（用于淘汰优先级判断）"""
        with self._lock:
            conn = self._connect()
            conn.execute(
                "UPDATE comments SET hover_count=hover_count+1 WHERE comment_id=?",
                (comment_id,),
            )
            conn.commit()
            conn.close()

    def get_comment_revives_by_keyword(self, page_id: int, keyword: str) -> int:
        """统计某关键词对应的文字在该页面的累计续命次数（用于 Tier3 批注解锁检测）。"""
        with self._lock:
            conn = self._connect()
            row = conn.execute(
                "SELECT COALESCE(SUM(revive_count), 0) FROM words "
                "WHERE page_id=? AND is_deleted=0 AND content LIKE ?",
                (page_id, f"%{keyword}%"),
            ).fetchone()
            conn.close()
        return row[0] or 0

    def comment_count_on_page(self, page_id: int) -> int:
        with self._lock:
            conn = self._connect()
            row = conn.execute(
                "SELECT COUNT(*) FROM comments WHERE page_id = ? AND is_overwrite_dead = 0",
                (page_id,)
            ).fetchone()
            conn.close()
        return row[0] or 0

    def get_evictable_comment(self, page_id: int) -> int | None:
        """按淘汰优先级返回可淘汰的 comment_id。
        优先级严格排序：unlock_time最早 → hover_count=0 → keyword_match为空。"""
        with self._lock:
            conn = self._connect()
            candidates = [dict(r) for r in conn.execute(
                "SELECT comment_id, hover_count, keyword_match, unlock_time FROM comments "
                "WHERE page_id=? AND is_overwrite_dead=0 ORDER BY unlock_time ASC",
                (page_id,)
            ).fetchall()]
            conn.close()
            if not candidates:
                return None
            def _evict_score(c):
                s = c["unlock_time"] * 1000
                s += (1 if c["hover_count"] == 0 else 1000)
                s += (1 if not c["keyword_match"] else 1000)
                return s
            candidates.sort(key=_evict_score)
        return candidates[0]["comment_id"] if candidates else None

    # ---- Settings ----
    def get_setting(self, key: str, default: str = "") -> str:
        with self._lock:
            conn = self._connect()
            row = conn.execute(
                "SELECT value FROM settings WHERE key = ?", (key,)
            ).fetchone()
            conn.close()
        return row["value"] if row else default

    def set_setting(self, key: str, value: str):
        with self._lock:
            conn = self._connect()
            conn.execute(
                "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
                (key, value),
            )
            conn.commit()
            conn.close()

    # ---- 导入字体（手写体） ----
    def get_imported_fonts(self) -> list:
        """返回用户导入的手写字体列表：[{'path':..., 'family':...}, ...]"""
        raw = self.get_setting("imported_fonts", "[]")
        try:
            data = json.loads(raw)
            if isinstance(data, list):
                return [d for d in data if isinstance(d, dict) and d.get("path")]
        except Exception:
            pass
        return []

    def add_imported_font(self, path: str, family: str) -> bool:
        """记录一个导入的手写字体；已存在同路径则忽略。返回是否为新添加。"""
        fonts = self.get_imported_fonts()
        norm = os.path.normpath(path)
        if any(os.path.normpath(f.get("path", "")) == norm for f in fonts):
            return False
        fonts.append({"path": path, "family": family})
        self.set_setting("imported_fonts", json.dumps(fonts, ensure_ascii=False))
        return True

    def remove_imported_font(self, path: str) -> bool:
        """按路径移除一个导入字体；返回是否真有移除。"""
        fonts = self.get_imported_fonts()
        norm = os.path.normpath(path)
        new = [f for f in fonts if os.path.normpath(f.get("path", "")) != norm]
        if len(new) == len(fonts):
            return False
        self.set_setting("imported_fonts", json.dumps(new, ensure_ascii=False))
        return True

    def clear_cache(self):
        """清除残影渲染缓存等临时数据（不影响页面/批注/设置）。"""
        # 1. 删除 data 目录下的临时文件
        data_dir = os.path.dirname(self._path)
        if os.path.isdir(data_dir):
            for f in os.listdir(data_dir):
                if f.endswith(".cache") or f.startswith("tmp_"):
                    try:
                        os.remove(os.path.join(data_dir, f))
                    except OSError:
                        pass


# Global instance
db = DB()
