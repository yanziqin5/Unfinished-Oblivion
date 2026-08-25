"""
《未完成·遗忘》桌面笔记软件 —— 主入口。
氛围升级版：纯画布模式、动态光影、磨砂UI、文艺化文案。
"""
import sys
import os
import random

from PyQt5.QtCore import (
    Qt, QTimer, QRect, QObject, QEvent, QByteArray,
)
from PyQt5.QtGui import (
    QColor, QFont, QPainter, QFontMetrics, QKeySequence, QCursor,
)
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QStackedWidget, QLabel, QShortcut, QToolTip, QDialog,
)

from utils.constants import (
    SYSTEM_FONT, SERIF_FONT,
    EPIGRAPHS, BG_DEFAULT,
    TEXT_COLOR, HINT_TEXT_COLOR,
    DURATION_TOAST_FADE, DURATION_TOAST_VISIBLE,     DURATION_TOAST_FADE_OUT,
    TOAST_UNSEALED,
    DARK_BG, DARK_TEXT, DARK_HINT,
    TOAST_NEW_PAGE,
    TOAST_DELETED,
    TOAST_CACHE_CLEARED, TOAST_DATA_CORRUPT,
    SHORTCUT_NEW, SHORTCUT_EXPORT,
    SHORTCUT_BACK, SHORTCUT_ARCHIVE, SHORTCUT_FULLSCREEN,
    SHORTCUT_PURE_MODE, SHORTCUT_ATMOSPHERE,     SHORTCUT_DARK_MODE,
)
from utils.db import db
from utils.helpers import compute_alpha
# 音效模块已移除

from widgets.canvas import CanvasWidget
from widgets.toolbar import Toolbar
from widgets.statusbar import StatusBar
from widgets.guide import GuideOverlay
from widgets.archive_grid import ArchiveGrid
from widgets.archive import ArchiveSidebar
from widgets.archive_trigger import ArchiveTrigger
from widgets.export_dialog import ExportDialog
from widgets.api_dialog import ApiDialog
from widgets.menus import ShortcutsDialog, AboutDialog


class MainWindow(QMainWindow):
    """主窗口 —— 无边框，5:3 比例。"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("未完成 · 遗忘")
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

        # ---- 全局状态 ----
        self._dark_mode: bool = False
        self._fullscreen: bool = False
        self._pure_mode: bool = False
        self._atmosphere_enabled: bool = db.get_setting("atmosphere_enabled", "1") == "1"
        self._current_page_id: int = 0
        self._current_tone: str = "岁月静谧"
        self._show_guide_once: bool = True

        # ---- 初始化 DB ----
        try:
            db.init()
        except Exception as e:
            from widgets.rounded_dialogs import info_dialog
            info_dialog(None, "数据损坏",
                "页面数据似乎有些损坏……\n请尝试删除 data.db 文件后重新启动。")
            sys.exit(1)

        # ---- 中央容器 ----
        central = QWidget()
        central.setObjectName("CentralWidget")
        central.setStyleSheet("background: transparent;")
        self.setCentralWidget(central)
        self._root_layout = QVBoxLayout(central)
        self._root_layout.setContentsMargins(0, 0, 0, 0)
        self._root_layout.setSpacing(0)

        # ---- 主 stacked 布局（编辑页 / 档案馆） ----
        self._stack = QStackedWidget()
        self._root_layout.addWidget(self._stack, 1)

        # ---- 编辑页面 ----
        self._editor_page = QWidget()
        editor_layout = QVBoxLayout(self._editor_page)
        editor_layout.setContentsMargins(0, 0, 0, 0)
        editor_layout.setSpacing(0)

        # 画布 + 侧边栏水平排列
        canvas_sidebar_layout = QHBoxLayout()
        canvas_sidebar_layout.setContentsMargins(0, 0, 0, 0)
        canvas_sidebar_layout.setSpacing(0)
        self._canvas_layout = canvas_sidebar_layout
        self._canvas_win_margins = (0, 0, 0, 0)   # 画布铺满窗口，四角填满

        self.canvas = CanvasWidget()
        self.canvas.toast_requested.connect(self._show_toast)
        self.canvas.word_revived.connect(self._on_word_revived)
        self.canvas.comment_added.connect(self._on_comment_added)
        self.canvas.char_count_changed.connect(self._on_char_count_changed)
        self.canvas.unseal_requested.connect(self._on_unseal_page)

        # 画布铺满窗口（无留白、无阴影），四角由纸张/画布底色填满
        canvas_sidebar_layout.setContentsMargins(*self._canvas_win_margins)

        # ---- 启动时登记已导入的手写字体（持久化） ----
        self._load_imported_fonts()

        # ---- 启动时若上次开启了手写体，重新解析并加载字体（否则会回退成打印体） ----
        if self.canvas._use_handwriting:
            self.canvas.set_handwriting(True, silent=True)

        self.sidebar = ArchiveSidebar()
        self.sidebar.hide()
        self.sidebar.page_selected.connect(self._open_page)
        self.sidebar.sidebar_hidden.connect(self._on_sidebar_hidden)
        self.sidebar_visible: bool = False

        # 右侧触发条：提升为窗口级控件，贴附在工具栏下沿与状态栏上沿之间的右边，
        # 因此编辑器页与档案馆页的右边都可点击，在两者间切换（取代原返回按钮）。
        self.archive_trigger = ArchiveTrigger(central)
        self.archive_trigger.setVisible(False)   # 等布局就绪定位后再显示，避免启动瞬间停在左上角
        self.archive_trigger.triggered.connect(self._on_trigger_activated)            # hover 展开侧栏
        self.archive_trigger.page_toggle_requested.connect(self._on_back_to_archive)  # 点击切换页面

        canvas_sidebar_layout.addWidget(self.sidebar)
        canvas_sidebar_layout.addWidget(self.canvas, 1)
        editor_layout.addLayout(canvas_sidebar_layout, 1)
        self._position_trigger()

        self._stack.addWidget(self._editor_page)

        # ---- 档案馆页面 ----
        self.archive_grid = ArchiveGrid()
        self.archive_grid.page_opened.connect(self._open_page)
        self.archive_grid.page_deleted.connect(self._on_page_deleted)
        self.archive_grid.toast_requested.connect(self._show_toast)
        self.archive_grid.new_page_requested.connect(self._new_page)
        self._stack.addWidget(self.archive_grid)

        # ---- 工具栏 ----
        self.toolbar = Toolbar()
        self.toolbar.export_requested.connect(self._show_export)
        self.toolbar.api_settings_requested.connect(self._show_api)
        self.toolbar.new_page_requested.connect(self._new_page)
        self.toolbar.reset_requested.connect(self._reset_page)
        self.toolbar.delete_all_requested.connect(self._delete_all)
        self.toolbar.tone_changed.connect(self._on_tone_changed)
        self.toolbar.dark_mode_toggled.connect(self._toggle_dark_mode)
        self.toolbar.pure_mode_toggled.connect(self._toggle_pure_mode)
        self.toolbar.atmosphere_toggled.connect(self._toggle_atmosphere)
        self.toolbar.clear_cache_requested.connect(self._clear_cache)
        self.toolbar.handwriting_toggled.connect(self.canvas.set_handwriting)
        self.toolbar.import_font_requested.connect(self._import_font)
        self.toolbar.manage_fonts_requested.connect(self._manage_fonts)
        self.toolbar.performance_mode_toggled.connect(self._cycle_perf_tier)
        self.toolbar.shortcuts_requested.connect(self._show_shortcuts)
        self.toolbar.about_requested.connect(self._show_about)
        self.toolbar.toast_requested.connect(self._show_toast)
        self._root_layout.addWidget(self.toolbar)

        # ---- 状态栏 ----
        self.statusbar = StatusBar()
        self._root_layout.addWidget(self.statusbar)

        # 状态栏创建后再定位一次触发条：此时工具栏已存在，可正确地把工具栏
        # 提升至触发条之上（窗口控制按钮可点），同时让右边缘贯穿整个窗口。
        self._position_trigger()

        # ---- 引导页（覆盖整个窗口，非仅编辑区）----
        self.guide = GuideOverlay(self)
        self.guide.hide()

        # ---- Toast 标签 ----
        # 挂在画布下（而非 editor_page）：定位以画布自身尺寸为基准，
        # 侧栏展开导致画布变窄/右移时，Toast 仍稳定贴在编辑区右下角。
        self._toast_label = QLabel("", self.canvas)
        self._toast_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self._toast_label.setAlignment(Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignRight)
        self._toast_label.setFont(QFont(self.canvas.copy_font_family(), 12))
        self._toast_label.setStyleSheet(f"""
            QLabel {{
                color: {HINT_TEXT_COLOR};
                background: transparent;
                padding: 8px 16px;
                font-family: "{SERIF_FONT}";
            }}
        """)
        self._toast_label.hide()
        self._toast_opacity: float = 0.0
        self._toast_phase: str = "hidden"  # hidden / fading_in / visible / fading_out
        self._toast_timer: float = 0.0

        # ---- Toast 淡入淡出定时器 ----
        self._toast_frame_timer = QTimer(self)
        self._toast_frame_timer.setInterval(16)
        self._toast_frame_timer.timeout.connect(self._toast_tick)
        self._toast_frame_timer.start()

        # ---- 自动存档叙事文案定时器（~5min 一次） ----
        self._auto_narrative_timer = QTimer(self)
        self._auto_narrative_timer.setInterval(5 * 60 * 1000)  # 5 min
        self._auto_narrative_timer.timeout.connect(self._show_auto_save_narrative)
        self._auto_narrative_timer.start()

        # ---- 快捷键 ----
        QShortcut(QKeySequence(SHORTCUT_NEW), self, self._new_page)
        QShortcut(QKeySequence(SHORTCUT_EXPORT), self, self._show_export)
        QShortcut(QKeySequence(SHORTCUT_BACK), self, self._on_back_to_archive)
        QShortcut(QKeySequence(SHORTCUT_ARCHIVE), self, self._toggle_sidebar)
        QShortcut(QKeySequence(SHORTCUT_FULLSCREEN), self, self._toggle_fullscreen)
        QShortcut(QKeySequence(SHORTCUT_PURE_MODE), self, lambda: self._toggle_pure_mode(not self._pure_mode))
        # 纯画布模式下按 Esc 也能退出（更直观，避免隐藏 UI 后无路可走）
        QShortcut(QKeySequence("Esc"), self, lambda: self._toggle_pure_mode(False) if self._pure_mode else None)
        QShortcut(QKeySequence(SHORTCUT_DARK_MODE), self, lambda: self._toggle_dark_mode(not self._dark_mode))
        QShortcut(QKeySequence(SHORTCUT_ATMOSPHERE), self, lambda: self._toggle_atmosphere(not self._atmosphere_enabled))

        # ---- 设置窗口尺寸 ----
        self._apply_ratio()
        self._apply_style()

        # ---- 初始加载：首页为写作页（无页面则自动创建）----
        self._show_editor_startup()
        self._show_guide_if_needed()

    # ========== 尺寸 & 样式 ==========

    def _apply_ratio(self):
        """默认窗口尺寸 1200×800；超出可用屏幕时按比例缩放到屏幕内并居中。
        若已保存上次关闭时的窗口几何，则优先恢复，使文字 reflow 结果与关闭前一致。"""
        saved_geo = db.get_setting("window_geometry", "")
        if saved_geo:
            try:
                self.restoreGeometry(QByteArray.fromBase64(saved_geo.encode("utf-8")))
                self._update_rounded_mask()
                return
            except Exception:
                pass
        sw, sh = 1200, 800
        screen = QApplication.primaryScreen()
        av = screen.availableGeometry() if screen else QRect(0, 0, 1280, 800)
        margin = 16
        max_w = max(320, av.width() - margin * 2)
        max_h = max(240, av.height() - margin * 2)
        if sw > max_w or sh > max_h:
            scale = min(max_w / sw, max_h / sh)
            sw = int(sw * scale)
            sh = int(sh * scale)
        x = av.x() + max(0, (av.width() - sw) // 2)
        y = av.y() + max(0, (av.height() - sh) // 2)
        self.setGeometry(x, y, sw, sh)
        self._update_rounded_mask()

    def _apply_style(self):
        if self._dark_mode:
            bg = DARK_BG
            self.setStyleSheet(f"""
                QMainWindow {{
                    background: transparent;
                }}
                QWidget {{
                    background: {DARK_BG};
                    color: {DARK_TEXT};
                    font-family: "{SYSTEM_FONT}";
                }}
            """)
        else:
            self.setStyleSheet(f"""
                QMainWindow {{
                    background: transparent;
                }}
                QWidget {{
                    background: {BG_DEFAULT};
                    color: {TEXT_COLOR};
                    font-family: "{SYSTEM_FONT}";
                }}
            """)

    # ========== 圆角窗口（边框绘制 + 遮罩） ==========

    def _update_rounded_mask(self):
        """窗口为直角矩形：清除任何遮罩，恢复默认方形边框。"""
        self.clearMask()

    def showEvent(self, event):
        super().showEvent(event)
        # 首次显示后布局几何才就绪；延迟一帧再定位触发条与圆角，
        # 避免初始化时子控件几何为 0 导致触发条未定位（停在默认左上角）。
        QTimer.singleShot(0, self._position_trigger)
        QTimer.singleShot(0, self._update_rounded_mask)
        # 首次显示时恢复已持久化的界面设置，避免重新打开程序后重置
        if not getattr(self, "_settings_restored", False):
            self._settings_restored = True
            # 深色模式：保存过则恢复（按钮与各控件一并同步）
            if db.get_setting("dark_mode", "0") == "1":
                self._toggle_dark_mode(True)
            # 氛围按钮视觉同步到保存的状态（画布模式已读取，但按钮高亮需显式同步）
            self.toolbar.set_atmosphere_on(self._atmosphere_enabled)

    def resizeEvent(self, event):
        self._update_rounded_mask()
        self._position_trigger()
        super().resizeEvent(event)

    def _position_trigger(self):
        """右侧触发条（右边框）从窗口顶（内容区顶部）一直贯穿到工具栏上沿，
        不覆盖工具栏本身（工具栏内不再绘右竖条）。"""
        if not (hasattr(self, "archive_trigger") and hasattr(self, "toolbar")):
            return
        tb_top = self.toolbar.mapTo(self, self.toolbar.rect().topLeft()).y()
        if tb_top < 1:
            return
        self.archive_trigger.setGeometry(self.width() - 14, 0, 14, tb_top)
        self.archive_trigger.raise_()
        self.archive_trigger.setVisible(True)   # 布局就绪，定位完成后显示

    def paintEvent(self, event):
        rect = self.rect()
        # 单 painter 完成「填充 → 子控件 → 描边」：避免半透明窗口上边框闪烁；
        # 窗口为直角矩形，四角被内部控件完全填满。
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        # 底色：深色模式用 DARK_BG；浅色模式用纸张色，避免最外圈露出深色底形成“黑线”
        base = QColor(DARK_BG) if self._dark_mode else QColor(BG_DEFAULT)
        painter.fillRect(rect, base)   # 直角铺满，四角不留透明
        # 子控件（画布 / 工具栏 / 状态栏）绘制于填充之上
        super().paintEvent(event)
        # 窗口四边边框改由各子控件自绘：
        # 工具栏画上边、画布画左/右边、状态栏画下边，均半透明、悬停更清晰。
        # 各控件在自己 paintEvent 内绘制，互相重绘不会覆盖彼此 → 不闪烁，
        # 也避免主窗口深色底在边框外露出形成“黑线”。
        painter.end()

    # ========== 页面管理 ==========

    def _open_page(self, page_id: int, is_new_page: bool = False,
                   show_placeholder: bool = False):
        """打开指定页面进入编辑模式。"""
        try:
            page = db.get_page(page_id)
        except Exception:
            self._show_toast(TOAST_DATA_CORRUPT)
            return
        if not page:
            return

        self._current_page_id = page_id
        db.touch_page(page_id)  # 更新"最近打开"时间，供启动/列表排序使用

        # 根据创建时间动态计算纸张阶段（随时间自然老化）
        from utils.constants import get_paper_stage
        paper_type = get_paper_stage(page.create_time, page.is_sealed) if page.create_time else "黄1"

        try:
            self.canvas.set_page(
                page_id,
                paper_type=paper_type,
                is_sealed=page.is_sealed,
                is_new_page=is_new_page,
                show_placeholder=show_placeholder,
            )
        except Exception:
            self._show_toast(TOAST_DATA_CORRUPT)
            return

        self.canvas._tone = self._current_tone

        # 更新工具栏
        epigraph = page.epigraph or random.choice(EPIGRAPHS)
        self.toolbar.set_epigraph(epigraph)
        self.toolbar.set_sealed(page.is_sealed)
        self.toolbar.set_tone(self._current_tone)
        self.toolbar.set_page_count(len(db.list_pages()))  # 同步页计数（新建/重开页后启用按钮）

        # 更新状态栏
        self._update_statusbar()

        # 翻到编辑页
        self._stack.setCurrentIndex(0)
        self.canvas.setFocus()

    def _new_page(self):
        """真正新建一篇空白笔记。总是从 黄1 纸张开始，100% 生成 1 条初始批注。"""
        page = db.create_page(paper_type="黄1", title="")
        self._current_page_id = page.page_id
        self._open_page(page.page_id, is_new_page=True, show_placeholder=False)
        self._show_toast(TOAST_NEW_PAGE)
        self.sidebar.refresh()
        self.archive_grid.refresh()

    def _reset_page(self):
        """重置当前页面——删除所有文字。"""
        if self._current_page_id <= 0:
            return
        db.delete_all_words_on_page(self._current_page_id)
        self._open_page(self._current_page_id, show_placeholder=False)
        self._show_toast("纸面恢复如初，空白的温柔。")
        self.sidebar.refresh()

    def _delete_all(self):
        """删除所有笔记。"""
        db.delete_all_pages()
        self._current_page_id = 0
        self.canvas.set_page(0)  # 重置画布，避免残留已删除页内容
        self.toolbar.set_page_count(0)
        self._show_archive()
        self.archive_grid.refresh()
        self.sidebar.refresh()
        self._show_toast(TOAST_DELETED)

    def _on_page_deleted(self, page_id: int):
        """档案馆删除单页后：同步当前页/画布/工具栏状态，避免串页或残留。"""
        if page_id == self._current_page_id:
            # 删除的正是当前编辑页：归零当前页并清空画布
            self._current_page_id = 0
            self.canvas.set_page(0)
        pages = db.list_pages()
        self.toolbar.set_page_count(len(pages))  # M2：同步工具栏按钮启用态
        self.sidebar.refresh()
        # 当前编辑页被删且仍处于编辑视图时，退回档案馆
        if self._stack.currentIndex() == 0 and self._current_page_id <= 0:
            self._show_archive()

    # ========== 模式切换 ==========

    def _toggle_dark_mode(self, enabled: bool):
        self._dark_mode = enabled
        self._apply_style()
        self.toolbar.set_dark_mode(enabled)
        self.statusbar.set_dark_mode(enabled)
        self.canvas.set_dark_mode(enabled)
        self.guide.set_dark_mode(enabled)
        self.sidebar.set_dark_mode(enabled)
        self.archive_grid.set_dark_mode(enabled)
        self.update()   # 重绘窗口底色（直角矩形，无圆角）
        db.set_setting("dark_mode", "1" if enabled else "0")

    def _toggle_pure_mode(self, enabled: bool):
        """纯画布模式：隐藏所有 UI。"""
        self._pure_mode = enabled
        self.toolbar.setVisible(not enabled)
        self.statusbar.setVisible(not enabled)

    def _toggle_atmosphere(self, enabled: bool):
        """高级氛围开关（此处统一负责持久化，覆盖按钮与快捷键两条路径）。"""
        self._atmosphere_enabled = enabled
        db.set_setting("atmosphere_enabled", "1" if enabled else "0")
        self.canvas.set_atmosphere(enabled)
        self.toolbar.set_atmosphere_on(enabled)

    def _toggle_fullscreen(self):
        """全屏切换。窗口始终为直角矩形，全屏时铺满整屏。"""
        self._fullscreen = not self._fullscreen
        if self._fullscreen:
            self.clearMask()   # 全屏时不裁剪，铺满整屏
            self.showFullScreen()
        else:
            self.showNormal()
            self._apply_ratio()
        self.toolbar.set_fullscreen(self._fullscreen)
        self.statusbar.set_fullscreen(self._fullscreen)
        self.update()   # 重绘框体

    # ========== 视图切换 ==========

    def _show_editor_startup(self):
        """启动时显示编辑页。若无页面则自动创建一页。"""
        pages = db.list_pages()
        if pages:
            # 打开最近一页（list_pages 按 last_open_time DESC，索引 0 为最近）
            self._open_page(pages[0].page_id)
        else:
            # 自动创建第一页（首次启动：显示占位示例文字）
            page = db.create_page(paper_type="黄1", title="")
            self._current_page_id = page.page_id
            self._open_page(page.page_id, is_new_page=True, show_placeholder=True)
        self.archive_grid.refresh()

    def _on_back_to_archive(self):
        """工具栏返回按钮：书写页 ↔ 档案馆 双向切换（文字已持久化，无需确认）。"""
        if self._stack.currentIndex() == 1:
            # 当前在档案馆，返回书写页
            if self._current_page_id > 0:
                self._open_page(self._current_page_id)
            else:
                self._show_archive()
        else:
            # 当前在书写页，进入档案馆
            if self._current_page_id > 0:
                self.sidebar.refresh()
            self._show_archive()

    def _show_archive(self):
        """返回档案馆首页。"""
        pages = db.list_pages()
        self.toolbar.set_page_count(len(pages))
        self.archive_grid.refresh()
        self._stack.setCurrentIndex(1)
        self.sidebar.hide_sidebar()
        self.sidebar_visible = False
        self.archive_trigger.set_sidebar_visible(False)

    def _toggle_sidebar(self):
        """切换侧边栏（Ctrl+Tab）。"""
        if self.sidebar_visible:
            self.sidebar.hide_sidebar()
        else:
            self.sidebar_visible = True
            self.sidebar.refresh()
            self.sidebar.show_sidebar()
            self.archive_trigger.set_sidebar_visible(True)

    def _on_trigger_activated(self):
        """右侧触发条被激活（悬停300ms或点击）。"""
        self.sidebar_visible = True
        self.sidebar.refresh()
        self.sidebar.show_sidebar()
        self.archive_trigger.set_sidebar_visible(True)

    def _on_sidebar_hidden(self):
        """侧边栏收起时更新触发条状态。"""
        self.sidebar_visible = False
        self.archive_trigger.set_sidebar_visible(False)

    # ========== 对话框 ==========

    def _show_export(self):
        """导出面板。"""
        dlg = ExportDialog(self)
        dlg.move(
            self.x() + (self.width() - dlg.width()) // 2,
            self.y() + (self.height() - dlg.height()) // 2,
        )
        if dlg.exec_() == dlg.Accepted:
            try:
                res = dict(dlg.result_data)
                if res.get("epigraph"):
                    res["epigraph_text"] = self.toolbar.get_epigraph()
                self.canvas.trigger_export(res)
                self._show_toast("已导出画布")
            except Exception as exc:  # 磁盘满 / 路径非法 / 保存失败
                self._show_toast(f"导出失败：{exc}")

    def _show_api(self):
        """API 密钥设置。"""
        dlg = ApiDialog(self, dark_mode=self._dark_mode)
        dlg.move(
            self.x() + (self.width() - dlg.width()) // 2,
            self.y() + (self.height() - dlg.height()) // 2,
        )
        dlg.exec_()

    # ========== 导入手写字体 ==========

    def _load_imported_fonts(self):
        """启动时把持久化的导入字体重新登记到 Qt 字体库与画布。"""
        from PyQt5.QtGui import QFontDatabase
        for item in db.get_imported_fonts():
            path = item.get("path", "")
            if not path or not os.path.exists(path):
                continue
            fid = QFontDatabase.addApplicationFont(path)
            if fid < 0:
                continue
            fams = self._app_font_families(fid, item.get("family", ""))
            if fams:
                for fam in fams:
                    self.canvas.register_imported_font(fam)

    def _import_font(self):
        """从文件导入手写字体（ttf/otf/ttc 等），登记后可立即用于批注。"""
        from PyQt5.QtWidgets import QFileDialog
        from PyQt5.QtGui import QFontDatabase
        paths, _ = QFileDialog.getOpenFileNames(
            self, "导入手写字体",
            "",
            "字体文件 (*.ttf *.otf *.ttc *.woff *.woff2);;所有文件 (*.*)",
        )
        if not paths:
            return
        loaded = []
        for p in paths:
            fid = QFontDatabase.addApplicationFont(p)
            if fid < 0:
                self._show_toast("字体加载失败：%s" % os.path.basename(p))
                continue
            fams = self._app_font_families(fid, "")
            if not fams:
                self._show_toast("无法读取字体族：%s" % os.path.basename(p))
                continue
            for fam in fams:
                if db.add_imported_font(p, fam):
                    self.canvas.register_imported_font(fam)
                    if fam not in loaded:
                        loaded.append(fam)
        if not loaded:
            return
        # 启用手写模式（已导入字体，必然成功），并立即套用到当前批注
        self.canvas.set_handwriting(True)
        self.canvas.rebind_all_comments_to_font(loaded[-1])
        self._show_toast("已导入手写字体：%s" % "、".join(loaded))

    @staticmethod
    def _app_font_families(fid: int, fallback: str) -> list:
        """返回某次 addApplicationFont 注册的字体族列表，失败则用 fallback。"""
        try:
            from PyQt5.QtGui import QFontDatabase
            fams = QFontDatabase.applicationFontFamilies(fid)
            if fams:
                return list(fams)
        except Exception:
            pass
        return [fallback] if fallback else []

    def _manage_fonts(self):
        """管理已导入的手写字体（右键删除 / 应用）。"""
        from widgets.font_manager_dialog import FontManagerDialog
        dlg = FontManagerDialog(self.canvas, toast_fn=self._show_toast, parent=self)
        dlg.move(
            self.x() + (self.width() - dlg.width()) // 2,
            self.y() + (self.height() - dlg.height()) // 2,
        )
        dlg.exec_()

    # ========== 信号处理 ==========

    def _on_word_revived(self):
        self._update_statusbar()

    def _on_comment_added(self):
        self._update_statusbar()

    def _on_char_count_changed(self, count: int):
        self.statusbar.set_chars(count)

    def _show_auto_save_narrative(self):
        """周期性自动存档叙事文案——在不打扰的前提下，提醒用户文字已被保存。"""
        if self._current_page_id <= 0:
            return
        narrative = self.canvas.get_save_narrative()
        self._show_toast(narrative)

    def _on_unseal_page(self, page_id: int):
        """解封页面：恢复文字消亡机制。"""
        if page_id <= 0:
            return
        try:
            db.unseal_page(page_id)
            self._show_toast(TOAST_UNSEALED)
            self.archive_grid.refresh()
            # 重新加载当前页面以刷新 sealed 状态
            self._open_page(page_id)
        except Exception:
            self._show_toast("无法解封此页……封印纹丝不动。")

    def _on_tone_changed(self, tone: str):
        self._current_tone = tone
        self.canvas.set_tone(tone)

    def _update_statusbar(self):
        """更新状态栏统计。实时计算：已写字数/续命总次数/批注数/衰老值百分比。"""
        if self._current_page_id <= 0:
            return
        page = db.get_page(self._current_page_id)
        if not page:
            return

        # 已写字数（仅有效未消散文字）
        self.statusbar.set_chars(self.canvas.get_char_count())
        # 续命总次数（当前页面所有文字累计）
        revives = db.total_revives_on_page(self._current_page_id)
        self.statusbar.set_revives(revives)
        # 批注数（无正文字时画布不绘制批注，状态栏亦不显示计数，保持口径一致）
        self.statusbar.set_comments(
            self.canvas.get_comment_count() if self.canvas.has_words() else 0, 8)

        # 衰老值：1 - 平均alpha（越淡越衰老）
        if page.is_sealed:
            self.statusbar.set_freshness(1.0, is_sealed=True)
        else:
            alive_words = db.get_alive_words(self._current_page_id)
            if alive_words:
                avg_alpha = sum(
                    compute_alpha(w.create_timestamp, w.life_total_sec,
                                  w.revive_count or 0) for w in alive_words
                ) / len(alive_words)
                avg_decay = 1.0 - avg_alpha  # 衰老值 = 1 - 透明度
            else:
                avg_decay = 0  # 无文字时衰老值为 0%
            self.statusbar.set_freshness(avg_decay, is_sealed=False)

    # ========== 引导页 ==========

    def _show_guide_if_needed(self):
        """首次启动显示引导页（覆盖整个窗口）。点击任意处 300ms 淡出。"""
        if not self._show_guide_once:
            return
        shown = db.get_setting("guide_shown", "0")
        if shown == "0":
            db.set_setting("guide_shown", "1")
            self.guide.set_dark_mode(self._dark_mode)
            self.guide.show_overlay()
            # 20 秒后自动淡出作为后备（用户也可点击任意处提前关闭）
            QTimer.singleShot(20000, self.guide.start_fade_out)

    # ========== Toast 系统 ==========

    def _show_toast(self, message: str):
        """显示文艺化 Toast（柔和淡入淡出）。"""
        self._toast_label.setText(message)
        self._toast_label.adjustSize()
        self._toast_phase = "fading_in"
        self._toast_opacity = 0.0
        self._toast_timer = 0.0
        # 定位到右下角
        cw, ch = self.canvas.width(), self.canvas.height()
        lw = self._toast_label.width()
        self._toast_label.setGeometry(cw - lw - 40, ch - 60, lw + 20, 40)
        self._toast_label.show()

    def _toast_tick(self):
        """Toast 帧更新（16ms间隔）。"""
        dt = 0.016
        if self._toast_phase == "hidden":
            return

        self._toast_timer += dt

        if self._toast_phase == "fading_in":
            progress = self._toast_timer / (DURATION_TOAST_FADE / 1000.0)
            if progress >= 1.0:
                self._toast_opacity = 1.0
                self._toast_phase = "visible"
                self._toast_timer = 0.0
            else:
                self._toast_opacity = progress * progress  # ease-in

        elif self._toast_phase == "visible":
            if self._toast_timer >= DURATION_TOAST_VISIBLE / 1000.0:
                self._toast_phase = "fading_out"
                self._toast_timer = 0.0

        elif self._toast_phase == "fading_out":
            progress = self._toast_timer / (DURATION_TOAST_FADE_OUT / 1000.0)
            if progress >= 1.0:
                self._toast_opacity = 0.0
                self._toast_phase = "hidden"
                self._toast_label.hide()
            else:
                self._toast_opacity = 1.0 - progress * progress  # ease-out

        # 应用透明度
        alpha = int(self._toast_opacity * 200)  # max 200 alpha for subtlety
        color = DARK_HINT if self._dark_mode else HINT_TEXT_COLOR
        self._toast_label.setStyleSheet(f"""
            QLabel {{
                color: rgba({200},{190},{175},{alpha});
                background: transparent;
                padding: 8px 16px;
                font-family: "{SERIF_FONT}";
                font-size: 12px;
            }}
        """)

    # ========== 鼠标事件（窗口拖动） ==========

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if hasattr(self, '_drag_pos') and event.buttons() == Qt.LeftButton:
            self.move(event.globalPos() - self._drag_pos)
            event.accept()

    def mouseDoubleClickEvent(self, event):
        self._toggle_fullscreen()

    # ========== 更多功能处理 ==========

    def _clear_cache(self):
        """清除本地残影渲染缓存。"""
        db.clear_cache()
        self._show_toast(TOAST_CACHE_CLEARED)

    def _cycle_perf_tier(self, _checked=False):
        """三档性能模式轮转：HIGH → MEDIUM → LOW → HIGH ..."""
        from utils.constants import PerfTier
        current = self.canvas._perf_tier
        order = [PerfTier.HIGH, PerfTier.MEDIUM, PerfTier.LOW]
        try:
            idx = order.index(current)
            next_tier = order[(idx + 1) % len(order)]
        except ValueError:
            next_tier = PerfTier.HIGH
        self.canvas.set_perf_tier(next_tier)
        labels = {PerfTier.HIGH: "画质优先", PerfTier.MEDIUM: "均衡模式", PerfTier.LOW: "性能优先"}
        tip = f"性能模式 → {labels.get(next_tier, next_tier)}"
        self._show_toast(tip)

    def _show_shortcuts(self):
        """快捷键查看弹窗。"""
        dlg = ShortcutsDialog(self)
        dlg.move(
            self.x() + (self.width() - dlg.width()) // 2,
            self.y() + (self.height() - dlg.height()) // 2,
        )
        dlg.exec_()

    def _show_about(self):
        """关于软件弹窗。"""
        dlg = AboutDialog(self)
        dlg.move(
            self.x() + (self.width() - dlg.width()) // 2,
            self.y() + (self.height() - dlg.height()) // 2,
        )
        dlg.exec_()

    # ========== 关闭 ==========

    def closeEvent(self, event):
        """关闭前：优雅关闭画布后台线程、冲洗延迟批注、刷新列表。"""
        try:
            self.canvas.shutdown()
        except Exception:
            pass
        try:
            self.canvas._flush_deferred_unlocks()
        except Exception:
            pass
        try:
            if self._current_page_id > 0:
                self.sidebar.refresh()
                self.archive_grid.refresh()
        except Exception:
            pass
        # 记忆窗口几何（尺寸与位置），使下次打开时文字 reflow 结果与关闭前一致
        try:
            geo = self.saveGeometry().toBase64().data()
            if isinstance(geo, bytes):
                geo = geo.decode("utf-8")
            db.set_setting("window_geometry", geo)
        except Exception:
            pass
        event.accept()


class _TipBox(QDialog):
    def __init__(self):
        super().__init__(None, Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self._text = ""
        self._font = QFont("Microsoft YaHei UI", 11)
        self.hide()

    def setTipText(self, text):
        self._text = text
        fm = QFontMetrics(self._font)
        text_width = fm.horizontalAdvance(text)
        text_height = fm.height()
        padding = 10
        self.setFixedSize(text_width + padding * 2, text_height + 8)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        # 先整块填米色：不透明窗口底层在 Win11 dark mode 下是系统深色背景，
        # 不先填满的话圆角/边框外会露出黑色。按需求不做圆角。
        painter.fillRect(self.rect(), QColor("#F5EDDE"))
        # 1px 米色边框（直角矩形）
        rect = self.rect().adjusted(0, 0, -1, -1)
        painter.setPen(QColor("#D0C4B0"))
        painter.drawRect(rect)
        # 文字（深棕）
        painter.setPen(QColor("#5C5244"))
        painter.setFont(self._font)
        fm = QFontMetrics(self._font)
        x = (self.width() - fm.horizontalAdvance(self._text)) // 2
        y = (self.height() + fm.ascent()) // 2 - 1
        painter.drawText(x, y, self._text)
        painter.end()


class _TipFilter(QObject):
    def __init__(self):
        super().__init__()
        self._tip = _TipBox()
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._tip.hide)

    def eventFilter(self, obj, event):
        t = event.type()
        if t == QEvent.ToolTip and obj is not None and obj.toolTip():
            QToolTip.hideText()
            self._tip.setTipText(obj.toolTip())
            gpos = QCursor.pos()
            self._tip.move(gpos.x() + 14, gpos.y() + 14)
            self._tip.show()
            self._timer.start(5000)
            return True
        if t == QEvent.Leave:
            self._timer.start(300)
            return False
        if t == QEvent.MouseButtonPress:
            self._tip.hide()
            return False
        return False


def main():
    QApplication.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True)
    app = QApplication(sys.argv)
    app.setFont(QFont(SYSTEM_FONT, 10))
    app.installEventFilter(_TipFilter())
    app.setStyleSheet(
        "QMenu {"
        "  background: transparent;"
        "  border: none;"
        "  padding: 6px;"
        "}"
        "QMenu::item {"
        "  color: #4A453B;"
        "  padding: 6px 18px 6px 14px;"
        "  border-radius: 6px;"
        "}"
        "QMenu::item:selected {"
        "  background: rgba(196,186,168,0.45);"
        "}"
        "QMenu::separator {"
        "  height: 1px;"
        "  background: rgba(196,186,168,0.5);"
        "  margin: 4px 8px;"
        "}"
    )

    window = MainWindow()
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
