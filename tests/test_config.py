# -*- coding: utf-8 -*-
"""
Config 单元测试
"""

import unittest
import json
import tempfile
import os

# 添加项目根目录到路径
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from kernel.config import Config, DEFAULT_CONFIG


class TestConfig(unittest.TestCase):
    """测试 Config"""
    
    def setUp(self):
        """测试前准备"""
        # 创建临时配置文件
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = os.path.join(self.temp_dir, "config.json")
    
    def tearDown(self):
        """测试后清理"""
        # 删除临时文件
        if os.path.exists(self.config_path):
            os.remove(self.config_path)
        os.rmdir(self.temp_dir)
    
    def test_default_config(self):
        """测试默认配置"""
        config = Config(self.config_path)
        
        # 检查默认值
        self.assertEqual(config.get("version"), "3.1.0")
        self.assertEqual(config.get("opacity"), 0.9)
        self.assertTrue(config.get("always_on_top"))
        self.assertEqual(config.get("position"), "top-right")
    
    def test_load_existing_config(self):
        """测试加载已有配置"""
        # 写入测试配置
        test_config = {
            "version": "1.0.0",
            "opacity": 0.5,
            "always_on_top": False
        }
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(test_config, f)
        
        config = Config(self.config_path)
        
        # 检查加载的值
        self.assertEqual(config.get("version"), "1.0.0")
        self.assertEqual(config.get("opacity"), 0.5)
        self.assertFalse(config.get("always_on_top"))
    
    def test_get_with_default(self):
        """测试获取配置项带默认值"""
        config = Config(self.config_path)
        
        # 存在的配置项
        self.assertEqual(config.get("opacity"), 0.9)
        
        # 不存在的配置项，返回默认值
        self.assertEqual(config.get("nonexistent", "default"), "default")
        self.assertIsNone(config.get("nonexistent"))
    
    def test_set_config(self):
        """测试设置配置项"""
        config = Config(self.config_path)
        
        config.set("opacity", 0.5)
        self.assertEqual(config.get("opacity"), 0.5)
        
        # 验证保存到文件
        with open(self.config_path, "r", encoding="utf-8") as f:
            saved_config = json.load(f)
        self.assertEqual(saved_config["opacity"], 0.5)
    
    def test_nested_config(self):
        """测试嵌套配置"""
        config = Config(self.config_path)
        
        # 设置嵌套配置
        config.set("reminders.游戏.interval_minutes", 30)
        self.assertEqual(config.get("reminders.游戏.interval_minutes"), 30)
    
    def test_batch_update(self):
        """测试批量更新"""
        config = Config(self.config_path)
        
        # 使用批量更新
        with config.batch_update():
            config.set("opacity", 0.5)
            config.set("always_on_top", False)
        
        # 验证值已更新
        self.assertEqual(config.get("opacity"), 0.5)
        self.assertFalse(config.get("always_on_top"))
    
    def test_get_categories(self):
        """测试获取分类配置"""
        config = Config(self.config_path)
        
        categories = config.get_categories()
        
        # 检查内置分类
        self.assertIn("游戏", categories)
        self.assertIn("办公", categories)
        self.assertIn("摸鱼", categories)
        self.assertIn("开发", categories)
        self.assertIn("工具", categories)
    
    def test_set_categories(self):
        """测试设置分类配置"""
        config = Config(self.config_path)
        
        new_categories = {
            "自定义": {
                "icon": "🎯",
                "color": [255, 0, 0],
                "rules": []
            }
        }
        
        config.set_categories(new_categories)
        categories = config.get_categories()
        
        self.assertIn("自定义", categories)
        self.assertEqual(categories["自定义"]["icon"], "🎯")
    
    def test_opacity(self):
        """测试透明度配置"""
        config = Config(self.config_path)
        
        self.assertEqual(config.get_opacity(), 0.9)
        
        config.set_opacity(0.5)
        self.assertEqual(config.get_opacity(), 0.5)
    
    def test_always_on_top(self):
        """测试置顶配置"""
        config = Config(self.config_path)
        
        self.assertTrue(config.is_always_on_top())
        
        config.set_always_on_top(False)
        self.assertFalse(config.is_always_on_top())
    
    def test_position(self):
        """测试位置配置"""
        config = Config(self.config_path)
        
        self.assertEqual(config.get_position(), "top-right")
        
        config.set_position("bottom-left")
        self.assertEqual(config.get_position(), "bottom-left")
    
    def test_plugin_config(self):
        """测试插件配置"""
        config = Config(self.config_path)
        
        # 检查默认插件配置
        self.assertTrue(config.is_plugin_enabled("monitor"))
        self.assertTrue(config.is_plugin_enabled("overlay"))
        
        # 禁用插件
        config.disable_plugin("overlay")
        self.assertFalse(config.is_plugin_enabled("overlay"))
        
        # 启用插件
        config.enable_plugin("overlay")
        self.assertTrue(config.is_plugin_enabled("overlay"))
    
    def test_get_enabled_plugins(self):
        """测试获取启用的插件列表"""
        config = Config(self.config_path)
        
        enabled_plugins = config.get_enabled_plugins()
        
        # 检查默认启用的插件
        self.assertIn("monitor", enabled_plugins)
        self.assertIn("overlay", enabled_plugins)
        self.assertIn("tray", enabled_plugins)
        self.assertIn("stats", enabled_plugins)
    
    def test_merge_defaults(self):
        """测试合并默认配置"""
        # 写入不完整的配置
        test_config = {
            "opacity": 0.5
        }
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(test_config, f)
        
        config = Config(self.config_path)
        
        # 检查用户配置保留
        self.assertEqual(config.get("opacity"), 0.5)
        
        # 检查默认配置合并
        self.assertTrue(config.get("always_on_top"))
        self.assertEqual(config.get("position"), "top-right")
    
    def test_migrate_config(self):
        """测试配置迁移"""
        # 写入旧版本配置
        test_config = {
            "version": "2.0.0",
            "enabled_plugins": ["monitor", "overlay"]
        }
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(test_config, f)
        
        config = Config(self.config_path)
        
        # 检查迁移后的版本
        self.assertEqual(config.get("version"), "3.1.0")
        
        # 检查插件配置迁移
        self.assertTrue(config.is_plugin_enabled("monitor"))
        self.assertTrue(config.is_plugin_enabled("overlay"))


class TestConfigIntegration(unittest.TestCase):
    """Config 集成测试"""
    
    def test_full_workflow(self):
        """测试完整工作流程"""
        temp_dir = tempfile.mkdtemp()
        config_path = os.path.join(temp_dir, "config.json")
        
        try:
            # 创建配置
            config = Config(config_path)
            
            # 修改配置
            config.set("opacity", 0.7)
            config.set_position("bottom-left")
            config.set_always_on_top(False)
            config.disable_plugin("desktop_pet")
            
            # 重新加载配置
            config2 = Config(config_path)
            
            # 验证配置持久化
            self.assertEqual(config2.get_opacity(), 0.7)
            self.assertEqual(config2.get_position(), "bottom-left")
            self.assertFalse(config2.is_always_on_top())
            self.assertFalse(config2.is_plugin_enabled("desktop_pet"))
            
        finally:
            # 清理
            if os.path.exists(config_path):
                os.remove(config_path)
            os.rmdir(temp_dir)


if __name__ == "__main__":
    unittest.main()
