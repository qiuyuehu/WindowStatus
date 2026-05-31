# -*- coding: utf-8 -*-
"""
桌宠记住位置功能 - TDD 测试
测试目标：桌宠位置应该被记住，不被自动定位覆盖
"""

import unittest
import sys
import os
from unittest.mock import MagicMock, patch, PropertyMock

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class MockConfig:
    """模拟配置"""
    def __init__(self):
        self._data = {}

    def get(self, key, default=None):
        return self._data.get(key, default)

    def set(self, key, value):
        self._data[key] = value

    def save(self):
        pass


class MockKernel:
    """模拟 Kernel"""
    def __init__(self):
        self.config = MockConfig()
        self.logger = MagicMock()
        self.plugin_manager = MagicMock()
        self.event_bus = MagicMock()


class MockPetWidget:
    """模拟桌宠 Widget"""
    def __init__(self):
        self._is_dragging = False
        self._pos = (0, 0)
        self._on_drag_move_callback = None
        self._visible = True

    def pos(self):
        p = MagicMock()
        p.x.return_value = self._pos[0]
        p.y.return_value = self._pos[1]
        return p

    def move(self, x, y):
        self._pos = (x, y)

    def width(self):
        return 80

    def height(self):
        return 80

    def size(self):
        s = MagicMock()
        s.width.return_value = 80
        s.height.return_value = 80
        return s

    def show(self):
        self._visible = True

    def hide(self):
        self._visible = False

    def isVisible(self):
        return self._visible

    def update(self):
        pass

    def windowFlags(self):
        return 0


class TestPetRememberPosition(unittest.TestCase):
    """测试桌宠记住位置功能"""

    def _create_plugin(self):
        """创建桌宠插件实例"""
        from plugins.desktop_pet.plugin import DesktopPetPlugin

        kernel = MockKernel()
        plugin = DesktopPetPlugin(kernel)

        # mock get_plugin 返回 None（不需要真实的 overlay）
        plugin.get_plugin = MagicMock(return_value=None)

        # 替换 widget
        plugin._pet_widget = MockPetWidget()

        # 停止定时器（避免真实 QTimer 在测试中运行）
        plugin._follow_timer = MagicMock()

        return plugin

    def test_drag_end_saves_position(self):
        """测试：拖拽结束后，位置应该保存到 config"""
        plugin = self._create_plugin()

        # 模拟用户把桌宠拖到 (200, 300)
        plugin._pet_widget.move(200, 300)

        # 调用保存位置
        plugin._save_pet_position(200, 300)

        # 验证 config 里保存了位置
        saved_pos = plugin._kernel.config.get("desktop_pet.position")
        self.assertIsNotNone(saved_pos, "位置应该被保存到 config")
        self.assertEqual(saved_pos["x"], 200)
        self.assertEqual(saved_pos["y"], 300)

    def test_user_positioned_flag_blocks_follow(self):
        """测试：用户定位后，_follow_overlay 不应该覆盖位置"""
        plugin = self._create_plugin()

        # 模拟用户拖拽到 (200, 300)
        plugin._pet_widget.move(200, 300)
        plugin._save_pet_position(200, 300)
        plugin._user_positioned = True

        # 调用 _follow_overlay
        plugin._follow_overlay()

        # 桌宠位置不应该变
        pos = plugin._pet_widget.pos()
        self.assertEqual(pos.x(), 200, "x 坐标不应该被覆盖")
        self.assertEqual(pos.y(), 300, "y 坐标不应该被覆盖")

    def test_user_positioned_flag_blocks_delayed_init(self):
        """测试：用户定位后，_delayed_init 不应该覆盖位置"""
        plugin = self._create_plugin()

        # 模拟用户拖拽到 (200, 300)
        plugin._pet_widget.move(200, 300)
        plugin._save_pet_position(200, 300)
        plugin._user_positioned = True

        # 调用 _delayed_init
        plugin._delayed_init()

        # 桌宠位置不应该变
        pos = plugin._pet_widget.pos()
        self.assertEqual(pos.x(), 200, "x 坐标不应该被覆盖")
        self.assertEqual(pos.y(), 300, "y 坐标不应该被覆盖")

    def test_user_positioned_flag_blocks_category_match(self):
        """测试：用户定位后，分类切换不应该覆盖位置"""
        plugin = self._create_plugin()

        # 模拟用户拖拽到 (200, 300)
        plugin._pet_widget.move(200, 300)
        plugin._save_pet_position(200, 300)
        plugin._user_positioned = True

        # 模拟分类匹配事件
        plugin._pet_widget.update_category = MagicMock()
        plugin._on_category_matched(
            category="游戏", icon="🎮",
            color=(255, 107, 107), title="Steam",
            process_name="steam.exe"
        )

        # 桌宠位置不应该变
        pos = plugin._pet_widget.pos()
        self.assertEqual(pos.x(), 200, "x 坐标不应该被覆盖")
        self.assertEqual(pos.y(), 300, "y 坐标不应该被覆盖")

    def test_startup_restores_position(self):
        """测试：启动时，应该从 config 恢复桌宠位置"""
        plugin = self._create_plugin()

        # 预设 config 里有保存的位置
        plugin._kernel.config.set("desktop_pet.position", {"x": 200, "y": 300})

        # 调用恢复位置
        plugin._restore_pet_position()

        # 桌宠应该被移到保存的位置
        pos = plugin._pet_widget.pos()
        self.assertEqual(pos.x(), 200, "启动时应该恢复 x 坐标")
        self.assertEqual(pos.y(), 300, "启动时应该恢复 y 坐标")

    def test_delayed_init_retries_overlay_sync(self):
        """测试：overlay 未就绪时，_delayed_init 应该重试同步气泡"""
        plugin = self._create_plugin()

        # 模拟用户已定位，但 overlay 未同步
        plugin._pet_widget.move(200, 300)
        plugin._save_pet_position(200, 300)
        plugin._user_positioned = True
        plugin._overlay_synced = False

        # 第一次 get_plugin 返回 None（overlay 未就绪）
        plugin.get_plugin = MagicMock(return_value=None)

        # 调用 _delayed_init — 应该跳过定位但不跳过同步检查
        plugin._delayed_init()

        # overlay 仍未同步（因为 get_plugin 返回 None）
        self.assertFalse(plugin._overlay_synced)

        # 模拟 overlay 就绪了
        mock_overlay = MagicMock()
        mock_overlay.widget = MagicMock()
        mock_overlay.widget.BUBBLE_WIDTH = 260
        mock_overlay.widget.BUBBLE_HEIGHT = 70
        mock_overlay.widget.DOT_RADIUS = 3
        mock_overlay.widget.move = MagicMock()
        plugin.get_plugin = MagicMock(return_value=mock_overlay)

        # 再次调用 _delayed_init — 应该同步气泡
        plugin._delayed_init()

        # 现在 overlay 应该被同步了
        self.assertTrue(plugin._overlay_synced)

    def test_no_saved_position_falls_back_to_default(self):
        """测试：config 里没有保存位置时，应该走默认定位逻辑"""
        plugin = self._create_plugin()

        # config 里没有位置数据
        # 调用恢复位置（应该不移动桌宠）
        plugin._restore_pet_position()

        # 桌宠应该还在默认位置 (0, 0)
        pos = plugin._pet_widget.pos()
        self.assertEqual(pos.x(), 0)
        self.assertEqual(pos.y(), 0)


if __name__ == "__main__":
    unittest.main()
