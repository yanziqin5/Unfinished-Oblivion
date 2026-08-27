"""共享：Frameless 弹窗真圆角背景绘制。

frameless + 透明背景下，若用 fillRect 铺满整个矩形，四角仍是直角（仅半透明）。
必须只填充圆角路径，四角之外的像素保持透明，才能“清理干净四个直角”。
"""
from PyQt5.QtCore import QRectF, Qt
from PyQt5.QtGui import QPainter, QColor, QPen, QPainterPath
from PyQt5.QtWidgets import QMenu


class RoundedMenu(QMenu):
    """真·无直角圆角菜单：frameless + 透明背景 + 自绘圆角底，支持深浅色。

    用于替换所有系统直角 QMenu（右键菜单、下拉菜单等）。
    """

    def __init__(self, parent=None, dark: bool = False):
        super().__init__(parent)
        self._dark = bool(dark)
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        fg = "#D8CEC0" if dark else "#4A453B"
        sel = "rgba(255,255,255,0.12)" if dark else "rgba(196,186,168,0.45)"
        self.setStyleSheet(
            "QMenu{ background: transparent; border: none; padding: 6px; }"
            f"QMenu::item{{ color: {fg}; padding: 6px 18px 6px 14px; border-radius: 6px; }}"
            f"QMenu::item:selected{{ background: {sel}; }}"
            "QMenu::separator{ height: 1px; background: rgba(196,186,168,0.5); margin: 4px 8px; }"
        )

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        bg = "#2E2A24" if self._dark else "#ECE6D8"
        path = QPainterPath()
        path.addRoundedRect(QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5), 10, 10)
        painter.fillPath(path, QColor(bg))
        painter.end()
        super().paintEvent(event)


def paint_rounded_bg(widget, bg, radius: int = 12, border=None, border_alpha: int = 40, shadow: bool = True):
    """在 frameless + 透明背景下绘制真·圆角背景，四角透明。

    Args:
        widget: 目标 QWidget（需已 setAttribute(WA_TranslucentBackground, True)）。
        bg: 背景色，可为 '#RRGGBB' 字符串、rgba 元组 (r,g,b,a) 或 QColor。
        radius: 圆角半径。
        border: 边框色（同 bg 格式），为 None 时不画边框。
        border_alpha: 边框默认透明度（当 border 不含 alpha 时）。
        shadow: 是否绘制极淡模糊阴影（向下偏移的半透明圆角矩形堆叠）。
    """
    # 覆盖全局 QWidget 背景（浅色模式下被硬编码为深棕 #2C2A27，会泄漏到弹窗内
    # 未显式声明背景的子控件，如标题文字，造成“米色弹窗 + 深棕块”割裂）。
    if not getattr(widget, "_rounded_bg_inited", False):
        widget.setStyleSheet(widget.styleSheet() + "\nQWidget { background: transparent; }")
        widget._rounded_bg_inited = True
    painter = QPainter(widget)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    rect = QRectF(widget.rect()).adjusted(0.5, 0.5, -0.5, -0.5)

    # 极淡模糊阴影：数层向下偏移的半透明圆角矩形堆叠，柔化边缘
    if shadow:
        for k in range(4):
            sh = QColor(70, 56, 38, max(4, 20 - k * 5))
            rr = QRectF(rect).adjusted(-k * 1.0, -k * 0.4, k * 1.0, 1.5 + k * 1.4)
            p = QPainterPath()
            p.addRoundedRect(rr, radius, radius)
            painter.fillPath(p, sh)

    path = QPainterPath()
    path.addRoundedRect(rect, radius, radius)

    color = _to_color(bg)
    painter.fillPath(path, color)

    if border is not None:
        bc = _to_color(border, border_alpha)
        painter.setPen(QPen(bc, 1))
        painter.drawPath(path)
    painter.end()


def _to_color(bg, default_alpha: int = 255):
    if isinstance(bg, QColor):
        return bg
    if isinstance(bg, tuple):
        r, g, b = bg[0], bg[1], bg[2]
        a = bg[3] if len(bg) > 3 else default_alpha
        return QColor(r, g, b, a)
    if isinstance(bg, str):
        if bg.startswith("rgba"):
            # rgba(r,g,b,a) —— a 为 0~1
            nums = bg.replace("rgba", "").strip("()").split(",")
            r, g, b = int(nums[0]), int(nums[1]), int(nums[2])
            a = int(float(nums[3]) * 255)
            return QColor(r, g, b, a)
        return QColor(bg)
    return QColor(bg)


