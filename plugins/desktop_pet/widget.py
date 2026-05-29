# -*- coding: utf-8 -*-
"""
桌宠窗口控件
附着在Overlay悬浮窗旁边，显示静态图片+状态气泡
"""

import os
from typing import Optional, Dict

from PyQt5.QtWidgets import QWidget, QLabel, QGraphicsOpacityEffect
from PyQt5.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QPixmap, QPainter, QFont


class PetBubble(QWidget):
    """状态气泡"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Tool | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(200, 60)
        
        # 气泡文字
        self._label = QLabel("", self)
        self._label.setFont(QFont('Microsoft YaHei UI', 9))
        self._label.setStyleSheet("color: white; background: rgba(26, 26, 46, 200); padding: 8px; border-radius: 10px;")
        self._label.setWordWrap(True)
        self._label.setAlignment(Qt.AlignCenter)
        self._label.setGeometry(0, 0, 200, 60)
        
        # 淡入淡出动画
        self._opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self._opacity_effect)
        self._opacity_effect.setOpacity(0.0)
        
        self._fade_anim = QPropertyAnimation(self._opacity_effect, b"opacity")
        self._fade_anim.setDuration(300)
        self._fade_anim.setEasingCurve(QEasingCurve.InOutQuad)
        
        # 自动隐藏定时器
        self._hide_timer = QTimer()
        self._hide_timer.setSingleShot(True)
        self._hide_timer.timeout.connect(self.fade_out)
    
    def show_message(self, text: str, duration: int = 3000):
        """显示气泡消息"""
        self._label.setText(text)
        self._hide_timer.stop()
        
        # 淡入
        self._fade_anim.stop()
        self._fade_anim.setStartValue(self._opacity_effect.opacity())
        self._fade_anim.setEndValue(1.0)
        self._fade_anim.start()
        
        self.show()
        
        # 设置自动隐藏
        if duration > 0:
            self._hide_timer.start(duration)
    
    def fade_out(self):
        """淡出"""
        self._fade_anim.stop()
        self._fade_anim.setStartValue(self._opacity_effect.opacity())
        self._fade_anim.setEndValue(0.0)
        try:
            self._fade_anim.finished.disconnect(self.hide)
        except TypeError:
            pass  # 未连接时 disconnect 会抛 TypeError
        self._fade_anim.finished.connect(self.hide)
        self._fade_anim.start()


class DesktopPetWidget(QWidget):
    """
    桌宠控件
    
    附着在Overlay旁边，显示静态图片和状态气泡
    """
    
    # 分类到状态的映射（中文）
    CATEGORY_TO_STATE = {
        "办公": "坐着",
        "开发": "坐着",
        "学习": "坐着",
        "游戏": "兴奋",
        "娱乐": "兴奋",
        "社交": "兴奋",
        "摸鱼": "打瞌睡",
        "空闲": "打瞌睡",
        "其他": "待机",
    }
    
    # 状态对应的图片文件名
    STATE_TO_IMAGE = {
        "坐着": "sit.png",
        "兴奋": "walk.png",
        "打瞌睡": "sleep.png",
        "待机": "idle.png",
        "拖拽": "drag.png",
    }
    
    def __init__(self, assets_dir: str, parent=None):
        super().__init__(parent)
        self._assets_dir = assets_dir
        self._current_state = "待机"
        self._current_pixmap: Optional[QPixmap] = None
        
        # 图片缓存
        self._image_cache: Dict[str, QPixmap] = {}
        
        # 窗口设置 - 无边框、置顶、透明背景
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowTitle("WindowStatus - 桌宠")
        self.setFixedSize(256, 256)
        
        # 气泡
        self._bubble = PetBubble()
        
        # 加载所有状态的图片
        self._images = {}
        self._load_images()
        
        # 默认显示待机
        self._set_state("待机")
    
    def _load_images(self):
        """加载所有状态的静态图片（带缓存）"""
        for state_name, filename in self.STATE_TO_IMAGE.items():
            filepath = os.path.join(self._assets_dir, filename)
            if os.path.exists(filepath):
                # 检查缓存
                if filepath in self._image_cache:
                    self._images[state_name] = self._image_cache[filepath]
                else:
                    pixmap = QPixmap(filepath)
                    if not pixmap.isNull():
                        self._images[state_name] = pixmap
                        self._image_cache[filepath] = pixmap
    
    def _set_state(self, state: str):
        """设置状态并更新图片"""
        self._current_state = state
        pixmap = self._images.get(state)
        if pixmap:
            self._current_pixmap = pixmap
            self.setFixedSize(pixmap.size())
            self.update()
    
    def update_category(self, category: str, icon: str, title: str):
        """根据分类更新桌宠状态"""
        # 映射分类到状态
        state = self.CATEGORY_TO_STATE.get(category, "待机")
        self._set_state(state)
        
        # 不再每次切换窗口都显示气泡
        # 气泡只在特定情况下显示（比如鼠标悬停）
        # self._bubble.show_message(f"{icon} {category}\n{title[:15]}...", 5000)
    
    def paintEvent(self, event):
        """绘制桌宠"""
        if self._current_pixmap:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.SmoothPixmapTransform)
            painter.drawPixmap(0, 0, self._current_pixmap)
    
    def showEvent(self, event):
        """显示时同步气泡"""
        super().showEvent(event)
        self._bubble.show()
    
    def hideEvent(self, event):
        """隐藏时同步气泡"""
        super().hideEvent(event)
        self._bubble.hide()
    
    def moveEvent(self, event):
        """移动时同步气泡位置"""
        super().moveEvent(event)
        if self._bubble.isVisible():
            bubble_x = self.x() + (self.width() - self._bubble.width()) // 2
            bubble_y = self.y() - self._bubble.height() - 5
            self._bubble.move(bubble_x, bubble_y)
