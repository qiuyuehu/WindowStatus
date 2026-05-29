# -*- coding: utf-8 -*-
"""
State Machine 单元测试
"""

import unittest
import tempfile
import os

# 添加项目根目录到路径
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from plugins.desktop_pet.state_machine import PetStateMachine, PetState


class TestPetState(unittest.TestCase):
    """测试 PetState 枚举"""
    
    def test_states(self):
        """测试状态枚举值"""
        self.assertEqual(PetState.IDLE.value, "idle")
        self.assertEqual(PetState.WALK.value, "walk")
        self.assertEqual(PetState.SIT.value, "sit")
        self.assertEqual(PetState.SLEEP.value, "sleep")
        self.assertEqual(PetState.DRAG.value, "drag")


class TestPetStateMachine(unittest.TestCase):
    """测试 PetStateMachine"""
    
    def setUp(self):
        """测试前准备"""
        # 创建临时目录和假素材
        self.temp_dir = tempfile.mkdtemp()
        
        # 创建每个状态的目录和假素材
        for state in ["idle", "walk", "sit", "sleep", "drag"]:
            state_dir = os.path.join(self.temp_dir, state)
            os.makedirs(state_dir, exist_ok=True)
            # 创建假的 PNG 文件
            for i in range(3):
                fake_png = os.path.join(state_dir, f"{i}.png")
                with open(fake_png, "wb") as f:
                    # 写入最小的 PNG 头
                    f.write(b'\x89PNG\r\n\x1a\n')
    
    def tearDown(self):
        """测试后清理"""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_init(self):
        """测试初始化"""
        sm = PetStateMachine(self.temp_dir)
        
        self.assertEqual(sm.current_state, PetState.IDLE)
        self.assertIsNotNone(sm.current_frame)
    
    def test_has_state(self):
        """测试检查状态是否有素材"""
        sm = PetStateMachine(self.temp_dir)
        
        self.assertTrue(sm.has_state(PetState.IDLE))
        self.assertTrue(sm.has_state(PetState.WALK))
        self.assertTrue(sm.has_state(PetState.SIT))
        self.assertTrue(sm.has_state(PetState.SLEEP))
        self.assertTrue(sm.has_state(PetState.DRAG))
    
    def test_set_state(self):
        """测试设置状态"""
        sm = PetStateMachine(self.temp_dir)
        
        sm.set_state(PetState.WALK)
        self.assertEqual(sm.current_state, PetState.WALK)
        
        sm.set_state(PetState.SIT)
        self.assertEqual(sm.current_state, PetState.SIT)
    
    def test_current_frame(self):
        """测试获取当前帧"""
        sm = PetStateMachine(self.temp_dir)
        
        frame = sm.current_frame
        self.assertIsNotNone(frame)
        if frame:  # 类型检查
            self.assertTrue(frame.endswith(".png"))
    
    def test_update(self):
        """测试更新状态机"""
        sm = PetStateMachine(self.temp_dir)
        
        # 更新多次
        for _ in range(100):
            sm.update(0.016)  # 16ms
        
        # 状态应该有变化
        # 注意：由于是随机的，这个测试可能不稳定
    
    def test_start(self):
        """测试启动状态机"""
        sm = PetStateMachine(self.temp_dir)
        sm.start()
        
        self.assertEqual(sm.current_state, PetState.IDLE)
    
    def test_animation_speed(self):
        """测试动画速度配置"""
        sm = PetStateMachine(self.temp_dir, animation_speed=0.1)
        
        self.assertEqual(sm._animation_speed, 0.1)
    
    def test_no_assets(self):
        """测试没有素材的情况"""
        empty_dir = tempfile.mkdtemp()
        
        try:
            with self.assertRaises(FileNotFoundError):
                PetStateMachine(empty_dir)
        finally:
            os.rmdir(empty_dir)


class TestPetStateMachineEdgeCases(unittest.TestCase):
    """测试边界情况"""
    
    def test_partial_assets(self):
        """测试部分素材"""
        temp_dir = tempfile.mkdtemp()
        
        try:
            # 只创建 idle 素材
            idle_dir = os.path.join(temp_dir, "idle")
            os.makedirs(idle_dir, exist_ok=True)
            fake_png = os.path.join(idle_dir, "0.png")
            with open(fake_png, "wb") as f:
                f.write(b'\x89PNG\r\n\x1a\n')
            
            sm = PetStateMachine(temp_dir)
            
            self.assertTrue(sm.has_state(PetState.IDLE))
            self.assertFalse(sm.has_state(PetState.WALK))
            self.assertFalse(sm.has_state(PetState.SIT))
            
        finally:
            import shutil
            shutil.rmtree(temp_dir)
    
    def test_set_state_without_assets(self):
        """测试设置没有素材的状态"""
        temp_dir = tempfile.mkdtemp()
        
        try:
            # 只创建 idle 素材
            idle_dir = os.path.join(temp_dir, "idle")
            os.makedirs(idle_dir, exist_ok=True)
            fake_png = os.path.join(idle_dir, "0.png")
            with open(fake_png, "wb") as f:
                f.write(b'\x89PNG\r\n\x1a\n')
            
            sm = PetStateMachine(temp_dir)
            
            # 尝试设置没有素材的状态
            sm.set_state(PetState.WALK)
            
            # 状态应该不变
            self.assertEqual(sm.current_state, PetState.IDLE)
            
        finally:
            import shutil
            shutil.rmtree(temp_dir)


if __name__ == "__main__":
    unittest.main()
