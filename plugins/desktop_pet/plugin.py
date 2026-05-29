# -*- coding: utf-8 -*-
"""
桌宠插件 - 插件层
显示桌宠和状态气泡，替代原悬浮窗
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
    - 显示状态气泡（替代原悬浮窗）
    - 处理拖拽、透明度等
    """
    
    name = "desktop_pet"
    version = "3.0.0"
    description = "桌宠插件，显示桌宠和状态气泡"
    dependencies = []  # 不再依赖 overlay
    
    DEFAULT_CONFIG = {
        "enabled": True,        # 始终启用，不可禁用
        "position": "top",      # 桌宠在屏幕上方或下方
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
        self.event_bus.on(Events.TOGGLE_TOP, self._on_toggle_top)
        self.event_bus.on(Events.OVERLAY_SHOW, self._on_overlay_show)
        self.event_bus.on(Events.OVERLAY_HIDE, self._on_overlay_hide)
        self.event_bus.on(Events.OPACITY_CHANGED, self._on_opacity_changed)
        self.event_bus.on(Events.OVERLAY_DATA_CHANGED, self._on_overlay_data_changed)
        
        self.logger.info("桌宠插件已加载")
    
    def on_unload(self):
        """插件卸载"""
        self.event_bus.off(Events.CATEGORY_MATCHED, self._on_category_matched)
        self.event_bus.off(Events.TOGGLE_TOP, self._on_toggle_top)
        self.event_bus.off(Events.OVERLAY_SHOW, self._on_overlay_show)
        self.event_bus.off(Events.OVERLAY_HIDE, self._on_overlay_hide)
        self.event_bus.off(Events.OPACITY_CHANGED, self._on_opacity_changed)
        self.event_bus.off(Events.OVERLAY_DATA_CHANGED, self._on_overlay_data_changed)
        
        self._follow_timer.stop()
        
        if self._pet_widget:
            self._pet_widget.hide()
            self._pet_widget = None
        
        self.logger.info("桌宠插件已卸载")
    
    def on_enable(self):
        """插件启用（始终启用）"""
        # 延迟创建桌宠
        self._follow_timer.start(500)
        QTimer.singleShot(800, self._create_pet)
        self.logger.info("桌宠插件已启用")
    
    def on_disable(self):
        """插件禁用（不允许禁用）"""
        # 不执行任何操作，保持启用状态
        self.logger.info("桌宠插件不允许禁用")
    
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
            
            # 定位到屏幕右下角
            self._initialized = False
            self._position_pet()
            self._pet_widget.show()
            
            # 记录初始状态
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
    
    def _position_pet(self):
        """将桌宠定位到屏幕右下角"""
        if not self._pet_widget:
            return
        
        # 获取屏幕可用区域
        from PyQt5.QtWidgets import QDesktopWidget
        screen = QDesktopWidget().availableGeometry()
        screen_right = screen.right()
        screen_bottom = screen.bottom()
        
        # 获取配置
        config = self.get_plugin_config()
        position = config.get("position", "top")
        
        # 计算桌宠位置（屏幕右下角）
        pet_size = self._pet_widget.size()
        pet_w = pet_size.width()
        pet_h = pet_size.height()
        
        # 水平靠右，留出边距
        x = screen_right - pet_w - 20
        
        if position == "top":
            # 靠上
            y = screen.top() + 20
        else:  # bottom
            # 靠下
            y = screen_bottom - pet_h - 20
        
        self._pet_widget.move(x, y)
    
    def _follow_overlay(self):
        """跟随Overlay移动（保留兼容性）"""
        try:
            if not self._pet_widget:
                return
            # 首次定位完成前，即使不可见也要尝试定位
            if not self._initialized:
                self._position_pet()
                return
            if not self._pet_widget.isVisible():
                return
            # 不再跟随Overlay，桌宠独立定位
        except Exception as e:
            self.logger.error(f"桌宠插件: 跟随移动失败: {e}")
    
    def _delayed_init(self):
        """延迟初始化：重新定位桌宠"""
        try:
            if self._pet_widget and self.enabled:
                self._position_pet()
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
                
                # 更新气泡数据
                self._pet_widget.update_bubble(icon, title, process_name, category)
                
                self.logger.info(f"桌宠插件: 更新气泡数据: icon={icon}, category={category}, title={title}, process={process_name}")
        except Exception as e:
            self.logger.error(f"桌宠插件: 处理分类匹配事件失败: {e}")
    
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
            if self._pet_widget._status_bubble:
                if enabled:
                    self._pet_widget._status_bubble.setWindowFlags(self._pet_widget._status_bubble.windowFlags() | Qt.WindowStaysOnTopHint)
                else:
                    self._pet_widget._status_bubble.setWindowFlags(self._pet_widget._status_bubble.windowFlags() & ~Qt.WindowStaysOnTopHint)
                if self._pet_widget._status_bubble.isVisible():
                    self._pet_widget._status_bubble.show()
        except Exception as e:
            self.logger.error(f"桌宠插件: 处理置顶切换事件失败: {e}")

    def _on_overlay_show(self, **kwargs):
        """处理显示事件，显示桌宠和气泡"""
        try:
            if self._pet_widget and self.enabled:
                self._pet_widget.show()
                if self._pet_widget._status_bubble:
                    self._pet_widget._status_bubble.show()
        except Exception as e:
            self.logger.error(f"桌宠插件: 处理显示事件失败: {e}")

    def _on_overlay_hide(self, **kwargs):
        """处理隐藏事件，隐藏桌宠和气泡"""
        try:
            if self._pet_widget:
                self._pet_widget.hide()
                if self._pet_widget._status_bubble:
                    self._pet_widget._status_bubble.hide()
        except Exception as e:
            self.logger.error(f"桌宠插件: 处理隐藏事件失败: {e}")
    
    def _on_opacity_changed(self, opacity: float, **kwargs):
        """处理透明度变更事件，同步气泡透明度"""
        try:
            if self._pet_widget and self._pet_widget._status_bubble and self.enabled:
                self._pet_widget._status_bubble.set_opacity(opacity)
        except Exception as e:
            self.logger.error(f"桌宠插件: 处理透明度变更失败: {e}")
    
    def _on_overlay_data_changed(self, icon: str, category: str, title: str, process_name: str, **kwargs):
        """处理Overlay数据变更事件，更新气泡"""
        try:
            if self._pet_widget and self.enabled:
                self._pet_widget.update_bubble(icon, title, process_name, category)
                self.logger.info(f"桌宠插件: 收到Overlay数据变更: icon={icon}, category={category}, title={title}, process={process_name}")
        except Exception as e:
            self.logger.error(f"桌宠插件: 处理Overlay数据变更失败: {e}")
    
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
        self._position_pet()


# 约定：PluginClass 变量指向插件类
PluginClass = DesktopPetPlugin
