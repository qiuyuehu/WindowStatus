# -*- coding: utf-8 -*-
"""
事件总线 - 核心层
负责插件间的事件通信
支持线程安全的事件分发
"""

from typing import Dict, List, Callable, Any, Optional
import threading
import logging

logger = logging.getLogger("WindowStatus.event_bus")


class Events:
    """
    事件类型常量
    
    所有事件名称都定义在这里，插件应该使用这些常量而不是硬编码字符串。
    
    使用方法：
        from kernel.event_bus import Events
        
        # 注册事件
        self.event_bus.on(Events.WINDOW_CHANGED, self._handler)
        
        # 发送事件
        self.event_bus.emit(Events.WINDOW_CHANGED, window_info=...)
    """
    
    # 窗口事件
    WINDOW_CHANGED = "window.changed"      # 窗口切换
    IDLE_DETECTED = "idle.detected"        # 用户空闲
    IDLE_RESUMED = "idle.resumed"          # 用户回来
    
    # 分类事件
    CATEGORY_MATCHED = "category.matched"  # 分类匹配完成
    
    # 统计事件
    STATS_RECORDED = "stats.recorded"      # 统计记录完成
    
    # 配置事件
    CONFIG_CHANGED = "config.changed"      # 配置变更
    
    # 插件事件
    PLUGIN_LOADED = "plugin.loaded"        # 插件加载
    PLUGIN_UNLOADED = "plugin.unloaded"    # 插件卸载
    PLUGIN_ENABLED = "plugin.enabled"      # 插件启用
    PLUGIN_DISABLED = "plugin.disabled"    # 插件禁用
    
    # 用户操作事件
    OPACITY_CHANGED = "opacity.changed"    # 透明度变更
    TOGGLE_TOP = "toggle.top"              # 切换置顶
    SHOW_STATS = "show.stats"              # 显示统计
    SHOW_SETTINGS = "show.settings"        # 显示设置
    SHOW_ABOUT = "show.about"              # 显示关于
    QUIT = "quit"                          # 退出应用
    
    # Overlay事件
    OVERLAY_POSITION_CHANGED = "overlay.position.changed"  # Overlay位置变更
    OVERLAY_MOVED = "overlay.moved"                        # Overlay被拖动
    OVERLAY_SHOW = "overlay.show"                          # 显示Overlay
    OVERLAY_HIDE = "overlay.hide"                          # 隐藏Overlay
    OVERLAY_DATA_CHANGED = "overlay.data.changed"          # Overlay数据变更
    OVERLAY_SET_THEME = "overlay.set.theme"                # 设置Overlay主题
    
    # Rules事件
    RULES_RELOAD = "rules.reload"                          # 重新加载规则


class EventBus:
    """
    事件总线
    
    支持两种事件发送方式：
    1. emit() - 同步发送，在调用线程执行
    2. emit_to_main() - 发送到主线程执行（用于 GUI 插件）
    
    线程安全：
    - 所有公共方法都使用锁保护
    - emit_to_main() 确保 GUI 操作在主线程执行
    
    使用方法：
        # 注册事件
        event_bus.on(Events.WINDOW_CHANGED, self._on_window_changed)
        
        # 注销事件
        event_bus.off(Events.WINDOW_CHANGED, self._on_window_changed)
        
        # 发送事件
        event_bus.emit(Events.WINDOW_CHANGED, window_info=window_info)
        
        # 发送到主线程（GUI 插件使用）
        event_bus.emit_to_main(Events.CATEGORY_MATCHED, category="游戏")
    """
    
    def __init__(self) -> None:
        self._handlers: Dict[str, List[Callable]] = {}
        self._main_thread: Optional[threading.Thread] = None
        self._qt_app = None  # QApplication 实例，用于跨线程调用
        self._lock = threading.Lock()
    
    def set_main_thread(self, thread: threading.Thread) -> None:
        """
        设置主线程引用
        
        Args:
            thread: 主线程对象
        """
        self._main_thread = thread
    
    def set_qt_app(self, app: Any) -> None:
        """
        设置 QApplication 实例
        
        Args:
            app: QApplication 实例
        """
        self._qt_app = app
    
    def on(self, event: str, handler: Callable) -> None:
        """
        注册事件监听器
        
        Args:
            event: 事件名称（建议使用 Events 类中的常量）
            handler: 事件处理函数
        """
        with self._lock:
            if event not in self._handlers:
                self._handlers[event] = []
            if handler not in self._handlers[event]:
                self._handlers[event].append(handler)
    
    def off(self, event: str, handler: Callable) -> None:
        """
        注销事件监听器
        
        Args:
            event: 事件名称
            handler: 事件处理函数
        """
        with self._lock:
            if event in self._handlers:
                try:
                    self._handlers[event].remove(handler)
                except ValueError:
                    pass
    
    def off_all(self, event: str) -> None:
        """
        注销事件的所有监听器
        
        Args:
            event: 事件名称
        """
        with self._lock:
            self._handlers.pop(event, None)
    
    def off_all_handlers(self) -> None:
        """注销所有事件的所有监听器"""
        with self._lock:
            self._handlers.clear()
    
    def emit(self, event: str, **kwargs: Any) -> None:
        """
        同步发送事件，在调用线程执行
        
        Args:
            event: 事件名称
            **kwargs: 事件参数
        """
        with self._lock:
            handlers = self._handlers.get(event, []).copy()

        for handler in handlers:
            try:
                handler(**kwargs)
            except TypeError as e:
                # 签名不匹配：handler 接受的参数和 emit 传入的不一致
                handler_name = getattr(handler, '__name__', repr(handler))
                logger.error(
                    f"EventBus: handler 签名不匹配 [{event}] "
                    f"handler={handler_name}, kwargs={list(kwargs.keys())}, error={e}"
                )
            except Exception as e:
                handler_name = getattr(handler, '__name__', repr(handler))
                logger.error(
                    f"EventBus: 事件处理异常 [{event}] "
                    f"handler={handler_name}, error={e}"
                )
    
    def emit_to_main(self, event: str, **kwargs: Any) -> None:
        """
        发送事件到主线程执行（用于 GUI 插件）
        
        如果当前就在主线程，直接执行。
        如果不在主线程，通过 Qt 的信号机制转发到主线程。
        
        Args:
            event: 事件名称
            **kwargs: 事件参数
        """
        current_thread = threading.current_thread()
        
        # 如果没有设置主线程，或者当前就是主线程，直接执行
        if self._main_thread is None or current_thread == self._main_thread:
            self.emit(event, **kwargs)
            return
        
        # 通过 Qt 的信号机制转发到主线程
        if self._qt_app is not None:
            # 使用 QTimer.singleShot 在主线程执行
            from PyQt5.QtCore import QTimer
            QTimer.singleShot(0, lambda: self.emit(event, **kwargs))
        else:
            # 没有 Qt 应用，直接执行（可能不安全，但至少不会丢事件）
            self.emit(event, **kwargs)
    
    def has_handlers(self, event: str) -> bool:
        """
        检查事件是否有监听器
        
        Args:
            event: 事件名称
            
        Returns:
            是否有监听器
        """
        with self._lock:
            return event in self._handlers and len(self._handlers[event]) > 0
    
    def get_handler_count(self, event: str) -> int:
        """
        获取事件的监听器数量
        
        Args:
            event: 事件名称
            
        Returns:
            监听器数量
        """
        with self._lock:
            return len(self._handlers.get(event, []))
