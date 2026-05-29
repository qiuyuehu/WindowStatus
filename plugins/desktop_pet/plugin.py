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
    dependencies = ["overlay"]  # 依赖overlay插件
    
    DEFAULT_CONFIG = {
        "enabled": False,       # 默认关闭
        "position": "top",      # 桌宠在Overlay的上方或下方
    }
    
    def __init__(self, kernel):
        super().__init__(kernel)
        self._pet_widget: Optional[DesktopPetWidget] = None
        self._initialized = False  # 标记是否完成首次定位
        self._delayed_timers: list = []  # 跟踪延迟初始化定时器
        
        # 跟随Overlay移动的定时器
        self._follow_timer = QTimer()
        self._follow_timer.timeout.connect(self._follow_overlay)
        self._follow_timer.start(500)  # 每500ms检查一次
    
    def on_load(self):
        """插件加载"""
        self.logger = self.kernel.logger
        
        # 注册事件监听
        self.event_bus.on(Events.CATEGORY_MATCHED, self._on_category_matched)
        self.event_bus.on(Events.OVERLAY_POSITION_CHANGED, self._on_overlay_position_changed)
        self.event_bus.on(Events.OVERLAY_MOVED, self._on_overlay_moved)
        self.event_bus.on(Events.TOGGLE_TOP, self._on_toggle_top)
        self.event_bus.on(Events.OVERLAY_SHOW, self._on_overlay_show)
        self.event_bus.on(Events.OVERLAY_HIDE, self._on_overlay_hide)
        
        self.logger.info("桌宠插件已加载")
    
    def on_unload(self):
        """插件卸载"""
        self.event_bus.off(Events.CATEGORY_MATCHED, self._on_category_matched)
        self.event_bus.off(Events.OVERLAY_POSITION_CHANGED, self._on_overlay_position_changed)
        self.event_bus.off(Events.OVERLAY_MOVED, self._on_overlay_moved)
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
            
            # 创建桌宠控件
            self._pet_widget = DesktopPetWidget(assets_dir)
            
            # 定位到Overlay旁边
            self._initialized = False
            self._position_next_to_overlay()
            self._pet_widget.show()
            
            # 记录初始状态
            overlay_plugin = self.kernel.plugin_manager.get_plugin("overlay")
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
        """将桌宠定位到Overlay上方或下方，带屏幕边界检测"""
        if not self._pet_widget:
            return
        
        # 如果没有传入Overlay位置，尝试从overlay插件获取
        if overlay_x is None or overlay_y is None:
            overlay_plugin = self.kernel.plugin_manager.get_plugin("overlay")
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
        from PyQt5.QtWidgets import QDesktopWidget
        screen = QDesktopWidget().availableGeometry()
        screen_left = screen.left()
        screen_top = screen.top()
        screen_right = screen.right()
        screen_bottom = screen.bottom()
        
        # 获取配置
        config = self.get_plugin_config()
        position = config.get("position", "top")
        
        # 计算桌宠位置（居中对齐，重叠一点）
        pet_size = self._pet_widget.size()
        pet_w = pet_size.width()
        pet_h = pet_size.height()
        overlap = 50
        
        # 水平居中，但不超出屏幕
        x = overlay_x + (overlay_width - pet_w) // 2
        x = max(screen_left, min(x, screen_right - pet_w))
        
        if position == "top":
            y = overlay_y - pet_h + overlap
            # 如果上方空间不够，翻转到下方
            if y < screen_top:
                y = overlay_y + overlay_height - overlap
        else:  # bottom
            y = overlay_y + overlay_height - overlap
            # 如果下方空间不够，翻转到上方
            if y + pet_h > screen_bottom:
                y = overlay_y - pet_h + overlap
        
        # 最终边界钳制（防止极端情况）
        y = max(screen_top, min(y, screen_bottom - pet_h))
        
        self._pet_widget.move(x, y)
    
    def _sync_position(self, x=None, y=None, width=None, height=None):
        """根据Overlay位置同步桌宠位置（共享逻辑）"""
        try:
            if self._pet_widget and self.enabled and x is not None and y is not None:
                self._position_next_to_overlay(x, y, width, height)
        except Exception as e:
            self.logger.error(f"桌宠插件: 同步Overlay位置失败: {e}")

    def _on_overlay_position_changed(self, position=None, x=None, y=None, width=None, height=None, **kwargs):
        """处理Overlay位置变化事件"""
        self._sync_position(x, y, width, height)

    def _on_overlay_moved(self, x=None, y=None, width=None, height=None, **kwargs):
        """处理Overlay被拖动事件"""
        self._sync_position(x, y, width, height)

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
            # 气泡也要同步
            if self._pet_widget._bubble:
                if enabled:
                    self._pet_widget._bubble.setWindowFlags(self._pet_widget._bubble.windowFlags() | Qt.WindowStaysOnTopHint)
                else:
                    self._pet_widget._bubble.setWindowFlags(self._pet_widget._bubble.windowFlags() & ~Qt.WindowStaysOnTopHint)
                if self._pet_widget._bubble.isVisible():
                    self._pet_widget._bubble.show()
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
    
    def _follow_overlay(self):
        """跟随Overlay移动"""
        try:
            if not self._pet_widget:
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
                # 强制让Overlay重新计算布局后再定位
                overlay_plugin = self.kernel.plugin_manager.get_plugin("overlay")
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
                
                # 重新定位（Overlay可能被拖动了）
                self._position_next_to_overlay()
        except Exception as e:
            self.logger.error(f"桌宠插件: 处理分类匹配事件失败: {e}")
    
    def set_pet_position(self, position: str):
        """设置桌宠位置"""
        # 验证配置值
        valid_positions = ["top", "bottom"]
        if position not in valid_positions:
            self.logger.error(f"桌宠插件: 无效的位置值 '{position}'，有效值: {valid_positions}")
            return
        
        # 保存配置
        self.set_plugin_config("position", position)
        
        # 重新定位
        self._position_next_to_overlay()


# 约定：PluginClass 变量指向插件类
PluginClass = DesktopPetPlugin
