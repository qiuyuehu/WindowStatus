# -*- coding: utf-8 -*-
"""
桌宠插件单元测试
"""

import os
import sys
import tempfile
import unittest
from unittest.mock import MagicMock, patch

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from kernel.event_bus import EventBus, Events
from plugins.desktop_pet.plugin import DesktopPetPlugin
from plugins.desktop_pet.widget import DesktopPetWidget


class MockKernel:
    """模拟Kernel"""
    def __init__(self):
        self.event_bus = EventBus()
        self.config = MockConfig()
        self.logger = MockLogger()
        self.plugin_manager = MockPluginManager()


class MockConfig:
    """模拟Config"""
    def __init__(self):
        self._config = {}
    
    def get(self, key, default=None):
        return self._config.get(key, default)
    
    def set(self, key, value):
        self._config[key] = value


class MockLogger:
    """模拟Logger"""
    def info(self, msg):
        pass
    
    def error(self, msg):
        pass
    
    def warning(self, msg):
        pass


class MockPluginManager:
    """模拟PluginManager"""
    def __init__(self):
        self._plugins = {}
    
    def get_plugin(self, name):
        return self._plugins.get(name)


class TestDesktopPetPlugin(unittest.TestCase):
    """桌宠插件测试"""
    
    def setUp(self):
        """测试前准备"""
        self.kernel = MockKernel()
        self.plugin = DesktopPetPlugin(self.kernel)
        
        # 创建临时目录和测试图片
        self.temp_dir = tempfile.mkdtemp()
        self.assets_dir = os.path.join(self.temp_dir, "assets")
        os.makedirs(self.assets_dir, exist_ok=True)
        
        # 创建测试图片
        from PIL import Image
        for state in ["sit", "walk", "sleep", "idle", "drag"]:
            img = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
            img.save(os.path.join(self.assets_dir, f"{state}.png"))
    
    def tearDown(self):
        """测试后清理"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_plugin_metadata(self):
        """测试插件元信息"""
        self.assertEqual(self.plugin.name, "desktop_pet")
        self.assertEqual(self.plugin.version, "2.0.0")
        self.assertIn("overlay", self.plugin.dependencies)
    
    def test_default_config(self):
        """测试默认配置"""
        config = self.plugin.DEFAULT_CONFIG
        self.assertEqual(config["enabled"], False)
        self.assertEqual(config["position"], "top")
    
    def test_set_pet_position_valid(self):
        """测试设置有效位置"""
        # 模拟set_plugin_config
        self.plugin.set_plugin_config = MagicMock()
        
        # 设置有效位置
        self.plugin.set_pet_position("top")
        self.plugin.set_plugin_config.assert_called_once_with("position", "top")
    
    def test_set_pet_position_invalid(self):
        """测试设置无效位置"""
        # 模拟set_plugin_config
        self.plugin.set_plugin_config = MagicMock()
        
        # 设置无效位置
        self.plugin.set_pet_position("left")
        self.plugin.set_plugin_config.assert_not_called()
    
    def test_state_mapping(self):
        """测试状态映射"""
        mapping = DesktopPetWidget.CATEGORY_TO_STATE
        
        # 测试坐着状态
        self.assertEqual(mapping.get("办公"), "坐着")
        self.assertEqual(mapping.get("开发"), "坐着")
        self.assertEqual(mapping.get("学习"), "坐着")
        
        # 测试兴奋状态
        self.assertEqual(mapping.get("游戏"), "兴奋")
        self.assertEqual(mapping.get("娱乐"), "兴奋")
        self.assertEqual(mapping.get("社交"), "兴奋")
        
        # 测试打瞌睡状态
        self.assertEqual(mapping.get("摸鱼"), "打瞌睡")
        self.assertEqual(mapping.get("空闲"), "打瞌睡")
        
        # 测试待机状态
        self.assertEqual(mapping.get("其他"), "待机")
    
    def test_image_loading(self):
        """测试图片加载"""
        # 创建widget
        widget = DesktopPetWidget(self.assets_dir)
        
        # 检查图片是否加载
        self.assertIn("坐着", widget._images)
        self.assertIn("兴奋", widget._images)
        self.assertIn("打瞌睡", widget._images)
        self.assertIn("待机", widget._images)
    
    def test_state_switching(self):
        """测试状态切换"""
        widget = DesktopPetWidget(self.assets_dir)
        
        # 初始状态
        self.assertEqual(widget._current_state, "待机")
        
        # 切换到坐着
        widget._set_state("坐着")
        self.assertEqual(widget._current_state, "坐着")
        
        # 切换到兴奋
        widget._set_state("兴奋")
        self.assertEqual(widget._current_state, "兴奋")
    
    def test_category_update(self):
        """测试分类更新"""
        widget = DesktopPetWidget(self.assets_dir)
        
        # 更新分类
        widget.update_category("办公", "📊", "VSCode")
        self.assertEqual(widget._current_state, "坐着")
        
        widget.update_category("游戏", "🎮", "Steam")
        self.assertEqual(widget._current_state, "兴奋")
        
        widget.update_category("摸鱼", "🐟", "B站")
        self.assertEqual(widget._current_state, "打瞌睡")


class TestEventBus(unittest.TestCase):
    """事件总线测试"""
    
    def test_event_constants(self):
        """测试事件常量"""
        self.assertEqual(Events.CATEGORY_MATCHED, "category.matched")
        self.assertEqual(Events.OVERLAY_POSITION_CHANGED, "overlay.position.changed")
        self.assertEqual(Events.OVERLAY_MOVED, "overlay.moved")
    
    def test_event_registration(self):
        """测试事件注册"""
        bus = EventBus()
        handler = MagicMock()
        
        # 注册事件
        bus.on(Events.CATEGORY_MATCHED, handler)
        self.assertTrue(bus.has_handlers(Events.CATEGORY_MATCHED))
        self.assertEqual(bus.get_handler_count(Events.CATEGORY_MATCHED), 1)
    
    def test_event_emission(self):
        """测试事件发送"""
        bus = EventBus()
        handler = MagicMock()
        
        # 注册事件
        bus.on(Events.CATEGORY_MATCHED, handler)
        
        # 发送事件
        bus.emit(Events.CATEGORY_MATCHED, category="办公", icon="📊")
        handler.assert_called_once_with(category="办公", icon="📊")
    
    def test_event_unregistration(self):
        """测试事件注销"""
        bus = EventBus()
        handler = MagicMock()
        
        # 注册事件
        bus.on(Events.CATEGORY_MATCHED, handler)
        
        # 注销事件
        bus.off(Events.CATEGORY_MATCHED, handler)
        self.assertFalse(bus.has_handlers(Events.CATEGORY_MATCHED))
    
    def test_event_error_handling(self):
        """测试事件错误处理"""
        bus = EventBus()
        
        # 注册一个会抛出异常的handler
        def bad_handler(**kwargs):
            raise ValueError("Test error")
        
        bus.on(Events.CATEGORY_MATCHED, bad_handler)
        
        # 发送事件应该不会崩溃
        bus.emit(Events.CATEGORY_MATCHED, category="办公")


if __name__ == "__main__":
    unittest.main()
