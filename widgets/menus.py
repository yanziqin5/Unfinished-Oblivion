"""
弹窗组件：快捷键查看、关于。
（导出、API 设置弹窗分别位于 widgets/export_dialog.py、widgets/api_dialog.py）
"""
from PyQt5.QtCore import Qt, QRect
from PyQt5.QtGui import QFont, QPainter, QColor, QPen
from PyQt5.QtWidgets import (
    QDialog, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget,
)

from utils.constants import (
    TEXT_COLOR, HINT_TEXT_COLOR, BODY_FONT_SIZE,
    SHORTCUTS,
)
from utils.db import db
from widgets.round_helper import paint_rounded_bg


class FramelessDialog(QDialog):
    def __init__(self, parent=None, width=480, height=360):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        self.setFixedSize(width, height)
        # 透明背景 + 圆角路径填充，才能去掉四角直角
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

    def paintEvent(self, event):
        paint_rounded_bg(self, QColor("#ECE6D8"), 12, border=QColor(196, 186, 168, 110))


class ShortcutsDialog(FramelessDialog):
    def __init__(self, parent=None):
        super().__init__(parent, 420, 340)
        self.setWindowTitle("快捷键")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 16)

        title = QLabel("快捷键说明")
        title.setStyleSheet(
            f"font-size: 15px; color: {TEXT_COLOR}; font-family: 'Microsoft YaHei'; "
            "font-weight: bold; border: none; background: transparent;"
        )
        layout.addWidget(title)

        for key, desc in SHORTCUTS:
            row = QHBoxLayout()
            k = QLabel(key)
            k.setStyleSheet(
                f"color: {TEXT_COLOR}; font-family: 'Microsoft YaHei'; font-size: 11px; "
                "border: none; background: transparent;"
            )
            k.setFixedWidth(100)
            d = QLabel(desc)
            d.setStyleSheet(
                f"color: {HINT_TEXT_COLOR}; font-family: 'Microsoft YaHei'; font-size: 11px; "
                "border: none; background: transparent;"
            )
            row.addWidget(k)
            row.addWidget(d)
            layout.addLayout(row)

        layout.addStretch()
        ok_btn = QPushButton("知道了")
        ok_btn.setStyleSheet(
            "QPushButton { background: #E4E0D3; color: #5A5548; border-radius: 12px; "
            "padding: 6px 16px; font-family: 'Microsoft YaHei'; font-size: 11px; border: none; }"
            "QPushButton:hover { background: #D9D4C6; } QPushButton:pressed { background: #C9C4B3; }"
        )
        ok_btn.clicked.connect(self.accept)
        layout.addWidget(ok_btn, alignment=Qt.AlignmentFlag.AlignRight)


class AboutDialog(FramelessDialog):
    def __init__(self, parent=None):
        super().__init__(parent, 400, 280)
        self.setWindowTitle("关于")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 16)

        title = QLabel("未完成 · 遗忘")
        title.setStyleSheet(
            f"font-size: 18px; color: {TEXT_COLOR}; font-family: 'Microsoft YaHei'; "
            "font-weight: bold; border: none; background: transparent;"
        )
        layout.addWidget(title)

        info = QLabel("v1.0 · 2026\n文艺治愈向桌面文字笔记\n"
                      "文字随时间自然褪色 · 凝视文字续命 · AI随机生成旧批注")
        info.setStyleSheet(
            f"font-size: 11px; color: {HINT_TEXT_COLOR}; font-family: 'Microsoft YaHei'; "
            "border: none; background: transparent; line-height: 1.6;"
        )
        info.setWordWrap(True)
        layout.addWidget(info)

        layout.addStretch()
        ok_btn = QPushButton("关闭")
        ok_btn.setStyleSheet(
            "QPushButton { background: #E4E0D3; color: #5A5548; border-radius: 12px; "
            "padding: 6px 16px; font-family: 'Microsoft YaHei'; font-size: 11px; border: none; }"
            "QPushButton:hover { background: #D9D4C6; } QPushButton:pressed { background: #C9C4B3; }"
        )
        ok_btn.clicked.connect(self.accept)
        layout.addWidget(ok_btn, alignment=Qt.AlignmentFlag.AlignRight)
