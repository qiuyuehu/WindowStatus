# -*- coding: utf-8 -*-
"""
窗口监控模块 - 核心层
负责监控当前活动窗口，检测窗口切换事件
"""

import win32gui
import win32process
import psutil
from typing import Tuple, Optional, Callable


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


class WindowMonitor:
    """
    窗口监控器
    
    监控当前活动窗口，当窗口切换时触发回调
    使用事件驱动，CPU占用极低
    """
    
    def __init__(self):
        self._last_window: Optional[WindowInfo] = None
        self._callback: Optional[Callable] = None
        self._running = False
    
    def set_callback(self, callback: Callable[[WindowInfo, WindowInfo], None]):
        """
        设置窗口切换回调
        
        Args:
            callback: 回调函数，参数为 (new_window, old_window)
        """
        self._callback = callback
    
    def get_active_window(self) -> WindowInfo:
        """
        获取当前活动窗口信息
        
        Returns:
            WindowInfo: 窗口信息
        """
        try:
            hwnd = win32gui.GetForegroundWindow()
            title = win32gui.GetWindowText(hwnd)
            
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            
            try:
                process = psutil.Process(pid)
                process_name = process.name()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
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
    
    def check_window_change(self) -> bool:
        """
        检查窗口是否切换
        
        Returns:
            bool: 是否切换了窗口
        """
        current_window = self.get_active_window()
        
        if self._last_window is None or current_window != self._last_window:
            old_window = self._last_window
            self._last_window = current_window
            
            if self._callback and old_window is not None:
                self._callback(current_window, old_window)
            
            return True
        
        return False
    
    def get_last_window(self) -> Optional[WindowInfo]:
        """获取上一个窗口信息"""
        return self._last_window
    
    def reset(self):
        """重置监控器状态"""
        self._last_window = None