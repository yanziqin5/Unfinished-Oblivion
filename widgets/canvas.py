"""
《未完成·遗忘》画布 —— 氛围升级版。
六层分层渲染 + 纸纤维纹理 + 黄斑折痕 + 墨水氧化 + 笔画残缺
+ 文字消散粒子 + 预置淡残影 + 动态暖柔光 + 封存暗角复古滤镜
+ 旧主人魂魄批注（停笔时自动苏醒） + 漂浮尘埃粒子。
"""
import math
import time
import random
import os
import hashlib
import threading
from typing import Optional

from PyQt5.QtCore import (
    Qt, QTimer, pyqtSignal, QPointF, QUrl, QPoint, QRectF, QRect,
)
from PyQt5.QtGui import QInputMethodEvent
from PyQt5.QtGui import (
    QPainter, QColor, QFont, QPen, QBrush, QFontMetrics,
    QRadialGradient, QLinearGradient, QImage,
    QPixmap,
)
from PyQt5.QtWidgets import QWidget, QApplication

from utils.constants import (
    SERIF_FONT, SERIF_FONT_FALLBACK, BODY_FONT_SIZE,
    TEXT_COLOR, HINT_TEXT_COLOR, HINT_TEXT_COLOR_DARK, INK_FRESH,
    GHOST_TEXT_COLOR,
    BG_YELLOW_1,
    BG_DEFAULT,
    PAPER_BG_MAP, PAPER_BG_HEX,
    WRITING_AREA_MARGIN,
    DURATION_BREATHING_CYCLE,
    DURATION_LIGHT_SWEEP, DURATION_TEXTURE_DRIFT,
    DURATION_COMMENT_STROKE,
    HOVER_HOLD_MS, REVIVE_HOVER_MIN_ALPHA,
    LINE_STEP,
    GHOST_MAX_DOTS, \
    GHOST_DUST_COLORS, GHOST_DUST_RADIUS_MIN, GHOST_DUST_RADIUS_MAX,
    DECAY_LINE_COLOR, DECAY_LINE_ALPHA,
    DECAY_LINE_COLOR_LIGHT, DECAY_LINE_ALPHA_LIGHT,
    WARNING_LINE_COLOR, WARNING_LINE_ALPHA,
    WARNING_LINE_COLOR_LIGHT, WARNING_LINE_ALPHA_LIGHT,
    TERMINAL_GLOW_DARK, TERMINAL_GLOW_LIGHT,
    PLACEHOLDER_SAMPLES,
    COMMENT_MAX_COUNT, PAUSE_DETECTION_MS, MIN_CHARS_FOR_COMMENT, COMMENT_COOLDOWN_MS,
    COMMENT_COLOR, COMMENT_COLOR_DARK,
    COMMENT_GUTTER_RATIO, COMMENT_BASE_ALPHA_MIN, COMMENT_BASE_ALPHA_MAX,
    HANDWRITING_FONT_FAMILIES,

    DUST_PARTICLE_MAX, DUST_PARTICLE_COUNT,

    LIGHT_SWEEP_CENTER_X_AMPLITUDE, LIGHT_SWEEP_CENTER_Y_BASE,
    LIGHT_SWEEP_RADIUS, LIGHT_SWEEP_COLOR, LIGHT_SWEEP_ALPHA_MAX,
    LIGHT_SWEEP_COLOR_DARK, LIGHT_SWEEP_ALPHA_MAX_DARK,
    SEALED_OVERLAY_COLOR, SEALED_OVERLAY_ALPHA,
    SEALED_VIGNETTE_INTENSITY,
    DARK_BG_CANVAS, DARK_HINT, EPIGRAPH_COLOR_LIGHT,
    WINDOW_BORDER_LIGHT, WINDOW_BORDER_DARK, BORDER_OPACITY_LOW,
    EMPTY_HINTS, EMPTY_HINTS_FADED,
    GHOST_PHRASES, GHOST_PHRASES_DAWN, GHOST_PHRASES_DUSK, GHOST_PHRASES_NIGHT,
    TOAST_REVIVED, TOAST_REVIVE_CAPPED, TOAST_REVIVE_LAST, TOAST_DISSOLVE_FINAL,
    TOAST_UNSEALING_PROGRESS,
    TOAST_FONT_FALLBACK, TOAST_COMMENT_ADDED, TOAST_EXPORTED, TOAST_COMMENT_EVICTED,
    REVIVE_TOASTS,
    CURSOR_COLOR, CURSOR_COLOR_DARK, CURSOR_GLOW_COLOR, CURSOR_GLOW_COLOR_DARK,
    FROST_BASE, FROST_BASE_DARK, FROST_GRAIN, FROST_GRAIN_DARK,
    FROST_LIGHT, FROST_LIGHT_DARK,
    STAR_COUNT, STAR_LIGHT_COLOR,
    # 纸张纹理相关
    FIBER_COLOR_BASE, FIBER_DRIFT_AMPLITUDE,
    CREASE_COLOR, CREASE_WIDTH,
    PAPER_GRAIN_OPACITY, PAPER_GRAIN_TILE,
    # === 文字生命周期 ===
    LIFE_BASE_SEC, LIFE_END_WARN_RATIO, GAZE_REVIVE_ALPHA, REVIVE_MAX_COUNT,
    GAZE_REVIVE_SPEED, FADE_DECAY_SPEED, REVIVE_FLASH_DURATION,
    TEXT_GRAYSCALE_THRESHOLD, TEXT_GRAYSCALE_MAX_FACTOR,
    # === 纸面积淀温度 ===
    PAPER_WARMTH_PER_CHAR, PAPER_WARMTH_MAX, PAPER_WARMTH_PER_SECOND, PAPER_WARMTH_COOL_PER_SECOND,
    # === 三层解锁体系 ===
    TIER1_UNLOCK_PROB,
    TOAST_TIER1_UNLOCK, TOAST_TIER2_UNLOCK, TOAST_TIER3_UNLOCK,
    TIER2_KEYWORDS,
    TIER3_MIN_SENTENCE_CHARS, TIER3_KEYWORD_REPEAT, TIER3_MIN_REVIVES,
    TIER3_MAX_PAGE_TURNS, TIER3_PAGE_TURN_DURATION_MS,     TIER3_MAX_PER_PAGE,
    # === 性能分级 & 颜色体系统一 ===
    PerfTier,
    PAPER_CACHE_REFRESH_INTERVAL,
    CANVAS_BORDER_COLOR_DARK, CANVAS_BORDER_COLOR_LIGHT,
    PAGE_CONTENT_BG_DARK, PAGE_CONTENT_BG_LIGHT,
    DUST_COLOR_LIGHT, DUST_COLOR_DARK,
    SEALED_GRAIN_RGB_DARK, SEALED_GRAIN_RGB_LIGHT, SEALED_GRAIN_ALPHA,
    SEALED_OVERLAY_LIGHT_RGB, SEALED_OVERLAY_LIGHT_ALPHA, SEALED_LOWLIGHT_RGB,
    SEALED_SEPIA_LIGHT, SEALED_SEPIA_DARK,
    SEALED_HIGHLIGHT_LIGHT, SEALED_HIGHLIGHT_DARK,
    SEALED_HALO_LIGHT, SEALED_HALO_DARK,
    TEXT_HALO_RGB_DARK,
    PAGE_TURN_COLOR,
    COMMENT_INK_LIGHT, COMMENT_INK_DARK,
)
from utils.helpers import (
    compute_alpha,
    get_word_warning_stage, revive_word,
    breathing_alpha_for_display,
    compute_afterglow_alpha,
    get_ink_oxidation_color, get_eroded_alpha,
    generate_dissolve_particles,
    generate_dust_particles,
    generate_fiber_lines,
    generate_stains,
    generate_creases,
    get_paper_grain,
    get_day_period, get_daynight_bg_color,
    compute_particle_limits,
    get_dying_grayscale_color, lerp_hex_colors,
)
from utils.db import db
from utils.ai_client import ai_client


class CanvasWidget(QWidget):
    """核心画布组件。"""

    # 信号
    word_revived = pyqtSignal()              # 文字被续命
    comment_added = pyqtSignal()             # 批注被添加
    toast_requested = pyqtSignal(str)        # 请求显示 Toast
    char_count_changed = pyqtSignal(int)     # 字数变化
    unseal_requested = pyqtSignal(int)       # 请求解封页面（page_id）

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setAttribute(Qt.WidgetAttribute.WA_InputMethodEnabled, True)
        self.setCursor(Qt.CursorShape.IBeamCursor)

        # 思源宋体回退：检查字体是否可用，不可用则降级 SimSun
        from PyQt5.QtGui import QFontDatabase
        available = QFontDatabase().families()
        if SERIF_FONT in available:
            self._serif_font = SERIF_FONT
        else:
            self._serif_font = SERIF_FONT_FALLBACK

        # 正文手写字体在 _imported_fonts 初始化后再解析（含本地 ttf / 系统手写字体）
        self._body_handwriting_font = None

        # ---- 页面状态 ----
        self.page_id: int = 0
        self.is_sealed: bool = False
        self._paper_type: str = "黄1"
        self._paper_bg_img: QImage | None = None

        # ---- 文字数据 ----
        self._words: list = []           # list of dict from db
        self._comments: list = []        # list of Comment
        self._char_count: int = 0

        # ---- 键盘输入 ----
        self._input_buffer: str = ""
        self._input_x: float = WRITING_AREA_MARGIN + 4
        self._input_y: float = WRITING_AREA_MARGIN + 24
        self._cursor_index: int = 0          # 光标在文字序列中的插入位置（0..len(_words)）
        self._cursor_visible: bool = True

        # ---- 鼠标/悬停续命 ----
        self._hover_word_idx: int = -1
        self._ghost_cache = None
        self._ghost_cache_t = 0.0
        self._hover_hold_timer: float = 0.0
        self._hover_active: bool = False
        self._revive_flash: float = 0.0          # 续命提亮当前强度（绘制用，0=无）
        self._revive_flash_word_idx: int = -1     # 最近续命/提亮的字索引（用于柔和回润）
        self._revive_flash_t: float = 0.0         # 续命回润脉冲已播放时间（秒）
        self._revive_flash_peak: float = 0.0      # 续命回润脉冲峰值强度
        self._display_alpha_cache: dict = {}  # 悬停透明度动画缓存 {word_idx: current_alpha}

        # ---- 动画时间基准 ----
        self._anim_time: float = 0.0

        # ---- 星空背景（深色模式）：归一化坐标，绘制时映射当前尺寸 ----
        _srng = random.Random(20260607)
        self._stars = [
            (_srng.random(), _srng.random(),
             0.5 + _srng.random() * 1.7,
             _srng.random() * math.pi * 2,
             0.55 + _srng.random() * 0.45)
            for _ in range(STAR_COUNT)
        ]
        # 星空背景缓存：避免每帧重绘 150 个星点；仅在尺寸/模式变化或节流间隔时重渲染
        self._star_cache: Optional[QPixmap] = None
        self._star_cache_w: int = 0
        self._star_cache_h: int = 0
        self._star_cache_dark: object = None
        self._star_cache_t: float = 0.0

        # ---- 纸张纹理静态缓存（避免每帧重绘纤维/黄斑/折痕/底色，静态内容预渲染为 QPixmap）----
        self._paper_cache: Optional[QPixmap] = None
        self._paper_cache_w: int = 0
        self._paper_cache_h: int = 0
        self._paper_cache_key: object = None
        self._paper_cache_t: float = 0.0

        # ---- 垂直无限滚动（视图偏移 + 柔和缓动）----
        # 画布单张无分页，文字从上至下无限延伸；滚动仅移动视口，内容坐标不变。
        # 旧文字滑出屏幕只是"远去"，数据不丢，滚回仍保留褪色状态。
        self._scroll_y: float = 0.0            # 当前已施加的滚动偏移（内容相对视图）
        self._scroll_target: float = 0.0       # 缓动目标偏移
        self._scroll_timer = QTimer(self)
        self._scroll_timer.timeout.connect(self._on_scroll_tick)

        # ---- 消散粒子 ----
        self._dissolve_particles: list = []  # List[DissolveParticle]

        # ---- 漂浮尘埃 ----
        self._dust_particles: list = []
        self._atmosphere_enabled: bool = True

        # ---- 纸纤维纹理 ----
        self._fiber_lines: list = []
        self._stains: list = []
        self._creases: list = []
        self._texture_seeded: bool = False

        # ---- 预置淡残影 ----
        self._ghost_phrases_data: list = []  # [(x, y, text, alpha, phase)]
        self._last_ghost_period: str = ""    # 上一帧的时辰，用于切换残影

        # ---- 空提示轮播 ----
        self._empty_hint_index: int = 0
        self._empty_hint_alpha: float = 1.0   # 当前提示 alpha
        self._empty_hint_timer: float = 0.0   # 轮播计时器
        self._empty_hint_fading: bool = False
        self._empty_hint_phase: float = 0.0    # 随机起点相位，使每页起始句不同

        # ---- 纸面积淀温度 ----
        self._paper_warmth: float = 0.0       # 0~PAPER_WARMTH_MAX
        self._ever_had_words: bool = False     # 本页是否曾有过字（区分"曾写全散"与"从未写"的空状态文案）

        # ---- 深色模式 ----
        self._dark_mode: bool = False

        # ---- 窗口边框（左/右）：恒定暖灰，由画布自绘（不再随悬停明暗跳变，避免"跳动"）----
        self._border_opacity: float = BORDER_OPACITY_LOW

        # ---- 纯画布模式 ----
        self._pure_mode: bool = False

        # ---- 手写体模式（默认开启：画布文字默认手写体） ----
        self._use_handwriting: bool = db.get_setting("use_handwriting", "1") == "1"

        # ---- 用户导入的手写字体（族名列表，渲染时作为 QFont 家族） ----
        self._imported_fonts: list = []

        # 解析正文手写字体（含本地 ttf / 导入字体 / 系统手写字体）；无则保持 None 回退宋体
        try:
            self._body_handwriting_font = self._resolve_handwriting_family()
        except Exception:
            self._body_handwriting_font = None

        # ---- 性能模式 ----
        setting = db.get_setting("perf_tier", PerfTier.HIGH)
        self._perf_tier: str = setting if setting in PerfTier.__dict__.values() else PerfTier.HIGH
        self._particle_limits: dict = {'dust': DUST_PARTICLE_MAX, 'ghost': GHOST_MAX_DOTS,
                                        'star': STAR_COUNT, 'dissolve_max': 60}
        self._perf_frame_counter: int = 0

        # ---- 光标 ----

        # ---- 批注浮现动画 ----
        self._comment_anim: dict = {}  # comment_id -> float 0~1

        # ---- 页面载入淡入动画 ----
        self._page_load_alpha: float = 0.0
        self._page_load_active: bool = False
        self._page_load_text: str = ""

        # ---- 主渲染定时器（60fps） ----
        self._ticker = QTimer(self)
        self._ticker.setInterval(16)  # ~60fps
        self._ticker.timeout.connect(self._tick)
        self._last_tick_time = time.perf_counter()
        self._pending_positions: list = []
        self._positions_dirty: bool = False
        self._last_pos_persist: float = 0.0
        self._ticker.start()

        # ---- 自然死亡文字追踪 ----
        self._dead_word_ids: set = set()  # 已处理过死亡粒子效果的文字ID

        # ---- 停笔检测（旧主人魂魄苏醒） ----
        self._pause_timer = QTimer(self)
        self._pause_timer.setSingleShot(True)
        self._pause_timer.setInterval(PAUSE_DETECTION_MS)
        self._pause_timer.timeout.connect(self._on_typing_pause)
        self._last_comment_time: float = 0.0
        self._shutting_down: bool = False

        # ---- 输入光标激活（点击画布前不显示光标）----
        self._cursor_user_activated: bool = False

        # ---- 三层解锁体系 ----
        self._page_turn_count: int = 0           # 本页翻页动画次数（≤3）
        self._page_turn_anim: float = 0.0        # 翻页动画进度 0→1
        self._page_turn_active: bool = False
        self._hovered_comment_id: int = -1        # 正在悬停的批注 ID
        self._prev_hovered_comment_id: int = -1   # 上一帧的悬停批注（用于检测离开）
        self._comment_alpha_cache: dict = {}      # 批注悬停透明度动画缓存 {comment_id: current_alpha}
        self._gaze_revive_count: int = 0          # 当前页凝视续命累计次数
        self._last_add_time: float = 0.0          # 上一次落字时间（用于连续输入共享寿命）
        self._current_batch_life: float = 0.0     # 当前连续输入批次的基准寿命
        self._gazed_word_idx: int = -1            # 当前凝视会话已计数的字索引（防重复计数）
        self._drag_candidate: bool = False        # 空白处按下，可能是拖拽窗口或点击定位
        self._drag_press: QPoint = QPoint(0, 0)
        self._window_dragging: bool = False
        self._win_drag_offset: QPoint = QPoint(0, 0)

        # ---- resize 节流：避免快速拖动窗口时连续重排 ----
        self._reflow_throttle_timer = QTimer(self)
        self._reflow_throttle_timer.setSingleShot(True)
        self._reflow_throttle_timer.setInterval(150)  # 150ms 防抖
        self._reflow_throttle_timer.timeout.connect(self._on_resize_throttled)

        # ---- 长按解封 ----
        self._unseal_pressing: bool = False     # 是否正在长按封存覆盖层
        self._unseal_press_pos: QPoint = QPoint(0, 0)
        self._unseal_hold_time: float = 0.0     # 已按住时间（秒）
        self._unseal_progress: float = 0.0      # 0~1 解封进度

        # ---- 昼夜纸色调 ----
        self._daynight_color: str = get_daynight_bg_color()
        self._daynight_check_counter: int = 0
        self._pending_comments: list = []          # 线程安全：子线程创建的批注在此排队，_tick 处理
        self._pending_comments_lock = threading.Lock()  # 保护 _pending_comments 的线程锁
        self._deferred_unlocks: list = []          # 延迟解锁队列（翻页/关闭时冲出）
        self._deferred_keys: set = set()           # 延迟解锁去重键
        self._typed_pages: set = set()             # 已打过字的页面（占位示例不再出现）
        self._placeholder_alpha: float = 0.0       # 占位示例文字透明度（1=显示，0=消失）
        self._placeholder_fading: bool = False     # 占位示例是否正在淡出
        self._placeholder_text: str = ""           # 本页选定的占位示例（随机，避免每页同句）

    # ========== 公共 API ==========

    def set_page(self, page_id: int, paper_type: str = "黄1",
                 is_sealed: bool = False, is_new_page: bool = False,
                 show_placeholder: bool = False):
        """加载/切换页面。is_new_page=True 时 100% 生成初始浅层批注。"""
        # 切页前：先把延迟的批注解锁冲出（归属旧页面），
        # 制造"翻页/关闭后才偶然发现"的错愕感，避免精确归因。
        self._deferred_unlocks = getattr(self, '_deferred_unlocks', [])
        self._deferred_keys = getattr(self, '_deferred_keys', set())
        self._typed_pages = getattr(self, '_typed_pages', set())
        self._flush_positions()
        self._flush_deferred_unlocks()
        self.page_id = page_id
        self._paper_type = paper_type
        self.is_sealed = is_sealed
        self._is_new_page = is_new_page
        self._load_paper_image()
        self._refresh_words()
        self._comment_anim.clear()
        self._refresh_comments()
        self._seed_texture()
        self._seed_ghost_phrases()
        self._dissolve_particles.clear()
        # 占位示例文字"去年冬天…"仅在软件【首次启动】出现一次；
        # 之后（新建页 / 重置 / 其它启动）一律只显示画布中央的空状态文案。
        first_launch = db.get_setting("first_launch_done", "0") != "1"
        if show_placeholder and first_launch and self.page_id not in self._typed_pages and len(self._words) == 0:
            self._placeholder_alpha = 1.0
            self._placeholder_text = PLACEHOLDER_SAMPLES[0]
            db.set_setting("first_launch_done", "1")
        else:
            self._placeholder_alpha = 0.0
        # 空提示轮播随机起点：每打开一页都从不同句子开始（之后再轮播变换）
        if EMPTY_HINTS:
            self._empty_hint_phase = random.randrange(len(EMPTY_HINTS)) * 8.0
        self._placeholder_fading = False
        # 延迟解锁队列（本页切换时已在上方 flush）
        self._deferred_unlocks = []
        self._deferred_keys = set()
        self._input_buffer = ""
        self._hover_word_idx = -1
        self._ghost_cache = None
        self._hover_hold_timer = 0
        self._hover_active = False
        self._anim_time = 0
        self._last_tick_time = time.perf_counter()  # 真实耗时追踪，消除主题间帧率差异
        # 光标置于文末（继续书写）
        self._cursor_index = len(self._words)
        self._sync_cursor(scroll_into_view=False)
        # 滚动到光标位置，确保光标可见
        self._ensure_cursor_visible()
        # 重置停笔检测状态
        self._pause_timer.stop()
        self._last_comment_time = 0.0
        # 重置三层解锁状态
        self._page_turn_count = 0
        self._page_turn_anim = 0.0
        self._page_turn_active = False
        self._dead_word_ids.clear()
        self._hovered_comment_id = -1
        self._prev_hovered_comment_id = -1
        self._gaze_revive_count = db.total_revives_on_page(page_id)  # 凝视累计
        
        # 启动页面载入淡入动画
        self._page_load_alpha = 0.0
        self._page_load_active = True
        self._page_load_text = self._get_load_narrative(is_new_page, is_sealed)
        
        self.setFocus()
        self.update()

        # === Tier 1：新建空白页 100% 生成初始浅层批注；其余页按 30% 概率解锁旧主人批注 ===
        if not self.is_sealed:
            if self._is_new_page:
                QTimer.singleShot(600, lambda: self._try_tier1_unlock(self.page_id))
            elif len(self._words) > 0 and random.random() < TIER1_UNLOCK_PROB:
                QTimer.singleShot(600, lambda: self._try_tier1_unlock(self.page_id))

    def _get_load_narrative(self, is_new_page: bool, is_sealed: bool) -> str:
        """生成页面载入时的叙事提示文案——充满文学气息的短句。"""
        if is_new_page:
            narratives = [
                "新的一页，等待书写...",
                "空白的纸张，准备承载记忆",
                "时间在此展开新的篇章",
                "落笔前的寂静",
                "等待被记录的瞬间",
                "白纸如雪，未染墨痕",
                "这一刻，一切尚未发生",
                "面对空白，即是面对无限可能",
                "第一笔落下之前，世界是安静的",
                "崭新的页码，如同初雪",
            ]
        elif is_sealed:
            narratives = [
                "记忆已封存，静静沉睡",
                "这些文字曾鲜活过",
                "时间在此停驻",
                "被锁住的故事",
                "封存的过往",
                "封印之下，字迹永恒",
                "仿佛合上了一本旧书",
                "这些句子不再老去",
                "被保存的，不仅是文字",
                "封存的温度，尚有余温",
            ]
        else:
            narratives = [
                "旧纸重翻，字迹依稀",
                "昨日的文字，今日的回忆",
                "重新触摸这些痕迹",
                "时光流转，墨迹尚存",
                "翻开旧页，重温旧梦",
                "那些未完成的片段",
                "墨色浅了，心事却还在",
                "像打开了一个尘封的信封",
                "字里行间，还有当时的温度",
                "有些话，隔了许久才重新读到",
                "纸张微黄，记忆犹新",
                "翻开的不只是一页，还有一段时日",
            ]
        return random.choice(narratives)

    def get_save_narrative(self) -> str:
        """存档时的叙事文案——每次保存时随机一句。"""
        narratives = [
            "写下的字，从此有了归处",
            "这一页被小心地收好了",
            "墨迹未干，已存入时光",
            "存档完毕。字迹将安然沉睡",
            "你写下的，都会被记住",
            "保存了这一页的呼吸",
            "如同合上一本笔记本，轻轻放回书架",
            "这些字不会消失——至少在存档里",
            "一份安静的备份",
            "锁住了此刻",
        ]
        return random.choice(narratives)

    def set_dark_mode(self, enabled: bool):
        self._dark_mode = enabled
        self.update()

    def set_atmosphere(self, enabled: bool):
        self._atmosphere_enabled = enabled
        if not enabled:
            self._dust_particles.clear()
        else:
            self._seed_dust()
        self.update()

    def set_tone(self, tone: str):
        """文风切换（仅供 Toolbar 绑定）。"""
        self._tone = tone

    # 品牌手写体（应用签名字体）：批注与文案固定使用，不随正文导入字体改变
    BRAND_FONT_FILE = "张穸洛浮生楷体.ttf"

    def _brand_font_family(self) -> str:
        """返回品牌手写体(张穸洛浮生楷体)的字体族名；加载失败时回退宋体。
        批注与文案固定使用此字体，不受正文导入字体影响。"""
        cached = getattr(self, '_brand_font_family_cached', None)
        if cached:
            return cached
        fam = self._serif_font
        try:
            import os
            from PyQt5.QtGui import QFontDatabase
            base = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "fonts")
            path = os.path.join(base, self.BRAND_FONT_FILE)
            if os.path.isfile(path):
                fid = QFontDatabase.addApplicationFont(path)
                if fid >= 0:
                    fams = QFontDatabase.applicationFontFamilies(fid)
                    if fams:
                        fam = fams[0]
        except Exception:
            pass
        self._brand_font_family_cached = fam
        return fam

    def _load_local_fonts(self):
        """加载 assets/fonts 下的所有字体文件（.ttf/.otf/.ttc）并登记为默认手写字体池。"""
        import os
        from PyQt5.QtGui import QFontDatabase
        try:
            base = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "fonts")
            if not os.path.isdir(base):
                self._local_font_families = []
                return
            exts = (".ttf", ".otf", ".ttc")
            fams = []
            for name in sorted(os.listdir(base)):
                if name.lower().endswith(exts):
                    fid = QFontDatabase.addApplicationFont(os.path.join(base, name))
                    if fid >= 0:
                        fams.extend(QFontDatabase.applicationFontFamilies(fid))
            if fams:
                self._local_font_families = fams
                self._local_fonts_loaded = True   # 仅成功加载才标记；失败则下次重试
        except Exception:
            pass

    def _resolve_handwriting_family(self):
        """解析一个可用的手写/书法字体族：导入字体 > 本地 fonts 字体 > 系统精确匹配 > 模糊匹配。"""
        from PyQt5.QtGui import QFontDatabase
        # 1) 用户导入手写字体（最高优先级）
        if self._imported_fonts:
            return self._imported_fonts[0]
        # 2) 本地字体资源（assets/fonts/ 下所有字体，作为默认手写字体）
        if not getattr(self, '_local_fonts_loaded', False):
            self._load_local_fonts()
        if getattr(self, '_local_font_families', None):
            return self._local_font_families[0]
        # 3) 系统精确匹配
        try:
            avail = set(QFontDatabase().families())
        except Exception:
            return None
        for f in HANDWRITING_FONT_FAMILIES:
            if f in avail:
                return f
        # 4) 模糊匹配：捕捉本机可能存在的书法/手写字体（含中文楷书、行书、隶书等）
        keywords = ("kai", "楷", "xing", "行", "shu", "书", "li", "隶",
                    "zhuan", "篆", "script", "ink", "brush", "comic",
                    "segoe print", "han", "华文", "fz", "st", "founder")
        for fam in avail:
            low = fam.lower()
            if any(k in low for k in keywords):
                return fam
        return None

    def set_handwriting(self, enabled: bool, silent: bool = False):
        """手写体模式切换。只要有可用手写字体（本地 ttf / 导入字体 / 系统手写字体）之一即可启用。"""
        if not enabled:
            self._use_handwriting = False
            self._body_handwriting_font = None
            db.set_setting("use_handwriting", "0")
            self.update()
            return
        fam = None
        # 优先沿用上次在"手写体管理"里选定的正文手写体（已持久化），
        # 若该字体仍可用则用之；否则回退到自动解析（避免重启后正文手写体被重置）。
        saved_family = db.get_setting("default_handwriting_family", "")
        if saved_family:
            from PyQt5.QtGui import QFontDatabase
            try:
                available = set(QFontDatabase().families())
            except Exception:
                available = set()
            if saved_family in available:
                fam = saved_family
        if not fam:
            fam = self._resolve_handwriting_family()
        if fam:
            self._body_handwriting_font = fam
            self._use_handwriting = True
            db.set_setting("use_handwriting", "1")
        else:
            self._use_handwriting = False
            self._body_handwriting_font = None
            db.set_setting("use_handwriting", "0")
            if not silent:
                self.toast_requested.emit(TOAST_FONT_FALLBACK)
        self.update()

    def set_body_handwriting(self, family: str):
        """将正文手写体切换为指定字体族（管理器"应用"时调用）。
        不影响批注与文案（二者固定使用品牌手写体）。
        持久化选择，重启后由 set_handwriting 恢复。"""
        if family:
            self._body_handwriting_font = family
            db.set_setting("default_handwriting_family", family)
        self.update()

    def _body_font(self, size: int):
        """返回当前正文应使用的字体：手写体可用且启用时用手写体，否则宋体。"""
        fam = self._body_handwriting_font if (self._use_handwriting and self._body_handwriting_font) else self._serif_font
        return QFont(fam, size)

    def _copy_font(self, size: int):
        """文案(空状态/占位/toast)固定使用品牌手写体(张穸洛浮生楷体)，不随正文切换。"""
        return QFont(self._brand_font_family(), size)

    def copy_font_family(self) -> str:
        """供画布外文案(如 toast)取用品牌手写体；无则回退宋体。"""
        return self._brand_font_family()

    def _body_metrics(self, size: int):
        """返回当前正文字体对应的度量（用于字宽测量/光标/选区对齐）。"""
        return QFontMetrics(self._body_font(size))

    def set_perf_tier(self, tier: str):
        """设置性能档位；三档直接控制纹理/尘埃/粒子开销。"""
        self._perf_tier = tier
        db.set_setting("perf_tier", tier)
        self._invalidate_paper_cache()
        self._star_cache = None  # 强制重建星场
        if tier == PerfTier.LOW:
            self._dust_particles.clear()
            self._dissolve_particles.clear()
        else:
            self._adapt_particle_limits()
            self._seed_dust()
        self.update()

    def trigger_export(self, params: dict):
        """导出为图片。"""
        self._grab_and_save(params)

    def get_char_count(self) -> int:
        return self._char_count

    def get_comment_count(self) -> int:
        return len(self._comments)

    def has_words(self) -> bool:
        """当前页是否存在可见正文文字（决定批注层是否绘制）。"""
        return bool(self._words)

    # ========== 内部加载 ==========

    def _load_paper_image(self):
        path = PAPER_BG_MAP.get(self._paper_type, "")
        if path and os.path.exists(path):
            self._paper_bg_img = QImage(path)
        else:
            self._paper_bg_img = None
        self._grain_img = None

    def _seed_texture(self):
        """初始化纸张纹理（纤维、黄斑、折痕、细颗粒）。"""
        w = max(self.width(), 100)
        h = max(self.height(), 100)
        seed = hash(self._paper_type + str(self.page_id)) % 10000
        self._fiber_lines = generate_fiber_lines(w, h, seed)
        self._stains = generate_stains(w, h, seed + 1)
        self._creases = generate_creases(w, h, seed + 2)
        # 程序化纸面细颗粒（模块级缓存，复用同一张，几乎零成本）
        self._grain_img = get_paper_grain(PAPER_GRAIN_TILE)
        self._texture_seeded = True

    def _seed_ghost_phrases(self):
        """在空画布上预置淡残影文字。时辰感知：不同时段显示不同残影诗句。"""
        self._ghost_phrases_data.clear()
        if not self._words:
            rng = random.Random(self.page_id + 42)
            ww = max(self.width(), 100)
            wh = max(self.height(), 100)

            # 按当前时辰混合专属残影
            period = get_day_period()
            phrases = GHOST_PHRASES[:]
            if period == "dawn":
                phrases = phrases + GHOST_PHRASES_DAWN
            elif period == "dusk":
                phrases = phrases + GHOST_PHRASES_DUSK
            elif period == "night":
                phrases = phrases + GHOST_PHRASES_NIGHT
            # Day 时段仅用通用残影

            rng.shuffle(phrases)
            margin = 60
            for i, phrase in enumerate(phrases[:4]):
                x = rng.uniform(margin, ww - margin - 200)
                y = rng.uniform(margin + i * 60, wh - margin)
                alpha = rng.uniform(0.04, 0.09)
                phase = rng.random() * math.pi * 2
                self._ghost_phrases_data.append((x, y, phrase, alpha, phase))

            self._last_ghost_period = period
        else:
            self._ghost_phrases_data.clear()

    def _seed_dust(self):
        """按 self._particle_limits['dust'] 补充尘埃（只增不覆盖）。

        这是尘埃数量的**唯一**上限来源：_adapt_particle_limits、showEvent、
        set_perf_tier 都通过它对齐，避免"先按临时状态生成一堆、随后被裁剪"
        造成的启动跳变。
        """
        if not self._atmosphere_enabled:
            return
        target = self._particle_limits['dust']
        need = target - len(self._dust_particles)
        if need > 0:
            w = max(self.width(), 100)
            h = max(self.height(), 100)
            self._dust_particles.extend(generate_dust_particles(w, h, need))

    def _refresh_words(self):
        """从数据库加载当前页面的存活文字。"""
        if self.page_id > 0:
            self._words = db.get_alive_words(self.page_id)
            # 数据库已按 order_index 排序，确保文字的正确顺序
            # 重新计算所有文字的坐标，确保显示位置正确
            self._reflow_from(0, persist=False)
        else:
            self._words = []
        # 重载/切换页面后判定"曾写"标志：
        # - 当前有存活字       → 曾写过
        # - 当前无存活字，但 DB 中该页曾存在字（自然消散）→ 曾写全散，用专属文案
        # - DB 从未有字（或被用户主动物理删除）→ 从未写过，用通用引导
        # 这样"字全散后"才能正确呈现专属空状态文案，而非退回通用引导。
        self._ever_had_words = bool(self._words) or (
            self.page_id > 0 and db.page_ever_had_words(self.page_id)
        )
        self._char_count = sum(len(w.content) for w in self._words if w.content != '\n')
        self.char_count_changed.emit(self._char_count)
        # 纸面积淀温度：保留跨页面累积效果，不再强制重置
        # self._paper_warmth = min(self._char_count * PAPER_WARMTH_PER_CHAR, PAPER_WARMTH_MAX)
        # 光标索引不得超过文字数量
        self._cursor_index = min(self._cursor_index, len(self._words))
        # 加载文字时不强制滚动，由调用方控制滚动行为
        self._sync_cursor(scroll_into_view=False)

    def _refresh_comments(self):
        # 正文不足阈值时不加载历史批注，并清理库内陈旧数据，
        # 避免出现“空/短正文却显示旧批注”的情况。
        if self.page_id > 0 and len(self._words) < MIN_CHARS_FOR_COMMENT:
            self._clear_page_comments()
            return
        if self.page_id > 0:
            self._comments = db.get_comments(self.page_id)
            # 为从数据库加载的批注设置手写字体（如果未设置）
            for c in self._comments:
                if not c.font_path or not c.font_path.strip():
                    c.font_path = self._pick_handwriting_font()
            # 页面载入时为批注设置错峰渐显进度，避免直接弹出：
            # 用负进度充当"延迟"，使批注依次从纸面显出（自带墨迹扩散+淡入）。
            stagger = 0.18
            for idx, c in enumerate(self._comments):
                self._comment_anim[c.comment_id] = -(idx * stagger)
        else:
            self._comments = []

    def _clear_page_comments(self):
        """正文不足阈值（或被清空）时，清理该页全部批注（含数据库），
        使批注始终依附于正文，避免出现“空/短正文却残留陈旧批注”的情况。"""
        pid = self.page_id
        if pid > 0:
            db.delete_page_comments(pid)
        self._comments = []
        self._comment_anim.clear()
        self._comment_alpha_cache.clear()
        self._deferred_unlocks = []
        self._deferred_keys = set()
        self.update()

    # ========== 主循环 ==========

    def _tick(self):
        """每帧更新（~60fps）；使用真实耗时确保深浅主题下粒子游速一致。"""
        now = time.perf_counter()
        dt = max(0.004, min(0.050, now - self._last_tick_time))  # 夹紧防止帧率突变
        self._last_tick_time = now
        # 节流落库：排版修正后的字坐标批量写库，避免每次按键都写整段（长文档中间编辑 O(n²) 卡顿）
        if self._positions_dirty and (now - self._last_pos_persist) > 0.4:
            try:
                db.batch_update_word_positions(self._pending_positions)
            except Exception:
                pass
            self._positions_dirty = False
            self._last_pos_persist = now
        self._anim_time += dt

        # 纸面积淀温度：有字时随书写/停留累积（停留越久、写得越多纸越暖）；
        # 全空（字已散尽）时缓缓冷却回落，让"失去"有一个安静的收束——余温散尽，
        # 纸归于最初的凉。仅当本页曾写过、如今全散时才明显冷却（B 项微动效）。
        if self._words:
            self._paper_warmth = min(self._paper_warmth + PAPER_WARMTH_PER_SECOND * dt, PAPER_WARMTH_MAX)
        else:
            self._paper_warmth = max(0.0, self._paper_warmth - PAPER_WARMTH_COOL_PER_SECOND * dt)

        # 窗口边框：恒定暖灰，由画布自绘，不再随悬停变化
        self._border_opacity = BORDER_OPACITY_LOW

        # 处理子线程排队的批注（线程安全：只在主线程操作 GUI）
        pending = []
        with self._pending_comments_lock:
            if self._pending_comments:
                pending = self._pending_comments[:]
                self._pending_comments.clear()
        for c, tier, is_fallback in pending:
            # 同页内容去重：避免 AI 生成与当前页已有批注完全一致的重复语句
            if any(oc.page_id == c.page_id and oc.content == c.content
                   for oc in self._comments):
                continue
            cid = db.add_comment(c)
            c.comment_id = cid
            # 绑定一条手写字体（延迟加载，首次使用才解析可用字体族）
            c.font_path = self._pick_handwriting_font()
            if c.page_id != self.page_id:
                # 延迟解锁归属旧页面：仅落库，等用户回到该页时由 _refresh_comments 自然浮现，
                # 不在当前页弹出，避免破坏"偶然发现"的惊喜感。
                continue
            self._comments.append(c)
            self._comment_anim[cid] = 0.0
            self._last_comment_time = time.time()
            self.comment_added.emit()
            if tier == 1:
                self.toast_requested.emit(TOAST_TIER1_UNLOCK)
            elif tier == 2:
                self.toast_requested.emit(TOAST_TIER2_UNLOCK)
            elif tier == 3:
                self.toast_requested.emit(TOAST_TIER3_UNLOCK)
                self._trigger_page_turn()
            else:
                if is_fallback:
                    self.toast_requested.emit("纸上的旧痕微微浮现……")
                else:
                    self.toast_requested.emit(TOAST_COMMENT_ADDED)
                # 满 8 条滚动淘汰
                self._check_and_evict()

        # 凝视续命：悬停时立即开始缓慢渐出，0.3 秒后再进行续命操作
        if self._hover_active and not self._window_dragging and 0 <= self._hover_word_idx < len(self._words) and self._hovered_comment_id <= 0:
            w = self._words[self._hover_word_idx]
            alpha = compute_alpha(w.create_timestamp, w.life_total_sec, w.revive_count or 0)
            if alpha <= REVIVE_HOVER_MIN_ALPHA:
                self._hover_hold_timer += dt * 1000
                if self._hover_hold_timer >= HOVER_HOLD_MS:
                    # 每个字每次凝视仅记一次续命；续命 = 重置生命周期（重新开始消散计时）
                    # 并延长总寿命，使反复凝视的字能更久留存。
                    if self._gazed_word_idx != self._hover_word_idx:
                        self._gazed_word_idx = self._hover_word_idx
                        self._do_revive(self._hover_word_idx)
            else:
                # 鲜活的字：凝视不续命，重置计时避免离开阈值瞬间误触
                self._hover_hold_timer = 0
        else:
            self._hover_hold_timer = 0
            self._gazed_word_idx = -1

        # 续命柔和回润脉冲：用 sin 包络实现"渐入→峰→渐出"，不再瞬间跳亮；
        # 总时长 REVIVE_FLASH_DURATION（约 3.5s），缓缓沉静，消除突兀感。
        if self._revive_flash_peak > 0:
            self._revive_flash_t += dt
            if self._revive_flash_t >= REVIVE_FLASH_DURATION:
                self._revive_flash = 0.0
                self._revive_flash_peak = 0.0
                self._revive_flash_t = 0.0
                self._revive_flash_word_idx = -1
            else:
                env = math.sin(math.pi * self._revive_flash_t / REVIVE_FLASH_DURATION)
                self._revive_flash = self._revive_flash_peak * env

        # 检测自然死亡的文字（生命周期结束），生成消散粒子
        dead_indices = []
        for i, w in enumerate(self._words):
            if w.word_id in self._dead_word_ids:
                continue
            alpha = compute_alpha(w.create_timestamp, w.life_total_sec, w.revive_count or 0)
            if alpha <= 0:
                self._spawn_dissolve_particles(w)
                self._dead_word_ids.add(w.word_id)
                dead_indices.append(i)
                # 曾被人反复挽留（续命到上限）却最终仍消散的字，给一句告别叙事
                if w.revive_count >= REVIVE_MAX_COUNT:
                    self.toast_requested.emit(TOAST_DISSOLVE_FINAL)
                # 从数据库标记死亡文字为残影点（记录消散坐标），供残影层绘制
                try:
                    db.mark_word_dissolved(w.word_id, w.x, w.y)
                except Exception:
                    pass
        # 从列表中移除死亡文字（逆序删除避免索引错乱）
        for i in reversed(dead_indices):
            del self._words[i]
            if self._cursor_index > i:
                self._cursor_index -= 1
        if dead_indices:
            self._char_count = sum(len(w.content) for w in self._words if w.content != '\n')
            self.char_count_changed.emit(self._char_count)
            self._reflow_from(min(dead_indices))
            self._sync_cursor()

        # 消散粒子更新
        self._dissolve_particles = [
            p for p in self._dissolve_particles if not p.update(dt)
        ]

        # 漂浮尘埃更新
        ww = max(self.width(), 100)
        wh = max(self.height(), 100)
        for p in self._dust_particles:
            p.update(dt, ww, wh)

        # 占位示例文字淡出：缓出（约 1.6s），接近消失时更慢，
        # 避免"啪"地直接消失的突兀感（中间那句话应优雅退场）
        if self._placeholder_fading and self._placeholder_alpha > 0:
            self._placeholder_alpha -= (dt / 1.6) * (0.5 + 0.5 * self._placeholder_alpha)
            if self._placeholder_alpha <= 0:
                self._placeholder_alpha = 0
                self._placeholder_fading = False

        # 页面载入淡入动画：1.2秒完成文案显现和淡出
        if self._page_load_active:
            self._page_load_alpha += dt * 0.55
            if self._page_load_alpha >= 1.2:
                self._page_load_alpha = 1.2
                self._page_load_active = False

        # 批注浮现动画（支持按 tier 不同时长）：完成后保持 1.0
        for cid, progress in list(self._comment_anim.items()):
            new_progress = progress + dt / (DURATION_COMMENT_STROKE / 1000.0)
            self._comment_anim[cid] = 1.0 if new_progress >= 1.0 else new_progress

        # 翻页动画进度（Tier 3 深层尘封解锁）
        if self._page_turn_active:
            self._page_turn_anim += dt / (TIER3_PAGE_TURN_DURATION_MS / 1000.0)
            if self._page_turn_anim >= 1.0:
                self._page_turn_anim = 1.0
                self._page_turn_active = False

        # 光标闪烁 —— 改为呼吸微光，不再生硬地开关
        self._cursor_visible = True  # 始终可见，呼吸光晕自带律动

        # 动态时辰检测：时段变化时刷新残影文案
        current_period = get_day_period()
        if current_period != self._last_ghost_period and not self._words:
            self._seed_ghost_phrases()

        # ---- 长按解封计时 ----
        if self._unseal_pressing:
            self._unseal_hold_time += dt
            self._unseal_progress = min(1.0, self._unseal_hold_time / 5.0)
            if self._unseal_hold_time >= 5.0:
                # 5 秒到达自动触发
                self._unseal_pressing = False
                self.setCursor(Qt.CursorShape.ForbiddenCursor)
                self.toast_requested.emit(TOAST_UNSEALING_PROGRESS)
                self.unseal_requested.emit(self.page_id or 0)

        # ---- 昼夜纸色调定时刷新（每 30 帧检测一次） ----
        self._daynight_check_counter += 1
        if self._daynight_check_counter >= 30:
            self._daynight_check_counter = 0
            new_color = get_daynight_bg_color()
            if new_color != self._daynight_color:
                self._daynight_color = new_color
                self._invalidate_paper_cache()

        # ---- 动态粒子管控：每 60 帧（~1 秒）按窗口尺寸 + 性能档位调整粒子上限 ----
        self._perf_frame_counter += 1
        if self._perf_frame_counter >= 60:
            self._perf_frame_counter = 0
            self._adapt_particle_limits()

        self.update()

    # ========== 绘制 ==========

    def paintEvent(self, event):
        """绘制总调度。包裹在 try/except 中，避免绘制期异常被 PyQt 当作硬错误直接终止进程（闪退）。"""
        try:
            self._paint_impl(event)
        except Exception:
            import traceback as _tb
            _tb.print_exc()

    def _paint_impl(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        if self._dark_mode:
            painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)

        w, h = self.width(), self.height()

        # 页面载入雾面阶段：内容离屏渲染后经平滑缩放模糊，再叠雾蒙砂蒙版，
        # 呈现"玻璃起雾、视线逐渐聚焦"的磨砂模糊感（性能模式跳过模糊，仅保留轻量淡入）
        needs_frost = self._page_load_active and self._page_load_alpha > 0.01
        if needs_frost and self._perf_tier != PerfTier.LOW:
            strength = 1.0 - self._page_load_alpha / 1.2
            strength = max(0.0, min(1.0, strength))
            img = self._render_content_offscreen(w, h)
            if strength > 0.02:
                img = self._blur_image(img, strength)
            painter.drawImage(0, 0, img)
            self._draw_frost_overlay(painter, w, h, strength)
        else:
            self._draw_content(painter, w, h)

        # === 装饰层（固定视口，不参与滚动）===
        # 漂浮尘埃（绘于文字之上，作为空气感）
        if self._atmosphere_enabled:
            self._draw_dust_particles(painter)
        # 封存遮罩
        if self.is_sealed:
            self._draw_sealed_overlay(painter, w, h)
        # Tier 3 翻页动画
        if self._page_turn_active:
            self._draw_page_turn_animation(painter, w, h)

        # 窗口左/右边框：由画布自绘，半透明、悬停更清晰
        # （画布每帧重绘，边框随之刷新；不依赖主窗口描边，故不闪烁、无黑线）
        bc = QColor(*(WINDOW_BORDER_DARK if self._dark_mode else WINDOW_BORDER_LIGHT))
        bc.setAlphaF(self._border_opacity)
        painter.setPen(QPen(bc, 1))
        painter.drawLine(0, 0, 0, h)              # 左边框
        painter.drawLine(w - 1, 0, w - 1, h)      # 右边框（贯穿画布：与右侧触发条共同构成右边缘）

        # 叙事提示文案：简洁显现后快速淡出
        if needs_frost and self._page_load_text:
            # 文案在雾面可见期间清晰显示，雾面将散时才淡出（避免过早消失看不见）
            if self._page_load_alpha <= 0.5:
                text_alpha = (self._page_load_alpha / 0.5) * 0.7
            elif self._page_load_alpha <= 0.85:
                text_alpha = 0.7
            else:
                text_alpha = max(0, 0.7 * (1 - (self._page_load_alpha - 0.85) / 0.35))

            if text_alpha > 0.01:
                painter.setOpacity(text_alpha)
                painter.setPen(QColor(CANVAS_BORDER_COLOR_DARK) if not self._dark_mode else QColor(CANVAS_BORDER_COLOR_LIGHT))
                font = self._body_font(12)
                font.setItalic(True)
                painter.setFont(font)
                painter.drawText(0, h - 115, w, 20, Qt.AlignmentFlag.AlignHCenter, self._page_load_text)
                painter.setOpacity(1.0)

        painter.end()

    # ========== 纸张纹理静态缓存（底层优化：避免每帧重绘纤维/黄斑/折痕）==========

    def _invalidate_paper_cache(self):
        """使纸张纹理缓存失效（尺寸变化、纸张切换、性能档位变化时调用）。"""
        self._paper_cache = None
        self._paper_cache_key = None

    def _adapt_particle_limits(self):
        """依据窗口尺寸和性能档位动态调整尘/残影/星场上限。

        在 LOW 档下大幅减少开销，MEDIUM 档取中位数，HIGH 全量。
        同时兼容窗口缩放后的自适应增减。
        """
        ww = max(self.width(), 100)
        wh = max(self.height(), 100)
        limits = compute_particle_limits(ww, wh, self._perf_tier)
        self._particle_limits = limits

        # 尘粒：按新上限截断或保持
        target_dust = limits['dust']
        while len(self._dust_particles) < target_dust:
            # 补充新尘粒：必须用均匀位置生成，不可传 (ww, wh)（那样会全堆在右下角）。
            # 之前 showEvent 先调本函数时 self._dust_particles 为空，整批被生成在
            # 右下角后再散开，加上中间被文字占据，视觉上只剩左右两侧空白边距可见。
            p = generate_dust_particles(ww, wh, 1)[0]
            self._dust_particles.append(p)
        if len(self._dust_particles) > target_dust:
            self._dust_particles = self._dust_particles[:target_dust]

    def _ensure_paper_cache(self, w: int, h: int):
        """确保纸张纹理缓存有效（背景底色 + 纸纹理）。若失效则重建。"""
        if w <= 0 or h <= 0:
            return self._paper_cache

        # 缓存键：包含尺寸、暗色模式、纸张类型、动画时间桶（用于纤维微动刷新）
        time_bucket = int(self._anim_time / PAPER_CACHE_REFRESH_INTERVAL)
        key = (w, h, self._dark_mode, self._paper_type, time_bucket)

        if self._paper_cache is not None and self._paper_cache_key == key:
            return self._paper_cache

        # 重新渲染纸张纹理到缓存
        if self._paper_cache is None or self._paper_cache.width() != w or self._paper_cache.height() != h:
            self._paper_cache = QPixmap(w, h)

        self._paper_cache.fill(Qt.transparent)
        cache_painter = QPainter(self._paper_cache)
        cache_painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        self._draw_background(cache_painter, w, h)
        self._draw_paper_texture(cache_painter, w, h)
        cache_painter.end()

        self._paper_cache_key = key
        self._paper_cache_w = w
        self._paper_cache_h = h
        return self._paper_cache

    # ========== 分块绘制 ==========

    def _draw_content(self, painter, w, h):
        """绘制页面全部内容层（背景/纸纹/光效/残影/文字/批注/空状态/光标）。
        抽离为独立方法，以便页面载入雾面阶段将其渲染到离屏缓冲并做模糊。"""
        # L0: 画布底色 + 纸纹理（缓存：避免每帧重绘 170 纤维 + 25 黄斑 + 5 折痕）
        paper_cache = self._ensure_paper_cache(w, h)
        if paper_cache is not None:
            painter.drawPixmap(0, 0, paper_cache)
        else:
            self._draw_background(painter, w, h)
            self._draw_paper_texture(painter, w, h)
        # 动态暖柔光（绘于文字之下，避免遮挡正文）
        if not self.is_sealed:
            self._draw_light_sweep(painter, w, h)

        # === 第一层：消散点阵残影层（固定视口，不随滚动）===
        self._draw_ghost_phrases(painter, w, h)

        # 进入"内容滚动坐标系"：整体按 -scroll_y 平移，模拟一张完整信纸上下滑动
        painter.save()
        painter.translate(0, -self._scroll_y)

        self._draw_ghost_dots(painter)
        self._draw_dissolve_particles(painter)

        # === 第二层：临终预警线条层 ===
        self._draw_warning_lines(painter)

        # === 第三层：用户正文文字层 ===
        self._draw_text_layer(painter)

        # === 第四层：旧主人批注层 ===
        # 没有文字时不再显示旧主人批注（避免空页面两侧悬着批注），
        # 此时由下方"空状态提示层"呈现画布中央文案。
        if self._words:
            self._draw_comments(painter)

        # === 第五层：空状态提示层 ===
        if not self._words:
            # 占位示例文字优先：帮助用户"进入状态"，打字后淡出
            if self._placeholder_alpha > 0.01:
                self._draw_placeholder(painter)
            else:
                self._draw_empty_hint(painter, w, h)

        # 输入光标（随内容滚动）；需用户点击画布后才激活显示
        if self._cursor_user_activated and self.hasFocus() and not self.is_sealed:
            self._draw_cursor(painter)

        painter.restore()

    def _render_content_offscreen(self, w, h):
        """把内容层渲染到离屏 QImage，供雾面阶段做模糊。"""
        img = QImage(w, h, QImage.Format_ARGB32_Premultiplied)
        if self._dark_mode:
            img.fill(QColor(*PAGE_CONTENT_BG_DARK))
        else:
            img.fill(QColor(*PAGE_CONTENT_BG_LIGHT))
        p = QPainter(img)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        if self._dark_mode:
            p.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        self._draw_content(p, w, h)
        p.end()
        return img

    def _blur_image(self, src, strength):
        """基于多次平滑缩放的廉价模糊：strength 越大越模糊（1=最强）。"""
        if strength <= 0.02:
            return src
        factor = max(0.06, 1.0 - 0.94 * strength)
        sw = max(1, int(src.width() * factor))
        sh = max(1, int(src.height() * factor))
        small = src.scaled(sw, sh, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        return small.scaled(src.width(), src.height(), Qt.IgnoreAspectRatio, Qt.SmoothTransformation)

    def _draw_frost_overlay(self, painter, w, h, strength):
        """雾面蒙版：整体磨砂底 + 边缘磨砂渐变（中心也微雾）+ 顶部窗光 + 细柔颗粒。
        叠加在（已模糊的）内容之上，模拟玻璃起雾后逐渐聚焦。strength: 1=全雾，0=清晰。"""
        if strength <= 0.01:
            return
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        base_r, base_g, base_b = FROST_BASE if not self._dark_mode else FROST_BASE_DARK
        grain_r, grain_g, grain_b = FROST_GRAIN if not self._dark_mode else FROST_GRAIN_DARK
        light_r, light_g, light_b = FROST_LIGHT if not self._dark_mode else FROST_LIGHT_DARK

        # 1) 整体磨砂底（更浓，中心也带薄雾，模糊感更足）
        base_a = int(strength * 150)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(base_r, base_g, base_b, base_a))
        painter.drawRect(0, 0, w, h)

        # 2) 边缘磨砂渐变：中心微雾、四周更浓，像视线从模糊逐渐聚焦
        vig = QRadialGradient(w / 2, h / 2, max(w, h) * 0.82)
        edge_a = int(strength * 150)
        center_a = int(strength * 55)
        vig.setColorAt(0.0, QColor(base_r, base_g, base_b, center_a))
        vig.setColorAt(0.5, QColor(base_r, base_g, base_b, int(center_a + (edge_a - center_a) * 0.4)))
        vig.setColorAt(1.0, QColor(base_r, base_g, base_b, edge_a))
        painter.setBrush(QBrush(vig))
        painter.drawRect(0, 0, w, h)

        # 3) 顶部窗光晕：柔和暖光自上方漫入，呼应"窗光"叙事
        top = QLinearGradient(0, 0, 0, int(h * 0.55))
        top.setColorAt(0.0, QColor(light_r, light_g, light_b, int(strength * 70)))
        top.setColorAt(1.0, QColor(light_r, light_g, light_b, 0))
        painter.setBrush(QBrush(top))
        painter.drawRect(0, 0, w, h)

        # 4) 细柔颗粒胶片噪点：多而细，模拟磨砂玻璃表面颗粒感
        grain_a = int(strength * 45)
        if grain_a > 0:
            painter.setOpacity(grain_a / 255.0)
            for i in range(280):
                nx = int((self._anim_time * 60 + i * 137) % w)
                ny = int((self._anim_time * 80 + i * 211) % h)
                a = 0.35 + 0.65 * ((i * 53) % 7) / 6.0
                painter.setPen(QColor(grain_r, grain_g, grain_b, int(255 * a)))
                painter.drawPoint(nx, ny)
            painter.setOpacity(1.0)

        painter.restore()

    # ========== 各层实现 ==========

    def _draw_background(self, painter: QPainter, w: int, h: int):
        """底色 + 纸张图片 + 昼夜微色调 + 纸面积淀温度。"""
        if self._dark_mode:
            painter.fillRect(0, 0, w, h, QColor(DARK_BG_CANVAS))
            # 深色模式也保留极克制的"昼夜微色调"，与浅色光影语言统一
            dt = QColor(self._daynight_color)
            dt.setAlpha(26)
            painter.fillRect(0, 0, w, h, dt)
            # 轻微暗角：让画面有被窗光包围的纵深感，避免死板纯色
            vig = QRadialGradient(w / 2, h / 2, max(w, h) * 0.72)
            vig.setColorAt(0.0, QColor(0, 0, 0, 0))
            vig.setColorAt(1.0, QColor(0, 0, 0, int(255 * 0.22)))
            painter.setBrush(QBrush(vig))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRect(0, 0, w, h)
            # 深色模式：叠加星空背景（稳定不闪，缓慢呼吸）
            self._draw_starfield(painter, w, h)
            return

        # 基础纸色
        bg_hex = PAPER_BG_HEX.get(self._paper_type, BG_YELLOW_1)
        painter.fillRect(0, 0, w, h, QColor(bg_hex))

        # 昼夜时辰微色调叠层（根据真实时间变化，alpha=40，非常克制）
        dt = QColor(self._daynight_color)
        dt.setAlpha(40)  # 非常透明，仅仅是一种"气氛"
        painter.fillRect(0, 0, w, h, dt)

        # 纸面积淀温度叠层（写字越多、停留越久纸越暖）
        if self._paper_warmth > 0.001:
            # 暖色效果随时间和书写字数累积，最高可达明显的暖黄色调
            warm_alpha = int(self._paper_warmth * 150)  # 最高约 alpha=45
            warm = QColor("#F5E6C8")
            warm.setAlpha(warm_alpha)
            painter.fillRect(0, 0, w, h, warm)

        # 纸纹理图片
        if self._paper_bg_img and not self._paper_bg_img.isNull():
            scaled = self._paper_bg_img.scaled(
                w, h, Qt.AspectRatioMode.IgnoreAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            painter.setOpacity(0.42)
            painter.drawImage(0, 0, scaled)
            painter.setOpacity(1.0)

        # 程序化纸面细颗粒（纸齿质感）：放大铺满，低透明度，提供细腻肌理
        if self._grain_img and not self._grain_img.isNull():
            scaled_grain = self._grain_img.scaled(
                w, h, Qt.AspectRatioMode.IgnoreAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            painter.setOpacity(PAPER_GRAIN_OPACITY)
            painter.drawImage(0, 0, scaled_grain)
            painter.setOpacity(1.0)

        # 浅色模式也保留极弱暗角，与深色模式光影语言对称
        vig = QRadialGradient(w / 2, h / 2, max(w, h) * 0.78)
        vig.setColorAt(0.0, QColor(0, 0, 0, 0))
        vig.setColorAt(1.0, QColor(0, 0, 0, int(255 * 0.13)))
        painter.setBrush(QBrush(vig))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRect(0, 0, w, h)

    def _draw_paper_texture(self, painter: QPainter, w: int, h: int):
        """纸纤维线条 + 黄斑 + 折痕。纤维会缓慢微动。"""
        if self._dark_mode or self._perf_tier == PerfTier.LOW:
            return
        offset = math.sin(self._anim_time / (DURATION_TEXTURE_DRIFT / 1000) * 2 * math.pi) * FIBER_DRIFT_AMPLITUDE * 0.3

        # 纤维
        for f in self._fiber_lines:
            drift = math.sin(f.seed + self._anim_time * 0.3) * FIBER_DRIFT_AMPLITUDE
            painter.setPen(QPen(QColor(FIBER_COLOR_BASE), 0.7))
            painter.setOpacity(f.alpha * (0.7 + 0.3 * math.sin(self._anim_time * 0.5 + f.seed)))
            painter.drawLine(
                int(f.x1 + drift), int(f.y1 + drift * 0.3),
                int(f.x2 + drift), int(f.y2 + drift * 0.3),
            )
        painter.setOpacity(1.0)

        # 黄斑
        for s in self._stains:
            painter.setBrush(QBrush(QColor(s.color)))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setOpacity(s.alpha)
            painter.drawEllipse(QPointF(s.x, s.y), s.radius, s.radius * 0.7)
        painter.setOpacity(1.0)

        # 折痕
        for c in self._creases:
            painter.setPen(QPen(QColor(CREASE_COLOR), CREASE_WIDTH))
            painter.setOpacity(c.alpha)
            painter.drawLine(int(c.x1), int(c.y1), int(c.x2), int(c.y2))
        painter.setOpacity(1.0)

    def _draw_ghost_phrases(self, painter: QPainter, w: int, h: int):
        """空画布预置淡残影文字。缓慢呼吸。"""
        if self._dark_mode:
            return
        for x, y, text, base_alpha, phase in self._ghost_phrases_data:
            breath = (math.sin(self._anim_time * 0.25 + phase) + 1) * 0.5
            alpha = base_alpha * (0.6 + breath * 0.4)
            painter.setOpacity(alpha)
            font = self._body_font(11)
            font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 1.0)
            painter.setFont(font)
            painter.setPen(QColor(GHOST_TEXT_COLOR))
            painter.drawText(int(x), int(y), text)
        painter.setOpacity(1.0)

    def _draw_dissolve_particles(self, painter: QPainter):
        """文字消散时的黄褐色浮动粒子。"""
        for p in self._dissolve_particles:
            painter.setOpacity(p.alpha * 0.7)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(QColor(p.color)))
            painter.drawEllipse(QPointF(p.x, p.y), p.radius, p.radius)
        painter.setOpacity(1.0)

    def _draw_ghost_dots(self, painter: QPainter):
        """已消散文字的残影圆点（浅色模式更明显；深色模式由星空背景替代）。"""
        if self.page_id <= 0 or self._dark_mode:
            return
        now = time.time()
        if self._ghost_cache is None or now - self._ghost_cache_t > 2.0:
            try:
                self._ghost_cache = db.get_dissolved_dots(self.page_id, GHOST_MAX_DOTS)
            except Exception:
                self._ghost_cache = []
            self._ghost_cache_t = now
        dissolved = self._ghost_cache
        if not dissolved:
            return
        painter.setPen(Qt.PenStyle.NoPen)
        for dot in dissolved:
            # 残影密度梯度：revive_count 越高尘埃越实（文档规定 0-5 → alpha 0.06~0.22）
            revive = min(dot.revive_count or 0, 5)
            alpha = 0.14 + revive * 0.045   # 浅色模式更明显（0.14~0.365）
            # 缓慢漂浮：以坐标为种子做极慢正弦漂移，体现时间堆积的厚重感
            seed = (dot.dissolved_x or 50) * 0.013 + (dot.dissolved_y or 50) * 0.017
            drift_x = math.sin(self._anim_time * 0.12 + seed) * 3.0
            drift_y = math.cos(self._anim_time * 0.09 + seed) * 2.2
            cx = (dot.dissolved_x or 50) + drift_x
            cy = (dot.dissolved_y or 50) + drift_y
            # 黄褐半透明尘埃：柔斑径向渐变（拒绝死板灰色圆点）
            # 用稳定种子生成尺寸/颜色，避免每帧随机重掷导致闪烁
            rng = random.Random(int(dot.dissolved_x or 50) * 1000 + int(dot.dissolved_y or 50))
            r = GHOST_DUST_RADIUS_MIN + rng.random() * (GHOST_DUST_RADIUS_MAX - GHOST_DUST_RADIUS_MIN)
            color = QColor(rng.choice(GHOST_DUST_COLORS))
            grad = QRadialGradient(cx, cy, r)
            grad.setColorAt(0.0, color)
            edge = QColor(color)
            edge.setAlpha(0)
            grad.setColorAt(1.0, edge)
            painter.setOpacity(alpha)
            painter.setBrush(QBrush(grad))
            painter.drawEllipse(QPointF(cx, cy), r, r * 0.85)
        painter.setOpacity(1.0)

    def _draw_starfield(self, painter: QPainter, w: int, h: int):
        """深色模式星空背景：静态星点 + 极缓慢呼吸闪烁（缓存为 pixmap，降低重绘开销）。"""
        if w <= 0 or h <= 0:
            return
        now = time.time()
        if (self._star_cache is None
                or self._star_cache_w != w or self._star_cache_h != h
                or self._star_cache_dark != self._dark_mode
                or now - self._star_cache_t > 0.25):  # 呼吸极慢，0.25s 重渲染一次即可
            self._render_starfield(w, h)
            self._star_cache_t = now
        painter.drawPixmap(0, 0, self._star_cache)

    def _render_starfield(self, w: int, h: int):
        """将星空渲染到透明 pixmap（仅星点，背景透明，由 drawPixmap 叠加到暗色画布上）。"""
        pix = QPixmap(w, h)
        pix.fill(Qt.transparent)
        p = QPainter(pix)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setPen(Qt.PenStyle.NoPen)
        for (nx, ny, radius, phase, bright) in self._stars:
            x = nx * w
            y = ny * h
            tw = 0.5 + 0.5 * math.sin(self._anim_time * 0.5 + phase)
            alpha = (0.10 + bright * 0.28) * (0.55 + 0.45 * tw)
            col = QColor(*STAR_LIGHT_COLOR)
            col.setAlphaF(alpha)
            p.setBrush(QBrush(col))
            p.drawEllipse(QPointF(x, y), radius, radius)
        p.end()
        self._star_cache = pix
        self._star_cache_w = w
        self._star_cache_h = h
        self._star_cache_dark = self._dark_mode

    def _draw_warning_lines(self, painter: QPainter):
        """两段预警线条：衰退预警（淡暖虚线）+ 临终预警（更明显虚线）。

        第一段（衰退预警，寿命耗尽 ≥75%）：极淡，对字开始褪色给较早提示。
        第二段（临终预警，寿命耗尽 ≥90%）：较明显，暗示再不注意就要消失。
        """
        if self.is_sealed:
            return
        if self._dark_mode:
            decay_color = QColor(DECAY_LINE_COLOR)
            decay_alpha = DECAY_LINE_ALPHA
            dying_color = QColor(WARNING_LINE_COLOR)
            dying_alpha = WARNING_LINE_ALPHA
        else:
            decay_color = QColor(DECAY_LINE_COLOR_LIGHT)
            decay_alpha = DECAY_LINE_ALPHA_LIGHT
            dying_color = QColor(WARNING_LINE_COLOR_LIGHT)
            dying_alpha = WARNING_LINE_ALPHA_LIGHT
        now = time.time()
        for w in self._words:
            stage = get_word_warning_stage(w.create_timestamp, w.life_total_sec,
                                           w.revive_count or 0, now)
            if stage == 0:
                continue
            if stage == 1:
                painter.setPen(QPen(decay_color, 1.0, Qt.PenStyle.DotLine))
                painter.setOpacity(decay_alpha)
            else:
                painter.setPen(QPen(dying_color, 1.0, Qt.PenStyle.DotLine))
                painter.setOpacity(dying_alpha)
            fm = self._body_metrics(BODY_FONT_SIZE)
            tw = fm.width(w.content)
            painter.drawLine(
                int(w.x), int(w.y + 4),
                int(w.x + tw), int(w.y + 4),
            )
        painter.setOpacity(1.0)

    def _draw_text_layer(self, painter: QPainter):
        """正文文字层 —— 墨水氧化色阶 + 笔画残缺 + 呼吸动画 + 临终辉光 + 悬停渐变 + 残影。"""
        now = time.time()

        # 预计算临终字中心，用于辉光"密度感知"：大面积文字同时临终时，
        # 各自压低辉光，避免满屏暖斑连成一片像发霉。
        _dying_centers = []
        for w in self._words:
            if w.content == '\n':
                continue
            _a = compute_alpha(w.create_timestamp, w.life_total_sec,
                               w.revive_count or 0, now)
            if 0 < _a <= LIFE_END_WARN_RATIO:
                _fm = self._body_metrics(BODY_FONT_SIZE)
                _dying_centers.append((
                    w.x + _fm.horizontalAdvance(w.content) / 2,
                    w.y - _fm.height() / 2,
                ))

        for i, w in enumerate(self._words):
            if w.content == '\n':
                continue
            
            base_alpha = compute_alpha(
                w.create_timestamp, w.life_total_sec,
                w.revive_count or 0, now,
            )

            # 每字稳定的伪随机种子：供临终辉光闪烁相位与笔画侵蚀共用，
            # 必须在辉光块(引用 seed)之前定义，避免单字/首字进入临终窗口时
            # 触发 UnboundLocalError（此前 seed 仅在后方侵蚀块定义）。
            seed = w.x * 13.7 + w.y * 37.3 + hash(w.content) * 0.01

            if not self.is_sealed:
                breath_alpha = breathing_alpha_for_display(
                    base_alpha, self._anim_time,
                    DURATION_BREATHING_CYCLE,
                    is_warning=(base_alpha <= LIFE_END_WARN_RATIO),
                )
            else:
                breath_alpha = base_alpha
            
            target_alpha = breath_alpha
            is_hovering = i == self._hover_word_idx and not self.is_sealed
            
            if is_hovering:
                target_alpha = min(1.0, max(base_alpha, GAZE_REVIVE_ALPHA))
            
            cached = self._display_alpha_cache.get(i, breath_alpha)
            
            if is_hovering:
                new_alpha = min(cached + GAZE_REVIVE_SPEED, target_alpha)
            else:
                if cached > breath_alpha:
                    new_alpha = max(cached - FADE_DECAY_SPEED, breath_alpha)
                else:
                    new_alpha = breath_alpha
            
            self._display_alpha_cache[i] = new_alpha
            display_alpha = new_alpha
            
            if display_alpha <= 0 and not is_hovering:
                continue
            
            if 0 < base_alpha <= 0.10 and not self.is_sealed:
                fm = self._body_metrics(BODY_FONT_SIZE)
                tw = fm.horizontalAdvance(w.content)
                th = fm.height()
                # 临终辉光（回光返照）—— v3 收敛版：
                #   之前是"双层叠加 + 18s 呼吸振幅 22%"，结果：
                #     1) 底色常驻层（1.5x 半径、永久不灭）让相邻字光斑融合成"光斑群"；
                #     2) 核心层 22% 振幅即使有 seed 错相，仍在每个字周围造成局部明灭。
                #   整页临终字叠加 → "满屏闪烁群"画布显乱。
                #   本版改为：单层极弱稳定微光，无振幅、无呼吸、半径收紧至 0.9x，
                #   强度降至 35/55（深/浅），使辉光只作为"余温感"而非"光效"。
                #   生效窗口从 ≤0.15 收紧到 ≤0.10 —— 临终末期才微微有光，
                #   与下方"灰化褪色"协同传达"墨迹渐渐熄灭"的叙事。
                if self._dark_mode:
                    glow_hex = TERMINAL_GLOW_DARK
                    glow_strength = 150
                else:
                    glow_hex = TERMINAL_GLOW_LIGHT
                    glow_strength = 210
                glow_radius_mult = 0.85
                # 临终辉光强度：保底 0.45，临终末期叠加至 1.0。
                # 原公式 (0.10-base_alpha)/0.10 在刚进临终时强度为 0 → 完全不可见；
                # 改为带保底，使整个临终区间(0.10→0)周围都有可见余温光晕，且随逼近消散缓缓增强。
                glow_intensity = 0.45 + 0.55 * (0.10 - base_alpha) / 0.10
                glow_intensity = max(0.0, min(1.0, glow_intensity))
                stable_alpha = int(glow_intensity * glow_strength)
                stable_alpha = max(0, min(255, stable_alpha))
                gcx, gcy = w.x + tw / 2, w.y - th / 2
                # 密度感知：附近临终字越多，单个辉光越淡，避免成片暖斑像发霉
                _nb = 0
                _spread = max(tw, th) * 1.2
                for (_cx, _cy) in _dying_centers:
                    if _cx == gcx and _cy == gcy:
                        continue
                    if abs(_cx - gcx) <= _spread and abs(_cy - gcy) <= _spread:
                        _nb += 1
                _density_factor = 1.0 / (1.0 + 0.7 * _nb)
                stable_alpha = int(stable_alpha * _density_factor)
                stable_alpha = max(0, min(255, stable_alpha))
                glow_core = QColor(glow_hex)
                glow_core.setAlpha(stable_alpha)
                glow_edge = QColor(glow_hex)
                glow_edge.setAlpha(0)
                glow_hue = QRadialGradient(gcx, gcy, max(tw, th) * glow_radius_mult)
                glow_hue.setColorAt(0, glow_core)
                glow_hue.setColorAt(1, glow_edge)
                painter.setBrush(QBrush(glow_hue))
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setOpacity(1.0)
                painter.drawEllipse(
                    QPointF(gcx, gcy),
                    max(tw, th) * 0.85, max(tw, th) * 0.85,
                )
            
            ink_color = get_ink_oxidation_color(base_alpha,
                                              is_dark_mode=self._dark_mode)

            # 续命柔和"回润"：刚被续命（或达上限仍被注视）的字，墨色短暂向鲜墨轻混，
            # 并叠加一档提亮，随 _revive_flash 缓慢衰减（约 2.8s），
            # 表现为"墨迹被重新浸润、轻轻亮起、缓缓沉静回氧化态"，消除瞬间跳变的突兀感。
            f = self._revive_flash if (self._revive_flash > 0
                                       and i == self._revive_flash_word_idx) else 0.0
            if f > 0:
                ink_color = QColor(lerp_hex_colors(ink_color.name(), INK_FRESH, f * 0.45))

            eroded = get_eroded_alpha(display_alpha, seed)
            if f > 0:
                eroded = min(1.0, eroded + f * 0.28)
            # 修复"未进临终却比临终更透明"：笔画残缺侵蚀会把衰退期(寿命75%~90%)的
            # 字侵蚀到接近/低于 0.10，反而比临终字更淡，破坏"临终=最淡"的直觉层级。
            # 对非临终字(base_alpha>临终阈值)设侵蚀下限=临终起始阈值，使其永不比临终
            # 起始更透明；临终字不受限，仍可沉到 0。既保留笔画残缺纹理，又修正层级倒置。
            if base_alpha > LIFE_END_WARN_RATIO:
                eroded = max(eroded, min(base_alpha, LIFE_END_WARN_RATIO))
            ink_color.setAlpha(int(max(0.0, min(1.0, eroded)) * 255))

            # 临终灰度偏移：消失前墨迹向灰色褪变，强化"墨水氧化消逝"观感
            ink_color = get_dying_grayscale_color(ink_color, base_alpha)

            # 浅色模式临终文字"溶入纸面"：深/黄褐墨在浅米纸上对比过强，
            # 单纯向灰色偏移（仍偏中灰）在浅底上依然显眼，造成"临终字太清晰"。
            # 故在临终窗口内，把墨色按接近死亡的程度向纸色叠加混合，
            # 让字迹像被纸吸走般淡出，降低浅色模式临终文字的可见度。
            # 深色模式保持原灰度行为（浅亮墨在暗底上靠灰度即可自然消隐）。
            if not self._dark_mode and base_alpha <= TEXT_GRAYSCALE_THRESHOLD:
                paper = QColor(BG_DEFAULT)
                t = 1.0 - (base_alpha / TEXT_GRAYSCALE_THRESHOLD)   # 0→1 越接近死亡越溶
                melt = t * TEXT_GRAYSCALE_MAX_FACTOR                # 临终最多溶入纸色 75%
                ink_color = QColor(
                    int(ink_color.red() * (1 - melt) + paper.red() * melt),
                    int(ink_color.green() * (1 - melt) + paper.green() * melt),
                    int(ink_color.blue() * (1 - melt) + paper.blue() * melt),
                    ink_color.alpha(),
                )
            
            font = self._body_font(BODY_FONT_SIZE + 1)

            age = 1.0 - display_alpha
            if age > 0.30 and not self._dark_mode:
                # v2：下调光晕强度并抬高门槛。
                # 原版 age>0.12 即套深褐光晕（alpha 最高 ~0.18），本意是让浅底上
                # 的淡字更清晰，但结果反而"刻意提亮临终字"，与需求相悖。
                # 现仅对相当老化（age>0.30）的文字施加很弱光晕，且上限压到 ~0.06，
                # 不再与下方"溶入纸色"抵消，临终字整体更安静地淡出。
                feather = age * 0.5
                halo = QColor(*TEXT_HALO_RGB_DARK)
                for _dx, _dy in ((-1, 0), (1, 0), (0, -1), (0, 1), (1, 1), (-1, -1)):
                    halo.setAlphaF(feather * 0.08)
                    painter.setPen(halo)
                    painter.setFont(font)
                    painter.drawText(int(w.x) + _dx, int(w.y) + _dy, w.content)
            
            painter.setFont(font)
            painter.setPen(ink_color)
            painter.setBrush(Qt.BrushStyle.NoBrush)

            # 临终透明度闪烁：v2 收敛版 —— 直接去掉。
            # 原版用 sin(t*1.2) 让文字透明度在 [base, base+0.22] 间脉动，
            # 这是最硬的"硬闪"：文字本身在跳。即使有 seed 错相，5s 周期
            # 仍让整页临终字显得"集体不稳定"，画布显乱。
            # 临终明灭感现由上方"极弱稳定微光" + "灰化褪色"共同承担——
            # 字会缓慢褪灰变暗、不再有跳变，但仍有"渐渐熄灭"的诗意。
            painter.setOpacity(display_alpha)
            painter.drawText(int(w.x), int(w.y), w.content)
            painter.setOpacity(1.0)
        
        self._clean_display_alpha_cache()
        
        self._draw_text_afterglow(painter, now)
    
    def _draw_text_afterglow(self, painter: QPainter, current_time: float):
        """绘制文字消散后的残影。"""
        for i, w in enumerate(self._words):
            if w.content == '\n':
                continue
            
            afterglow_alpha = compute_afterglow_alpha(
                w.create_timestamp, w.life_total_sec, current_time
            )
            
            if afterglow_alpha <= 0:
                continue
            
            base_alpha = compute_alpha(
                w.create_timestamp, w.life_total_sec,
                w.revive_count or 0, current_time,
            )
            
            if base_alpha > 0:
                continue
            
            ink_color = get_ink_oxidation_color(0.01,
                                               is_dark_mode=self._dark_mode)
            ink_color.setAlpha(int(afterglow_alpha * 255))
            
            font = self._body_font(BODY_FONT_SIZE + 1)

            painter.setFont(font)
            painter.setPen(ink_color)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawText(int(w.x), int(w.y), w.content)
    
    def _clean_display_alpha_cache(self):
        """清理透明度缓存中过期的条目。"""
        valid_indices = set(range(len(self._words)))
        keys_to_remove = [k for k in self._display_alpha_cache.keys() if k not in valid_indices]
        for k in keys_to_remove:
            del self._display_alpha_cache[k]

    def _draw_comments(self, painter: QPainter):
        """AI 批注层 —— 三层解锁 + 悬停缓慢显现 + 淘汰呼吸 + 终身锁定 + 墨迹扩散效果。"""
        now = time.time()
        for i, c in enumerate(self._comments):
            cid = c.comment_id
            progress = self._comment_anim.get(cid, 1.0)

            base_alpha = c.base_alpha
            target_alpha = base_alpha * min(progress, 1.0)
            
            if self._hovered_comment_id == cid:
                target_alpha = 1.0
            
            cached = self._comment_alpha_cache.get(cid, target_alpha)
            
            if self._hovered_comment_id == cid:
                new_alpha = min(cached + 0.04, target_alpha)
            else:
                if cached > target_alpha:
                    new_alpha = max(cached - 0.02, target_alpha)
                else:
                    new_alpha = target_alpha
            
            self._comment_alpha_cache[cid] = new_alpha
            display_alpha = new_alpha

            if display_alpha <= 0.01:
                continue

            # 显出动画：进度 < 1 时文字从下方轻微"升起"归位，增强浮现感
            reveal_offset = 0.0
            if progress < 1.0:
                reveal_offset = (1.0 - max(0.0, progress)) * 9.0

            painter.setOpacity(display_alpha)
            color = QColor(COMMENT_COLOR) if not self._dark_mode else QColor(COMMENT_COLOR_DARK)
            color.setAlpha(255)
            cfs = self._comment_font_size(c)
            # 批注使用与文案一致的"当前字体"（启动钉住的当前手写体），不随手写体切换而改变
            font = QFont(self.copy_font_family(), cfs)
            font.setItalic(True)
            painter.setFont(font)
            painter.setPen(color)
            painter.save()
            _cdx, _cdy = self._comment_avoid_pos(c)
            painter.translate(_cdx, _cdy + reveal_offset)
            if c.rotate_angle:
                painter.rotate(c.rotate_angle)
            # 使用自动换行绘制批注
            side = 'left' if (c.comment_id % 2 == 0) else 'right'
            x0, x1 = self._comment_gutter_bounds(side)
            gutter_width = x1 - x0
            max_width = gutter_width - 24 if gutter_width > 24 else 100
            text_rect = QRectF(0, 0, max_width, 9999)
            
            # 墨迹扩散效果 v2 —— 首次出场时多层墨晕（模拟墨汁在纸纤维中洇开）
            if progress < 1.0:
                inv_progress = 1.0 - progress
                # 深/浅模式墨色基础
                ink_base = COMMENT_INK_LIGHT if not self._dark_mode else COMMENT_INK_DARK
                painter.setPen(Qt.PenStyle.NoPen)
                # 第一层：大半径扩散光晕（最外圈，已快消退）
                g1 = QRadialGradient(0, 0, 18 + inv_progress * 12)
                c1_center = QColor(ink_base)
                c1_center.setAlpha(int(22 * inv_progress * inv_progress))
                c1_edge = QColor(ink_base)
                c1_edge.setAlpha(0)
                g1.setColorAt(0, c1_center)
                g1.setColorAt(1, c1_edge)
                painter.setBrush(QBrush(g1))
                painter.drawEllipse(QPointF(0, 0), 18 + inv_progress * 12, 18 + inv_progress * 12)
                # 第二层：中圈墨迹扩散
                g2 = QRadialGradient(0, 0, 10 + inv_progress * 8)
                c2_center = QColor(ink_base)
                c2_center.setAlpha(int(38 * inv_progress))
                c2_edge = QColor(ink_base)
                c2_edge.setAlpha(0)
                g2.setColorAt(0, c2_center)
                g2.setColorAt(1, c2_edge)
                painter.setBrush(QBrush(g2))
                painter.drawEllipse(QPointF(0, 0), 10 + inv_progress * 8, 10 + inv_progress * 8)
                # 第三层：内核——最浓、但范围最小
                g3 = QRadialGradient(0, 0, 4 + inv_progress * 4)
                c3 = QColor(ink_base)
                c3.setAlpha(int(55 * inv_progress * inv_progress))
                g3.setColorAt(0, c3)
                g3.setColorAt(1, QColor(ink_base))
                g3.setColorAt(1, QColor(ink_base))
                g3_edge = QColor(ink_base)
                g3_edge.setAlpha(0)
                g3.setColorAt(1, g3_edge)
                painter.setBrush(QBrush(g3))
                painter.drawEllipse(QPointF(0, 0), 4 + inv_progress * 4, 4 + inv_progress * 4)
                # 墨迹微粒飞溅（模拟纸纤维吸墨不均）
                splatter = QColor(ink_base)
                splatter.setAlpha(int(12 * inv_progress))
                painter.setBrush(QBrush(splatter))
                splat_count = int(6 + inv_progress * 10)
                for _ in range(splat_count):
                    angle = random.random() * math.pi * 2
                    dist = (5 + inv_progress * 12) * (0.4 + random.random() * 0.6)
                    sx = math.cos(angle) * dist
                    sy = math.sin(angle) * dist
                    sr = 0.5 + random.random() * 1.5
                    painter.drawEllipse(QPointF(sx, sy), sr, sr)
                painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.setPen(color)
            
            painter.drawText(text_rect, Qt.TextWordWrap, c.content)
            painter.restore()
        
        self._clean_comment_alpha_cache()
        
        painter.setOpacity(1.0)
    
    def _clean_comment_alpha_cache(self):
        """清理批注透明度缓存中过期的条目。"""
        valid_ids = {c.comment_id for c in self._comments}
        keys_to_remove = [k for k in self._comment_alpha_cache.keys() if k not in valid_ids]
        for k in keys_to_remove:
            del self._comment_alpha_cache[k]

    # ========== 批注布局（落在页面两侧留白带，不覆盖用户所写文字） ==========
    def _comment_font_size(self, c):
        return 8 + (c.comment_id % 3)   # 8/9/10pt，比正文更小

    def _comment_gutter_bounds(self, side):
        """返回某侧留白带的 [x0, x1] 区间（文字居中，批注在两侧）。"""
        gw = self._gutter_width()
        margin = 14
        if side == 'left':
            return margin, gw - margin
        return self.width() - gw + margin, self.width() - margin

    def _pick_handwriting_font(self):
        """批注统一使用的手写体：固定为品牌手写体(张穸洛浮生楷体)，
        不随正文导入字体改变；品牌字体不可用时回退宋体。"""
        return self._brand_font_family()

    def register_imported_font(self, family: str):
        """登记一个已通过 QFontDatabase.addApplicationFont 加载的手写字体族。"""
        if family and family not in self._imported_fonts:
            self._imported_fonts.append(family)

    def unregister_imported_font(self, family: str):
        """移除一个导入字体：从可用列表删除，并把曾使用该字体的批注改绑到其它字体。
        若该字体恰是正文手写体，则回退到其它可用手写体并清除持久化选择。"""
        if family in self._imported_fonts:
            self._imported_fonts.remove(family)
        changed = False
        for c in self._comments:
            if c.font_path == family:
                c.font_path = self._pick_handwriting_font()
                changed = True
        if family and family == self._body_handwriting_font:
            # 正文手写体被删：回退到其它可用手写体，并清除持久化选择（重启会重新解析）
            self._body_handwriting_font = self._resolve_handwriting_font()
            db.set_setting("default_handwriting_family", "")
        if changed or (family and family == self._body_handwriting_font):
            self.update()

    def rebind_all_comments_to_font(self, family: str):
        """将当前页面所有批注重新绑定到指定手写字体（导入后立即生效）。"""
        for c in self._comments:
            c.font_path = family
        self.update()

    def _comment_block_metrics(self, c, gutter_width=None):
        """返回 (max_width, block_height)：与 _draw_comments 中
        drawText(QRectF(0,0,max_width,9999), WordWrap) 真实换行后占用的尺寸一致。
        用 boundingRect 取得真实行高，避免手算行数在标点/混排/手写体下偏差导致批注重叠。"""
        if gutter_width is None:
            side = 'left' if (c.comment_id % 2 == 0) else 'right'
            x0, x1 = self._comment_gutter_bounds(side)
            gutter_width = x1 - x0
        max_width = gutter_width - 24 if gutter_width > 24 else 100
        fs = self._comment_font_size(c)
        # 批注使用"当前字体"（与文案一致，钉住不随切换改变）
        font = QFont(self.copy_font_family(), fs)
        font.setItalic(True)
        fm = QFontMetrics(font)
        block_rect = fm.boundingRect(QRect(0, 0, int(max_width), 9999), Qt.TextWordWrap, c.content)
        return max_width, block_rect.height()

    def _comment_avoid_pos(self, c):
        """返回批注绘制锚点 (dx, dy)。

        批注固定在页面两侧留白带（左/右），与中央书写列互不重叠；
        同侧批注按 comment_id 顺序占稳定槽位自上而下排布，
        不因逐帧计算而上下跳动；槽位高度用 QFontMetrics.boundingRect
        取真实换行高度，避免标点/混排/手写体下手算行数偏差造成重叠。
        """
        fs = self._comment_font_size(c)
        # 批注使用"当前字体"（与文案一致，钉住不随切换改变）
        font = QFont(self.copy_font_family(), fs)
        font.setItalic(True)
        fm = QFontMetrics(font)
        cw = fm.width(c.content)
        # 侧边由 comment_id 奇偶决定（左右交替），稳定不随窗口缩放翻转
        side = 'left' if (c.comment_id % 2 == 0) else 'right'
        x0, x1 = self._comment_gutter_bounds(side)
        # x 锚定在留白带"靠内侧"（贴近中央正文列），放大时不被甩到窗口两边
        gap = 12  # 与正文列之间的间隙
        if x1 - cw >= x0:
            bx = (x1 - cw - gap) if side == 'left' else (x0 + gap)
        else:
            bx = (x1 - cw) if side == 'left' else x0
        # 稳定槽位：同侧批注按创建顺序排布，位置固定，不抖动
        gutter_width = x1 - x0
        # 用 boundingRect 取得真实换行后高度；并计入 rotate_angle 旋转后的
        # 包围盒垂直高度(h*cosθ + w*sinθ)，否则倾斜批注会向上下延伸与相邻批注重叠。
        _, actual_height = self._comment_block_metrics(c, gutter_width)
        total_height = 0
        for oc in self._comments:
            if ((oc.comment_id % 2 == 0) == (side == 'left')) and oc.comment_id < c.comment_id:
                _, oactual_height = self._comment_block_metrics(oc, gutter_width)
                rot = math.radians(abs(oc.rotate_angle or 0))
                ocw = gutter_width - 24
                vis_h = oactual_height * math.cos(rot) + ocw * math.sin(rot)
                total_height += vis_h + 40
        top = self._text_top() + fm.height()
        by = top + total_height
        return bx, by

    def _draw_light_sweep(self, painter: QPainter, w: int, h: int):
        """20秒周期缓慢移动的窗边柔光：浅色暖光、深色冷光，光影节奏一致。"""
        if self.is_sealed or self._perf_tier == PerfTier.LOW:
            return
        phase = (self._anim_time % (DURATION_LIGHT_SWEEP / 1000)) / (DURATION_LIGHT_SWEEP / 1000)
        # 光心水平缓慢移动
        light_cx = w * (0.5 + math.sin(phase * 2 * math.pi) * LIGHT_SWEEP_CENTER_X_AMPLITUDE)
        light_cy = h * LIGHT_SWEEP_CENTER_Y_BASE

        max_dist = math.sqrt(w * w + h * h) * LIGHT_SWEEP_RADIUS

        # 浅色=暖白窗光；深色=冷调月光般柔光（更克制），光影语言统一
        if self._dark_mode:
            base = LIGHT_SWEEP_COLOR_DARK
            alpha_max = LIGHT_SWEEP_ALPHA_MAX_DARK
        else:
            base = LIGHT_SWEEP_COLOR
            alpha_max = LIGHT_SWEEP_ALPHA_MAX

        # 使用径向渐变模拟光斑
        gradient = QRadialGradient(light_cx, light_cy, max_dist)
        light_color = QColor(base)
        light_color.setAlpha(int(255 * alpha_max))
        mid_color = QColor(base).darker(120)
        transparent = QColor(base)
        transparent.setAlpha(0)
        gradient.setColorAt(0.0, light_color)
        gradient.setColorAt(0.4, mid_color)
        gradient.setColorAt(1.0, transparent)

        painter.setBrush(QBrush(gradient))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRect(0, 0, w, h)

    def _draw_dust_particles(self, painter: QPainter):
        """空中漂浮的尘埃粒子。

        两模式统一克制：按当前模式取"贴近底色"的柔灰，避免浅色米色上的灰褐圆点、
        或深色暗底上的亮灰点显得突兀；同时整体降低不透明度。
        """
        if self._perf_tier == PerfTier.LOW:
            return
        # 双模式尘埃色：浅色用偏暗暖棕灰（落在米白纸上的落灰）、
        # 深色用偏亮暖浅灰（暗底上反光的微尘），各自与底色拉开对比度、彼此区分明显。
        dust_col = QColor(*DUST_COLOR_LIGHT) if not self._dark_mode else QColor(*DUST_COLOR_DARK)
        for p in self._dust_particles:
            painter.setOpacity(p.alpha * 0.50)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(dust_col))
            painter.drawEllipse(QPointF(p.x, p.y), p.radius, p.radius)
        painter.setOpacity(1.0)

    def _draw_sealed_overlay(self, painter: QPainter, w: int, h: int):
        """封存页面 v2 —— 撕裂纸边纹理 + sepia 褪色滤镜 + 颗粒泛黄 + 暗角。

        视觉层次（由底→顶）：
          1. 牛皮纸遮罩（sepia 底调）
          2. 颗粒泛黄 dither 层
          3. 撕裂纸边锯齿纹理
          4. 四边暗角晕影
          5. 标题/提示文字
          6. 解封进度环（如果长按中）
        """
        # ---- 0. 确定基础色调 ----
        if self._dark_mode:
            sepia_base = QColor(*SEALED_LOWLIGHT_RGB)      # 暗色 sepia 底
            edge_color = QColor(*SEALED_OVERLAY_LIGHT_RGB, SEALED_OVERLAY_LIGHT_ALPHA)
            grain_alpha = SEALED_GRAIN_ALPHA
        else:
            sepia_base = QColor(SEALED_OVERLAY_COLOR)
            edge_color = QColor(180, 160, 130, 55)
            grain_alpha = 14

        # ---- 1. 牛皮纸 sepia 遮罩 ----
        overlay = QColor(sepia_base)
        overlay.setAlpha(int(255 * SEALED_OVERLAY_ALPHA))
        painter.fillRect(0, 0, w, h, overlay)

        # ---- 2. 褪色/泛黄叠加层（sepia warmth） ----
        fade_tint = QColor(SEALED_SEPIA_LIGHT if not self._dark_mode else SEALED_SEPIA_DARK)
        fade_tint.setAlpha(25 if not self._dark_mode else 18)
        painter.fillRect(0, 0, w, h, fade_tint)

        # ---- 3. 颗粒泛黄（procedural grain dither） ----
        # 使用确定性 hash 而非 random，保证每帧一致性 & 不高频抖闪
        painter.setPen(Qt.PenStyle.NoPen)
        seed_str = f"{self.page_id}_{self._seed_grain if hasattr(self, '_seed_grain') else 0}"
        seed_int = int(hashlib.md5(seed_str.encode()).hexdigest()[:8], 16)
        rng = random.Random(seed_int)
        grain = QColor(*SEALED_GRAIN_RGB_LIGHT, grain_alpha) if not self._dark_mode else QColor(*SEALED_GRAIN_RGB_DARK, grain_alpha)
        painter.setBrush(QBrush(grain))
        grain_count = int(w * h * 0.00008)  # ~200 点/1920px
        for _ in range(grain_count):
            gx = rng.random() * w
            gy = rng.random() * h
            gs = 1.0 + rng.random() * 1.8
            painter.drawEllipse(QPointF(gx, gy), gs, gs)

        # ---- 4. 撕裂纸边 —— 上下锯齿纹理 ----
        pen = QPen(edge_color)
        pen.setWidthF(0.8)
        painter.setPen(pen)
        painter.setOpacity(0.22)
        # 顶部撕裂锯齿
        top_points: list[tuple[float, float]] = []
        step = max(6, w / 60)  # ~30 个锯齿点
        x = 0.0
        while x <= w:
            jitter = (math.sin(x * 0.15 + seed_int * 0.001) * 5.5 +
                      math.cos(x * 0.23 + 3.7) * 3.5)
            y_top = max(4, 10 + jitter)
            top_points.append((x, y_top))
            x += step
        # 锯齿连线
        for i in range(len(top_points) - 1):
            painter.drawLine(
                QPointF(top_points[i][0], top_points[i][1]),
                QPointF(top_points[i + 1][0], top_points[i + 1][1])
            )
        # 底部撕裂锯齿
        bottom_points: list[tuple[float, float]] = []
        x = 0.0
        while x <= w:
            jitter = (math.sin(x * 0.13 + seed_int * 0.002) * 4.5 +
                      math.cos(x * 0.27 + 1.2) * 3.0)
            y_bot = min(h - 4, h - 10 - jitter)
            bottom_points.append((x, y_bot))
            x += step
        for i in range(len(bottom_points) - 1):
            painter.drawLine(
                QPointF(bottom_points[i][0], bottom_points[i][1]),
                QPointF(bottom_points[i + 1][0], bottom_points[i + 1][1])
            )

        # 撕裂纸边 —— 纸纤维残留（微小碎线从锯齿处垂下）
        pen.setWidthF(0.5)
        painter.setPen(pen)
        for i in range(int(len(top_points) * 0.3)):
            idx = rng.randint(0, len(top_points) - 1)
            px, py = top_points[idx]
            fiber_len = 2 + rng.random() * 5
            painter.drawLine(QPointF(px, py), QPointF(px + rng.random() * 3 - 1.5,
                                                       py + fiber_len))
        for i in range(int(len(bottom_points) * 0.3)):
            idx = rng.randint(0, len(bottom_points) - 1)
            px, py = bottom_points[idx]
            fiber_len = 2 + rng.random() * 4
            painter.drawLine(QPointF(px, py), QPointF(px + rng.random() * 3 - 1.5,
                                                       py - fiber_len))
        painter.setOpacity(1.0)

        # ---- 5. 四边暗角晕影 ----
        painter.setPen(Qt.PenStyle.NoPen)
        margin_w = int(w * 0.15)
        margin_h = int(h * 0.15)
        vig = QColor(0, 0, 0, int(255 * SEALED_VIGNETTE_INTENSITY))
        grad_top = QLinearGradient(0, 0, 0, margin_h)
        grad_top.setColorAt(0, vig)
        grad_top.setColorAt(1, QColor(0, 0, 0, 0))
        painter.setBrush(QBrush(grad_top))
        painter.drawRect(0, 0, w, margin_h)
        grad_bot = QLinearGradient(0, h, 0, h - margin_h)
        grad_bot.setColorAt(0, vig)
        grad_bot.setColorAt(1, QColor(0, 0, 0, 0))
        painter.setBrush(QBrush(grad_bot))
        painter.drawRect(0, h - margin_h, w, margin_h)
        vig2 = QColor(0, 0, 0, int(255 * SEALED_VIGNETTE_INTENSITY * 0.6))
        grad_left = QLinearGradient(0, 0, margin_w, 0)
        grad_left.setColorAt(0, vig2)
        grad_left.setColorAt(1, QColor(0, 0, 0, 0))
        painter.setBrush(QBrush(grad_left))
        painter.drawRect(0, 0, margin_w, h)
        grad_right = QLinearGradient(w, 0, w - margin_w, 0)
        grad_right.setColorAt(0, vig2)
        grad_right.setColorAt(1, QColor(0, 0, 0, 0))
        painter.setBrush(QBrush(grad_right))
        painter.drawRect(w - margin_w, 0, margin_w, h)

        # ---- 5b. 褪色二次强调（让文字看起来更旧）----
        fade2 = QColor(SEALED_HIGHLIGHT_LIGHT if not self._dark_mode else SEALED_HIGHLIGHT_DARK)
        fade2.setAlpha(18)
        painter.fillRect(0, 0, w, h, fade2)

        # 顶部中央 "已封存" 标签（10pt，文档规定）+ 诗意副标题
        painter.setPen(QColor(TEXT_COLOR))
        painter.setOpacity(0.6)

        # 主标签
        font = QFont(self._serif_font, 10)
        font.setItalic(True)
        painter.setFont(font)
        painter.drawText(0, 44, w, 24, Qt.AlignmentFlag.AlignHCenter, "已封存")

        # 副标题 —— 微妙的仪式感
        font_sub = QFont(self._serif_font, 8)
        painter.setFont(font_sub)
        painter.setOpacity(0.35)
        painter.drawText(0, 68, w, 20, Qt.AlignmentFlag.AlignHCenter, "时间在此停驻，字迹将不再褪去。")

        # 微微的静止光晕 —— 暗示时间的停滞
        center_glow = QRadialGradient(w / 2, 100, w * 0.35)
        center_glow.setColorAt(0, QColor(SEALED_HALO_LIGHT))
        center_glow.setColorAt(0.4, QColor(SEALED_HALO_LIGHT))
        center_glow_core = QColor(SEALED_HALO_LIGHT)
        center_glow_core.setAlpha(0)
        center_glow.setColorAt(1, center_glow_core)
        painter.setBrush(QBrush(center_glow))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setOpacity(0.06)
        painter.drawEllipse(QPointF(w / 2, 80), w * 0.35, 120)

        # ---- 解封长按进度环 ----
        if self._unseal_pressing and self._unseal_progress > 0:
            painter.save()
            painter.setOpacity(0.7)
            cx, cy = self._unseal_press_pos.x(), self._unseal_press_pos.y()
            radius = 28
            # 外圈暗底
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(0, 0, 0, 28))
            painter.drawEllipse(QPointF(cx, cy), radius, radius)
            # 进度弧
            pen = QPen()
            pen.setWidth(3)
            pen.setColor(QColor(SEALED_HALO_DARK))
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            span = int(self._unseal_progress * 360 * 16)
            painter.drawArc(QRectF(cx - radius + 3, cy - radius + 3,
                                   (radius - 3) * 2, (radius - 3) * 2),
                            90 * 16, -span)
            # 中心图标：锁→开锁过渡
            painter.setPen(QColor(SEALED_HALO_DARK))
            f = QFont(self._serif_font, 11)
            painter.setFont(f)
            if self._unseal_progress >= 0.9:
                symbol = "✦"
            elif self._unseal_progress >= 0.5:
                symbol = "◇"
            else:
                symbol = "◆"
            painter.drawText(QRectF(cx - 20, cy - 14, 40, 28),
                             Qt.AlignmentFlag.AlignCenter, symbol)
            # 进度百分比小字
            pct = int(self._unseal_progress * 100)
            f2 = QFont(self._serif_font, 7)
            painter.setFont(f2)
            painter.setOpacity(0.5)
            painter.drawText(QRectF(cx - 20, cy - 34, 40, 16),
                             Qt.AlignmentFlag.AlignCenter, f"{pct}%")
            painter.restore()
        # ---- 解封提示文案（非长按中时显示） ----
        elif not self._unseal_pressing:
            f_hint = QFont(self._serif_font, 8)
            painter.setFont(f_hint)
            painter.setPen(QColor(TEXT_COLOR))
            painter.setOpacity(0.25)
            painter.drawText(0, h - 36, w, 20,
                             Qt.AlignmentFlag.AlignHCenter,
                             "长按画面即可解封 · 让褪色的字重新远行")

        painter.setOpacity(1.0)

    def _draw_page_turn_animation(self, painter: QPainter, w: int, h: int):
        """Tier 3 深层尘封解锁：全局纸张光影翻页动画（1000ms）。"""
        t = self._page_turn_anim  # 0→1

        # 光影：页面中央一道光横扫（模拟翻页的光线变化）
        sweep_x = w * (0.5 + math.sin(t * math.pi) * 0.6)
        sweep_w = w * (0.15 + 0.25 * math.sin(t * math.pi * 2))

        # 高光渐变：从中心向两侧
        grad = QLinearGradient(sweep_x - sweep_w / 2, 0, sweep_x + sweep_w / 2, 0)
        center_alpha = int(80 * math.sin(t * math.pi))  # 最高 80，翻毕归零
        grad.setColorAt(0.0, QColor(*PAGE_TURN_COLOR, 0))
        grad.setColorAt(0.4, QColor(*PAGE_TURN_COLOR, center_alpha))
        grad.setColorAt(0.6, QColor(*PAGE_TURN_COLOR, center_alpha))
        grad.setColorAt(1.0, QColor(*PAGE_TURN_COLOR, 0))
        painter.fillRect(0, 0, w, h, grad)

        # 全局微微暗一下再恢复（纸张被"翻了一下"的感觉）
        dim_alpha = int(30 * math.sin(t * math.pi))
        if dim_alpha > 0:
            painter.fillRect(0, 0, w, h, QColor(0, 0, 0, dim_alpha))

    def _draw_empty_hint(self, painter: QPainter, w: int, h: int):
        """空状态文艺提示 —— 多句轮播 + 缓慢淡入淡出。

        本页曾落笔、如今字已全散 → 用专属"曾写全散"文案(EMPTY_HINTS_FADED)；
        从未写过 → 用常规引导文案(EMPTY_HINTS)。
        """
        hints = EMPTY_HINTS_FADED if self._ever_had_words else EMPTY_HINTS
        if not hints:
            return

        # 每 8 秒切换一句，1.5 秒淡出 + 1.5 秒淡入（正确的交叉淡入淡出）
        SWITCH_INTERVAL = 8.0
        FADE_DURATION = 1.5
        total = SWITCH_INTERVAL * len(hints)
        cycle_time = (self._anim_time + self._empty_hint_phase) % total
        slot = cycle_time / SWITCH_INTERVAL
        idx = int(slot)
        frac = slot - idx
        fade_frac = FADE_DURATION / SWITCH_INTERVAL

        text_color = QColor(DARK_HINT if self._dark_mode else HINT_TEXT_COLOR)
        font = self._copy_font(16)
        painter.setFont(font)
        fm = QFontMetrics(font)
        ty = h // 2 + int(fm.ascent() * 0.35)

        def _draw_hint(text, alpha):
            if alpha <= 0.01:
                return
            breath = (math.sin(self._anim_time * 0.3) + 1) * 0.5
            col = QColor(text_color)
            col.setAlpha(int((130 + breath * 80) * alpha))
            painter.setPen(col)
            tw = fm.horizontalAdvance(text)
            painter.drawText((w - tw) // 2, ty, text)

        # 同一时刻只显示一句，用 alpha 包络（淡入→保持→淡出），
        # 避免两句不同长度文字同时居中重叠导致的"乱跳"。
        if frac < fade_frac:
            alpha = frac / fade_frac
        elif frac > 1 - fade_frac:
            alpha = (1 - frac) / fade_frac
        else:
            alpha = 1.0
        _draw_hint(hints[idx % len(hints)], alpha)

    def _draw_cursor(self, painter: QPainter):
        """暖墨渗纸光标 —— 对齐文字行高的墨色竖笔，带柔和呼吸。"""
        if not self._cursor_visible:
            return
        if self.is_sealed:
            return

        # 呼吸周期：更缓慢的暖光脉动（周期约 8 秒）
        breath = (math.sin(self._anim_time * 0.8) + 1.0) * 0.5  # 0~1

        # 墨色：墨水色
        base_color = QColor(CURSOR_COLOR) if not self._dark_mode else QColor(CURSOR_COLOR_DARK)
        glow_color = QColor(CURSOR_GLOW_COLOR) if not self._dark_mode else QColor(CURSOR_GLOW_COLOR_DARK)

        fm = self._body_metrics(BODY_FONT_SIZE)
        # 光标精确对齐文字行高：文字基线为 self._input_y
        top = int(self._input_y - fm.ascent())
        bottom = int(self._input_y + fm.descent())
        cx = int(self._input_x + 1)

        # 外层柔光：沿竖线方向的极淡宽描边，而非圆形墨点
        soft = QColor(glow_color)
        soft.setAlpha(int((30 + breath * 25)))
        painter.setPen(QPen(soft, 5, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        painter.setOpacity(0.5)
        painter.drawLine(cx, top, cx, bottom)
        painter.setOpacity(1.0)

        # 主墨线（均匀墨色竖笔，呼吸微调浓淡）
        main = QColor(base_color)
        main.setAlpha(int(200 + breath * 55))
        painter.setPen(QPen(main, 1.8, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        painter.drawLine(cx, top, cx, bottom)

    def _draw_placeholder(self, painter: QPainter):
        """半透明占位示例文字：帮助用户'进入状态'，开始打字后自动淡出。"""
        a = self._placeholder_alpha
        if a <= 0.01:
            return
        # 本页选定句（随机）；兜底取列表首句
        sample = self._placeholder_text or PLACEHOLDER_SAMPLES[0]
        # 占位文案始终使用手写体（如果有可用手写字体），固定为"当前字体"，不随正文手写体切换而变
        font = self._copy_font(BODY_FONT_SIZE)
        fm = QFontMetrics(font)
        max_w = max(80, self.width() - self._input_x * 2)
        # 按字符宽度折行（支持显式换行）
        lines, cur = [], ""
        for ch in sample:
            if ch == "\n":
                lines.append(cur); cur = ""
            elif fm.horizontalAdvance(cur + ch) > max_w:
                lines.append(cur); cur = ch
            else:
                cur += ch
        if cur:
            lines.append(cur)
        color = QColor(HINT_TEXT_COLOR_DARK if self._dark_mode else HINT_TEXT_COLOR)
        color.setAlpha(int(255 * a * 0.55))   # 半透明占位态
        painter.setFont(font)
        painter.setPen(color)
        lh = int(fm.height())
        x = int(self._input_x)
        y = int(self._input_y)
        for i, line in enumerate(lines):
            painter.drawText(x, y + i * lh, line)

    # ========== 鼠标/交互事件 ==========

    def mouseMoveEvent(self, event):
        if self.is_sealed:
            # 封存页面：长按解封——移动过大则取消
            if self._unseal_pressing:
                delta = event.pos() - self._unseal_press_pos
                if abs(delta.x()) > 30 or abs(delta.y()) > 30:
                    self._cancel_unseal_longpress()
            return
        pos = event.pos()
        now = time.time()

        # 空白处按下并移动 = 拖动无边框窗口（OpenHand→ClosedHand）
        if self._drag_candidate:
            if (pos - self._drag_press).manhattanLength() > 4:
                self._window_dragging = True
                self.setCursor(Qt.CursorShape.ClosedHandCursor)
            if self._window_dragging:
                win = self.window()
                if win is not None:
                    win.move(event.globalPos() - self._win_drag_offset)
                return

        nearest_idx = -1

        for i, w in enumerate(self._words):
            alpha = compute_alpha(w.create_timestamp, w.life_total_sec,
                                 w.revive_count or 0, now)
            afterglow_alpha = compute_afterglow_alpha(
                w.create_timestamp, w.life_total_sec, now
            )
            if alpha <= 0 and afterglow_alpha <= 0:
                continue
            fm = self._body_metrics(BODY_FONT_SIZE)
            tw = fm.width(w.content)
            th = fm.height()
            # 精确矩形检测，鼠标必须落在文字范围内
            mx = pos.x()
            my = pos.y() + self._scroll_y
            if w.x <= mx <= w.x + tw and w.y - th <= my <= w.y:
                nearest_idx = i
                break

        if nearest_idx != self._hover_word_idx:
            self._hover_word_idx = nearest_idx
            self._hover_hold_timer = 0
            if nearest_idx >= 0:
                self._hover_active = True
            else:
                self._hover_active = False

        # 检测批注悬停（终身锁定：临时 alpha=1.0）
        self._prev_hovered_comment_id = self._hovered_comment_id
        self._hovered_comment_id = -1
        for c in self._comments:
            # 用与绘制一致的避让坐标，确保鼠标落在"实际显示位置"才命中
            _ax, _ay = self._comment_avoid_pos(c)
            side = 'left' if (c.comment_id % 2 == 0) else 'right'
            x0, x1 = self._comment_gutter_bounds(side)
            gutter_width = x1 - x0
            max_width, actual_height = self._comment_block_metrics(c, gutter_width)
            # 鼠标坐标换算到内容坐标（加滚动偏移）
            mx = pos.x()
            my = pos.y() + self._scroll_y
            # 绘制时以 (_ax, _ay) 为局部原点、顶部对齐绘制文本块，
            # 文本占据局部 [0, max_width] × [0, actual_height]；
            # 含旋转时做逆变换回到局部坐标再判定（与 painter.rotate 对称）
            dx, dy = mx - _ax, my - _ay
            ang = math.radians(c.rotate_angle or 0)
            lx = dx * math.cos(ang) + dy * math.sin(ang)
            ly = -dx * math.sin(ang) + dy * math.cos(ang)
            if 0 <= lx <= max_width and 0 <= ly <= actual_height:
                self._hovered_comment_id = c.comment_id
                break

        # 悬停进入时增加 hover_count
        if self._hovered_comment_id != self._prev_hovered_comment_id:
            if self._prev_hovered_comment_id > 0:
                # 离开旧批注：不做额外操作（alpha 自动复原已在渲染中处理）
                pass
            if self._hovered_comment_id > 0:
                db.increment_comment_hover(self._hovered_comment_id)

        # 光标形态：文字/批注上→手型，空白处→文本输入光标
        if nearest_idx >= 0 or self._hovered_comment_id > 0:
            self.setCursor(Qt.CursorShape.PointingHandCursor)
        else:
            self.setCursor(Qt.CursorShape.IBeamCursor)

    def mousePressEvent(self, event):
        # ---- 封存页面：长按解封 ----
        if self.is_sealed:
            if event.button() == Qt.MouseButton.LeftButton:
                self._unseal_pressing = True
                self._unseal_press_pos = event.pos()
                self._unseal_hold_time = 0.0
                self._unseal_progress = 0.0
                self.setCursor(Qt.CursorShape.BusyCursor)
                self.toast_requested.emit("按住不放，封印将松动…")
            return

        if event.button() == Qt.MouseButton.LeftButton:
            self.setFocus()
            self._cursor_user_activated = True
            pos = event.pos()
            hit_word = self._hit_word(pos)
            if hit_word is None and self._hovered_comment_id <= 0:
                # 空白处按下：可能是拖动窗口，也可能是点击定位光标，延迟到释放判定
                self._drag_candidate = True
                self._drag_press = event.pos()
                self._window_dragging = False
                win = self.window()
                self._win_drag_offset = (event.globalPos() - win.frameGeometry().topLeft()) if win is not None else QPoint(0, 0)
                self.setCursor(Qt.CursorShape.OpenHandCursor)
            else:
                # 文字/批注上：直接定位光标（保持编辑体验），不进入拖拽
                self._drag_candidate = False
                ww = self.width()
                wh = self.height()
                cx = max(self._text_left() + 4, min(pos.x(), self._text_right()))
                cy = max(self._text_top(), min(pos.y() + self._scroll_y, self._scroll_y + (wh - WRITING_AREA_MARGIN)))
                self._cursor_index = self._nearest_insert_index(cx, cy)
                self._sync_cursor(scroll_into_view=False)

        elif event.button() == Qt.MouseButton.RightButton:
            # 右键无操作——批注由旧主人魂魄在停笔时自动留下
            pass

    def mouseReleaseEvent(self, event):
        if self.is_sealed:
            # 封存页面：长按解封——松手时判定是否完成 5 秒
            if self._unseal_pressing and event.button() == Qt.MouseButton.LeftButton:
                if self._unseal_hold_time >= 5.0:
                    self._unseal_pressing = False
                    self.setCursor(Qt.CursorShape.ForbiddenCursor)
                    self.toast_requested.emit(TOAST_UNSEALING_PROGRESS)
                    self.unseal_requested.emit(self.page_id or 0)
                else:
                    self._cancel_unseal_longpress()
            return

        if event.button() == Qt.MouseButton.LeftButton:
            if self._drag_candidate and not self._window_dragging:
                # 视为点击：将光标移动到点击处
                pos = event.pos()
                ww = self.width()
                wh = self.height()
                cx = max(self._text_left() + 4, min(pos.x(), self._text_right()))
                cy = max(self._text_top(), min(pos.y() + self._scroll_y, self._scroll_y + (wh - WRITING_AREA_MARGIN)))
                self._cursor_index = self._nearest_insert_index(cx, cy)
                self._sync_cursor(scroll_into_view=False)
            self._drag_candidate = False
            self._window_dragging = False
            self.setCursor(Qt.CursorShape.IBeamCursor)
        super().mouseReleaseEvent(event)

    # ---- 长按解封辅助 ----
    def _cancel_unseal_longpress(self):
        self._unseal_pressing = False
        self._unseal_progress = 0.0
        self._unseal_hold_time = 0.0
        self.setCursor(Qt.CursorShape.ArrowCursor)

    def mouseDoubleClickEvent(self, event):
        """双击删除文字，并把光标移到该处。"""
        if self.is_sealed:
            return
        pos = event.pos()
        now = time.time()
        for i, w in enumerate(self._words):
            if w.content == '\n':
                continue
            alpha = compute_alpha(w.create_timestamp, w.life_total_sec,
                                 w.revive_count or 0, now)
            if alpha <= 0:
                continue
            fm = self._body_metrics(BODY_FONT_SIZE)
            tw = fm.width(w.content)
            th = fm.height()
            if w.x <= pos.x() <= w.x + tw and w.y - th <= pos.y() + self._scroll_y <= w.y:
                self._spawn_dissolve_particles(w)
                try:
                    db.delete_word(w.word_id)
                except Exception:
                    pass
                del self._words[i]
                self._cursor_index = i
                self._char_count = max(0, self._char_count - (0 if w.content == '\n' else 1))
                self.char_count_changed.emit(self._char_count)
                self._reflow_from(i)
                self._sync_cursor()
                self._hover_word_idx = -1
                self._hover_active = False
                self._hovered_comment_id = -1
                break

    def _hit_word(self, pos) -> int:
        """返回点击位置下方的文字索引，无则 -1。"""
        now = time.time()
        fm = self._body_metrics(BODY_FONT_SIZE)
        for i, w in enumerate(self._words):
            alpha = compute_alpha(w.create_timestamp, w.life_total_sec,
                                 w.revive_count or 0, now)
            if alpha <= 0:
                continue
            tw = fm.width(w.content)
            th = fm.height()
            if w.x <= pos.x() <= w.x + tw and w.y - th <= pos.y() + self._scroll_y <= w.y:
                return i
        return -1

    # ========== 垂直无限滚动 ==========
    def _max_scroll(self) -> float:
        """内容可滚动的最大距离：保证最底一行完整可见并留一行余量。"""
        bottom_y = self._text_top()
        for wd in self._words:
            if wd.content != '\n' and wd.y > bottom_y:
                bottom_y = wd.y
        visible_bottom = self.height() - WRITING_AREA_MARGIN
        return max(0.0, bottom_y + LINE_STEP - visible_bottom)

    def _clamp_scroll(self, val: float) -> float:
        return max(0.0, min(val, self._max_scroll()))

    def _start_smooth_scroll(self):
        if not self._scroll_timer.isActive():
            self._scroll_timer.start(16)

    def _on_scroll_tick(self):
        diff = self._scroll_target - self._scroll_y
        if abs(diff) < 0.4:
            self._scroll_y = self._scroll_target
            self._scroll_timer.stop()
        else:
            # 柔和阻尼：缓慢收敛，不超调、不弹跳（模拟纸张拖动厚重感）
            self._scroll_y += diff * 0.14
        self.update()

    def _ensure_cursor_visible(self):
        """让当前光标始终落在可视书写区内（写满时旧文字自然向上远去）。"""
        cx, cy = self._cursor_pos()
        vh = self.height()
        top_limit = self._scroll_y + self._text_top()
        bottom_limit = self._scroll_y + (vh - WRITING_AREA_MARGIN)
        if cy > bottom_limit - LINE_STEP:
            self._scroll_target = max(0.0, cy - (vh - WRITING_AREA_MARGIN) + LINE_STEP)
        elif cy < top_limit:
            self._scroll_target = max(0.0, cy - self._text_top())
        self._scroll_target = self._clamp_scroll(self._scroll_target)
        self._start_smooth_scroll()

    def wheelEvent(self, event):
        """滚轮上下滚动浏览整条时间线（垂直无限滚动）。"""
        delta = event.angleDelta().y()
        # 每次滚动约半行，配合柔和阻尼缓动，不快速弹跳
        self._scroll_target = self._clamp_scroll(self._scroll_target - delta * 0.5)
        self._start_smooth_scroll()

    # ========== 光标与排版（支持中间位置光标、插入/删除）==========

    def _gutter_width(self) -> int:
        """左右两侧批注留白带宽度（随窗口缩放）。"""
        return max(180, int(self.width() * COMMENT_GUTTER_RATIO))

    def _text_left(self) -> int:
        """中央书写列左边界（文字在中间，批注在两侧）。"""
        return self._gutter_width()

    def _text_right(self) -> int:
        """中央书写列右边界。"""
        return self.width() - self._gutter_width()

    def _text_top(self) -> int:
        """中央书写列顶部（避开顶部工具栏）。"""
        return WRITING_AREA_MARGIN + 24

    def _right_limit(self) -> int:
        return self._text_right()

    def _char_width(self, content: str) -> int:
        if content == ' ' or content == '\n':
            return 10
        fm = self._body_metrics(BODY_FONT_SIZE)
        return fm.horizontalAdvance(content)

    def _reflow_from(self, start: int, persist: bool = True):
        """从 start 处起重排 _words[start:] 的坐标（基于前字位置，右边界换行）。"""
        spacing = 1.5 if self._use_handwriting else 1
        if start <= 0 or not self._words:
            cx = self._text_left() + 4
            cy = self._text_top()
        else:
            prev = self._words[start - 1]
            if prev.content == '\n':
                cx = self._text_left() + 4
                cy = prev.y + LINE_STEP
            else:
                cw = self._char_width(prev.content)
                cx = prev.x + cw + spacing
                cy = prev.y
                if cx > self._right_limit():
                    cx = self._text_left() + 4
                    cy = cy + LINE_STEP
        n = len(self._words)
        for j in range(max(start, 0), n):
            wd = self._words[j]
            if wd.content == '\n':
                wd.x = cx
                wd.y = cy
                cx = self._text_left() + 4
                cy = cy + LINE_STEP
                continue
            cw = self._char_width(wd.content)
            wd.x = cx
            wd.y = cy
            ncx = cx + cw + spacing
            if ncx > self._right_limit() and j < n - 1:
                cx = self._text_left() + 4
                cy = cy + LINE_STEP
            else:
                cx = ncx
        if persist:
            positions = []
            for j in range(max(start, 0), n):
                wd = self._words[j]
                if wd.content == '\n':
                    continue
                positions.append((wd.word_id, wd.x, wd.y, wd.order_index))
            if positions:
                self._pending_positions = positions
                self._positions_dirty = True

    def _cursor_pos(self):
        """返回当前光标（_cursor_index 处）的视觉坐标。"""
        spacing = 1.5 if self._use_handwriting else 1
        if self._cursor_index <= 0 or not self._words:
            return self._text_left() + 4, self._text_top()
        
        # 找到最后一个非换行字符
        prev_idx = self._cursor_index - 1
        while prev_idx >= 0 and self._words[prev_idx].content == '\n':
            prev_idx -= 1
        
        if prev_idx < 0:
            return self._text_left() + 4, self._text_top()
        
        prev = self._words[prev_idx]
        cw = self._char_width(prev.content)
        cx = prev.x + cw + spacing
        cy = prev.y
        if cx > self._right_limit():
            cx = self._text_left() + 4
            cy = cy + LINE_STEP
        return cx, cy

    def _sync_cursor(self, scroll_into_view: bool = True):
        self._input_x, self._input_y = self._cursor_pos()
        # 键盘输入 / 粘贴后若光标移出可视区，柔和滚动使其可见（写满自动翻页感）
        # 加载页面与鼠标点击不强制跟随，避免一打开就跳到文末
        if scroll_into_view:
            self._ensure_cursor_visible()

    def _nearest_insert_index(self, cx: float, cy: float) -> int:
        """根据点击位置，找出最近的文字插入点索引（含换行字跳过）。"""
        if not self._words:
            return 0
        fm = self._body_metrics(BODY_FONT_SIZE)
        best_idx = 0
        best_d = float('inf')
        for i, w in enumerate(self._words):
            if w.content == '\n':
                continue
            tw = fm.width(w.content)
            th = fm.height()
            dx = max(w.x - cx, 0.0, cx - (w.x + tw))
            dy = max((w.y - th) - cy, 0.0, cy - w.y)
            d = dx * dx + dy * dy
            if d < best_d:
                best_d = d
                center = w.x + tw / 2
                best_idx = i if cx < center else i + 1
        return best_idx

    def _backspace(self):
        """删除光标前的一个字（支持中间位置删除）。"""
        if self._cursor_index <= 0:
            return
        idx = self._cursor_index - 1
        w = self._words[idx]
        self._spawn_dissolve_particles(w)
        try:
            db.delete_word(w.word_id)
        except Exception:
            pass
        del self._words[idx]
        self._cursor_index = idx
        self._char_count = max(0, self._char_count - 1)
        self.char_count_changed.emit(self._char_count)
        # 更新后续文字的 order_index
        for i in range(self._cursor_index, len(self._words)):
            self._words[i].order_index = i
        self._reflow_from(self._cursor_index)
        self._sync_cursor()
        self._hover_word_idx = -1
        self._hover_active = False
        self._hovered_comment_id = -1

    # ========== 键盘输入 ==========

    def keyPressEvent(self, event):
        if self.is_sealed:
            return

        key = event.key()
        modifiers = event.modifiers()

        # 每次按键都重置停笔计时器（旧主人的魂魄在等待沉默）
        self._pause_timer.start()

        # Ctrl 组合键
        if modifiers & Qt.ControlModifier:
            if key == Qt.Key.Key_V:
                # 粘贴：在光标处逐字插入，按写作区宽度自动换行
                clipboard = QApplication.clipboard()
                text = clipboard.text()
                if text:
                    # 规范化换行（Windows 的 \r\n / 老 Mac 的 \r → \n），避免多出一个空行
                    text = text.replace('\r\n', '\n').replace('\r', '\n')
                    for ch in text:
                        if ch == '\n':
                            self._add_word('\n')
                        elif ord(ch) >= 32 and ch.isprintable():
                            # 跳过零宽空格/控制字符等不可见字符，避免坐标错位与乱码
                            self._add_word(ch)
                    self._pause_timer.start()
                return
            elif key == Qt.Key.Key_S:
                return  # Ctrl+S 交给 main
            super().keyPressEvent(event)
            return

        if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self._add_word('\n')
            return

        if key == Qt.Key.Key_Backspace:
            self._backspace()
            return

        # 普通字符输入（ASCII 走 keyPressEvent；CJK 走 inputMethodEvent）
        text = event.text()
        if text and text.isprintable():
            self._add_word(text)

    # ========== 输入法支持（中文/日文/韩文等 CJK 输入）==========

    def inputMethodEvent(self, event: QInputMethodEvent):
        """处理 IME 组合输入（中文输入法等）。这是中文输入的唯一入口。"""
        if self.is_sealed:
            return

        commit = event.commitString()

        if commit:
            self._pause_timer.start()
            for ch in commit:
                if ch == '\n' or ch == '\r':
                    self._add_word('\n')
                elif ch.isprintable() or ord(ch) > 127:
                    self._add_word(ch)

        event.accept()

    def _add_word(self, ch: str):
        """在光标处插入单个字符（支持中间插入）。写入写作区内，超宽自动换行。"""
        if ch == '\r':
            ch = '\n'
        now = time.time()
        # 连续输入（间隔 ≤2s）的字共享同一基准寿命，仅做极小抖动（±5%），
        # 让一句话、一段随笔同生共死，避免句子内部出现“缺字”的观感。
        # 停顿超过 2s（思考/隔天）则开启新的一批，寿命自然错开。
        if now - self._last_add_time <= 2.0 and self._current_batch_life > 0:
            base_life = self._current_batch_life
        else:
            base_life = LIFE_BASE_SEC * random.uniform(0.6, 1.0)
            self._current_batch_life = base_life
        self._last_add_time = now
        life = base_life * random.uniform(0.95, 1.0)
        cx, cy = self._cursor_pos()
        w = Word(
            page_id=self.page_id,
            content=ch,
            x=cx,
            y=cy,
            create_timestamp=now,
            life_total_sec=life,
            order_index=self._cursor_index,
        )
        try:
            wid = db.add_word(w)
        except Exception as e:
            # 数据库异常（如页面未就绪）不应让整个程序崩溃
            print(f"[CanvasWidget] 写入文字失败: {e}")
            return
        w.word_id = wid
        self._words.insert(self._cursor_index, w)
        # 结构变化后清空按索引缓存的透明度动画，避免索引错位导致视觉抖动
        self._display_alpha_cache.clear()
        self._cursor_index += 1
        # 更新后续文字的 order_index
        for i in range(self._cursor_index, len(self._words)):
            self._words[i].order_index = i
        # 用户开始打字：占位示例文字淡出消失
        if self._placeholder_alpha > 0.01 and not self._placeholder_fading:
            self._placeholder_fading = True
            self._typed_pages.add(self.page_id)
        self._char_count += 1
        self.char_count_changed.emit(self._char_count)
        # 每写一个字，纸面积淀一丝暖意
        self._paper_warmth = min(self._paper_warmth + PAPER_WARMTH_PER_CHAR, PAPER_WARMTH_MAX)
        self._ever_had_words = True  # 用户落笔 → 本页记为"曾写过"，全散后走专属空状态

        # 插入点之后的字重新排版并持久化新坐标
        self._reflow_from(self._cursor_index)
        self._sync_cursor()

    # ========== 停笔检测：旧主人魂魄苏醒 ==========

    def _on_typing_pause(self):
        """停笔片刻后，旧主人魂魄苏醒。依次检查 Tier2 语义解锁 → Tier3 深层尘封 → 普通触发。"""
        if self.is_sealed:
            return
        if len(self._comments) >= COMMENT_MAX_COUNT:
            return

        # 正文不足阈值：清理该页批注（删除正文后旧批注不应残留）
        if len(self._words) < MIN_CHARS_FOR_COMMENT:
            if self._comments:
                self._clear_page_comments()
            return

        now = time.time()
        if now - self._last_comment_time < COMMENT_COOLDOWN_MS / 1000.0:
            return

        # 取最近文字
        recent_words = self._words[-40:] if len(self._words) > 40 else self._words
        recent = "".join(w.content for w in recent_words)
        if len(recent.strip()) < MIN_CHARS_FOR_COMMENT:
            return

        # === Tier 3 检测：深层尘封解锁（每页上限 1~2 条高门槛彩蛋） ===
        tier3_message = self._detect_tier3(recent)
        if tier3_message is not None:
            if db.count_comments_by_type(self.page_id, 3) < TIER3_MAX_PER_PAGE:
                self._defer_unlock(recent, tier=3, keyword=tier3_message)
            return

        # === Tier 2 检测：语义关键词解锁（按内容出现，不乱出现） ===
        tier2_keyword = self._detect_tier2(recent)
        if tier2_keyword is not None and random.random() < 0.7:
            self._defer_unlock(recent, tier=2, keyword=tier2_keyword)
            return

        # 停笔触发只为"按内容"的语义/深层批注；
        # 浅层随机批注仅在打开页面时按 30% 概率出现（见 _try_tier1_unlock），
        # 不在停笔时乱出现。
        return

    def _detect_tier2(self, text: str) -> str | None:
        """检测文本中是否命中 Tier2 关键词词库。返回命中的第一个关键词，或 None。"""
        for kw in TIER2_KEYWORDS:
            if kw in text:
                return kw
        return None

    def _detect_tier3(self, text: str) -> str | None:
        """检测 Tier 3 深层尘封触发条件。
        条件1：单句连续文字 ≥15 字 && 同一关键词重复 ≥3 次
        条件2：该主题对应文字累计续命 ≥3 次
        返回关键词或 None。"""
        # 条件1：扫描最近一段连续文字
        # 取最后 80 个字符作为"当前句子"
        tail = text[-80:] if len(text) > 80 else text
        if len(tail) >= TIER3_MIN_SENTENCE_CHARS:
            for kw in TIER2_KEYWORDS:
                count = tail.count(kw)
                if count >= TIER3_KEYWORD_REPEAT:
                    return kw

        # 条件2：累计续命 ≥3 次（该关键字相关的文字）
        for kw in TIER2_KEYWORDS:
            if kw in text:
                revives = db.get_comment_revives_by_keyword(self.page_id, kw)
                if revives >= TIER3_MIN_REVIVES:
                    return kw

        return None

    def _defer_unlock(self, recent, tier, keyword):
        """把语义/深层批注的解锁延迟到翻页或关闭时才浮现，
        让用户无法把批注精确归因于某次输入，保留'偶然发现'的惊喜。"""
        key = (tier, keyword)
        if key in self._deferred_keys:
            return
        self._deferred_keys.add(key)
        self._deferred_unlocks.append((recent, tier, keyword))

    def _flush_deferred_unlocks(self):
        """切页/关闭时把延迟的批注真正生成（归属旧页面）。"""
        if not self._deferred_unlocks:
            return
        items = self._deferred_unlocks
        self._deferred_unlocks = []
        self._deferred_keys = set()
        old_page = self.page_id
        for i, (recent, tier, keyword) in enumerate(items):
            QTimer.singleShot(
                500 + i * 400,
                lambda r=recent, t=tier, k=keyword, pid=old_page:
                    self._trigger_spirit_comment(r, tier=t, keyword_match=k, page_id=pid),
            )

    def _trigger_spirit_comment(self, recent_text: str = "", tier: int = 1,
                                 keyword_match: str = "", page_id: int | None = None):
        """旧主人魂魄在纸边留下一句低语（支持三层解锁体系）。
        page_id 由延迟解锁（翻页/关闭）传入，使批注归属旧页面；
        为 None 时归属当前页面。"""
        if page_id is None and self.is_sealed:
            return
        if len(recent_text.strip()) < MIN_CHARS_FOR_COMMENT:
            return

        tone = getattr(self, '_tone', '治愈')
        target_page = page_id if page_id is not None else self.page_id

        # 在主线程中预先获取 GUI 相关值，避免子线程访问
        cw, ch = self.width(), self.height()
        input_x, input_y = self._input_x, self._input_y

        def _fetch():
            text, is_fallback, _ = ai_client.get_comment(
                recent_text, tone, theme=keyword_match or None)
            rng = random.Random()
            margin = 50
            x = input_x + rng.uniform(-150, 150)
            y = input_y + rng.uniform(-80, 40)
            x = max(margin, min(cw - margin - 200, x))
            y = max(margin, min(ch - margin - 60, y))
            rot = rng.uniform(-12, 12)
            base_alpha_val = rng.uniform(COMMENT_BASE_ALPHA_MIN, COMMENT_BASE_ALPHA_MAX)

            c = Comment(
                page_id=target_page,
                content=text,
                x=x, y=y,
                rotate_angle=rot,
                base_alpha=base_alpha_val,
                font_path="",
                keyword_match=keyword_match,
                unlock_type=tier,
            )
            # 线程安全：推入待处理队列，主线程 _tick 负责 DB 写入和 GUI 更新
            if not self._shutting_down:
                with self._pending_comments_lock:
                    self._pending_comments.append((c, tier, is_fallback))

        if not self._shutting_down:
            threading.Thread(target=_fetch, daemon=True).start()

    # ========== Tier 1：浅层随机解锁 ==========

    def _try_tier1_unlock(self, pid: int | None = None):
        """每次打开页面 30% 概率新增一条 Tier 1 批注。

        pid 为调度时的页面 id：若 600ms 延迟期间已切到其它页，则跳过，
        避免把本属于旧页的批注错挂到新页（跨页串批注）。
        """
        if self.is_sealed:
            return
        if pid is not None and self.page_id != pid:
            return
        # Tier1 浅层随机批注同样需要正文达到阈值，避免空/短正文出现批注
        if len(self._words) < MIN_CHARS_FOR_COMMENT:
            return
        if len(self._comments) >= COMMENT_MAX_COUNT:
            self._check_and_evict()
            if len(self._comments) >= COMMENT_MAX_COUNT:
                return

        # 用无意义文本给 AI 生成一条"随机的旧主人低语"
        tone = getattr(self, '_tone', '治愈')
        seed_texts = [
            "这张纸被重新翻开了。",
            "又有人来了。",
            "纸的纹路还是老样子。",
            "新的墨香混着旧纸的气息。",
        ]
        seed_text = random.choice(seed_texts)

        # 在主线程中预先获取 GUI 相关值，避免子线程访问
        cw, ch = self.width(), self.height()
        current_page_id = self.page_id

        def _fetch():
            text, _, _ = ai_client.get_comment(seed_text, tone)
            rng = random.Random()
            margin = 50
            x = rng.uniform(margin, cw - margin - 200)
            y = rng.uniform(margin, ch - margin - 60)
            rot = rng.uniform(-12, 12)
            base_alpha_val = rng.uniform(COMMENT_BASE_ALPHA_MIN, COMMENT_BASE_ALPHA_MAX)

            c = Comment(
                page_id=current_page_id,
                content=text,
                x=x, y=y,
                rotate_angle=rot,
                base_alpha=base_alpha_val,
                font_path="",
                keyword_match="",
                unlock_type=1,
            )
            # 线程安全：推入待处理队列，主线程 _tick 负责 DB+GUI
            if not self._shutting_down:
                with self._pending_comments_lock:
                    self._pending_comments.append((c, 1, False))

        if not self._shutting_down:
            threading.Thread(target=_fetch, daemon=True).start()

    # ========== Tier 3：翻页动画 ==========

    def _trigger_page_turn(self):
        """触发全局纸张光影翻页动画（单页最多 3 次）。"""
        if self._page_turn_count >= TIER3_MAX_PAGE_TURNS:
            # 第4次起只显示提示
            self.toast_requested.emit(TOAST_TIER3_UNLOCK)
            return
        self._page_turn_count += 1
        self._page_turn_anim = 0.0
        self._page_turn_active = True
        # 尝试播放纸张摩擦音效
        try:
            from PyQt5.QtMultimedia import QSoundEffect
            import os
            sound_path = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                                      "assets", "page_turn.wav")
            if os.path.exists(sound_path):
                effect = QSoundEffect(self)
                effect.setSource(QUrl.fromLocalFile(sound_path))
                effect.setVolume(0.3)
                effect.play()
        except Exception:
            pass  # 音效非必需，静默失败

    def _flush_positions(self):
        """把未落库的排版修正字坐标批量写入数据库（节流后的落库点）。"""
        if self._positions_dirty and self._pending_positions:
            try:
                db.batch_update_word_positions(self._pending_positions)
            except Exception:
                pass
            self._positions_dirty = False

    def shutdown(self):
        """优雅关闭：设置关闭标志，阻止新的 AI 后台线程启动。"""
        self._flush_positions()
        self._shutting_down = True
        self._ticker.stop()

    # ========== 淘汰规则 ==========

    def _check_and_evict(self):
        """检查批注是否满 8 条，满则按优先级淘汰。彻底清除，无残留残影。"""
        if len(self._comments) <= COMMENT_MAX_COUNT:
            return

        evict_id = db.get_evictable_comment(self.page_id)
        if evict_id is None:
            return

        # 直接彻底删除（呼应"记忆彻底消失"设定，无呼吸残留）
        self._comments = [c for c in self._comments if c.comment_id != evict_id]
        db.delete_comment(evict_id)
        self.toast_requested.emit(TOAST_COMMENT_EVICTED)

    # ========== 续命 ==========

    def _do_revive(self, word_idx: int):
        """对指定文字执行续命。≥6次仅提亮，不增加寿命。"""
        if word_idx < 0 or word_idx >= len(self._words):
            return
        w = self._words[word_idx]
        now = time.time()
        revive_before = w.revive_count or 0
        new_ts, new_life, new_rc = revive_word(
            w.create_timestamp, w.life_total_sec,
            revive_before, now,
        )
        # 已到上限：仅提亮反馈，不再延长寿命，也不累加计数
        if new_rc == revive_before:
            self._revive_flash = 0.0
            self._revive_flash_peak = 0.6  # 仅提亮，弱脉冲
            self._revive_flash_word_idx = word_idx
            self._revive_flash_t = 0.0
            self.toast_requested.emit(TOAST_REVIVE_CAPPED)
            return
        w.create_timestamp = new_ts
        w.life_total_sec = new_life
        w.revive_count = new_rc
        db.update_word(w)
        self._revive_flash = 0.0
        self._revive_flash_peak = 1.0
        self._revive_flash_word_idx = word_idx
        self._revive_flash_t = 0.0
        self._gaze_revive_count += 1
        self.word_revived.emit()
        # 第 5 次（最后一次有效续命）明确告知这是挽留极限；其余按梯度文案
        if new_rc == REVIVE_MAX_COUNT:
            self.toast_requested.emit(TOAST_REVIVE_LAST)
        elif 1 <= new_rc <= len(REVIVE_TOASTS):
            self.toast_requested.emit(REVIVE_TOASTS[new_rc - 1])
        else:
            self.toast_requested.emit(TOAST_REVIVED)

    # ========== 删除文字 ==========

    def _spawn_dissolve_particles(self, w):
        """为即将删除的文字生成消散粒子。"""
        color = get_ink_oxidation_color(
            compute_alpha(w.create_timestamp, w.life_total_sec, w.revive_count or 0),
            is_dark_mode=self._dark_mode,
        )
        fm = self._body_metrics(BODY_FONT_SIZE)
        cx = w.x + fm.width(w.content) / 2
        cy = w.y - fm.height() / 2
        particles = generate_dissolve_particles(cx, cy, color.name(),
                                               DUST_PARTICLE_COUNT)
        self._dissolve_particles.extend(particles)

    # ========== 导出 ==========

    def _grab_and_save(self, params: dict):
        """导出画布为图片。"""
        from PyQt5.QtWidgets import QFileDialog
        fmt = params.get("format", "png")
        dpi = params.get("dpi", 300)
        ext = "png" if fmt == "png" else "jpg"
        path, _ = QFileDialog.getSaveFileName(
            self, "导出画布",
            f"未完成_遗忘_{int(time.time())}.{ext}",
            f"Images (*.{ext})",
        )
        if not path:
            return
        # 高分辨率渲染
        scale = dpi / 96.0
        pixmap = QPixmap(int(self.width() * scale), int(self.height() * scale))
        pixmap.fill(QColor(PAPER_BG_HEX.get(self._paper_type, BG_YELLOW_1)))
        pt = QPainter(pixmap)
        pt.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.render(pt)
        # 可选：带上页眉那句诗（导出弹窗勾选时由调用方传入 epigraph_text）
        epigraph_text = params.get("epigraph_text")
        if epigraph_text:
            m = int(24 * scale)
            top_y = int(30 * scale)
            font = QFont(self._brand_font_family(), int(13 * scale))
            pt.setFont(font)
            pt.setPen(QColor(EPIGRAPH_COLOR_LIGHT))
            pt.drawText(m, top_y, epigraph_text)
        pt.end()
        pixmap.save(path, ext.upper() if ext == "jpg" else "PNG", quality=95)
        self.toast_requested.emit(TOAST_EXPORTED)

    # ========== 尺寸变化 ==========

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self._texture_seeded:
            self._seed_texture()
        # 窗口尺寸变化 → 缓存失效（纸张纹理 + 星场）
        self._invalidate_paper_cache()
        self._star_cache = None
        # 节流：延迟重排，避免快速拖动窗口时连续触发完整 _reflow_from
        self._reflow_throttle_timer.start()

    def _on_resize_throttled(self):
        """resize 节流回调：仅在窗口稳定后执行一次文字重排。"""
        try:
            self._reflow_from(0, persist=False)
            self._sync_cursor(scroll_into_view=False)
        except Exception:
            pass

    def showEvent(self, event):
        super().showEvent(event)
        # 窗口首次显示后，重新计算所有文字坐标（之前窗口宽度为0导致计算错误）
        try:
            self._reflow_from(0, persist=False)
            self._sync_cursor(scroll_into_view=False)
            # 如果页面有文字，滚动到光标位置（文末），让用户看到光标
            if self._words and self._cursor_index == len(self._words):
                self._ensure_cursor_visible()
        except Exception:
            pass
        if self._atmosphere_enabled:
            # 用真实窗口尺寸 + 当前性能档位算尘埃上限，再按上限补充（不再覆盖式生成 80）。
            # 这正是之前"启动一闪而过 80 个然后被裁"的根因：原代码在此处无条件
            # generate_dust_particles(w,h)（count 默认 DUST_PARTICLE_MAX=80）覆盖生成。
            self._adapt_particle_limits()
            self._seed_dust()
        # 窗口尺寸变化（含全屏）时重排文字，使其随书写列重新流动
        if getattr(self, '_words', None) is not None:
            self._reflow_from(0)
        # 尺寸变化后内容高度可能改变，夹取滚动偏移避免越界露出空白
        self._scroll_target = self._clamp_scroll(self._scroll_target)
        self._scroll_y = self._clamp_scroll(self._scroll_y)


# 辅助类型（防止循环导入）
from utils.db import Word, Comment
