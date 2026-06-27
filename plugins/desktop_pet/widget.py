# -*- coding: utf-8 -*-
"""
桌宠窗口控件
附着在Overlay气泡下方，显示静态图片
"""

import os
from typing import Optional, Dict

from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPixmap, QPainter


class DesktopPetWidget(QWidget):
    """
    桌宠控件
    
    附着在Overlay气泡下方，显示静态图片
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
        
        # 拖拽状态
        self._is_dragging = False
        self._drag_pending = False  # 等待长按确认
        self._drag_offset = None
        self._state_before_drag = "待机"
        
        # 长按检测定时器
        self._long_press_timer = QTimer()
        self._long_press_timer.setSingleShot(True)
        self._long_press_timer.timeout.connect(self._on_long_press)
        self._long_press_pos = None
        
        # 外部回调：拖拽移动时通知（用于同步气泡位置）
        self._on_drag_move_callback = None
        self._on_drag_end_callback = None
        
        # 窗口设置 - 无边框、置顶、透明背景（不加 Qt.Tool，Win11 鼠标事件会失效）
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowTitle("WindowStatus - 桌宠")
        self.setFixedSize(256, 256)

        # TOPMOST 维护定时器（每 1 秒用 Win32 SetWindowPos 强制刷新置顶状态）
        self._always_on_top = True  # 跟踪置顶状态
        self._topmost_timer = QTimer()
        self._topmost_timer.timeout.connect(self._maintain_topmost)
        self._topmost_timer.start(1000)
        
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
        # 拖拽中不更新状态，避免和拖拽状态冲突
        if self._is_dragging:
            return
        # 长按等待中也不更新
        if self._drag_pending:
            return
        # 气泡拖拽中也不更新
        if self._current_state == "拖拽":
            return
        # 映射分类到状态
        state = self.CATEGORY_TO_STATE.get(category, "待机")
        self._set_state(state)
    
    def paintEvent(self, event):
        """绘制桌宠"""
        if self._current_pixmap:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.SmoothPixmapTransform)
            painter.drawPixmap(0, 0, self._current_pixmap)

    def _maintain_topmost(self):
        """Win32 强制刷新 TOPMOST 状态（防止 Windows 系统抢占置顶）"""
        if not self.isVisible():
            return
        if not self._always_on_top:
            return
        try:
            import ctypes
            hwnd = int(self.winId())
            # HWND_TOPMOST = -1
            # SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE | SWP_NOOWNERZORDER = 0x0203
            ctypes.windll.user32.SetWindowPos(hwnd, -1, 0, 0, 0, 0, 0x0203)
        except OSError:
            pass

    def set_always_on_top(self, enabled: bool):
        """设置置顶状态（供插件层调用）"""
        self._always_on_top = enabled
        if enabled:
            self._topmost_timer.start(3000)
            self._maintain_topmost()  # 立即刷新一次
        else:
            self._topmost_timer.stop()
    
    def _on_long_press(self):
        """长按确认 - 进入拖拽模式"""
        if self._drag_pending and not self._is_dragging:
            self._is_dragging = True
            self._drag_pending = False
            self._drag_offset = self._long_press_pos
            # 记录拖拽前的状态，切换到拖拽图片
            self._state_before_drag = self._current_state
            self._set_state("拖拽")
    
    def mousePressEvent(self, event):
        """鼠标按下 - 开始等待长按"""
        if event.button() == Qt.LeftButton:
            self._drag_pending = True
            self._long_press_pos = event.globalPos() - self.pos()
            self._long_press_timer.start(200)  # 200ms 后确认为长按
            event.accept()
    
    def mouseMoveEvent(self, event):
        """鼠标移动 - 拖拽中"""
        if self._is_dragging and (event.buttons() & Qt.LeftButton) and self._drag_offset:
            new_pos = event.globalPos() - self._drag_offset
            # 屏幕边界检测
            from PyQt5.QtWidgets import QApplication
            screen = QApplication.primaryScreen().geometry()
            x = max(screen.left(), min(new_pos.x(), screen.right() - self.width() + 20))
            y = max(screen.top(), min(new_pos.y(), screen.bottom() - self.height() + 20))
            self.move(x, y)
            # 通知外部（气泡）同步位置
            if self._on_drag_move_callback:
                self._on_drag_move_callback(x, y)
            event.accept()
    
    def mouseReleaseEvent(self, event):
        """鼠标释放 - 结束拖拽或取消等待"""
        if event.button() == Qt.LeftButton:
            self._long_press_timer.stop()
            self._drag_pending = False
            if self._is_dragging:
                self._is_dragging = False
                self._drag_offset = None
                # 切回拖拽前的状态
                self._set_state(self._state_before_drag)
                # 通知外部拖拽结束（用于保存位置）
                if self._on_drag_end_callback:
                    pos = self.pos()
                    self._on_drag_end_callback(pos.x(), pos.y())
            event.accept()
