"""
侧边档案栏 —— 氛围升级版。
拉动式展开，700ms 缓动，文艺化标签。
"""
import time
from PyQt5.QtCore import (
    Qt, QPropertyAnimation, QEasingCurve, pyqtSignal, QTimer,
)
from PyQt5.QtGui import QPainter, QColor, QFont, QFontMetrics, QLinearGradient
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QScrollArea,
)

from utils.constants import (
    SERIF_FONT, SYSTEM_FONT, TEXT_COLOR, HINT_TEXT_COLOR,
    BUTTON_BG, BUTTON_HOVER_BG, BUTTON_PRESSED_BG, PAPER_BG_HEX, get_paper_stage,
    DURATION_SIDEBAR_SLIDE, CONTROL_RADIUS, SIDEBAR_WIDTH,
    DARK_BG, DARK_TEXT, DARK_HINT, DARK_BUTTON_BG, DARK_BUTTON_HOVER,
)


class ArchiveSidebar(QWidget):
    """侧边栏档案列表。"""

    page_selected = pyqtSignal(int)
    sidebar_hidden = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        # 用 min/max 控制展开宽度（max 动画在 0↔SIDEBAR_WIDTH 间滑动）；
        # 不能用 setFixedWidth（会把 min 也锁成固定值，导致收起动画失效）。
        self.setMinimumWidth(0)
        self.setMaximumWidth(0)
        self._dark_mode: bool = False
        self._pages: list = []
        self._expanded: bool = False
        self._animating: bool = False
        self._sidebar_visible: bool = False

        # 离开后 1.5 秒自动收起
        self._auto_close_timer = QTimer(self)
        self._auto_close_timer.setSingleShot(True)
        self._auto_close_timer.setInterval(1500)
        self._auto_close_timer.timeout.connect(self._on_auto_close)

        # 移除生硬阴影，改用柔和边缘过渡

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        title = QLabel("旧纸页")
        title.setFont(QFont(SERIF_FONT, 14))
        title.setStyleSheet(f"color: {TEXT_COLOR};")
        layout.addWidget(title)

        # 滚动区域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("""
            QScrollArea { background: transparent; border: none; }
            QScrollBar:vertical { width: 3px; background: transparent; }
            QScrollBar::handle:vertical {
                background: #D9D3C5; border-radius: 3px;
            }
        """)

        self.list_widget = QWidget()
        self.list_layout = QVBoxLayout(self.list_widget)
        self.list_layout.setContentsMargins(0, 0, 0, 0)
        self.list_layout.setSpacing(6)
        self.list_layout.addStretch()
        scroll.setWidget(self.list_widget)
        layout.addWidget(scroll, 1)

    def set_dark_mode(self, enabled: bool):
        self._dark_mode = enabled
        self.update()

    def refresh(self):
        """重新加载页面列表。"""
        self._pages = db.list_pages()
        self._redraw_list()

    def _redraw_list(self):
        while self.list_layout.count() > 1:
            item = self.list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for page in self._pages:
            btn = self._make_item(page)
            self.list_layout.insertWidget(self.list_layout.count() - 1, btn)

        if not self._pages:
            empty = QLabel("尚无旧纸")
            empty.setFont(QFont(SERIF_FONT, 11))
            empty.setStyleSheet(f"color: {HINT_TEXT_COLOR};")
            self.list_layout.insertWidget(0, empty)

    def _make_item(self, page) -> QPushButton:
        age_days = (time.time() - page.create_time) / 86400 if page.create_time else 0
        freshness = max(0, 100 - int(age_days * 5))
        if page.is_sealed:
            freshness = 100
        stage_label = get_paper_stage(page.create_time, page.is_sealed) if page.create_time else "黄1"
        label = f"{page.title or '未命名'} · {stage_label} · {freshness}%"
        if page.is_sealed:
            label += " ♢"

        btn = QPushButton(label)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.clicked.connect(lambda checked, pid=page.page_id: self.page_selected.emit(pid))
        btn.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #{BUTTON_BG[1:]}, stop:0.6 #{BUTTON_BG[1:]}, stop:1 #{BUTTON_HOVER_BG[1:]});
                color: {TEXT_COLOR};
                border: none;
                border-radius: {CONTROL_RADIUS}px;
                padding: 8px 10px;
                font-family: "{SYSTEM_FONT}";
                font-size: 10px;
                text-align: left;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #{BUTTON_HOVER_BG[1:]}, stop:1 #{BUTTON_BG[1:]});
            }}
            QPushButton:pressed {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #{BUTTON_PRESSED_BG[1:]}, stop:1 #{BUTTON_HOVER_BG[1:]});
            }}
        """)
        return btn

    def toggle_expand(self):
        """展开/收起（带动画）。"""
        if self._animating:
            return
        self._expanded = not self._expanded
        self._sidebar_visible = self._expanded
        if not self._expanded:
            self._auto_close_timer.stop()
            self.sidebar_hidden.emit()
        target_width = SIDEBAR_WIDTH if self._expanded else 0
        self._animating = True

        anim = QPropertyAnimation(self, b"maximumWidth")
        anim.setDuration(DURATION_SIDEBAR_SLIDE)
        anim.setStartValue(self.width())
        anim.setEndValue(target_width)
        anim.setEasingCurve(QEasingCurve.Type.InOutCubic)
        anim.finished.connect(lambda: setattr(self, '_animating', False))
        anim.start()

    def show_sidebar(self):
        """展开侧边栏（用于外部触发）。"""
        if not self._expanded and not self._animating:
            if self._sidebar_visible:
                return
            self._expanded = True
            self._sidebar_visible = True
            self._animating = True
            self.show()   # 初始为 hide()；展开前必须可见，否则动画不显示
            anim = QPropertyAnimation(self, b"maximumWidth")
            anim.setDuration(DURATION_SIDEBAR_SLIDE)
            anim.setStartValue(self.maximumWidth())
            anim.setEndValue(SIDEBAR_WIDTH)
            anim.setEasingCurve(QEasingCurve.Type.InOutCubic)
            anim.finished.connect(lambda: setattr(self, '_animating', False))
            anim.start()

    def hide_sidebar(self):
        """收起侧边栏。"""
        if self._expanded and not self._animating:
            self._expanded = False
            self._sidebar_visible = False
            self._auto_close_timer.stop()
            self._animating = True
            anim = QPropertyAnimation(self, b"maximumWidth")
            anim.setDuration(DURATION_SIDEBAR_SLIDE)
            anim.setStartValue(self.maximumWidth())
            anim.setEndValue(0)
            anim.setEasingCurve(QEasingCurve.Type.InOutCubic)
            anim.finished.connect(lambda: [setattr(self, '_animating', False), self.sidebar_hidden.emit()])
            anim.start()

    def _on_auto_close(self):
        """1.5秒后自动收起。"""
        self.hide_sidebar()

    def enterEvent(self, event):
        """鼠标进入侧边栏，停止自动收起计时。"""
        self._auto_close_timer.stop()
        super().enterEvent(event)

    def leaveEvent(self, event):
        """鼠标离开侧边栏，启动1.5秒自动收起计时。"""
        if self._sidebar_visible:
            self._auto_close_timer.start()
        super().leaveEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        if self._dark_mode:
            c = QColor(DARK_BG)
        else:
            c = QColor(245, 240, 232)
        painter.fillRect(self.rect(), c)
        # 右侧边缘柔化渐变
        gradient = QLinearGradient(self.width() - 15, 0, self.width(), 0)
        if self._dark_mode:
            gradient.setColorAt(0, QColor(DARK_BG))
            gradient.setColorAt(1, QColor(DARK_BG).lighter(105))
        else:
            gradient.setColorAt(0, QColor(245, 240, 232))
            gradient.setColorAt(1, QColor(245, 240, 232).lighter(105))
        painter.fillRect(self.width() - 15, 0, 15, self.height(), gradient)
        painter.end()


from utils.db import db
