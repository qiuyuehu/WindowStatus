# -*- coding: utf-8 -*-
"""
插件层公共工具函数和共享组件
"""

from datetime import datetime
from typing import Optional

from PyQt5.QtCore import Qt, QRectF, QPoint
from PyQt5.QtGui import QPainter, QColor, QPen, QFont, QPainterPath
from PyQt5.QtWidgets import QTabBar, QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QWidget


def format_duration(seconds: int) -> str:
    """
    格式化时长为人类可读的字符串

    Args:
        seconds: 秒数

    Returns:
        格式化后的时长字符串，如 "3分钟"、"1小时30分钟"

    Examples:
        >>> format_duration(30)
        '30秒'
        >>> format_duration(90)
        '1分钟'
        >>> format_duration(3661)
        '1小时1分钟'
    """
    if seconds < 60:
        return f"{seconds}秒"
    elif seconds < 3600:
        minutes = seconds // 60
        return f"{minutes}分钟"
    else:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        if minutes > 0:
            return f"{hours}小时{minutes}分钟"
        return f"{hours}小时"


def truncate_text(text: str, max_length: int = 25) -> str:
    """
    截断过长的文本，超出部分用省略号替代

    Args:
        text: 原始文本
        max_length: 最大长度（含省略号）

    Returns:
        截断后的文本

    Examples:
        >>> truncate_text("Hello", 10)
        'Hello'
        >>> truncate_text("Hello World", 8)
        'Hello...'
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - 3] + "..."


def format_timestamp(dt: Optional[datetime | str], fmt: str = "%H:%M") -> str:
    """
    格式化时间戳

    Args:
        dt: datetime 对象，None 时返回空字符串
        fmt: 格式化模板

    Returns:
        格式化后的时间字符串

    Examples:
        >>> from datetime import datetime
        >>> format_timestamp(datetime(2026, 5, 28, 14, 30))
        '14:30'
        >>> format_timestamp(None)
        ''
    """
    if dt is None:
        return ""
    if isinstance(dt, str):
        dt = datetime.fromisoformat(dt)
    return dt.strftime(fmt)


# ── 自绘标签栏（共享组件）──────────────────────────────────────

class CustomTabBar(QTabBar):
    """
    极简风格标签栏：纯文字 + 底部下划线指示器

    与 HTML demo 一致：
    - 无圆角方框、无边框
    - 选中态：银灰文字 + 底部 2px 下划线
    - 未选中：灰色文字
    - 悬停：文字变亮
    - 标签栏底部有一条分隔线

    用法：
        tabs = QTabWidget()
        tabs.setTabBar(CustomTabBar())
    """

    # 配色
    TEXT_NORMAL = QColor("#999")          # 未选中文字
    TEXT_HOVER = QColor("#e8e8e8")       # 悬停文字
    TEXT_SELECTED = QColor("#a0a0a0")    # 选中文字
    INDICATOR = QColor("#a0a0a0")        # 底部下划线
    BAR_BG = QColor("#1a1a1a")           # 标签栏背景
    BAR_BORDER = QColor("#2a2a2a")       # 底部分隔线

    def __init__(self, parent=None):
        super().__init__(parent)
        self._hover_index = -1
        self.setMouseTracking(True)
        self.setDrawBase(False)

    def sizeHint(self):
        hint = super().sizeHint()
        hint.setHeight(40)
        return hint

    def minimumSizeHint(self):
        hint = super().minimumSizeHint()
        hint.setHeight(40)
        return hint

    def mouseMoveEvent(self, event):
        old = self._hover_index
        self._hover_index = self.tabAt(event.pos())
        if old != self._hover_index:
            self.update()

    def leaveEvent(self, event):
        self._hover_index = -1
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        h = self.height()
        w = self.width()

        # ── 标签栏背景 ──
        painter.fillRect(0, 0, w, h, self.BAR_BG)

        # ── 标签栏底部分隔线 ──
        painter.setPen(QPen(self.BAR_BORDER, 1))
        painter.drawLine(0, h - 1, w, h - 1)

        # ── 绘制每个 tab ──
        for i in range(self.count()):
            rect = self.tabRect(i)
            is_selected = (i == self.currentIndex())
            is_hover = (i == self._hover_index)

            # 文字颜色
            if is_selected:
                painter.setPen(self.TEXT_SELECTED)
            elif is_hover:
                painter.setPen(self.TEXT_HOVER)
            else:
                painter.setPen(self.TEXT_NORMAL)

            # 文字
            font = painter.font()
            font.setPointSize(10)
            font.setWeight(QFont.DemiBold if is_selected else QFont.Normal)
            painter.setFont(font)
            painter.drawText(rect, Qt.AlignCenter, self.tabText(i))

            # ── 选中指示器：底部 2px 下划线 ──
            if is_selected:
                pen = QPen(self.INDICATOR, 2)
                pen.setCapStyle(Qt.FlatCap)
                painter.setPen(pen)
                y = h - 2  # 紧贴底部分隔线上方
                x1 = int(rect.left()) + 12
                x2 = int(rect.right()) - 12
                painter.drawLine(x1, y, x2, y)


# ── 无边框圆角弹窗基类 ─────────────────────────────────────────

class FramelessDialog(QDialog):
    """
    无边框圆角弹窗，带自绘标题栏

    与 HTML demo 一致：
    - 圆角 12px + 1px #2a2a2a 边框
    - 标题栏：#1a1a1a 背景 + 底部分隔线
    - 标题文字左侧 + 关闭/帮助按钮右侧
    - 支持标题栏拖拽移动窗口

    用法：
        class MyDialog(FramelessDialog):
            def __init__(self):
                super().__init__(title="我的弹窗")
                # self.content_layout 是标题栏下方的内容布局
    """

    # 配色
    BG_COLOR = QColor("#121212")
    TITLEBAR_BG = QColor("#1a1a1a")
    BORDER_COLOR = QColor("#2a2a2a")
    TITLE_TEXT = QColor("#e8e8e8")
    BTN_NORMAL = QColor("#666")
    BTN_HOVER = QColor("#e8e8e8")
    CORNER_RADIUS = 12
    TITLEBAR_HEIGHT = 40

    def __init__(self, title: str = "", parent=None):
        super().__init__(parent)
        self._title_text = title
        self._drag_pos = None

        # 无边框 + 透明背景（圆角需要）
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)

        # 主布局（包含标题栏 + 内容区）
        self._main_layout = QVBoxLayout(self)
        self._main_layout.setContentsMargins(0, 0, 0, 0)
        self._main_layout.setSpacing(0)

        # 标题栏容器
        self._titlebar = QWidget()
        self._titlebar.setAttribute(Qt.WA_TranslucentBackground)
        self._titlebar.setFixedHeight(self.TITLEBAR_HEIGHT)
        self._titlebar_layout = QHBoxLayout(self._titlebar)
        self._titlebar_layout.setContentsMargins(16, 0, 8, 0)
        self._titlebar_layout.setSpacing(0)

        # 标题文字
        self._title_label = QLabel(title)
        self._title_label.setStyleSheet(
            "font-size: 13px; color: #e8e8e8; background: transparent;")
        self._titlebar_layout.addWidget(self._title_label)
        self._titlebar_layout.addStretch()

        # 帮助按钮（可选，子类决定是否显示）
        self._help_btn = self._create_title_btn("?")
        self._help_btn.clicked.connect(self._on_help)
        self._titlebar_layout.addWidget(self._help_btn)

        # 关闭按钮
        self._close_btn = self._create_title_btn("✕")
        self._close_btn.clicked.connect(self.close)
        self._titlebar_layout.addWidget(self._close_btn)

        self._main_layout.addWidget(self._titlebar)

        # 内容区容器（子类往这里添加内容）
        self._content_widget = QWidget()
        self._content_widget.setAttribute(Qt.WA_TranslucentBackground)
        self._content_widget.setObjectName("contentArea")
        self.content_layout = QVBoxLayout(self._content_widget)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(0)
        self._main_layout.addWidget(self._content_widget, 1)

    def _create_title_btn(self, text: str) -> QPushButton:
        """创建标题栏按钮"""
        btn = QPushButton(text)
        btn.setFixedSize(28, 28)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                color: #666;
                font-size: 14px;
                border-radius: 4px;
            }
            QPushButton:hover {
                color: #e8e8e8;
                background: rgba(255,255,255,0.08);
            }
        """)
        return btn

    def _on_help(self):
        """帮助按钮回调（子类可重写）"""
        pass

    def setWindowTitle(self, title: str):
        """同步更新标题栏文字"""
        self._title_text = title
        self._title_label.setText(title)
        super().setWindowTitle(title)

    def paintEvent(self, event):
        """自绘圆角背景 + 标题栏 + 边框"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        h = self.height()
        r = self.CORNER_RADIUS
        m = 1  # 边框留 1px

        # ── 1. 整体圆角背景（#121212）──
        bg_rect = QRectF(m, m, w - 2 * m, h - 2 * m)
        bg_path = QPainterPath()
        bg_path.addRoundedRect(bg_rect, r, r)
        painter.setPen(Qt.NoPen)
        painter.setBrush(self.BG_COLOR)
        painter.drawPath(bg_path)

        # ── 2. 标题栏背景（#1a1a1a，只有顶部圆角）──
        # 手动构造路径：左上弧 → 右上弧 → 右下直角 → 左下直角
        tb = QRectF(m, m, w - 2 * m, self.TITLEBAR_HEIGHT)
        tb_path = QPainterPath()
        tb_path.moveTo(tb.left() + r, tb.top())
        tb_path.arcTo(tb.left(), tb.top(), 2 * r, 2 * r, 90, 90)
        tb_path.lineTo(tb.left(), tb.bottom())
        tb_path.lineTo(tb.right(), tb.bottom())
        tb_path.arcTo(tb.right() - 2 * r, tb.top(), 2 * r, 2 * r, 0, 90)
        tb_path.closeSubpath()
        painter.setBrush(self.TITLEBAR_BG)
        painter.drawPath(tb_path)

        # ── 3. 标题栏底部分隔线 ──
        painter.setPen(QPen(self.BORDER_COLOR, 1))
        painter.drawLine(m, self.TITLEBAR_HEIGHT + m, w - m, self.TITLEBAR_HEIGHT + m)

        # ── 4. 外边框（圆角描边）──
        painter.setBrush(Qt.NoBrush)
        painter.setPen(QPen(self.BORDER_COLOR, 1))
        painter.drawRoundedRect(bg_rect, r, r)

    # ── 标题栏拖拽 ──

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and event.pos().y() <= self.TITLEBAR_HEIGHT:
            self._drag_pos = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if self._drag_pos and (event.buttons() & Qt.LeftButton):
            self.move(event.globalPos() - self._drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        self._drag_pos = None
