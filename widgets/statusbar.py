"""
底部状态栏 —— 需求文档精确实现。
高度 36px，左侧：已写字数 / 续命总次数 / 批注数。
右侧：页面衰老值百分比。封存页面标注"（封存定格）"。
自适应屏幕兼容：h<600隐藏全部文字，w<700隐藏续命次数。
"""
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPainter, QColor, QPen, QFont, QPalette
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel

from utils.constants import (
    SYSTEM_FONT, TEXT_COLOR, HINT_TEXT_COLOR,
    UI_OPACITY_HOVER, UI_OPACITY_FULLSCREEN,
    DARK_TEXT, DARK_HINT, DARK_BG,
    COMMENT_COUNTER_COLOR, COMMENT_COUNTER_COLOR_DARK,
    WINDOW_BORDER_DARK, WINDOW_BORDER_LIGHT, BG_DEFAULT,
    BORDER_OPACITY_LOW,
)


def _lerp(a: int, b: int, t: float) -> int:
    return int(a + (b - a) * t)
from utils.db import db


class StatusBar(QWidget):
    """底部统计栏：已写字数 / 续命总次数 / 批注数 / 衰老值。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(36)

        self._dark_mode: bool = False
        self._fullscreen: bool = False

        layout = QHBoxLayout(self)
        layout.setContentsMargins(40, 0, 40, 0)
        layout.setSpacing(32)

        self.label_chars = QLabel("纸页尚白")
        self.label_chars.setFont(QFont(SYSTEM_FONT, 9))
        self.label_chars.setAttribute(Qt.WA_TranslucentBackground)
        layout.addWidget(self.label_chars)

        self.label_revives = QLabel("")
        self.label_revives.setFont(QFont(SYSTEM_FONT, 9))
        self.label_revives.setAttribute(Qt.WA_TranslucentBackground)
        layout.addWidget(self.label_revives)

        self.label_comments = QLabel("")
        self.label_comments.setFont(QFont(SYSTEM_FONT, 9))
        self.label_comments.setAttribute(Qt.WA_TranslucentBackground)
        layout.addWidget(self.label_comments)

        layout.addStretch()

        self.label_freshness = QLabel("")
        self.label_freshness.setFont(QFont(SYSTEM_FONT, 9))
        self.label_freshness.setAttribute(Qt.WA_TranslucentBackground)
        layout.addWidget(self.label_freshness)

        self._apply_colors()

    def set_chars(self, count: int):
        if count == 0:
            self.label_chars.setText("纸页尚白")
        else:
            self.label_chars.setText(f"已写 {count} 字")

    def set_revives(self, count: int):
        if count == 0:
            self.label_revives.setText("")
        else:
            self.label_revives.setText(f"曾续命 {count} 次")

    def set_comments(self, count: int, max_c: int = 8):
        if count == 0:
            self.label_comments.setText("")
        else:
            self.label_comments.setText(f"批注 {count}/{max_c}")

    def set_freshness(self, ratio: float, is_sealed: bool = False):
        pct = int(ratio * 100)
        if is_sealed:
            self.label_freshness.setText(f"衰老 {pct}%（封存定格）")
        else:
            self.label_freshness.setText(f"衰老 {pct}%")

    def set_dark_mode(self, enabled: bool):
        self._dark_mode = enabled
        self._apply_colors()

    def set_fullscreen(self, fullscreen: bool):
        self._fullscreen = fullscreen
        if fullscreen:
            self.setFixedHeight(20)
        else:
            self.setFixedHeight(36)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        parent = self.window()
        if not parent:
            return
        w, h = parent.width(), parent.height()
        # 窗口过矮时隐藏全部文字标签；续命标签较宽，还需窗口够宽才显示
        self.label_chars.setVisible(h >= 600)
        self.label_comments.setVisible(h >= 600)
        self.label_revives.setVisible(h >= 600 and w >= 700)

    def _apply_colors(self):
        if self._dark_mode:
            text_color = "#9C9288"
            counter_color = COMMENT_COUNTER_COLOR_DARK
        else:
            text_color = "#999589"
            counter_color = COMMENT_COUNTER_COLOR
        style = f"""
            QLabel {{
                color: {text_color};
                font-family: "{SYSTEM_FONT}";
                background: transparent;
                font-size: 9px;
            }}
        """
        for lbl in [self.label_chars, self.label_revives, self.label_freshness]:
            lbl.setStyleSheet(style)
        counter_style = f"""
            QLabel {{
                color: {counter_color};
                font-family: "{SYSTEM_FONT}";
                background: transparent;
                font-size: 9px;
            }}
        """
        self.label_comments.setStyleSheet(counter_style)

    def paintEvent(self, event):
        painter = QPainter(self)
        if self._dark_mode:
            c = QColor(45, 42, 38)
        else:
            c = QColor("#ECE8DC")
        painter.fillRect(self.rect(), c)
        if self._dark_mode:
            line = QColor(220, 214, 200)
            line.setAlphaF(0.12)
        else:
            line = QColor(160, 145, 128)
            line.setAlphaF(0.22)
        painter.setPen(QPen(line, 1))
        painter.drawLine(0, 0, self.rect().width(), 0)
        w, h = self.width(), self.height()
        bc = QColor(*(WINDOW_BORDER_DARK if self._dark_mode else WINDOW_BORDER_LIGHT))
        bc.setAlphaF(0.15)
        painter.setPen(QPen(bc, 1))
        painter.drawLine(0, h - 1, w - 1, h - 1)
        painter.drawLine(0, 0, 0, h - 1)
        painter.drawLine(w - 1, 0, w - 1, h - 1)
        painter.end()
