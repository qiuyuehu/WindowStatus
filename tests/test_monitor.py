# -*- coding: utf-8 -*-
"""
Monitor 插件单元测试
"""

import unittest

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from plugins.monitor.plugin import WindowInfo


class TestWindowInfo(unittest.TestCase):
    """测试 WindowInfo 数据类"""

    def test_equality(self):
        """相同标题和进程名相等"""
        a = WindowInfo("VS Code", "code.exe", hwnd=1, pid=100)
        b = WindowInfo("VS Code", "code.exe", hwnd=2, pid=200)
        self.assertEqual(a, b)

    def test_inequality_different_title(self):
        """不同标题不相等"""
        a = WindowInfo("VS Code", "code.exe")
        b = WindowInfo("Chrome", "code.exe")
        self.assertNotEqual(a, b)

    def test_inequality_different_process(self):
        """不同进程不相等"""
        a = WindowInfo("VS Code", "code.exe")
        b = WindowInfo("VS Code", "chrome.exe")
        self.assertNotEqual(a, b)

    def test_inequality_different_type(self):
        """与非 WindowInfo 类型不相等"""
        a = WindowInfo("VS Code", "code.exe")
        self.assertNotEqual(a, "not a WindowInfo")

    def test_hash_equality(self):
        """相等对象哈希相同"""
        a = WindowInfo("VS Code", "code.exe", hwnd=1)
        b = WindowInfo("VS Code", "code.exe", hwnd=2)
        self.assertEqual(hash(a), hash(b))

    def test_hash_inequality(self):
        """不同对象哈希可能不同"""
        a = WindowInfo("VS Code", "code.exe")
        b = WindowInfo("Chrome", "chrome.exe")
        # 哈希冲突是可能的，但概率极低
        self.assertNotEqual(hash(a), hash(b))

    def test_str(self):
        """字符串表示"""
        info = WindowInfo("VS Code", "code.exe")
        result = str(info)
        self.assertIn("VS Code", result)
        self.assertIn("code.exe", result)

    def test_attributes(self):
        """属性正确设置"""
        info = WindowInfo("title", "process.exe", hwnd=123, pid=456)
        self.assertEqual(info.title, "title")
        self.assertEqual(info.process_name, "process.exe")
        self.assertEqual(info.hwnd, 123)
        self.assertEqual(info.pid, 456)

    def test_default_hwnd_pid(self):
        """默认 hwnd 和 pid 为 0"""
        info = WindowInfo("title", "process.exe")
        self.assertEqual(info.hwnd, 0)
        self.assertEqual(info.pid, 0)


if __name__ == "__main__":
    unittest.main()
