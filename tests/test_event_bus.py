# -*- coding: utf-8 -*-
"""
EventBus 单元测试
"""

import unittest
import threading
from unittest.mock import MagicMock, patch

# 添加项目根目录到路径
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from kernel.event_bus import EventBus, Events


class TestEvents(unittest.TestCase):
    """测试事件常量"""
    
    def test_window_events(self):
        """测试窗口事件常量"""
        self.assertEqual(Events.WINDOW_CHANGED, "window.changed")
        self.assertEqual(Events.IDLE_DETECTED, "idle.detected")
        self.assertEqual(Events.IDLE_RESUMED, "idle.resumed")
    
    def test_category_events(self):
        """测试分类事件常量"""
        self.assertEqual(Events.CATEGORY_MATCHED, "category.matched")
    
    def test_stats_events(self):
        """测试统计事件常量"""
        self.assertEqual(Events.STATS_RECORDED, "stats.recorded")
    
    def test_plugin_events(self):
        """测试插件事件常量"""
        self.assertEqual(Events.PLUGIN_LOADED, "plugin.loaded")
        self.assertEqual(Events.PLUGIN_UNLOADED, "plugin.unloaded")
        self.assertEqual(Events.PLUGIN_ENABLED, "plugin.enabled")
        self.assertEqual(Events.PLUGIN_DISABLED, "plugin.disabled")


class TestEventBus(unittest.TestCase):
    """测试 EventBus"""
    
    def setUp(self):
        """测试前准备"""
        self.bus = EventBus()
        self.results = []
    
    def _handler(self, **kwargs):
        """通用事件处理器"""
        self.results.append(kwargs)
    
    def test_on_and_emit(self):
        """测试注册和发送事件"""
        self.bus.on("test.event", self._handler)
        self.bus.emit("test.event", data="hello")
        
        self.assertEqual(len(self.results), 1)
        self.assertEqual(self.results[0]["data"], "hello")
    
    def test_multiple_handlers(self):
        """测试多个处理器"""
        results2 = []
        
        def handler2(**kwargs):
            results2.append(kwargs)
        
        self.bus.on("test.event", self._handler)
        self.bus.on("test.event", handler2)
        self.bus.emit("test.event", data="hello")
        
        self.assertEqual(len(self.results), 1)
        self.assertEqual(len(results2), 1)
    
    def test_off(self):
        """测试注销事件"""
        self.bus.on("test.event", self._handler)
        self.bus.off("test.event", self._handler)
        self.bus.emit("test.event", data="hello")
        
        self.assertEqual(len(self.results), 0)
    
    def test_off_nonexistent(self):
        """测试注销不存在的事件"""
        # 不应该抛出异常
        self.bus.off("nonexistent.event", self._handler)
    
    def test_off_all(self):
        """测试注销事件的所有处理器"""
        results2 = []
        
        def handler2(**kwargs):
            results2.append(kwargs)
        
        self.bus.on("test.event", self._handler)
        self.bus.on("test.event", handler2)
        self.bus.off_all("test.event")
        self.bus.emit("test.event", data="hello")
        
        self.assertEqual(len(self.results), 0)
        self.assertEqual(len(results2), 0)
    
    def test_off_all_handlers(self):
        """测试注销所有事件的所有处理器"""
        self.bus.on("event1", self._handler)
        self.bus.on("event2", self._handler)
        self.bus.off_all_handlers()
        
        self.bus.emit("event1", data="hello")
        self.bus.emit("event2", data="world")
        
        self.assertEqual(len(self.results), 0)
    
    def test_has_handlers(self):
        """测试检查是否有处理器"""
        self.assertFalse(self.bus.has_handlers("test.event"))
        
        self.bus.on("test.event", self._handler)
        self.assertTrue(self.bus.has_handlers("test.event"))
    
    def test_get_handler_count(self):
        """测试获取处理器数量"""
        self.assertEqual(self.bus.get_handler_count("test.event"), 0)
        
        self.bus.on("test.event", self._handler)
        self.assertEqual(self.bus.get_handler_count("test.event"), 1)
        
        results2 = []
        def handler2(**kwargs):
            results2.append(kwargs)
        self.bus.on("test.event", handler2)
        self.assertEqual(self.bus.get_handler_count("test.event"), 2)
    
    def test_duplicate_handler(self):
        """测试重复注册同一个处理器"""
        self.bus.on("test.event", self._handler)
        self.bus.on("test.event", self._handler)  # 重复注册
        
        self.assertEqual(self.bus.get_handler_count("test.event"), 1)
    
    def test_emit_no_handlers(self):
        """测试发送事件但没有处理器"""
        # 不应该抛出异常
        self.bus.emit("nonexistent.event", data="hello")
    
    def test_handler_exception(self):
        """测试处理器抛出异常"""
        def bad_handler(**kwargs):
            raise ValueError("Test error")
        
        self.bus.on("test.event", bad_handler)
        self.bus.on("test.event", self._handler)
        
        # 不应该抛出异常，第二个处理器应该仍然执行
        self.bus.emit("test.event", data="hello")
        
        self.assertEqual(len(self.results), 1)
    
    def test_handler_type_error(self):
        """测试处理器参数类型错误"""
        def bad_handler(wrong_param):
            pass
        
        self.bus.on("test.event", bad_handler)
        self.bus.on("test.event", self._handler)
        
        # 不应该抛出异常，第二个处理器应该仍然执行
        self.bus.emit("test.event", data="hello")
        
        self.assertEqual(len(self.results), 1)
    
    def test_thread_safety(self):
        """测试线程安全"""
        results = []
        lock = threading.Lock()
        
        def thread_handler(**kwargs):
            with lock:
                results.append(kwargs.get("thread_id"))
        
        self.bus.on("test.event", thread_handler)
        
        # 创建多个线程同时发送事件
        threads = []
        for i in range(10):
            thread = threading.Thread(
                target=self.bus.emit,
                args=("test.event",),
                kwargs={"thread_id": i}
            )
            threads.append(thread)
        
        # 启动所有线程
        for thread in threads:
            thread.start()
        
        # 等待所有线程完成
        for thread in threads:
            thread.join()
        
        # 验证所有事件都被处理
        self.assertEqual(len(results), 10)
    
    def test_set_main_thread(self):
        """测试设置主线程"""
        main_thread = threading.current_thread()
        self.bus.set_main_thread(main_thread)
        
        # 当前线程是主线程，emit_to_main 应该直接执行
        self.bus.on("test.event", self._handler)
        self.bus.emit_to_main("test.event", data="hello")
        
        self.assertEqual(len(self.results), 1)
    
    def test_emit_to_main_from_background(self):
        """测试从后台线程发送到主线程"""
        # 注意：这个测试在没有 QApplication 的情况下运行
        # 实际的跨线程行为需要 PyQt5 环境
        
        main_thread = threading.current_thread()
        self.bus.set_main_thread(main_thread)
        
        self.bus.on("test.event", self._handler)
        
        # 从后台线程发送
        results = []
        def background_emit():
            self.bus.emit_to_main("test.event", data="from_background")
            results.append(True)
        
        thread = threading.Thread(target=background_emit)
        thread.start()
        thread.join()
        
        # 由于没有 QApplication，事件会直接在后台线程执行
        self.assertEqual(len(self.results), 1)


class TestEventBusIntegration(unittest.TestCase):
    """EventBus 集成测试"""
    
    def test_typical_workflow(self):
        """测试典型工作流程"""
        bus = EventBus()
        results = []
        
        # 模拟 monitor 插件
        def on_window_changed(**kwargs):
            results.append(("window_changed", kwargs.get("title")))
        
        # 模拟 rules 插件
        def on_category_matched(**kwargs):
            results.append(("category_matched", kwargs.get("category")))
        
        bus.on(Events.WINDOW_CHANGED, on_window_changed)
        bus.on(Events.CATEGORY_MATCHED, on_category_matched)
        
        # 模拟事件流
        bus.emit(Events.WINDOW_CHANGED, title="Chrome")
        bus.emit(Events.CATEGORY_MATCHED, category="摸鱼")
        
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0], ("window_changed", "Chrome"))
        self.assertEqual(results[1], ("category_matched", "摸鱼"))


if __name__ == "__main__":
    unittest.main()
