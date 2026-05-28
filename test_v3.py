#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WindowStatus v3.0 测试脚本
测试事件总线和插件发现机制
"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_event_bus():
    """测试事件总线"""
    print("=== 测试事件总线 ===")
    
    from kernel.event_bus import EventBus, Events
    
    bus = EventBus()
    
    # 测试事件注册和触发
    results = []
    
    def handler1(**kwargs):
        results.append(("handler1", kwargs))
    
    def handler2(**kwargs):
        results.append(("handler2", kwargs))
    
    # 注册事件
    bus.on("test.event", handler1)
    bus.on("test.event", handler2)
    
    # 触发事件
    bus.emit("test.event", data="hello")
    
    assert len(results) == 2, f"期望 2 个结果，实际 {len(results)}"
    assert results[0] == ("handler1", {"data": "hello"}), f"handler1 结果不匹配: {results[0]}"
    assert results[1] == ("handler2", {"data": "hello"}), f"handler2 结果不匹配: {results[1]}"
    
    # 测试注销事件
    bus.off("test.event", handler1)
    results.clear()
    bus.emit("test.event", data="world")
    
    assert len(results) == 1, f"期望 1 个结果，实际 {len(results)}"
    assert results[0] == ("handler2", {"data": "world"}), f"handler2 结果不匹配: {results[0]}"
    
    # 测试 has_handlers
    assert bus.has_handlers("test.event") == True, "应该有处理器"
    assert bus.has_handlers("nonexistent.event") == False, "不应该有处理器"
    
    print("✓ 事件总线测试通过")


def test_config():
    """测试配置管理"""
    print("\n=== 测试配置管理 ===")
    
    import tempfile
    from kernel.config import Config
    
    # 使用临时文件
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        temp_path = f.name
    
    try:
        # 测试默认配置
        config = Config(temp_path)
        assert config.get_opacity() == 0.9, f"默认透明度应为 0.9，实际 {config.get_opacity()}"
        assert config.is_always_on_top() == True, "默认应该置顶"
        
        # 测试设置配置
        config.set_opacity(0.8)
        assert config.get_opacity() == 0.8, f"透明度应为 0.8，实际 {config.get_opacity()}"
        
        config.set_always_on_top(False)
        assert config.is_always_on_top() == False, "应该不置顶"
        
        # 测试插件启用/禁用
        assert config.is_plugin_enabled("overlay") == True, "overlay 应该启用"
        config.disable_plugin("overlay")
        assert config.is_plugin_enabled("overlay") == False, "overlay 应该禁用"
        config.enable_plugin("overlay")
        assert config.is_plugin_enabled("overlay") == True, "overlay 应该启用"
        
        print("✓ 配置管理测试通过")
    
    finally:
        # 清理临时文件
        os.unlink(temp_path)


def test_plugin_discovery():
    """测试插件发现"""
    print("\n=== 测试插件发现 ===")
    
    from kernel.plugin_manager import PluginManager
    
    # 创建一个简单的 kernel 代理
    class FakeKernel:
        def __init__(self):
            self.event_bus = None
            self.config = None
            self.logger = None
    
    kernel = FakeKernel()
    manager = PluginManager(kernel)
    
    # 发现插件
    plugin_classes = manager.discover_plugins()
    
    print(f"发现 {len(plugin_classes)} 个插件:")
    for cls in plugin_classes:
        print(f"  - {cls.name} v{cls.version}")
    
    # 检查是否发现了所有插件
    plugin_names = [cls.name for cls in plugin_classes]
    
    # 检查是否有 PyQt5
    try:
        import PyQt5
        has_pyqt5 = True
    except ImportError:
        has_pyqt5 = False
    
    # 根据环境选择期望的插件
    if has_pyqt5:
        expected_plugins = ["monitor", "overlay", "tray", "stats", "rules"]
    else:
        # WSL 环境下没有 PyQt5，只能测试不依赖 PyQt5 的插件
        expected_plugins = ["monitor", "rules", "stats"]
        print("  (WSL 环境，跳过 PyQt5 相关插件)")
    
    for name in expected_plugins:
        assert name in plugin_names, f"未发现插件: {name}"
    
    print("✓ 插件发现测试通过")


def test_rules_classification():
    """测试规则分类"""
    print("\n=== 测试规则分类 ===")
    
    from plugins.rules.plugin import RulesPlugin
    
    # 创建一个简单的 kernel 代理
    class FakeConfig:
        def get_categories(self):
            return {
                "游戏": {
                    "icon": "🎮",
                    "color": [255, 107, 107],
                    "rules": [
                        {"type": "process", "pattern": "steam.exe"},
                        {"type": "title", "pattern": "*原神*"}
                    ]
                },
                "开发": {
                    "icon": "💻",
                    "color": [168, 230, 207],
                    "rules": [
                        {"type": "process", "pattern": "Code.exe"},
                        {"type": "title", "pattern": "*VS Code*"}
                    ]
                }
            }
    
    class FakeKernel:
        def __init__(self):
            self.config = FakeConfig()
            import logging
            self.logger = logging.getLogger("test")
            self.logger.setLevel(logging.DEBUG)
            from kernel.event_bus import EventBus
            self.event_bus = EventBus()
    
    kernel = FakeKernel()
    rules = RulesPlugin(kernel)
    rules.on_load()
    
    # 测试进程名匹配
    result = rules.classify("Steam", "steam.exe")
    assert result.category == "游戏", f"期望 '游戏'，实际 '{result.category}'"
    assert result.icon == "🎮", f"期望 '🎮'，实际 '{result.icon}'"
    
    # 测试窗口标题匹配
    result = rules.classify("原神 - 启动器", "launcher.exe")
    assert result.category == "游戏", f"期望 '游戏'，实际 '{result.category}'"
    
    # 测试 VS Code
    result = rules.classify("main.py - VS Code", "Code.exe")
    assert result.category == "开发", f"期望 '开发'，实际 '{result.category}'"
    
    # 测试默认分类
    result = rules.classify("未知窗口", "unknown.exe")
    assert result.category == "其他", f"期望 '其他'，实际 '{result.category}'"
    
    print("✓ 规则分类测试通过")


def main():
    """运行所有测试"""
    print("WindowStatus v3.0 测试\n")
    
    try:
        test_event_bus()
        test_config()
        test_plugin_discovery()
        test_rules_classification()
        
        print("\n" + "=" * 50)
        print("✓ 所有测试通过！")
        print("=" * 50)
        
    except AssertionError as e:
        print(f"\n✗ 测试失败: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ 测试异常: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
