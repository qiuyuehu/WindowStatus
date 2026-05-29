# -*- coding: utf-8 -*-
"""
Rules 插件单元测试
"""

import unittest

# 添加项目根目录到路径
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from plugins.rules.plugin import RulesPlugin, ClassificationResult


class MockConfig:
    """模拟配置"""
    
    def __init__(self, categories):
        self._categories = categories
    
    def get_categories(self):
        return self._categories


class MockKernel:
    """模拟 Kernel"""
    
    def __init__(self, categories):
        self.config = MockConfig(categories)
        self.logger = None


class TestClassificationResult(unittest.TestCase):
    """测试 ClassificationResult"""
    
    def test_init(self):
        """测试初始化"""
        result = ClassificationResult(
            category="游戏",
            icon="🎮",
            color=(255, 107, 107),
            matched_rule="process:steam.exe"
        )
        
        self.assertEqual(result.category, "游戏")
        self.assertEqual(result.icon, "🎮")
        self.assertEqual(result.color, (255, 107, 107))
        self.assertEqual(result.matched_rule, "process:steam.exe")
    
    def test_str(self):
        """测试字符串表示"""
        result = ClassificationResult(
            category="游戏",
            icon="🎮",
            color=(255, 107, 107),
            matched_rule="process:steam.exe"
        )
        
        self.assertIn("游戏", str(result))
        self.assertIn("process:steam.exe", str(result))


class TestRulesPlugin(unittest.TestCase):
    """测试 RulesPlugin"""
    
    def setUp(self):
        """测试前准备"""
        self.categories = {
            "游戏": {
                "icon": "🎮",
                "color": [255, 107, 107],
                "rules": [
                    {"type": "process", "pattern": "steam.exe"},
                    {"type": "process", "pattern": "EpicGamesLauncher.exe"},
                    {"type": "title", "pattern": "*原神*"}
                ]
            },
            "办公": {
                "icon": "📊",
                "color": [78, 205, 196],
                "rules": [
                    {"type": "process", "pattern": "EXCEL.EXE"},
                    {"type": "process", "pattern": "WINWORD.EXE"}
                ]
            },
            "摸鱼": {
                "icon": "🐟",
                "color": [255, 230, 109],
                "rules": [
                    {"type": "process", "pattern": "chrome.exe"},
                    {"type": "title", "pattern": "*YouTube*"}
                ]
            }
        }
        
        kernel = MockKernel(self.categories)
        self.plugin = RulesPlugin(kernel)
        self.plugin._load_categories()
    
    def test_classify_process(self):
        """测试进程名匹配"""
        result = self.plugin.classify("Steam", "steam.exe")
        self.assertEqual(result.category, "游戏")
        self.assertEqual(result.icon, "🎮")
    
    def test_classify_process_case_insensitive(self):
        """测试进程名匹配（不区分大小写）"""
        result = self.plugin.classify("Steam", "Steam.exe")
        self.assertEqual(result.category, "游戏")
    
    def test_classify_title(self):
        """测试窗口标题匹配"""
        result = self.plugin.classify("原神 - 启动器", "launcher.exe")
        self.assertEqual(result.category, "游戏")
    
    def test_classify_title_wildcard(self):
        """测试窗口标题通配符匹配"""
        result = self.plugin.classify("YouTube - 视频", "chrome.exe")
        self.assertEqual(result.category, "摸鱼")
    
    def test_classify_no_match(self):
        """测试无匹配"""
        result = self.plugin.classify("记事本", "notepad.exe")
        self.assertEqual(result.category, "其他")
        self.assertEqual(result.icon, "💻")
    
    def test_classify_priority(self):
        """测试匹配优先级（先匹配到的分类优先）"""
        # chrome.exe 应该匹配到"摸鱼"而不是"游戏"
        result = self.plugin.classify("Chrome", "chrome.exe")
        self.assertEqual(result.category, "摸鱼")
    
    def test_match_rule_process(self):
        """测试单条规则匹配（进程）"""
        rule = {"type": "process", "pattern": "steam.exe"}
        
        self.assertTrue(self.plugin._match_rule(rule, "Steam", "steam.exe"))
        self.assertTrue(self.plugin._match_rule(rule, "Steam", "Steam.exe"))
        self.assertFalse(self.plugin._match_rule(rule, "Chrome", "chrome.exe"))
    
    def test_match_rule_title(self):
        """测试单条规则匹配（标题）"""
        rule = {"type": "title", "pattern": "*原神*"}
        
        self.assertTrue(self.plugin._match_rule(rule, "原神 - 启动器", "launcher.exe"))
        self.assertTrue(self.plugin._match_rule(rule, "原神", "game.exe"))
        self.assertFalse(self.plugin._match_rule(rule, "Chrome", "chrome.exe"))
    
    def test_match_rule_invalid_type(self):
        """测试无效规则类型"""
        rule = {"type": "invalid", "pattern": "test"}
        
        self.assertFalse(self.plugin._match_rule(rule, "test", "test.exe"))
    
    def test_reload_rules(self):
        """测试重新加载规则"""
        # 修改分类
        new_categories = {
            "自定义": {
                "icon": "🎯",
                "color": [255, 0, 0],
                "rules": [
                    {"type": "process", "pattern": "custom.exe"}
                ]
            }
        }
        
        kernel = MockKernel(new_categories)
        self.plugin.kernel = kernel
        self.plugin.reload_rules()
        
        result = self.plugin.classify("Custom", "custom.exe")
        self.assertEqual(result.category, "自定义")
    
    def test_get_categories(self):
        """测试获取分类"""
        categories = self.plugin.get_categories()
        
        self.assertIn("游戏", categories)
        self.assertIn("办公", categories)
        self.assertIn("摸鱼", categories)
    
    def test_test_classify(self):
        """测试测试分类方法"""
        result = self.plugin.test_classify("Steam", "steam.exe")
        self.assertEqual(result.category, "游戏")


class TestRulesPluginEdgeCases(unittest.TestCase):
    """测试边界情况"""
    
    def test_empty_categories(self):
        """测试空分类"""
        kernel = MockKernel({})
        plugin = RulesPlugin(kernel)
        plugin._load_categories()
        
        result = plugin.classify("Chrome", "chrome.exe")
        self.assertEqual(result.category, "其他")
    
    def test_empty_rules(self):
        """测试空规则"""
        categories = {
            "游戏": {
                "icon": "🎮",
                "color": [255, 107, 107],
                "rules": []
            }
        }
        
        kernel = MockKernel(categories)
        plugin = RulesPlugin(kernel)
        plugin._load_categories()
        
        result = plugin.classify("Steam", "steam.exe")
        self.assertEqual(result.category, "其他")
    
    def test_empty_title_and_process(self):
        """测试空标题和进程名"""
        categories = {
            "游戏": {
                "icon": "🎮",
                "color": [255, 107, 107],
                "rules": [
                    {"type": "process", "pattern": "steam.exe"}
                ]
            }
        }
        
        kernel = MockKernel(categories)
        plugin = RulesPlugin(kernel)
        plugin._load_categories()
        
        result = plugin.classify("", "")
        self.assertEqual(result.category, "其他")


if __name__ == "__main__":
    unittest.main()
