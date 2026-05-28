# -*- coding: utf-8 -*-
"""
Monitor 插件 - 插件层
负责监控当前活动窗口，检测窗口切换事件
"""

import threading
from typing import Optional, Callable

from plugins.base import Plugin
from kernel.event_bus import Events


class WindowInfo:
    """窗口信息数据类"""
    
    def __init__(self, title: str, process_name: str, hwnd: int = 0, pid: int = 0):
        self.title = title
        self.process_name = process_name
        self.hwnd = hwnd
        self.pid = pid
    
    def __eq__(self, other):
        if isinstance(other, WindowInfo):
            return self.title == other.title and self.process_name == other.process_name
        return False
    
    def __str__(self):
        return f"WindowInfo(title='{self.title}', process='{self.process_name}')"


class MonitorPlugin(Plugin):
    """
    窗口监控插件
    
    职责：
    - 监控当前活动窗口
    - 检测窗口切换事件
    - 通过事件总线发送 WINDOW_CHANGED 事件
    """
    
    name = "monitor"
    version = "1.0.0"
    description = "窗口监控插件，检测活动窗口切换"
    
    def __init__(self, kernel):
        super().__init__(kernel)
        
        self._last_window: Optional[WindowInfo] = None
        self._running = False
        self._timer = None
        
        # 导入 Windows API（延迟导入，避免在非 Windows 环境报错）
        self._win32gui = None
        self._win32process = None
        self._psutil = None
    
    def on_load(self):
        """插件加载"""
        self.logger = self.kernel.logger
        
        # 导入 Windows API
        try:
            import win32gui
            import win32process
            import psutil
            
            self._win32gui = win32gui
            self._win32process = win32process
            self._psutil = psutil
            
            self.logger.info("Monitor 插件: Windows API 加载成功")
        except ImportError as e:
            self.logger.error(f"Monitor 插件: Windows API 加载失败: {e}")
            raise
        
        # 启动监控
        self._start_monitoring()
    
    def on_unload(self):
        """插件卸载"""
        self._stop_monitoring()
        self.logger.info("Monitor 插件已卸载")
    
    def on_enable(self):
        """插件启用"""
        if not self._running:
            self._start_monitoring()
        self.logger.info("Monitor 插件已启用")
    
    def on_disable(self):
        """插件禁用"""
        self._stop_monitoring()
        self.logger.info("Monitor 插件已禁用")
    
    def _start_monitoring(self):
        """启动窗口监控"""
        if self._running:
            return
        
        self._running = True
        
        # 使用 QTimer 定期检查窗口切换
        # 注意：这里使用 Qt 的定时器，确保在主线程执行
        from PyQt5.QtCore import QTimer
        self._timer = QTimer()
        self._timer.timeout.connect(self._check_window_change)
        self._timer.start(100)  # 100ms 检查一次
        
        self.logger.info("Monitor 插件: 窗口监控已启动")
    
    def _stop_monitoring(self):
        """停止窗口监控"""
        if not self._running:
            return
        
        self._running = False
        
        if self._timer:
            self._timer.stop()
            self._timer = None
        
        self.logger.info("Monitor 插件: 窗口监控已停止")
    
    def _check_window_change(self):
        """检查窗口切换"""
        if not self.enabled:
            return
        
        try:
            current_window = self._get_active_window()
            
            if self._last_window is None or current_window != self._last_window:
                # 窗口切换
                self._last_window = current_window
                
                # 发送窗口切换事件
                self.event_bus.emit(
                    Events.WINDOW_CHANGED,
                    window_info=current_window
                )
                
                self.logger.debug(f"Monitor 插件: 窗口切换 -> {current_window.title[:30]}")
        
        except Exception as e:
            self.logger.error(f"Monitor 插件: 检查窗口切换失败: {e}")
    
    def _get_active_window(self) -> WindowInfo:
        """获取当前活动窗口信息"""
        try:
            hwnd = self._win32gui.GetForegroundWindow()
            title = self._win32gui.GetWindowText(hwnd)
            
            _, pid = self._win32process.GetWindowThreadProcessId(hwnd)
            
            try:
                process = self._psutil.Process(pid)
                process_name = process.name()
            except (self._psutil.NoSuchProcess, self._psutil.AccessDenied):
                process_name = ""
            
            return WindowInfo(
                title=title,
                process_name=process_name,
                hwnd=hwnd,
                pid=pid
            )
        except Exception as e:
            # 发生异常时返回空窗口信息
            return WindowInfo(title="", process_name="")
    
    def get_last_window(self) -> Optional[WindowInfo]:
        """获取上一个窗口信息"""
        return self._last_window
    
    def reset(self):
        """重置监控器状态"""
        self._last_window = None


# 约定：PluginClass 变量指向插件类
PluginClass = MonitorPlugin
