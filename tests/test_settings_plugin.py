# -*- coding: utf-8 -*-
"""
Settings 插件单元测试
"""

import unittest
from unittest.mock import MagicMock

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from plugins.settings.plugin import SettingsPlugin


class TestSettingsPluginInit(unittest.TestCase):
    """测试 Settings 插件初始化"""

    def setUp(self):
        self.mock_kernel = MagicMock()
        self.mock_kernel.event_bus = MagicMock()
        self.mock_kernel.config = MagicMock()
        self.mock_kernel.logger = MagicMock()
        self.mock_kernel.plugin_manager = MagicMock()
        self.mock_kernel.plugin_manager.get_all_plugins.return_value = []
        self.plugin = SettingsPlugin(self.mock_kernel)

    def test_plugin_metadata(self):
        """插件元信息"""
        self.assertEqual(self.plugin.name, "settings")
        self.assertEqual(self.plugin.version, "1.1.0")

    def test_on_load_registers_events(self):
        """on_load 注册事件监听"""
        self.plugin.on_load()
        self.mock_kernel.event_bus.on.assert_called()

    def test_on_unload_unregisters_events(self):
        """on_unload 注销事件监听"""
        self.plugin.on_load()
        self.plugin.on_unload()
        self.mock_kernel.event_bus.off.assert_called()


class TestSettingsPluginInfo(unittest.TestCase):
    """测试 Settings 插件信息获取"""

    def setUp(self):
        self.mock_kernel = MagicMock()
        self.mock_kernel.event_bus = MagicMock()
        self.mock_kernel.config = MagicMock()
        self.mock_kernel.logger = MagicMock()

        # 模拟已加载的插件
        mock_plugin_a = MagicMock()
        mock_plugin_a.name = "overlay"
        mock_plugin_a.description = "悬浮窗插件"
        mock_plugin_a.enabled = True

        mock_plugin_b = MagicMock()
        mock_plugin_b.name = "stats"
        mock_plugin_b.description = "统计插件"
        mock_plugin_b.enabled = False

        self.mock_kernel.plugin_manager = MagicMock()
        self.mock_kernel.plugin_manager.get_all_plugins.return_value = [
            mock_plugin_a, mock_plugin_b
        ]
        self.mock_kernel.config.get.return_value = {}

        self.plugin = SettingsPlugin(self.mock_kernel)

    def test_get_plugins_info(self):
        """获取插件信息列表"""
        info = self.plugin._get_plugins_info()
        names = [p["name"] for p in info]
        self.assertIn("overlay", names)
        self.assertIn("stats", names)

    def test_get_plugins_info_enabled_flag(self):
        """插件信息包含启用状态"""
        info = self.plugin._get_plugins_info()
        overlay_info = next(p for p in info if p["name"] == "overlay")
        self.assertTrue(overlay_info["enabled"])


class TestSettingsPluginSave(unittest.TestCase):
    """测试 Settings 插件保存逻辑"""

    def setUp(self):
        self.mock_kernel = MagicMock()
        self.mock_kernel.event_bus = MagicMock()
        self.mock_kernel.config = MagicMock()
        self.mock_kernel.logger = MagicMock()
        self.mock_kernel.plugin_manager = MagicMock()
        self.mock_kernel.plugin_manager.get_all_plugins.return_value = []
        self.plugin = SettingsPlugin(self.mock_kernel)

    def test_on_save_categories(self):
        """保存分类规则"""
        result = {"categories": {"开发": {"icon": "💻", "rules": []}}}
        self.plugin._on_save(result)
        self.mock_kernel.config.set_categories.assert_called_once()

    def test_on_save_theme(self):
        """保存主题配置"""
        result = {"categories": {}, "theme": "dark"}
        self.plugin._on_save(result)
        self.mock_kernel.config.set.assert_any_call("theme", "dark")

    def test_on_save_topmost(self):
        """保存窗口置顶配置"""
        result = {"categories": {}, "topmost": True}
        self.plugin._on_save(result)
        self.mock_kernel.config.set.assert_any_call("always_on_top", True)


if __name__ == "__main__":
    unittest.main()
