# -*- coding: utf-8 -*-
"""
Plugin 基类单元测试
"""

import unittest
from unittest.mock import MagicMock

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from plugins.base import Plugin


class TestPluginInit(unittest.TestCase):
    """测试 Plugin 初始化"""

    def setUp(self):
        self.mock_kernel = MagicMock()
        self.mock_kernel.event_bus = MagicMock()
        self.mock_kernel.config = MagicMock()
        self.mock_kernel.logger = MagicMock()
        self.mock_kernel.plugin_manager = MagicMock()
        self.plugin = Plugin(self.mock_kernel)

    def test_init_sets_kernel(self):
        """初始化设置 kernel 引用"""
        self.assertIs(self.plugin._kernel, self.mock_kernel)

    def test_init_sets_event_bus(self):
        """初始化设置 event_bus"""
        self.assertIs(self.plugin.event_bus, self.mock_kernel.event_bus)

    def test_init_sets_config(self):
        """初始化设置 config"""
        self.assertIs(self.plugin.config, self.mock_kernel.config)

    def test_init_sets_enabled_true(self):
        """初始化默认启用"""
        self.assertTrue(self.plugin.enabled)

    def test_init_sets_loaded_false(self):
        """初始化默认未加载"""
        self.assertFalse(self.plugin._loaded)


class TestPluginMethods(unittest.TestCase):
    """测试 Plugin 方法"""

    def setUp(self):
        self.mock_kernel = MagicMock()
        self.mock_kernel.event_bus = MagicMock()
        self.mock_kernel.config = MagicMock()
        self.mock_kernel.logger = MagicMock()
        self.mock_kernel.plugin_manager = MagicMock()
        self.plugin = Plugin(self.mock_kernel)

    def test_get_plugin(self):
        """获取其他插件"""
        mock_other = MagicMock()
        self.mock_kernel.plugin_manager.get_plugin.return_value = mock_other
        result = self.plugin.get_plugin("overlay")
        self.assertIs(result, mock_other)
        self.mock_kernel.plugin_manager.get_plugin.assert_called_once_with("overlay")

    def test_get_all_plugins(self):
        """获取所有插件"""
        mock_plugins = [MagicMock(), MagicMock()]
        self.mock_kernel.plugin_manager.get_all_plugins.return_value = mock_plugins
        result = self.plugin.get_all_plugins()
        self.assertEqual(result, mock_plugins)

    def test_main_window_with_attr(self):
        """获取主窗口（存在时）"""
        mock_window = MagicMock()
        self.mock_kernel.main_window = mock_window
        self.assertIs(self.plugin.main_window, mock_window)

    def test_main_window_without_attr(self):
        """获取主窗口（不存在时返回 None）"""
        del self.mock_kernel.main_window
        self.assertIsNone(self.plugin.main_window)

    def test_lifecycle_methods_exist(self):
        """生命周期方法存在且可调用"""
        self.plugin.on_load()
        self.plugin.on_unload()
        self.plugin.on_enable()
        self.plugin.on_disable()

    def test_str(self):
        """字符串表示"""
        self.plugin.name = "test"
        self.plugin.version = "1.0.0"
        self.assertEqual(str(self.plugin), "Plugin(test v1.0.0)")

    def test_repr(self):
        """repr 表示"""
        self.plugin.name = "test"
        self.plugin.version = "2.0.0"
        self.assertEqual(repr(self.plugin), "Plugin(test v2.0.0)")


if __name__ == "__main__":
    unittest.main()
