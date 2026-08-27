"""共享：真·圆角（无直角）的轻量对话框，替代系统直角 QMessageBox / QInputDialog。

所有实例均使用 paint_rounded_bg（frameless + 透明背景），四角透明圆角，
与软件整体的文艺风格一致，也支持深色模式。
"""
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor

from utils.constants import (
    TEXT_COLOR, HINT_TEXT_COLOR, BUTTON_BG, BUTTON_HOVER_BG,
    DARK_TEXT, DARK_HINT, DARK_BG, SERIF_FONT, SYSTEM_FONT,
    DARK_BUTTON_BG, DARK_BUTTON_HOVER, DARK_BUTTON_TEXT,
)
from widgets.round_helper import paint_rounded_bg


class _RoundedBase(QDialog):
    """圆角无直角对话框基类。"""

    def __init__(self, parent=None, dark: bool = False):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self._dark = bool(dark)
        self.setMinimumWidth(340)

    # ---- 配色（随深色模式） ----
    def _bg(self) -> QColor:
        return QColor(DARK_BG if self._dark else "#ECE6D8")

    def _fg(self) -> str:
        return DARK_TEXT if self._dark else "#4A453B"

    def _sub(self) -> str:
        return DARK_HINT if self._dark else "#8C8478"

    def _field_bg(self) -> str:
        return "rgba(236,230,216,0.7)" if not self._dark else "rgba(255,255,255,0.06)"

    def paintEvent(self, event):
        paint_rounded_bg(self, self._bg(), 14, border=QColor(196, 186, 168, 110))

    def _make_btn(self, text: str) -> QPushButton:
        b = QPushButton(text)
        if self._dark:
            bg, bg_hover, fg = DARK_BUTTON_BG, DARK_BUTTON_HOVER, DARK_BUTTON_TEXT
        else:
            bg, bg_hover, fg = BUTTON_BG, BUTTON_HOVER_BG, BUTTON_TEXT
        b.setStyleSheet(
            f"QPushButton{{background:{bg};color:{fg};border:none;"
            f"border-radius:12px;padding:7px 20px;font-family:'{SYSTEM_FONT}';"
            f"font-size:12px;}}"
            f"QPushButton:hover{{background:{bg_hover};}}"
        )
        return b


def _read_dark(parent) -> bool:
    return bool(getattr(parent, "_dark_mode", False))


def confirm_dialog(parent, title: str, text: str,
                   ok_text: str = "确定", cancel_text: str = "取消") -> bool:
    """圆角确认框。返回 True 表示确认（确定）。"""
    d = _RoundedBase(parent, _read_dark(parent))
    lay = QVBoxLayout(d)
    lay.setContentsMargins(26, 24, 26, 22)
    lay.setSpacing(14)
    if title:
        t = QLabel(title)
        t.setStyleSheet(f"color:{d._fg()};font-family:'{SERIF_FONT}';font-size:14px;")
        lay.addWidget(t)
    m = QLabel(text)
    m.setWordWrap(True)
    m.setStyleSheet(f"color:{d._sub()};font-family:'{SYSTEM_FONT}';font-size:12px;")
    lay.addWidget(m)
    row = QHBoxLayout()
    row.addStretch()
    cb = d._make_btn(cancel_text)
    ob = d._make_btn(ok_text)
    cb.clicked.connect(d.reject)
    ob.clicked.connect(d.accept)
    row.addWidget(cb)
    row.addWidget(ob)
    lay.addLayout(row)
    return d.exec_() == QDialog.Accepted


def info_dialog(parent, title: str, text: str, ok_text: str = "好的") -> None:
    """圆角信息框（单按钮）。"""
    d = _RoundedBase(parent, _read_dark(parent))
    lay = QVBoxLayout(d)
    lay.setContentsMargins(26, 24, 26, 22)
    lay.setSpacing(14)
    if title:
        t = QLabel(title)
        t.setStyleSheet(f"color:{d._fg()};font-family:'{SERIF_FONT}';font-size:14px;")
        lay.addWidget(t)
    m = QLabel(text)
    m.setWordWrap(True)
    m.setStyleSheet(f"color:{d._sub()};font-family:'{SYSTEM_FONT}';font-size:12px;")
    lay.addWidget(m)
    row = QHBoxLayout()
    row.addStretch()
    ob = d._make_btn(ok_text)
    ob.clicked.connect(d.accept)
    row.addWidget(ob)
    lay.addLayout(row)
    d.exec_()


def input_dialog(parent, title: str, label: str, default: str = "") -> "str | None":
    """圆角文本输入。取消返回 None，确定返回 strip 后的文本。"""
    d = _RoundedBase(parent, _read_dark(parent))
    lay = QVBoxLayout(d)
    lay.setContentsMargins(26, 24, 26, 22)
    lay.setSpacing(14)
    if title:
        t = QLabel(title)
        t.setStyleSheet(f"color:{d._fg()};font-family:'{SERIF_FONT}';font-size:14px;")
        lay.addWidget(t)
    if label:
        l = QLabel(label)
        l.setStyleSheet(f"color:{d._sub()};font-family:'{SYSTEM_FONT}';font-size:12px;")
        lay.addWidget(l)
    le = QLineEdit(default)
    le.setStyleSheet(
        f"QLineEdit{{background:{d._field_bg()};color:{d._fg()};"
        f"border:1px solid rgba(196,186,168,0.6);border-radius:12px;"
        f"padding:7px 10px;font-family:'{SYSTEM_FONT}';font-size:12px;}}"
    )
    lay.addWidget(le)
    row = QHBoxLayout()
    row.addStretch()
    cb = d._make_btn("取消")
    ob = d._make_btn("确定")
    cb.clicked.connect(d.reject)
    ob.clicked.connect(d.accept)
    row.addWidget(cb)
    row.addWidget(ob)
    lay.addLayout(row)
    le.selectAll()
    if d.exec_() == QDialog.Accepted:
        return le.text().strip()
    return None
