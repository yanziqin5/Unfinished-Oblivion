"""
手写字体管理弹窗 —— 圆角、磨砂风格。
列出已导入的手写字体，右键任意字体可删除或应用到当前批注。
"""
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QFont
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QMenu, QAbstractItemView,
)

from utils.constants import (
    SERIF_FONT, TEXT_COLOR, HINT_TEXT_COLOR, SYSTEM_FONT,
    BUTTON_BG, BUTTON_HOVER_BG,
)
from utils.db import db
from widgets.round_helper import paint_rounded_bg, RoundedMenu


class FontManagerDialog(QDialog):
    """已导入手写字体的管理（右键删除 / 应用）。"""

    def __init__(self, canvas, toast_fn=None, parent=None):
        super().__init__(parent)
        self._canvas = canvas
        self._toast = toast_fn
        self.setWindowTitle("手写字体")
        self.setFixedSize(360, 320)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(12)

        title = QLabel("手写字体")
        title.setFont(QFont(SERIF_FONT, 13))
        title.setStyleSheet(f"color: {TEXT_COLOR};")
        layout.addWidget(title)

        hint = QLabel("右键某个字体可删除，或应用到当前批注")
        hint.setFont(QFont(SYSTEM_FONT, 10))
        hint.setStyleSheet(f"color: {HINT_TEXT_COLOR};")
        layout.addWidget(hint)

        self._list = QListWidget()
        self._list.setStyleSheet(f"""
            QListWidget {{
                background: rgba(255,255,255,0.35);
                border: 1px solid rgba(196,186,168,0.6);
                border-radius: 8px;
                color: {TEXT_COLOR};
                font-family: "{SYSTEM_FONT}";
                font-size: 12px;
                padding: 4px;
            }}
            QListWidget::item {{
                padding: 8px 10px;
                border-radius: 12px;
            }}
            QListWidget::item:selected {{
                background: rgba(196,186,168,0.45);
            }}
        """)
        self._list.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self._list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._list.customContextMenuRequested.connect(self._on_context_menu)
        self._list.itemDoubleClicked.connect(self._apply)
        layout.addWidget(self._list, 1)

        self._empty = QLabel("还没有导入的手写字体")
        self._empty.setFont(QFont(SYSTEM_FONT, 11))
        self._empty.setStyleSheet(f"color: {HINT_TEXT_COLOR};")
        self._empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._empty)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_close = QPushButton("关闭")
        btn_close.setStyleSheet(
            "QPushButton{"
            f"background:{BUTTON_BG};color:{TEXT_COLOR};border:none;"
            f"border-radius:6px;padding:6px 18px;font-family:'{SYSTEM_FONT}';font-size:11px;"
            "}"
            f"QPushButton:hover{{background:{BUTTON_HOVER_BG};}}"
        )
        btn_close.clicked.connect(self.accept)
        btn_row.addWidget(btn_close)
        layout.addLayout(btn_row)

        self._refresh()

    def _refresh(self):
        self._list.clear()
        fonts = db.get_imported_fonts()
        for item in fonts:
            path = item.get("path", "")
            family = item.get("family", "")
            if not family:
                continue
            name = family if not path else f"{family}  ·  {path.split('/')[-1].split(chr(92))[-1]}"
            row = QListWidgetItem(name)
            row.setData(Qt.ItemDataRole.UserRole, {"path": path, "family": family})
            row.setFont(QFont(family if family else SERIF_FONT, 12))
            self._list.addItem(row)
        self._empty.setVisible(len(fonts) == 0)
        self._list.setVisible(len(fonts) > 0)

    def _on_context_menu(self, pos):
        item = self._list.itemAt(pos)
        if not item:
            return
        menu = RoundedMenu(self, getattr(self._canvas, "_dark_mode", False))
        act_apply = menu.addAction("应用到正文")
        act_delete = menu.addAction("删除")
        action = menu.exec_(self._list.mapToGlobal(pos))
        if action is None:
            return
        if action is act_apply:
            self._apply(item)
        elif action is act_delete:
            self._delete(item)

    def _apply(self, item):
        data = item.data(Qt.ItemDataRole.UserRole)
        family = data.get("family", "")
        if family and self._canvas:
            # 切换"正文"手写体到所选字体（文案与批注固定使用品牌字体，不受影响）
            self._canvas.set_body_handwriting(family)
        if self._toast:
            self._toast(f"已应用手写字体：{family}（正文已切换，文案与批注保持原字体）")

    def _delete(self, item):
        data = item.data(Qt.ItemDataRole.UserRole)
        path = data.get("path", "")
        family = data.get("family", "")
        if path:
            db.remove_imported_font(path)
        if family and self._canvas:
            self._canvas.unregister_imported_font(family)
        self._refresh()
        if self._toast:
            self._toast(f"已移除手写字体：{family}")

    def paintEvent(self, event):
        paint_rounded_bg(self, QColor("#ECE6D8"), 12, border=QColor(196, 186, 168, 110))

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.accept()
        else:
            super().keyPressEvent(event)
