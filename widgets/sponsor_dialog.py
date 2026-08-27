"""
爱发电赞助弹窗 —— 文艺风格，支持深色模式。
在“更多菜单 → 赞助支持”中打开，点击按钮跳转爱发电页面。
"""
from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtGui import QColor, QDesktopServices
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
)

from utils.constants import (
    TEXT_COLOR, HINT_TEXT_COLOR,
    BUTTON_BG, BUTTON_HOVER_BG, BUTTON_TEXT,
    DARK_BG, DARK_TEXT, DARK_HINT,
    DARK_BUTTON_BG, DARK_BUTTON_HOVER, DARK_BUTTON_TEXT,
    SERIF_FONT, SYSTEM_FONT,
)
from widgets.round_helper import paint_rounded_bg

SPONSOR_URL = "https://www.ifdian.net/a/yanziqin5"


class SponsorDialog(QDialog):
    """爱发电赞助弹窗（无边框圆角，随深色模式切换配色）。"""

    def __init__(self, parent=None, dark: bool = False):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self._dark = bool(dark)
        self.setFixedSize(460, 330)

        self._bg = QColor(DARK_BG if self._dark else "#ECE6D8")
        self._fg = DARK_TEXT if self._dark else TEXT_COLOR
        self._sub = DARK_HINT if self._dark else HINT_TEXT_COLOR
        if self._dark:
            self._btn_bg, self._btn_hover, self._btn_fg = DARK_BUTTON_BG, DARK_BUTTON_HOVER, DARK_BUTTON_TEXT
        else:
            self._btn_bg, self._btn_hover, self._btn_fg = BUTTON_BG, BUTTON_HOVER_BG, BUTTON_TEXT

        self._build_ui()

    def paintEvent(self, event):
        paint_rounded_bg(self, self._bg, 14, border=QColor(196, 186, 168, 110))

    def _build_ui(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(32, 28, 32, 24)
        lay.setSpacing(10)

        # 标题
        title = QLabel("赞助 · 未完成 · 遗忘")
        title.setStyleSheet(
            f"font-family:'{SERIF_FONT}'; font-size:17px; font-weight:bold; "
            f"color:{self._fg}; border:none; background:transparent;"
        )
        lay.addWidget(title, alignment=Qt.AlignmentFlag.AlignHCenter)

        # 文艺正文
        body = QLabel(
            "如果这一页纸，曾在深夜里接住过你的心事，\n"
            "如果你愿意，可以请作者喝一杯茶。\n\n"
            "你的每一份支持，都会让更多文字不被遗忘。"
        )
        body.setWordWrap(True)
        body.setStyleSheet(
            f"font-family:'{SYSTEM_FONT}'; font-size:12px; color:{self._sub}; "
            "border:none; background:transparent;"
        )
        lay.addWidget(body)

        # 爱发电地址
        url_label = QLabel(SPONSOR_URL.replace("https://", ""))
        url_label.setStyleSheet(
            f"font-family:'{SYSTEM_FONT}'; font-size:11px; color:{self._btn_bg}; "
            "border:none; background:transparent;"
        )
        lay.addWidget(url_label, alignment=Qt.AlignmentFlag.AlignHCenter)

        lay.addStretch()

        # 按钮行
        row = QHBoxLayout()
        row.addStretch()

        close_btn = QPushButton("暂不需要")
        close_btn.setStyleSheet(self._btn_style())
        close_btn.clicked.connect(self.reject)
        row.addWidget(close_btn)

        sponsor_btn = QPushButton("去爱发电支持")
        sponsor_btn.setStyleSheet(self._btn_style())
        sponsor_btn.clicked.connect(self._open_sponsor)
        row.addWidget(sponsor_btn)

        lay.addLayout(row)

    def _btn_style(self) -> str:
        return (
            f"QPushButton{{background:{self._btn_bg};color:{self._btn_fg};"
            f"border:none;border-radius:12px;padding:7px 18px;"
            f"font-family:'{SYSTEM_FONT}';font-size:12px;}}"
            f"QPushButton:hover{{background:{self._btn_hover};}}"
        )

    def _open_sponsor(self):
        QDesktopServices.openUrl(QUrl(SPONSOR_URL))
        self.accept()
