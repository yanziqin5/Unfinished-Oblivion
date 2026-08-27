"""
导出面板 —— 磨砂羽化弹窗风格。
"""
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPainter, QColor, QFont
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QComboBox, QCheckBox, QGroupBox,
)

from widgets.round_helper import paint_rounded_bg

from utils.constants import (
    SYSTEM_FONT, SERIF_FONT, TEXT_COLOR, HINT_TEXT_COLOR,
    BUTTON_BG, BUTTON_HOVER_BG, BUTTON_TEXT, DIALOG_BG_COLOR, DIALOG_BG_ALPHA,
    EXPORT_DIALOG_TITLE,
    EXPORT_FORMAT_LABEL, EXPORT_DPI_LABEL,
    EXPORT_EPIGRAPH_LABEL,
)

class ExportDialog(QDialog):
    """导出面板（非模态，磨砂底色）。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("")
        self.setFixedSize(340, 290)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.result_data: dict = {}

        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # 标题
        title = QLabel(EXPORT_DIALOG_TITLE)
        title.setFont(QFont(SERIF_FONT, 13))
        title.setStyleSheet(f"color: {TEXT_COLOR};")
        layout.addWidget(title)

        # 格式
        fmt_label = QLabel(EXPORT_FORMAT_LABEL)
        fmt_label.setFont(QFont(SYSTEM_FONT, 10))
        fmt_label.setStyleSheet(f"color: {HINT_TEXT_COLOR};")
        layout.addWidget(fmt_label)

        self.combo_format = QComboBox()
        self.combo_format.addItems(["PNG", "JPG"])
        self.combo_format.setStyleSheet(f"""
            QComboBox {{
                background: {BUTTON_BG};
                color: {BUTTON_TEXT};
                border: none;
                border-radius: 12px;
                padding: 6px;
                font-family: "{SYSTEM_FONT}";
            }}
        """)
        layout.addWidget(self.combo_format)

        # DPI
        dpi_label = QLabel(EXPORT_DPI_LABEL)
        dpi_label.setFont(QFont(SYSTEM_FONT, 10))
        dpi_label.setStyleSheet(f"color: {HINT_TEXT_COLOR};")
        layout.addWidget(dpi_label)

        self.combo_dpi = QComboBox()
        self.combo_dpi.addItems(["300 DPI（清晰）", "1080 DPI（极致）"])
        self.combo_dpi.setStyleSheet(f"""
            QComboBox {{
                background: {BUTTON_BG};
                color: {BUTTON_TEXT};
                border: none;
                border-radius: 12px;
                padding: 6px;
                font-family: "{SYSTEM_FONT}";
            }}
        """)
        layout.addWidget(self.combo_dpi)

        # 带上页眉诗句
        self.chk_epigraph = QCheckBox(EXPORT_EPIGRAPH_LABEL)
        self.chk_epigraph.setChecked(True)
        self.chk_epigraph.setFont(QFont(SYSTEM_FONT, 10))
        self.chk_epigraph.setStyleSheet(f"color: {HINT_TEXT_COLOR};")
        layout.addWidget(self.chk_epigraph)

        # 按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        btn_cancel = QPushButton("改日再存")
        btn_cancel.setStyleSheet(f"""
            QPushButton {{
                background: {BUTTON_BG};
                color: {BUTTON_TEXT};
                border: none;
                border-radius: 12px;
                padding: 6px 16px;
                font-family: "{SYSTEM_FONT}";
                font-size: 11px;
            }}
            QPushButton:hover {{
                background: {BUTTON_HOVER_BG};
            }}
        """)
        btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(btn_cancel)

        btn_export = QPushButton("定格此刻")
        btn_export.setStyleSheet(f"""
            QPushButton {{
                background: {BUTTON_HOVER_BG};
                color: {BUTTON_TEXT};
                border: none;
                border-radius: 12px;
                padding: 6px 16px;
                font-family: "{SYSTEM_FONT}";
                font-size: 11px;
            }}
            QPushButton:hover {{
                background: {BUTTON_BG};
            }}
        """)
        btn_export.clicked.connect(self._on_export)
        btn_layout.addWidget(btn_export)

        layout.addLayout(btn_layout)

    def _on_export(self):
        fmt = "png" if self.combo_format.currentIndex() == 0 else "jpg"
        dpi = 300 if self.combo_dpi.currentIndex() == 0 else 1080
        self.result_data = {
            "format": fmt,
            "dpi": dpi,
            "epigraph": self.chk_epigraph.isChecked(),
        }
        self.accept()

    def paintEvent(self, event):
        bg = QColor(DIALOG_BG_COLOR)
        bg.setAlpha(int(255 * DIALOG_BG_ALPHA))
        paint_rounded_bg(self, bg, 12, border=QColor(196, 186, 168, 110))
