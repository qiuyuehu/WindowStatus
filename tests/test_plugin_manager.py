# -*- coding: utf-8 -*-
"""
PluginManager 单元测试
"""

import unittest
from unittest.mock import MagicMock

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from kernel.plugin_manager import PluginManager


def _make_mock_plugin_class(name, version="1.0.0", enabled=True):
    """创建 mock 插件类（load_plugin 需要类的 name 属性和实例的 name 属性一致）"""
    mock_instance = MagicMock()
    mock_instance.name = name
    mock_instance.version = version
    mock_instance.enabled = enabled

    mock_class = MagicMock()
    mock_class.name = name
    mock_class.version = version
    mock_class.return_value = mock_instance
    return mock_class, mock_instance


class TestPluginManagerBasic(unittest.TestCase):
    """测试 PluginManager 基本操作"""

    def setUp(self):
        self.mock_kernel = MagicMock()
        self.mock_kernel.event_bus = MagicMock()
        self.mock_kernel.config = MagicMock()
        self.mock_kernel.logger = MagicMock()
        self.pm = PluginManager(self.mock_kernel)

    def test_init_empty_plugins(self):
        """初始化时插件列表为空"""
        self.assertEqual(len(self.pm.get_all_plugins()), 0)

    def test_load_plugin(self):
        """加载插件"""
        mock_class, mock_instance = _make_mock_plugin_class("test_plugin")
        result = self.pm.load_plugin(mock_class)
        self.assertIs(result, mock_instance)
        mock_instance.on_load.assert_called_once()

    def test_unload_plugin(self):
        """卸载插件"""
        mock_class, mock_instance = _make_mock_plugin_class("test_plugin")
        self.pm.load_plugin(mock_class)
        result = self.pm.unload_plugin("test_plugin")
        self.assertTrue(result)
        mock_instance.on_unload.assert_called_once()

    def test_unload_nonexistent_plugin(self):
        """卸载不存在的插件返回 False"""
        result = self.pm.unload_plugin("nonexistent")
        self.assertFalse(result)

    def test_enable_plugin(self):
        """启用插件"""
        mock_class, mock_instance = _make_mock_plugin_class("test_plugin", enabled=False)
        self.pm.load_plugin(mock_class)
        result = self.pm.enable_plugin("test_plugin")
        self.assertTrue(result)
        self.assertTrue(mock_instance.enabled)
        mock_instance.on_enable.assert_called_once()

    def test_disable_plugin(self):
        """禁用插件"""
        mock_class, mock_instance = _make_mock_plugin_class("test_plugin", enabled=True)
        self.pm.load_plugin(mock_class)
        result = self.pm.disable_plugin("test_plugin")
        self.assertTrue(result)
        self.assertFalse(mock_instance.enabled)
        mock_instance.on_disable.assert_called_once()

    def test_get_plugin(self):
        """按名称获取插件"""
        mock_class, mock_instance = _make_mock_plugin_class("test_plugin")
        self.pm.load_plugin(mock_class)
        result = self.pm.get_plugin("test_plugin")
        self.assertIs(result, mock_instance)

    def test_get_plugin_nonexistent(self):
        """获取不存在的插件返回 None"""
        result = self.pm.get_plugin("nonexistent")
        self.assertIsNone(result)

    def test_is_loaded(self):
        """检查插件是否已加载"""
        mock_class, _ = _make_mock_plugin_class("test_plugin")
        self.assertFalse(self.pm.is_loaded("test_plugin"))
        self.pm.load_plugin(mock_class)
        self.assertTrue(self.pm.is_loaded("test_plugin"))

    def test_is_enabled(self):
        """检查插件是否已启用"""
        mock_class, _ = _make_mock_plugin_class("test_plugin", enabled=True)
        self.pm.load_plugin(mock_class)
        self.assertTrue(self.pm.is_enabled("test_plugin"))

    def test_get_all_plugins(self):
        """获取所有已加载插件"""
        for name in ["a", "b"]:
            mock_class, _ = _make_mock_plugin_class(name)
            self.pm.load_plugin(mock_class)
        self.assertEqual(len(self.pm.get_all_plugins()), 2)

    def test_get_enabled_plugins(self):
        """获取所有已启用插件"""
        mock_class_a, _ = _make_mock_plugin_class("a", enabled=True)
        mock_class_b, _ = _make_mock_plugin_class("b", enabled=False)
        self.pm.load_plugin(mock_class_a)
        self.pm.load_plugin(mock_class_b)
        self.assertEqual(len(self.pm.get_enabled_plugins()), 1)


if __name__ == "__main__":
    unittest.main()
