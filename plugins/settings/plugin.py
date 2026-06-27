# -*- coding: utf-8 -*-
"""
Settings 插件 - 插件层
提供设置窗口，管理分类规则和插件启停
"""

from typing import List, Dict

from plugins.base import Plugin
from kernel.event_bus import Events


class SettingsPlugin(Plugin):
    """
    设置插件

    职责：
    - 监听 SHOW_SETTINGS 事件
    - 展示设置窗口（分类规则编辑 + 插件管理）
    - 保存修改后的配置
    - 通知 Rules 插件重新加载规则
    """

    name = "settings"
    version = "1.1.0"
    description = "设置插件，管理分类规则和插件"

    def on_load(self):
        """插件加载"""
        
        self.event_bus.on(Events.SHOW_SETTINGS, self._on_show_settings)
        self.logger.info("Settings 插件已加载")

    def on_unload(self):
        """插件卸载"""
        self.event_bus.off(Events.SHOW_SETTINGS, self._on_show_settings)
        self.logger.info("Settings 插件已卸载")

    def on_enable(self):
        """插件启用"""
        self.logger.info("Settings 插件已启用")

    def on_disable(self):
        """插件禁用"""
        self.logger.info("Settings 插件已禁用")

    def _get_plugins_info(self) -> List[dict]:
        """获取所有插件的信息"""
        plugins_info = []
        for plugin in self.get_all_plugins():
            plugins_info.append({
                "name": plugin.name,
                "description": getattr(plugin, "description", ""),
                "enabled": plugin.enabled
            })

        # 补充配置中存在但未加载的插件（被禁用的）
        loaded_names = {p["name"] for p in plugins_info}
        all_plugins_config = self.config.get("plugins", {})
        for name, enabled in all_plugins_config.items():
            if name not in loaded_names:
                plugins_info.append({
                    "name": name,
                    "description": "（未加载）",
                    "enabled": enabled
                })

        return plugins_info

    def _on_show_settings(self, **kwargs):
        """显示设置窗口"""
        from plugins.settings.dialog import SettingsDialog

        try:
            categories = self.config.get_categories()
            plugins_info = self._get_plugins_info()
            current_theme = self.config.get("theme", "dark")
            
            dialog = SettingsDialog(categories, plugins_info, current_theme,
                                   config=self.config, event_bus=self.event_bus)
            dialog.set_on_save(self._on_save)
            dialog.exec_()
        except Exception as e:
            self.logger.error(f"Settings 插件: 显示设置窗口失败: {e}")

    def _on_save(self, result: dict):
        """
        保存设置

        Args:
            result: {"categories": {...}, "plugins": {...} or None, "theme": "..."}
        """
        try:
            with self.config.batch_update():
                # 保存分类规则
                categories = result.get("categories")
                if categories:
                    self.config.set_categories(categories)
                    self.logger.info(f"Settings 插件: 分类配置已保存，{len(categories)} 个分类")

                    # 通知 Rules 插件重新加载（通过事件，不直接调用）
                    self.event_bus.emit(Events.RULES_RELOAD)

                # 保存插件配置
                plugins_config = result.get("plugins")
                self.logger.debug(f"Settings 插件: 收到插件配置: {plugins_config}")
                if plugins_config:
                    for name, enabled in plugins_config.items():
                        if enabled:
                            self.config.enable_plugin(name)
                        else:
                            self.config.disable_plugin(name)
                        self.logger.debug(f"Settings 插件: 插件 {name} -> {'启用' if enabled else '禁用'}")
                    self.logger.debug(f"Settings 插件: 插件配置已保存（下次启动生效）")
                    
                    # 验证保存结果
                    saved_plugins = self.config.get("plugins", {})
                    self.logger.debug(f"Settings 插件: 保存后的插件配置: {saved_plugins}")

                # 保存主题配置
                theme = result.get("theme")
                if theme:
                    self.config.set("theme", theme)
                    
                    # 立即应用主题（通过事件，不直接调用）
                    self.event_bus.emit(Events.OVERLAY_SET_THEME, theme=theme)
                    self.logger.info(f"Settings 插件: 主题已切换为 {theme}")

        except Exception as e:
            self.logger.error(f"Settings 插件: 保存配置失败: {e}")


# 约定：PluginClass 变量指向插件类
PluginClass = SettingsPlugin
