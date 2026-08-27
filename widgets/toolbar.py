"""
顶部工具栏 —— 氛围升级版。
常态低透明度，鼠标靠近清晰显示；全屏近乎隐形；
新增纯画布模式、氛围开关按钮。
"""
import re
from PyQt5.QtCore import (
    Qt, pyqtSignal, QTimer, QPropertyAnimation, QEasingCurve,
    QRect, QPoint,
)
from PyQt5.QtGui import (
    QPainter, QColor, QFont, QPen, QFontMetrics,
    QMouseEvent,
)
from PyQt5.QtWidgets import (
    QWidget, QPushButton, QHBoxLayout, QLabel,
    QApplication, QMenu, QAction,
)

from utils.constants import (
    SYSTEM_FONT,
    TEXT_COLOR, HINT_TEXT_COLOR, BUTTON_BG, BUTTON_HOVER_BG, BUTTON_PRESSED_BG, BUTTON_TEXT,
    TONE_OPTIONS, EPIGRAPHS,
    UI_OPACITY_HOVER, UI_OPACITY_FULLSCREEN,
    UI_HOVER_ZONE, CONTROL_RADIUS,
    DARK_BG, DARK_TEXT, DARK_HINT, DARK_BUTTON_BG, DARK_BUTTON_HOVER, DARK_BUTTON_TEXT,
    TOAST_PURE_MODE, TOAST_PURE_MODE_EXIT,
    TOAST_ATMOSPHERE_ON, TOAST_ATMOSPHERE_OFF,
    TOAST_STYLE_CHANGED, TOAST_DARK_ON, TOAST_DARK_OFF,
    WINDOW_BORDER_LIGHT, WINDOW_BORDER_DARK,
    BORDER_OPACITY_LOW,
    EPIGRAPH_COLOR_LIGHT, EPIGRAPH_HOVER_LIGHT, EPIGRAPH_COLOR_DARK,
)
from utils.db import db
from widgets.round_helper import RoundedMenu


class Toolbar(QWidget):
    """顶部工具栏（含页眉题记气泡）。"""

    # 信号
    export_requested = pyqtSignal()
    api_settings_requested = pyqtSignal()
    new_page_requested = pyqtSignal()
    reset_requested = pyqtSignal()
    delete_all_requested = pyqtSignal()
    tone_changed = pyqtSignal(str)
    dark_mode_toggled = pyqtSignal(bool)
    pure_mode_toggled = pyqtSignal(bool)
    atmosphere_toggled = pyqtSignal(bool)
    toast_requested = pyqtSignal(str)
    clear_cache_requested = pyqtSignal()
    handwriting_toggled = pyqtSignal(bool)
    import_font_requested = pyqtSignal()
    manage_fonts_requested = pyqtSignal()
    performance_mode_toggled = pyqtSignal(bool)
    shortcuts_requested = pyqtSignal()
    about_requested = pyqtSignal()
    sponsor_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(40)
        self.setMouseTracking(True)

        self._dark_mode: bool = False
        self._fullscreen: bool = False
        self._pure_mode: bool = False
        self._current_opacity: float = UI_OPACITY_HOVER
        self._target_opacity: float = UI_OPACITY_HOVER
        self._hover_zone_active: bool = False
        self._mouse_near: bool = False

        self._current_tone: str = "岁月静谧"
        self._epigraph_text: str = EPIGRAPHS[0]
        self._epigraph_visible: bool = False
        self._epigraph_timer: float = 0.0

        self._is_sealed: bool = False
        self._atmosphere_on: bool = False
        self._page_count: int = 0

        self._build_ui()

        # 透明度渐变动画
        self._anim = QPropertyAnimation(self, b"windowOpacity")
        self._anim.setDuration(500)
        self._anim.setEasingCurve(QEasingCurve.Type.InOutCubic)

        # 帧更新（60fps）
        self._ticker = QTimer(self)
        self._ticker.setInterval(16)
        self._ticker.timeout.connect(self._tick)
        self._ticker.start()

    def _build_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 0, 8, 0)
        layout.setSpacing(6)

        # 页眉题记（点击显示/隐藏气泡）
        self.label_epigraph = QPushButton("")
        self.label_epigraph.setFixedHeight(28)
        self.label_epigraph.setFixedWidth(320)   # 固定宽度：题记变长时，后面按钮不随之移动
        self.label_epigraph.setCursor(Qt.CursorShape.PointingHandCursor)
        self.label_epigraph.setFlat(True)
        self.label_epigraph.clicked.connect(self._toggle_epigraph)
        layout.addWidget(self.label_epigraph)

        # 文风下拉
        self.btn_tone = QPushButton("岁月静谧")
        self.btn_tone.setFixedHeight(28)
        self.btn_tone.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_tone.clicked.connect(self._show_tone_menu)
        layout.addWidget(self.btn_tone)

        # 氛围开关
        self.btn_atmosphere = QPushButton("✦")
        self.btn_atmosphere.setFixedSize(28, 28)
        self.btn_atmosphere.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_atmosphere.setToolTip("光影氛围")
        self.btn_atmosphere.clicked.connect(self._toggle_atmosphere)
        layout.addWidget(self.btn_atmosphere)

        # 导出按钮
        self.btn_export = QPushButton("⇩")
        self.btn_export.setFixedSize(28, 28)
        self.btn_export.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_export.setToolTip("导出画布")
        self.btn_export.clicked.connect(self.export_requested.emit)
        layout.addWidget(self.btn_export)

        # 深色模式
        self.btn_dark = QPushButton("◑")
        self.btn_dark.setFixedSize(28, 28)
        self.btn_dark.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_dark.setToolTip("深色模式")
        self.btn_dark.clicked.connect(self._toggle_dark)
        layout.addWidget(self.btn_dark)

        # 纯画布模式
        self.btn_pure = QPushButton("⊡")
        self.btn_pure.setFixedSize(28, 28)
        self.btn_pure.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_pure.setToolTip("纯画布模式（隐藏所有界面）")
        self.btn_pure.clicked.connect(self._toggle_pure_mode)
        layout.addWidget(self.btn_pure)

        # 手写模式
        self.btn_hand = QPushButton("✎")
        self.btn_hand.setFixedSize(28, 28)
        self.btn_hand.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_hand.setToolTip("手写模式")
        self.btn_hand.clicked.connect(self._toggle_handwriting)
        layout.addWidget(self.btn_hand)

        # 更多菜单
        self.btn_more = QPushButton("⋯")
        self.btn_more.setFixedSize(28, 28)
        self.btn_more.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_more.clicked.connect(self._show_more_menu)
        layout.addWidget(self.btn_more)

        layout.addStretch(1)

        # 窗口控制（最小化/最大化/关闭）
        self.btn_min = QPushButton("—")
        self.btn_min.setFixedSize(28, 28)
        self.btn_min.clicked.connect(lambda: self.window().showMinimized())
        layout.addWidget(self.btn_min)

        self.btn_max = QPushButton("□")
        self.btn_max.setFixedSize(28, 28)
        self.btn_max.clicked.connect(self._toggle_max)
        layout.addWidget(self.btn_max)

        self.btn_close = QPushButton("×")
        self.btn_close.setFixedSize(28, 28)
        self.btn_close.clicked.connect(lambda: self.window().close())
        layout.addWidget(self.btn_close)

        self._apply_style()

    def _apply_style(self):
        # 浅色按钮：暖中棕渐变底 + 暖白字，与深色模式同用 CONTROL_RADIUS 大圆角。
        # 颜色比深色模式亮一档，在米纸上清晰而不沉重。
        btn_style = f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {BUTTON_BG}, stop:0.6 {BUTTON_BG}, stop:1 {BUTTON_HOVER_BG});
                color: {BUTTON_TEXT};
                border: none;
                border-radius: {CONTROL_RADIUS}px;
                font-family: "{SYSTEM_FONT}";
                font-size: 12px;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {BUTTON_HOVER_BG}, stop:1 {BUTTON_BG});
            }}
            QPushButton:pressed {{
                background: {BUTTON_PRESSED_BG};
            }}
        """
        for btn in [self.btn_atmosphere, self.btn_export, self.btn_dark,
                     self.btn_pure, self.btn_hand, self.btn_more,
                     self.btn_min, self.btn_max, self.btn_close]:
            btn.setStyleSheet(btn_style)

        self.btn_tone.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {BUTTON_BG}, stop:0.6 {BUTTON_BG}, stop:1 {BUTTON_HOVER_BG});
                color: {BUTTON_TEXT};
                border: none;
                border-radius: {CONTROL_RADIUS}px;
                font-family: "{SYSTEM_FONT}";
                font-size: 12px;
                padding: 0 10px;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {BUTTON_HOVER_BG}, stop:1 {BUTTON_BG});
            }}
            QPushButton:pressed {{
                background: {BUTTON_PRESSED_BG};
            }}
        """)
        self.label_epigraph.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {EPIGRAPH_COLOR_LIGHT};
                border: none;
                font-family: "{SYSTEM_FONT}";
                font-size: 11px;
                padding: 0 6px;
                text-align: left;
            }}
            QPushButton:hover {{
                color: {EPIGRAPH_HOVER_LIGHT};
            }}
        """)

    # ========== 公共接口 ==========

    def set_sealed(self, sealed: bool):
        self._is_sealed = sealed
        disabled_style = f"""
            QPushButton {{
                background: {BUTTON_BG};
                color: {HINT_TEXT_COLOR};
                border: 1px solid rgba(166,156,138,0.15);
                border-radius: {CONTROL_RADIUS}px;
                font-family: "{SYSTEM_FONT}";
                font-size: 12px;
                padding: 0 10px;
                opacity: 0.4;
            }}
        """
        if sealed:
            self.btn_tone.setEnabled(False)
            self.btn_tone.setStyleSheet(disabled_style)
            self.btn_atmosphere.setEnabled(False)
            self.btn_hand.setEnabled(False)
        else:
            self.btn_tone.setEnabled(True)
            self.btn_atmosphere.setEnabled(True)
            self.btn_hand.setEnabled(True)
        self._apply_style()
        self.set_atmosphere_on(self._atmosphere_on)

    def set_page_count(self, count: int):
        self._page_count = count
        has_pages = count > 0
        disabled_style = f"""
            QPushButton {{
                background: {BUTTON_BG};
                color: {HINT_TEXT_COLOR};
                border: 1px solid rgba(166,156,138,0.15);
                border-radius: {CONTROL_RADIUS}px;
                font-family: "{SYSTEM_FONT}";
                font-size: 12px;
                opacity: 0.4;
            }}
        """
        for btn in [self.btn_export, self.btn_tone,
                     self.btn_atmosphere, self.btn_hand, self.btn_more]:
            btn.setEnabled(has_pages)
            if not has_pages:
                btn.setStyleSheet(disabled_style)

    def set_tone(self, tone: str):
        self._current_tone = tone
        self.btn_tone.setText(tone)

    def set_dark_mode(self, enabled: bool):
        self._dark_mode = enabled
        self.btn_dark.setText("◐" if enabled else "◑")
        self._apply_dark_style()
        self.set_atmosphere_on(self._atmosphere_on)

    def set_fullscreen(self, fullscreen: bool):
        self._fullscreen = fullscreen
        self.btn_max.setText("❐" if fullscreen else "□")
        if fullscreen:
            self._target_opacity = UI_OPACITY_FULLSCREEN
            self.setFixedHeight(30)
            self.label_epigraph.setVisible(False)
        else:
            self._target_opacity = UI_OPACITY_HOVER
            self.setFixedHeight(40)
            self.label_epigraph.setVisible(True)

    def set_pure_mode(self, pure: bool):
        self._pure_mode = pure
        self.btn_pure.setText("⊡" if not pure else "◉")

    def set_atmosphere_on(self, on: bool):
        self._atmosphere_on = on
        if self._dark_mode:
            bg = DARK_BUTTON_HOVER if on else DARK_BUTTON_BG
        else:
            bg = BUTTON_PRESSED_BG if on else BUTTON_BG
        style = self.btn_atmosphere.styleSheet()
        # 先清掉所有已知背景写法再写回，保证来回切换都能正确回退
        for old_bg in [BUTTON_BG, BUTTON_PRESSED_BG, DARK_BUTTON_BG, DARK_BUTTON_HOVER]:
            style = style.replace(f"background: {old_bg};", "BACKGROUND_PLACEHOLDER;")
        # 也清除渐变写法
        if "background: qlineargradient" in style:
            style = re.sub(
                r'background:\s*[\w-]+\([^)]+\)\s*;',
                'BACKGROUND_PLACEHOLDER;', style
            )
        self.btn_atmosphere.setStyleSheet(style.replace("BACKGROUND_PLACEHOLDER;", f"background: {bg};"))

    # ========== 页眉题记 ==========

    def set_epigraph(self, text: str):
        self._epigraph_text = text
        self.label_epigraph.setText(text[:26] + "…" if len(text) > 26 else text)

    def get_epigraph(self) -> str:
        """返回当前页眉题记文本（供导出"带上页眉那句诗"使用）。"""
        return self._epigraph_text

    def _toggle_epigraph(self):
        self._epigraph_visible = not self._epigraph_visible
        self._epigraph_timer = 0
        if self._epigraph_visible:
            self.toast_requested.emit(self._epigraph_text)

    def _popup_pos(self, menu, button):
        """计算菜单弹出位置：在按钮正下方，右边缘对齐按钮右边缘，并夹在屏幕内。

        工具栏按钮位于窗口最右侧，若直接左对齐向下弹出，菜单会向右延伸、
        整体越出屏幕右边界被裁切——既看不到（像“打不开”），裁切处又会露出
        全局 QMenu 的浅色边框。故改为右对齐并做屏幕边界夹取。
        """
        # 先算按钮锚点（必须在 screenAt 之前）
        pos = button.mapToGlobal(QPoint(button.width(), button.height()))
        screen = QApplication.screenAt(pos) or QApplication.primaryScreen()
        if screen is None:
            # 理论上不会发生（无可用屏幕），退回按钮正下方
            return QPoint(pos.x() - 200, pos.y())
        ag = screen.availableGeometry()
        mw = menu.sizeHint().width()
        mh = menu.sizeHint().height()
        # 菜单整体左移 mw，使右边缘对齐按钮右边缘
        x = pos.x() - mw
        y = pos.y()
        if x < ag.left():
            x = ag.left()
        if y + mh > ag.bottom():
            # 下方放不下则向上弹出
            y = pos.y() - mh - button.height()
        return QPoint(x, y)

    def _show_tone_menu(self):
        if self._is_sealed:
            return
        menu = RoundedMenu(self, self._dark_mode)
        for name, desc in TONE_OPTIONS:
            action = QAction(f"{name}  ·  {desc}", menu)
            action.triggered.connect(lambda checked, n=name: self._on_tone_selected(n))
            menu.addAction(action)
        menu.exec_(self._popup_pos(menu, self.btn_tone))

    def _on_tone_selected(self, tone: str):
        self._current_tone = tone
        self.btn_tone.setText(tone)
        self.tone_changed.emit(tone)
        self.toast_requested.emit(TOAST_STYLE_CHANGED)

    def _toggle_dark(self):
        self._dark_mode = not self._dark_mode
        self.dark_mode_toggled.emit(self._dark_mode)
        if self._dark_mode:
            self.toast_requested.emit(TOAST_DARK_ON)
        else:
            self.toast_requested.emit(TOAST_DARK_OFF)

    def _toggle_pure_mode(self):
        self._pure_mode = not self._pure_mode
        self.pure_mode_toggled.emit(self._pure_mode)
        if self._pure_mode:
            self.toast_requested.emit(TOAST_PURE_MODE)
        else:
            self.toast_requested.emit(TOAST_PURE_MODE_EXIT)

    def _toggle_atmosphere(self):
        from utils.db import db
        current = db.get_setting("atmosphere_enabled", "1") == "1"
        new_val = not current
        db.set_setting("atmosphere_enabled", "1" if new_val else "0")
        self.atmosphere_toggled.emit(new_val)
        if new_val:
            self.toast_requested.emit(TOAST_ATMOSPHERE_ON)
        else:
            self.toast_requested.emit(TOAST_ATMOSPHERE_OFF)

    def _toggle_handwriting(self):
        """手写体切换。"""
        current = db.get_setting("use_handwriting", "1") == "1"
        new_val = not current
        db.set_setting("use_handwriting", "1" if new_val else "0")
        self.handwriting_toggled.emit(new_val)
        self.toast_requested.emit("手写模式已启用" if new_val else "手写模式已关闭")

    def _show_more_menu(self):
        menu = RoundedMenu(self, self._dark_mode)
        # 注意：QAction.triggered 会带 bool 参数，不能直接接无参信号的 emit，
        # 否则多传参数触发 TypeError 崩溃；统一用 lambda 包裹。
        menu.addAction("导出画布…", lambda: self.export_requested.emit())
        menu.addSeparator()
        menu.addAction("设置 API 密钥…", lambda: self.api_settings_requested.emit())
        menu.addAction("导入手写字体…", lambda: self.import_font_requested.emit())
        menu.addAction("管理手写字体…", lambda: self.manage_fonts_requested.emit())
        menu.addSeparator()
        menu.addAction("新建一篇笔记", lambda: self.new_page_requested.emit())
        menu.addSeparator()
        menu.addAction("清除本地缓存", lambda: self.clear_cache_requested.emit())
        menu.addAction("重置当前页面", lambda: self.reset_requested.emit())
        menu.addAction("删除所有笔记", lambda: self.delete_all_requested.emit())
        menu.addSeparator()
        menu.addAction("性能模式（三档轮转）", lambda: self.performance_mode_toggled.emit(True))
        menu.addAction("快捷键查看…", lambda: self.shortcuts_requested.emit())
        menu.addSeparator()
        menu.addAction("赞助支持…", lambda: self.sponsor_requested.emit())
        menu.addAction("关于软件", lambda: self.about_requested.emit())
        menu.exec_(self._popup_pos(menu, self.btn_more))

    def _toggle_max(self):
        win = self.window()
        if win.isMaximized():
            win.showNormal()
        else:
            win.showMaximized()

    # ========== 帧更新 ==========

    def _tick(self):
        """平滑透明度过渡。"""
        if abs(self._current_opacity - self._target_opacity) > 0.005:
            step = (1.0 / 30) * (1 if self._target_opacity > self._current_opacity else -1)
            self._current_opacity = max(0.01, min(1.0, self._current_opacity + step))
            # 更新所有子控件透明度
            self.setWindowOpacity(self._current_opacity)
            # 通过样式表控制透明度
            self.setStyleSheet(self._get_opacity_style())

        # 题记气泡计时
        if self._epigraph_visible:
            self._epigraph_timer += 0.016

    def _get_opacity_style(self):
        """返回当前透明度的样式表。"""
        alpha = int(self._current_opacity * 255)
        bg = f"rgba({44},{42},{39},{self._current_opacity:.2f})"
        return f"""
            Toolbar {{
                background: {bg};
            }}
        """

    # ========== 鼠标检测 ==========

    def enterEvent(self, event):
        self._mouse_near = True

    def leaveEvent(self, event):
        self._mouse_near = False

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        c = QColor(44, 42, 39)
        c.setAlphaF(self._current_opacity)
        painter.fillRect(self.rect(), c)
        # 窗口上边框：由工具栏自绘，半透明、悬停更清晰
        # （各控件自绘自己的边，避免主窗口描边被子控件重绘覆盖而闪烁/露出黑线）
        bc = QColor(*(WINDOW_BORDER_DARK if self._dark_mode else WINDOW_BORDER_LIGHT))
        bc.setAlphaF(BORDER_OPACITY_LOW)
        painter.setPen(QPen(bc, 1))
        painter.drawLine(0, 0, self.width(), 0)
        painter.end()

    def _apply_dark_style(self):
        """应用深色模式样式。"""
        if self._dark_mode:
            self.setStyleSheet(f"""
                Toolbar {{
                    background: rgba({44},{42},{39},{self._current_opacity:.2f});
                }}
                QLabel {{
                    color: {DARK_HINT};
                    font-family: "{SYSTEM_FONT}";
                }}
            """)
            # 深色按钮：哑光深棕底+暖米字，与深色工具栏背景形成柔和层次
            dark_btn = f"""
                QPushButton {{
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {DARK_BUTTON_BG}, stop:0.6 {DARK_BUTTON_BG}, stop:1 {DARK_BUTTON_HOVER});
                    color: {DARK_BUTTON_TEXT};
                    border: none;
                    border-radius: {CONTROL_RADIUS}px;
                    font-family: "{SYSTEM_FONT}";
                    font-size: 12px;
                }}
                QPushButton:hover {{
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {DARK_BUTTON_HOVER}, stop:1 {DARK_BUTTON_BG});
                }}
                QPushButton:pressed {{
                    background: {DARK_BUTTON_HOVER};
                }}
            """
            for btn in [self.btn_atmosphere, self.btn_export, self.btn_dark,
                         self.btn_pure, self.btn_hand, self.btn_more,
                         self.btn_min, self.btn_max, self.btn_close]:
                btn.setStyleSheet(dark_btn)
            self.btn_tone.setStyleSheet(dark_btn + f"""
                QPushButton {{
                    padding: 0 10px;
                }}
            """)
            # 题词（epigraph）是 QPushButton，不受上面 QLabel 影响：
            # 深色模式下默认亮色，hover 更亮，避免与深色工具栏背景同色导致看不见
            self.label_epigraph.setStyleSheet(f"""
                QPushButton {{
                    background: transparent;
                    color: {EPIGRAPH_COLOR_DARK};
                    border: none;
                    font-family: "{SYSTEM_FONT}";
                    font-size: 11px;
                    padding: 0 6px;
                    text-align: left;
                }}
                QPushButton:hover {{
                    color: {DARK_TEXT};
                }}
            """)
        else:
            self._apply_style()
