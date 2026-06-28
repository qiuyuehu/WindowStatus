# -*- coding: utf-8 -*-
"""
通用样式模块 - 统一弹窗配色和组件样式

oklch 配色系统 + 通用组件工厂，供 stats/settings/about 三个弹窗共用。
"""

import colorsys
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QLabel, QPushButton, QFrame


# ============================================================
# oklch 配色系统
# ============================================================

def oklch_to_qcolor(l, c, h):
    """将 oklch 颜色转换为 QColor（简化版，使用 HSL 近似）"""
    h_norm = h / 360.0
    s = min(1.0, c * 2)
    l_norm = l
    r, g, b = colorsys.hls_to_rgb(h_norm, l_norm, s)
    return QColor(int(r * 255), int(g * 255), int(b * 255))


# 主色调（琥珀）
COLOR_PRIMARY = oklch_to_qcolor(0.75, 0.15, 70)  # 琥珀强调
COLOR_PRIMARY_HOVER = oklch_to_qcolor(0.65, 0.15, 70)
COLOR_PRIMARY_PRESSED = oklch_to_qcolor(0.55, 0.15, 70)

# 中性色
COLOR_BG_PRIMARY = QColor(18, 18, 18)  # #121212 深色底
COLOR_BG_SECONDARY = QColor(26, 26, 26)  # #1a1a1a 卡片背景
COLOR_BG_TERTIARY = QColor(36, 36, 36)  # #242424 悬停背景

COLOR_TEXT_PRIMARY = QColor(232, 232, 232)  # #e8e8e8 主文字
COLOR_TEXT_SECONDARY = QColor(153, 153, 153)  # #999 次要文字
COLOR_TEXT_MUTED = QColor(102, 102, 102)  # #666 弱化文字

COLOR_BORDER = QColor(42, 42, 42)  # #2a2a2a 边框
COLOR_BORDER_SUBTLE = QColor(30, 30, 30)  # #1e1e1e 细边框

# 状态色
COLOR_SUCCESS = oklch_to_qcolor(0.7, 0.15, 145)  # 绿色
COLOR_WARNING = oklch_to_qcolor(0.75, 0.15, 70)  # 黄色
COLOR_ERROR = oklch_to_qcolor(0.6, 0.2, 25)  # 红色

# ============================================================
# 字体规范
# ============================================================

FONT_FAMILY = "Microsoft YaHei, PingFang SC, sans-serif"

FONT_SIZE_TITLE = 16
FONT_SIZE_SUBTITLE = 14
FONT_SIZE_BODY = 13
FONT_SIZE_CAPTION = 11

FONT_WEIGHT_NORMAL = "normal"
FONT_WEIGHT_BOLD = "bold"

# ============================================================
# 间距规范
# ============================================================

SPACING_XS = 4
SPACING_SM = 8
SPACING_MD = 16
SPACING_LG = 24
SPACING_XL = 32

# ============================================================
# 圆角规范
# ============================================================

RADIUS_SM = 4
RADIUS_MD = 8
RADIUS_LG = 12
RADIUS_XL = 16

# ============================================================
# 通用样式表
# ============================================================

DIALOG_BASE_STYLE = f"""
QDialog {{
    background-color: {COLOR_BG_PRIMARY.name()};
    color: {COLOR_TEXT_PRIMARY.name()};
    font-family: {FONT_FAMILY};
    font-size: {FONT_SIZE_BODY}px;
}}
"""

BUTTON_PRIMARY_STYLE = f"""
QPushButton#primary {{
    background-color: {COLOR_PRIMARY.name()};
    color: white;
    border: none;
    padding: {SPACING_SM}px {SPACING_MD}px;
    border-radius: {RADIUS_SM}px;
    font-size: {FONT_SIZE_BODY}px;
    min-width: 80px;
}}
QPushButton#primary:hover {{
    background-color: {COLOR_PRIMARY_HOVER.name()};
}}
QPushButton#primary:pressed {{
    background-color: {COLOR_PRIMARY_PRESSED.name()};
}}
"""

BUTTON_SECONDARY_STYLE = f"""
QPushButton {{
    background-color: {COLOR_BG_SECONDARY.name()};
    color: {COLOR_TEXT_PRIMARY.name()};
    border: 1px solid {COLOR_BORDER.name()};
    padding: {SPACING_SM}px {SPACING_MD}px;
    border-radius: {RADIUS_SM}px;
    font-size: {FONT_SIZE_BODY}px;
    min-width: 80px;
}}
QPushButton:hover {{
    background-color: {COLOR_BG_TERTIARY.name()};
}}
"""

CARD_STYLE = f"""
QWidget#card {{
    background-color: {COLOR_BG_SECONDARY.name()};
    border: 1px solid {COLOR_BORDER.name()};
    border-radius: {RADIUS_LG}px;
}}
"""

# ============================================================
# 通用组件
# ============================================================

def create_title_label(text):
    """创建标题标签"""
    label = QLabel(text)
    label.setStyleSheet(f"""
        font-size: {FONT_SIZE_TITLE}px;
        font-weight: {FONT_WEIGHT_BOLD};
        color: {COLOR_TEXT_PRIMARY.name()};
    """)
    return label


def create_body_label(text):
    """创建正文标签"""
    label = QLabel(text)
    label.setStyleSheet(f"""
        font-size: {FONT_SIZE_BODY}px;
        color: {COLOR_TEXT_PRIMARY.name()};
    """)
    return label


def create_caption_label(text):
    """创建说明标签"""
    label = QLabel(text)
    label.setStyleSheet(f"""
        font-size: {FONT_SIZE_CAPTION}px;
        color: {COLOR_TEXT_SECONDARY.name()};
    """)
    return label


def create_primary_button(text):
    """创建主按钮"""
    btn = QPushButton(text)
    btn.setObjectName("primary")
    btn.setStyleSheet(BUTTON_PRIMARY_STYLE)
    return btn


def create_secondary_button(text):
    """创建次按钮"""
    btn = QPushButton(text)
    btn.setStyleSheet(BUTTON_SECONDARY_STYLE)
    return btn


def create_separator():
    """创建分隔线"""
    line = QFrame()
    line.setFrameShape(QFrame.HLine)
    line.setFrameShadow(QFrame.Sunken)
    line.setStyleSheet(f"background-color: {COLOR_BORDER.name()};")
    return line
