# -*- coding: utf-8 -*-
"""
桌宠插件 - 插件层
附着在Overlay悬浮窗旁边，显示静态图片+状态气泡
"""

from typing import Optional

from PyQt5.QtCore import QTimer

from plugins.base import Plugin
from plugins.desktop_pet.widget import DesktopPetWidget
from kernel.event_bus import Events


class DesktopPetPlugin(Plugin):
    """
    桌宠插件
    
    职责：
    - 监听 CATEGORY_MATCHED 事件
    - 根据分类切换桌宠状态
    - 附着在Overlay悬浮窗旁边
    - 跟随Overlay移动
    """
    
    name = "desktop_pet"
    version = "2.0.0"
    description = "桌宠插件，附着在Overlay旁边显示状态"
    dependencies = ("overlay",)  # 依赖overlay插件
    
    DEFAULT_CONFIG = {
        "enabled": False,       # 默认关闭
    }
    
    def __init__(self, kernel):
        super().__init__(kernel)
        self._pet_widget: Optional[DesktopPetWidget] = None
        self._initialized = False  # 标记是否完成首次定位
        self._user_positioned = False  # 标记用户是否手动定位过
        self._overlay_synced = False  # 标记气泡是否已同步到桌宠位置
        self._delayed_timers: list = []  # 跟踪延迟初始化定时器
        
        # 跟随Overlay移动的定时器
        self._follow_timer = QTimer()
        self._follow_timer.timeout.connect(self._follow_overlay)
        self._follow_timer.start(500)  # 每500ms检查一次
    
    def on_load(self):
        """插件加载"""
        
        
        # 注册事件监听
        self.event_bus.on(Events.CATEGORY_MATCHED, self._on_category_matched)
        self.event_bus.on(Events.OVERLAY_POSITION_CHANGED, self._on_overlay_position_changed)
        self.event_bus.on(Events.TOGGLE_TOP, self._on_toggle_top)
        self.event_bus.on(Events.OVERLAY_SHOW, self._on_overlay_show)
        self.event_bus.on(Events.OVERLAY_HIDE, self._on_overlay_hide)
        
        self.logger.info("桌宠插件已加载")
    
    def on_unload(self):
        """插件卸载"""
        self.event_bus.off(Events.CATEGORY_MATCHED, self._on_category_matched)
        self.event_bus.off(Events.OVERLAY_POSITION_CHANGED, self._on_overlay_position_changed)
        self.event_bus.off(Events.TOGGLE_TOP, self._on_toggle_top)
        self.event_bus.off(Events.OVERLAY_SHOW, self._on_overlay_show)
        self.event_bus.off(Events.OVERLAY_HIDE, self._on_overlay_hide)
        
        self._follow_timer.stop()
        
        if self._pet_widget:
            self._pet_widget.hide()
            self._pet_widget = None
        
        self.logger.info("桌宠插件已卸载")
    
    def on_enable(self):
        """插件启用"""
        # 延迟创建桌宠，等Overlay渲染完成
        self._follow_timer.start(500)
        QTimer.singleShot(800, self._create_pet)
        self.logger.info("桌宠插件已启用")
    
    def on_disable(self):
        """插件禁用"""
        # 停止跟随定时器
        self._follow_timer.stop()
        # 停止所有延迟初始化定时器
        for timer in self._delayed_timers:
            timer.stop()
        self._delayed_timers.clear()
        if self._pet_widget:
            self._pet_widget.hide()
        self.logger.info("桌宠插件已禁用")
    
    def _create_pet(self):
        """创建桌宠"""
        try:
            # 获取素材目录
            import os
            plugin_dir = os.path.dirname(os.path.abspath(__file__))
            assets_dir = os.path.join(plugin_dir, "assets")
            
            if not os.path.isdir(assets_dir):
                self.logger.error(f"桌宠素材目录不存在: {assets_dir}")
                return
            
            # 检查素材文件
            required_files = ["sit.png", "walk.png", "sleep.png", "idle.png"]
            for filename in required_files:
                filepath = os.path.join(assets_dir, filename)
                if not os.path.exists(filepath):
                    self.logger.error(f"桌宠素材文件不存在: {filepath}")
                    return
            
            # 创建桌宠控件（先隐藏，等位置设置好再显示）
            self._pet_widget = DesktopPetWidget(assets_dir)
            self._pet_widget.hide()
            
            # 注册拖拽回调：拖桌宠时同步气泡位置
            self._pet_widget._on_drag_move_callback = self._on_pet_drag_move
            # 注册拖拽结束回调：保存位置
            self._pet_widget._on_drag_end_callback = self._save_pet_position
            
            # 尝试恢复保存的位置，否则定位到Overlay旁边
            self._restore_pet_position()
            if not self._user_positioned:
                self._initialized = False
                self._position_next_to_overlay()
            else:
                self._initialized = True
            self._pet_widget.show()
            
            # 记录初始状态
            overlay_plugin = self.get_plugin("overlay")
            if overlay_plugin and overlay_plugin.widget:
                ow = overlay_plugin.widget
                self.logger.info(f"桌宠初始状态: overlay pos=({ow.pos().x()}, {ow.pos().y()}), size=({ow.width()}, {ow.height()})")
            pp = self._pet_widget.pos()
            self.logger.info(f"桌宠初始状态: pet pos=({pp.x()}, {pp.y()}), visible={self._pet_widget.isVisible()}")
            
            # 延迟重新定位（多次尝试，确保Overlay已渲染）
            for delay in [100, 300, 600, 1000]:
                t = QTimer()
                t.setSingleShot(True)
                t.timeout.connect(self._delayed_init)
                t.start(delay)
                self._delayed_timers.append(t)
            
            self.logger.info("桌宠已创建")
            
        except Exception as e:
            self.logger.error(f"创建桌宠失败: {e}")
    
    def _position_next_to_overlay(self, overlay_x=None, overlay_y=None, overlay_width=None, overlay_height=None):
        """将桌宠定位到气泡下方，带屏幕边界检测"""
        if not self._pet_widget:
            return
        
        # 如果没有传入Overlay位置，尝试从overlay插件获取
        if overlay_x is None or overlay_y is None:
            overlay_plugin = self.get_plugin("overlay")
            if not overlay_plugin or not overlay_plugin.widget:
                self.logger.warning("Overlay插件未加载，桌宠显示在屏幕右下角")
                self._pet_widget.move(100, 100)
                return
            
            overlay_widget = overlay_plugin.widget
            overlay_pos = overlay_widget.pos()
            overlay_size = overlay_widget.size()
            overlay_x = overlay_pos.x()
            overlay_y = overlay_pos.y()
            overlay_width = overlay_size.width()
            overlay_height = overlay_size.height()
        
        # 获取屏幕可用区域
        from PyQt5.QtWidgets import QApplication
        screen = QApplication.primaryScreen().availableGeometry()
        screen_left = screen.left()
        screen_top = screen.top()
        screen_right = screen.right()
        screen_bottom = screen.bottom()
        
        # 获取桌宠尺寸
        pet_size = self._pet_widget.size()
        pet_w = pet_size.width()
        pet_h = pet_size.height()
        
        # 从 overlay widget 动态获取常量
        overlay_plugin = self.get_plugin("overlay")
        overlay_widget = getattr(overlay_plugin, 'widget', None) if overlay_plugin else None
        if overlay_widget:
            bubble_width = overlay_widget.BUBBLE_WIDTH
            bubble_height = overlay_widget.BUBBLE_HEIGHT
            dot_radius = overlay_widget.DOT_RADIUS
        else:
            # fallback 硬编码
            bubble_width = 260
            bubble_height = 70
            dot_radius = 3
        
        # 小气泡在气泡底部右下角
        tail_x = overlay_x + bubble_width - 1
        
        # 桌宠在气泡下方，小气泡朝下
        tail_y = overlay_y + bubble_height + dot_radius + 1
        x = tail_x - pet_w // 2 + 8  # 向右偏移
        y = tail_y - 60  # 桌宠图片头顶大约在60像素的位置
        
        self._pet_widget.move(x, y)
    
    def _sync_position(self, x=None, y=None, width=None, height=None):
        """根据Overlay位置同步桌宠位置（共享逻辑）"""
        try:
            if self._pet_widget and self.enabled and x is not None and y is not None:
                # 用户手动定位过，不跟随
                if self._user_positioned:
                    return
                self._position_next_to_overlay(x, y, width, height)
        except Exception as e:
            self.logger.error(f"桌宠插件: 同步Overlay位置失败: {e}")

    def _on_overlay_position_changed(self, position=None, x=None, y=None, width=None, height=None, **kwargs):
        """处理Overlay位置变化事件"""
        self._sync_position(x, y, width, height)

    def _on_pet_drag_move(self, pet_x, pet_y, **kwargs):
        """拖桌宠时反向定位气泡位置"""
        try:
            overlay_plugin = self.get_plugin("overlay")
            if not overlay_plugin or not overlay_plugin.widget:
                return
            overlay_widget = overlay_plugin.widget
            
            # 从桌宠位置反算气泡位置
            # 关系：pet_x = overlay_x + bubble_width - 1 - pet_w // 2 + 8
            # 所以：overlay_x = pet_x - bubble_width + 1 + pet_w // 2 - 8
            pet_w = self._pet_widget.width()
            bubble_width = overlay_widget.BUBBLE_WIDTH
            bubble_height = overlay_widget.BUBBLE_HEIGHT
            dot_radius = overlay_widget.DOT_RADIUS
            
            new_overlay_x = pet_x - bubble_width + 1 + pet_w // 2 - 8
            # 关系：pet_y = overlay_y + bubble_height + dot_radius + 1 - 60
            # 所以：overlay_y = pet_y - bubble_height - dot_radius - 1 + 60
            new_overlay_y = pet_y - bubble_height - dot_radius - 1 + 60
            
            overlay_widget.move(new_overlay_x, new_overlay_y)
        except Exception as e:
            self.logger.error(f"桌宠插件: 同步气泡位置失败: {e}")

    def _on_toggle_top(self, enabled: bool, **kwargs):
        """处理置顶切换事件，同步桌宠置顶状态"""
        try:
            if not self._pet_widget:
                return
            from PyQt5.QtCore import Qt
            current = bool(self._pet_widget.windowFlags() & Qt.WindowStaysOnTopHint)
            if current == enabled:
                return
            if enabled:
                self._pet_widget.setWindowFlags(self._pet_widget.windowFlags() | Qt.WindowStaysOnTopHint)
            else:
                self._pet_widget.setWindowFlags(self._pet_widget.windowFlags() & ~Qt.WindowStaysOnTopHint)
            self._pet_widget.show()
            # 同步桌宠的 TOPMOST 维护定时器
            self._pet_widget.set_always_on_top(enabled)
            # 气泡由 OverlayPlugin 自行监听 TOGGLE_TOP 处理，无需这里同步
        except Exception as e:
            self.logger.error(f"桌宠插件: 处理置顶切换事件失败: {e}")

    def _on_overlay_show(self, **kwargs):
        """处理显示事件，跟随Overlay显示"""
        try:
            if self._pet_widget and self.enabled:
                self._pet_widget.show()
        except Exception as e:
            self.logger.error(f"桌宠插件: 处理显示事件失败: {e}")

    def _on_overlay_hide(self, **kwargs):
        """处理隐藏事件，跟随Overlay隐藏"""
        try:
            if self._pet_widget:
                self._pet_widget.hide()
        except Exception as e:
            self.logger.error(f"桌宠插件: 处理隐藏事件失败: {e}")
    
    def _save_pet_position(self, x: int, y: int):
        """保存桌宠位置到 config"""
        self._kernel.config.set("desktop_pet.position", {"x": x, "y": y})
        # 同时保存气泡位置
        overlay_plugin = self.get_plugin("overlay")
        if overlay_plugin:
            ow = getattr(overlay_plugin, 'widget', None)
            if ow:
                self._kernel.config.set("desktop_pet.overlay_position", {
                    "x": ow.pos().x(), "y": ow.pos().y()
                })
        self._kernel.config.save()
        self._user_positioned = True
        self.logger.info(f"桌宠位置已保存: ({x}, {y})")

    def _restore_pet_position(self):
        """从 config 恢复桌宠和气泡位置"""
        if not self._pet_widget:
            return
        saved = self._kernel.config.get("desktop_pet.position")
        if saved and "x" in saved and "y" in saved:
            self._pet_widget.move(saved["x"], saved["y"])
            self._user_positioned = True
            # 恢复气泡位置
            overlay_plugin = self.get_plugin("overlay")
            if overlay_plugin and overlay_plugin.widget:
                overlay_saved = self._kernel.config.get("desktop_pet.overlay_position")
                if overlay_saved and "x" in overlay_saved:
                    overlay_plugin.widget.move(overlay_saved["x"], overlay_saved["y"])
                else:
                    # 没有保存的气泡位置，从桌宠位置反算
                    self._on_pet_drag_move(saved["x"], saved["y"])
                self._overlay_synced = True
                self._pet_widget.show()
                self.logger.info(f"桌宠位置已恢复: ({saved['x']}, {saved['y']})")
            else:
                # overlay 未就绪，保持隐藏，等 _delayed_init 重试
                self.logger.info(f"桌宠位置已保存，等待 overlay 就绪")

    def _follow_overlay(self):
        """跟随Overlay移动"""
        try:
            if not self._pet_widget:
                return
            # 用户手动定位过，不跟随
            if self._user_positioned:
                return
            # 拖拽中不跟随，避免和鼠标拖拽冲突
            if self._pet_widget._is_dragging:
                return
            # 首次定位完成前，即使不可见也要尝试定位
            if not self._initialized:
                self._position_next_to_overlay()
                return
            if not self._pet_widget.isVisible():
                return
            self._position_next_to_overlay()
        except Exception as e:
            self.logger.error(f"桌宠插件: 跟随Overlay移动失败: {e}")
    
    def _delayed_init(self):
        """延迟初始化：重新定位桌宠"""
        try:
            if self._pet_widget and self.enabled:
                # 用户手动定位过，跳过定位但重试气泡同步
                if self._user_positioned:
                    self._initialized = True
                    if not self._overlay_synced:
                        overlay_plugin = self.get_plugin("overlay")
                        if overlay_plugin and overlay_plugin.widget:
                            # 先恢复气泡位置
                            overlay_saved = self._kernel.config.get("desktop_pet.overlay_position")
                            if overlay_saved and "x" in overlay_saved:
                                overlay_plugin.widget.move(overlay_saved["x"], overlay_saved["y"])
                            else:
                                pos = self._pet_widget.pos()
                                self._on_pet_drag_move(pos.x(), pos.y())
                            self._overlay_synced = True
                            self._pet_widget.show()
                    return
                # 强制让Overlay重新计算布局后再定位
                overlay_plugin = self.get_plugin("overlay")
                if overlay_plugin and overlay_plugin.widget:
                    overlay_plugin.widget.adjustSize()
                    overlay_plugin.widget.update()
                    ow = overlay_plugin.widget
                    self.logger.info(f"桌宠延迟定位: overlay pos=({ow.pos().x()}, {ow.pos().y()}), size=({ow.width()}, {ow.height()})")
                self._position_next_to_overlay()
                self._pet_widget.show()
                self._pet_widget.update()
                pp = self._pet_widget.pos()
                self.logger.info(f"桌宠延迟定位: pet pos=({pp.x()}, {pp.y()}), visible={self._pet_widget.isVisible()}")
                self._initialized = True
        except Exception as e:
            self.logger.error(f"桌宠插件: 延迟初始化失败: {e}")
    
    def _on_category_matched(self, category: str, icon: str, color: tuple, title: str, process_name: str, **kwargs):
        """处理分类匹配事件"""
        try:
            if self._pet_widget and self.enabled:
                # 更新桌宠状态
                self._pet_widget.update_category(category, icon, title)
                
                # 用户手动定位过，不重新定位
                if self._user_positioned:
                    return
                # 重新定位（Overlay可能被拖动了）
                self._position_next_to_overlay()
        except Exception as e:
            self.logger.error(f"桌宠插件: 处理分类匹配事件失败: {e}")
    


# 约定：PluginClass 变量指向插件类
PluginClass = DesktopPetPlugin
