"""
右侧触发条 —— 氛围升级版。
更低调，hover 慢慢显现。
"""
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QPainter, QColor, QFont
from PyQt5.QtWidgets import QWidget, QLabel

from utils.constants import (
    DURATION_SIDEBAR_SLIDE, HINT_TEXT_COLOR, SYSTEM_FONT,
    DARK_HINT,
)


class ArchiveTrigger(QWidget):
    """右侧触发条（14px宽，hover 升 opacity；点击在 编辑器 ↔ 档案馆 间切换）。"""

    triggered = pyqtSignal()               # hover 300ms：展开侧栏
    page_toggle_requested = pyqtSignal()   # 点击：编辑器 ↔ 档案馆 双向切换

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(14)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._opacity: float = 0.15
        self._hover: bool = False
        self._dark_mode: bool = False
        self._sidebar_visible: bool = False

        self._ticker = QTimer(self)
        self._ticker.setInterval(16)
        self._ticker.timeout.connect(self._tick)
        self._ticker.start()

        # 点击延迟（防误触）
        self._hover_timer = QTimer(self)
        self._hover_timer.setSingleShot(True)
        self._hover_timer.setInterval(300)
        self._hover_timer.timeout.connect(self.triggered.emit)

    def set_dark_mode(self, enabled: bool):
        self._dark_mode = enabled
        self.update()

    def set_sidebar_visible(self, visible: bool):
        """侧边栏已展开时禁止重复触发。"""
        self._sidebar_visible = visible

    def enterEvent(self, event):
        self._hover = True
        # 防抖动：侧边栏已展开时不启动悬停计时器
        if not self._sidebar_visible:
            self._hover_timer.start()

    def leaveEvent(self, event):
        self._hover = False
        self._hover_timer.stop()

    def mousePressEvent(self, event):
        # 点击：在 编辑器 ↔ 档案馆 两页间切换（取代原返回按钮）
        self.page_toggle_requested.emit()

    def _tick(self):
        target = 0.55 if self._hover else 0.15
        step = (1.0 / 30)
        if abs(self._opacity - target) > 0.005:
            self._opacity += step * (1 if target > self._opacity else -1)
            self._opacity = max(0.08, min(1.0, self._opacity))
            self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        color = QColor(DARK_HINT if self._dark_mode else HINT_TEXT_COLOR)
        color.setAlphaF(self._opacity)
        painter.fillRect(self.rect(), color)
        # 小三角指示符
        painter.setPen(QColor(0, 0, 0, 0))
        painter.setFont(QFont(SYSTEM_FONT, 8))
        painter.save()
        painter.setPen(color)
        painter.drawText(1, self.height() // 2 + 3, "◁")
        painter.restore()
        painter.end()
