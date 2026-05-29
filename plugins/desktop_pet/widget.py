# -*- coding: utf-8 -*-
"""
桌宠窗口控件
附着在Overlay悬浮窗旁边，显示静态图片+状态气泡
"""

import os
from typing import Optional, Dict
from datetime import datetime

from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPixmap, QPainter, QFont, QColor, QPainterPath, QRectF


class StatusBubble(QWidget):
    """
    状态气泡 - 替代原悬浮窗
    
    固定在桌宠头顶，显示图标+标题+进程名+时长+分类
    """
    
    # 气泡尺寸
    BUBBLE_WIDTH = 260
    BUBBLE_HEIGHT = 70
    ARROW_SIZE = 10  # 尾巴大小
    PADDING = 10
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        # 箭头在下方，所以高度要加上箭头
        self.setFixedSize(self.BUBBLE_WIDTH, self.BUBBLE_HEIGHT + self.ARROW_SIZE)
        
        # 当前数据
        self._icon = ""
        self._title = "等待窗口切换..."
        self._process_name = ""
        self._duration = "00:00"
        self._category = "其他"
        
        # 时长更新
        self._start_time: Optional[datetime] = None
        self._duration_timer = QTimer()
        self._duration_timer.timeout.connect(self._update_duration_display)
        self._duration_timer.start(1000)
        
        # 透明度（跟随全局设置）
        self._opacity = 0.85
    
    def update_data(self, icon: str, title: str, process_name: str, category: str = ""):
        """更新气泡数据"""
        self._icon = icon
        self._title = title
        self._process_name = process_name
        if category:
            self._category = category
        # 重置时长，开始重新计时
        self._start_time = datetime.now()
        self._duration = "00:00"
        self.update()  # 触发重绘
    
    def _update_duration_display(self):
        """更新时长显示"""
        if self._start_time:
            duration = int((datetime.now() - self._start_time).total_seconds())
            minutes = duration // 60
            seconds = duration % 60
            self._duration = f"{minutes:02d}:{seconds:02d}"
            self.update()
    
    def set_opacity(self, opacity: float):
        """设置透明度"""
        self._opacity = opacity
        self.setWindowOpacity(opacity)
    
    def paintEvent(self, event):
        """绘制气泡"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 气泡区域（上方，留出下方尾巴空间）
        bubble_rect = QRectF(0, 0, self.BUBBLE_WIDTH, self.BUBBLE_HEIGHT)
        
        # 绘制圆角矩形背景（非常圆润）
        path = QPainterPath()
        path.addRoundedRect(bubble_rect, 20, 20)
        
        # 绘制尾巴（指向下方，偏右）
        arrow_center_x = self.BUBBLE_WIDTH * 0.7  # 偏右
        arrow_y = self.BUBBLE_HEIGHT
        
        # 在圆角矩形底部切一个口子，让尾巴看起来是从气泡里延伸出来的
        cover_rect = QRectF(arrow_center_x - self.ARROW_SIZE - 2, arrow_y - 3, 
                           self.ARROW_SIZE * 2 + 4, 3)
        path.addRect(cover_rect)
        
        # 填充背景（深色半透明）
        painter.fillPath(path, QColor(26, 26, 46, 200))
        
        # 画独立的三角形尾巴
        tail_path = QPainterPath()
        tail_path.moveTo(arrow_center_x - self.ARROW_SIZE, arrow_y - 1)
        tail_path.lineTo(arrow_center_x, arrow_y + self.ARROW_SIZE)
        tail_path.lineTo(arrow_center_x + self.ARROW_SIZE, arrow_y - 1)
        tail_path.closeSubpath()
        painter.fillPath(tail_path, QColor(26, 26, 46, 200))
        
        # 绘制内容
        content_x = self.PADDING
        painter.setPen(Qt.white)
        
        # 图标（第一行左侧）
        icon_rect = QRectF(content_x, self.PADDING, 30, 20)
        painter.setFont(QFont('Segoe UI Emoji', 14))
        painter.drawText(icon_rect, Qt.AlignCenter, self._icon)
        
        # 标题（第一行右侧）
        title_rect = QRectF(content_x + 35, self.PADDING, self.BUBBLE_WIDTH - 35 - self.PADDING * 2, 20)
        painter.setFont(QFont('Microsoft YaHei UI', 10, QFont.Bold))
        # 截断过长标题
        title = self._title
        metrics = painter.fontMetrics()
        title = metrics.elidedText(title, Qt.ElideRight, int(title_rect.width()))
        painter.drawText(title_rect, Qt.AlignLeft | Qt.AlignVCenter, title)
        
        # 进程名（第二行左侧）
        process_rect = QRectF(content_x, self.PADDING + 25, self.BUBBLE_WIDTH - self.PADDING * 2, 18)
        painter.setFont(QFont('Microsoft YaHei UI', 8))
        painter.setPen(QColor(184, 184, 184))
        # 只显示最终子目录
        process_display = self._process_name.split('\\')[-1] if '\\' in self._process_name else self._process_name
        painter.drawText(process_rect, Qt.AlignLeft | Qt.AlignVCenter, process_display)
        
        # 时长（第二行右侧）
        duration_rect = QRectF(content_x + self.BUBBLE_WIDTH - 80 - self.PADDING, self.PADDING + 25, 80, 18)
        painter.setFont(QFont('Microsoft YaHei UI', 8))
        painter.setPen(QColor(78, 205, 196))  # 青色
        painter.drawText(duration_rect, Qt.AlignRight | Qt.AlignVCenter, self._duration)
        
        # 分类标签（第三行）
        category_rect = QRectF(content_x, self.PADDING + 48, self.BUBBLE_WIDTH - self.PADDING * 2, 18)
        painter.setFont(QFont('Microsoft YaHei UI', 8))
        painter.setPen(QColor(128, 128, 128))  # 灰色
        painter.drawText(category_rect, Qt.AlignLeft | Qt.AlignVCenter, self._category)


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
        
        # 状态气泡
        self._status_bubble = StatusBubble()
        
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
    
    def update_bubble(self, icon: str, title: str, process_name: str, category: str = ""):
        """更新气泡数据"""
        if self._status_bubble:
            self._status_bubble.update_data(icon, title, process_name, category)
    
    def paintEvent(self, event):
        """绘制桌宠"""
        if self._current_pixmap:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.SmoothPixmapTransform)
            painter.drawPixmap(0, 0, self._current_pixmap)
    
    def showEvent(self, event):
        """显示时同步气泡"""
        super().showEvent(event)
        if self._status_bubble:
            self._status_bubble.show()
    
    def hideEvent(self, event):
        """隐藏时同步气泡"""
        super().hideEvent(event)
        if self._status_bubble:
            self._status_bubble.hide()
    
    def moveEvent(self, event):
        """移动时同步气泡位置"""
        super().moveEvent(event)
        if self._status_bubble and self._status_bubble.isVisible():
            # 气泡在桌宠头顶上方，间距1像素
            bubble_x = self.x() + (self.width() - self._status_bubble.width()) // 2
            bubble_y = self.y() - self._status_bubble.height() - 1
            self._status_bubble.move(bubble_x, bubble_y)
