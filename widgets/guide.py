"""
首次启动引导页 —— 全屏遮罩、文艺叙事、点击任意处 900ms 淡出。
仅首次启动展示，DB 标记后不再出现。
"""
from PyQt5.QtCore import (
    Qt, QTimer, QPropertyAnimation, QEasingCurve, QRect,
    pyqtProperty,
)
from PyQt5.QtGui import (
    QPainter, QColor, QFont, QFontMetrics, QPen,
)
from PyQt5.QtWidgets import QWidget, QGraphicsOpacityEffect

from utils.constants import (
    GUIDE_FONT,
    BG_YELLOW_1, TEXT_COLOR, HINT_TEXT_COLOR,
    DURATION_GUIDE_FADE,
    GUIDE_LINES,
)


class GuideOverlay(QWidget):
    """
    全屏引导遮罩。
    - 底色 #F6F3E9，覆盖整个窗口
    - 居中引导文案 13pt，行距 1.8
    - 点击任意位置触发 900ms 淡出
    - 完成后 self.hide()
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        # 将 parent 设置为窗口本身（MainWindow），覆盖整个窗口
        self._opacity_effect = QGraphicsOpacityEffect(self)
        self._opacity_effect.setOpacity(1.0)
        self.setGraphicsEffect(self._opacity_effect)

        self._fading_out: bool = False
        self._dark_mode: bool = False

        # 淡出动画
        self._fade_anim = QPropertyAnimation(self._opacity_effect, b"opacity")
        self._fade_anim.setDuration(DURATION_GUIDE_FADE)
        self._fade_anim.setEasingCurve(QEasingCurve.Type.InOutCubic)
        self._fade_anim.finished.connect(self._on_fade_done)

    def set_dark_mode(self, enabled: bool):
        self._dark_mode = enabled
        self.update()

    def show_overlay(self):
        """显示引导页并覆盖整个父控件。"""
        if self.parent():
            self.setGeometry(self.parent().rect())
        self._fading_out = False
        self._opacity_effect.setOpacity(1.0)
        self.raise_()
        self.show()

    def start_fade_out(self):
        """手动触发淡出（但保留点击触发为主）。"""
        if self._fading_out:
            return
        self._fading_out = True
        self._fade_anim.stop()
        self._fade_anim.setStartValue(self._opacity_effect.opacity())
        self._fade_anim.setEndValue(0.0)
        self._fade_anim.start()

    # ---- Qt 事件 ----

    def resizeEvent(self, event):
        if self.parent():
            self.setGeometry(self.parent().rect())
        super().resizeEvent(event)

    def mousePressEvent(self, event):
        """点击任意位置立即淡出。"""
        if not self._fading_out:
            self.start_fade_out()

    def paintEvent(self, event):
        painter = QPainter(self)
        # 底色
        painter.fillRect(self.rect(), QColor(BG_YELLOW_1))

        # 文案
        w, h = self.width(), self.height()
        lines = GUIDE_LINES.split('\n')

        # 字号上限 12pt，同时按窗口宽、高自适应缩放，避免上下或左右溢出
        base_size = 12
        font = QFont(GUIDE_FONT, base_size)
        font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 1.0)
        fm = QFontMetrics(font)
        line_h0 = int(fm.height() * 1.7)

        bottom_pad = 70  # 底部预留给“轻触任意位置开始”提示的空间
        avail_h = h - bottom_pad
        max_text_w = max(120, int(w * 0.84))
        max_text_h = int(avail_h * 0.92)
        longest_w = max((fm.horizontalAdvance(ln) for ln in lines), default=0)

        # 宽度约束：最长行放入 max_text_w
        scale_w = max_text_w / longest_w if longest_w > 0 else 1.0
        # 高度约束：所有行总高放入 max_text_h
        n_lines = max(1, len(lines))
        scale_h = max_text_h / (n_lines * line_h0)
        scale = min(1.0, scale_w, scale_h)

        size = max(9, int(base_size * scale))
        if size != base_size:
            font.setPointSize(size)
            fm = QFontMetrics(font)
            line_h0 = int(fm.height() * 1.7)
        painter.setFont(font)

        line_h = line_h0
        total_h = n_lines * line_h
        start_y = max(8, (avail_h - total_h) // 2)

        # 文本色值 #3A3832
        text_color = QColor(TEXT_COLOR)
        painter.setPen(text_color)

        for i, line in enumerate(lines):
            if not line.strip():
                continue  # 保留空行作为间距
            lw = fm.horizontalAdvance(line)
            lx = (w - lw) // 2
            ly = start_y + i * line_h
            painter.drawText(lx, ly + fm.ascent(), line)

        # 底部小字提示
        hint_font = QFont(GUIDE_FONT, 10)
        painter.setFont(hint_font)
        hint_color = QColor(HINT_TEXT_COLOR)
        hint_color.setAlpha(160)
        painter.setPen(hint_color)
        hint_text = "—— 轻触任意位置开始 ——"
        hfm = QFontMetrics(hint_font)
        hw = hfm.horizontalAdvance(hint_text)
        painter.drawText((w - hw) // 2, h - 38, hint_text)

        painter.end()

    # ---- 内部 ----

    def _on_fade_done(self):
        self.hide()
        self._fading_out = False
