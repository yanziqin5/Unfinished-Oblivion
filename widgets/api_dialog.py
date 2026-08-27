"""
API 密钥 / 模型设置弹窗 —— 磨砂羽化风格。
支持更换 AI 模型（豆包 / DeepSeek / OpenAI 等 OpenAI 兼容端点）。
"""
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPainter, QColor, QFont
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QComboBox,
)

from widgets.round_helper import paint_rounded_bg

from utils.constants import (
    SYSTEM_FONT, SERIF_FONT,
    API_DIALOG_TITLE, API_DIALOG_HINT, API_PLACEHOLDER,
)
from utils.db import db
from utils.ai_client import list_model_presets

# 字段与按钮样式模板（底色 / 描边在实例化时按深浅模式填充）
_LINE_STYLE = """
    QLineEdit, QComboBox {{
        background: {bg};
        color: {fg};
        border: 1px solid {border};
        border-radius: 12px;
        padding: 8px;
        font-family: "{font}";
        font-size: 11px;
    }}
    QComboBox::drop-down {{ border: none; width: 18px; }}
    QComboBox QAbstractItemView {{
        background: {list_bg};
        color: {fg};
        border: 1px solid {border};
        selection-background-color: rgba(196,186,168,0.45);
        outline: none;
    }}
"""
_BTN_STYLE = """
    QPushButton {{
        background: {bg};
        color: {fg};
        border: 1px solid {border};
        border-radius: 12px;
        padding: 6px 14px;
        font-family: "{font}";
        font-size: 11px;
    }}
    QPushButton:hover {{
        background: {hover};
    }}
"""


class ApiDialog(QDialog):
    """API 密钥 / 模型设置弹窗。"""

    def __init__(self, parent=None, dark_mode=False):
        super().__init__(parent)
        self.setWindowTitle("")
        self.setFixedSize(400, 380)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self._dark_mode = dark_mode
        self._presets = list_model_presets()
        self._build_ui()

    def _palette(self):
        """按深浅模式返回协调配色；字段底色用不透明实色，杜绝半透明透出底部暗框造成的割裂。"""
        if self._dark_mode:
            return dict(
                text="#E8E6DE", sub="#9A9388", field_bg="#37332E",
                border="rgba(120,112,100,0.55)",
                btn_bg="rgba(120,112,100,0.25)", btn_hover="rgba(120,112,100,0.45)",
                btn_text="#E8E6DE",
                list_bg="#37332E",
                popup_bg="#2C2A27", popup_alpha=0.96,
                frame_border=QColor(120, 112, 100, 140),
            )
        return dict(
            # 浅色 — 暖中棕色按钮，与工具栏浅色按钮同色系
            text="#4A453B", sub="#8C8478", field_bg="#F4EFE5",
            border="rgba(160,148,130,0.50)",
            btn_bg="#8C7B65", btn_hover="#7D6D58",
            btn_text="#F5F0E8",
            list_bg="#ECE6D8",
            popup_bg="#ECE6D8", popup_alpha=0.92,
            frame_border=QColor(180, 166, 148, 105),
        )

    def _build_ui(self):
        p = self._palette()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        title = QLabel(API_DIALOG_TITLE)
        title.setFont(QFont(SERIF_FONT, 13))
        title.setStyleSheet(f"color: {p['text']};")
        layout.addWidget(title)

        hint = QLabel(API_DIALOG_HINT)
        hint.setFont(QFont(SYSTEM_FONT, 10))
        hint.setStyleSheet(f"color: {p['sub']};")
        hint.setWordWrap(True)
        layout.addWidget(hint)

        # ---- 模型选择 ----
        model_label = QLabel("AI 模型")
        model_label.setFont(QFont(SYSTEM_FONT, 10))
        model_label.setStyleSheet(f"color: {p['text']};")
        layout.addWidget(model_label)

        self.combo_model = QComboBox()
        self.combo_model.setStyleSheet(_LINE_STYLE.format(
            bg=p['field_bg'], fg=p['text'], border=p['border'],
            font=SYSTEM_FONT, list_bg=p['list_bg']))
        self.combo_model.setFixedHeight(34)
        for name, _m, _u in self._presets:
            self.combo_model.addItem(name)
        layout.addWidget(self.combo_model)

        # ---- 自定义模型 / 端点（默认隐藏） ----
        self.custom_model = QLineEdit()
        self.custom_model.setPlaceholderText("自定义模型名，如 doubao-pro-128k")
        self.custom_model.setStyleSheet(_LINE_STYLE.format(
            bg=p['field_bg'], fg=p['text'], border=p['border'],
            font=SYSTEM_FONT, list_bg=p['list_bg']))
        self.custom_model.setVisible(False)
        layout.addWidget(self.custom_model)

        self.custom_url = QLineEdit()
        self.custom_url.setPlaceholderText("自定义 Base URL，如 https://.../v1")
        self.custom_url.setStyleSheet(_LINE_STYLE.format(
            bg=p['field_bg'], fg=p['text'], border=p['border'],
            font=SYSTEM_FONT, list_bg=p['list_bg']))
        self.custom_url.setVisible(False)
        layout.addWidget(self.custom_url)

        self.combo_model.currentIndexChanged.connect(self._on_model_changed)

        # ---- API Key ----
        key_label = QLabel("API 密钥")
        key_label.setFont(QFont(SYSTEM_FONT, 10))
        key_label.setStyleSheet(f"color: {p['text']};")
        layout.addWidget(key_label)

        self.edit_key = QLineEdit()
        current = db.get_setting("api_key", "")
        self.edit_key.setText(current)
        self.edit_key.setPlaceholderText(API_PLACEHOLDER)
        self.edit_key.setEchoMode(QLineEdit.EchoMode.Password)
        self.edit_key.setStyleSheet(_LINE_STYLE.format(
            bg=p['field_bg'], fg=p['text'], border=p['border'],
            font=SYSTEM_FONT, list_bg=p['list_bg']))
        layout.addWidget(self.edit_key)

        layout.addStretch()

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        btn_cancel = QPushButton("取消")
        btn_cancel.setStyleSheet(_BTN_STYLE.format(
            bg=p['btn_bg'], fg=p['btn_text'], border=p['border'], font=SYSTEM_FONT, hover=p['btn_hover']))
        btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(btn_cancel)

        btn_clear = QPushButton("忘记密钥")
        btn_clear.setStyleSheet(_BTN_STYLE.format(
            bg=p['btn_bg'], fg=p['btn_text'], border=p['border'], font=SYSTEM_FONT, hover=p['btn_hover']))
        btn_clear.clicked.connect(self._clear_key)
        btn_layout.addWidget(btn_clear)

        btn_save = QPushButton("收好")
        btn_save.setStyleSheet(_BTN_STYLE.format(
            bg=p['btn_hover'], fg=p['btn_text'], border=p['border'], font=SYSTEM_FONT, hover=p['btn_hover']))
        btn_save.clicked.connect(self._save_key)
        btn_layout.addWidget(btn_save)
        layout.addLayout(btn_layout)

        # 初始化下拉与自定义字段的显示
        self._sync_model_ui()

    def _on_model_changed(self, idx):
        is_custom = self._presets[idx][1] == "custom"
        self.custom_model.setVisible(is_custom)
        self.custom_url.setVisible(is_custom)

    def _sync_model_ui(self):
        """根据已保存的设置还原下拉框与自定义字段。"""
        saved_model = db.get_setting("ai_model", "")
        saved_url = db.get_setting("ai_base_url", "")
        # 找到匹配的预设项
        match_idx = -1
        for i, (name, m, u) in enumerate(self._presets):
            if m == saved_model and (not m or u == saved_url):
                match_idx = i
                break
        if match_idx >= 0:
            self.combo_model.setCurrentIndex(match_idx)
        else:
            # 未匹配到预设 → 落入"自定义"
            custom_idx = next(
                (i for i, pr in enumerate(self._presets) if pr[1] == "custom"), 0)
            self.combo_model.setCurrentIndex(custom_idx)
            self.custom_model.setText(saved_model)
            self.custom_url.setText(saved_url)
        self._on_model_changed(self.combo_model.currentIndex())

    def _save_key(self):
        key = self.edit_key.text().strip()
        db.set_setting("api_key", key)

        idx = self.combo_model.currentIndex()
        name, model, url = self._presets[idx]
        if model == "custom":
            model = self.custom_model.text().strip()
            url = self.custom_url.text().strip()
        if model:
            db.set_setting("ai_model", model)
        if url:
            db.set_setting("ai_base_url", url)
        self.accept()

    def _clear_key(self):
        db.set_setting("api_key", "")
        self.edit_key.clear()
        self.accept()

    def paintEvent(self, event):
        p = self._palette()
        bg = QColor(p['popup_bg'])
        bg.setAlpha(int(255 * p['popup_alpha']))
        paint_rounded_bg(self, bg, 12, border=p['frame_border'])
