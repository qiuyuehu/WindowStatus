# -*- coding: utf-8 -*-
"""
Rules 插件 - 插件层
规则引擎，负责匹配窗口分类
"""

import fnmatch
from typing import Dict, List, Tuple, Optional

from plugins.base import Plugin
from kernel.event_bus import Events


class ClassificationResult:
    """分类结果"""
    
    def __init__(self, category: str, icon: str, color: tuple, matched_rule: str = ""):
        self.category = category
        self.icon = icon
        self.color = color
        self.matched_rule = matched_rule
    
    def __str__(self):
        return f"Classification(category='{self.category}', rule='{self.matched_rule}')"


class RulesPlugin(Plugin):
    """
    规则插件
    
    职责：
    - 监听 WINDOW_CHANGED 事件
    - 匹配窗口分类规则
    - 发送 CATEGORY_MATCHED 事件
    """
    
    name = "rules"
    version = "1.0.0"
    description = "规则插件，负责匹配窗口分类"
    
    def __init__(self, kernel):
        super().__init__(kernel)
        
        self._categories: Dict[str, dict] = {}
    
    def on_load(self):
        """插件加载"""
        self.logger = self.kernel.logger
        
        # 加载分类规则
        self._load_categories()
        
        # 注册事件监听
        self.event_bus.on(Events.WINDOW_CHANGED, self._on_window_changed)
        
        self.logger.info(f"Rules 插件已加载，{len(self._categories)} 个分类")
    
    def on_unload(self):
        """插件卸载"""
        # 注销事件监听
        self.event_bus.off(Events.WINDOW_CHANGED, self._on_window_changed)
        
        self.logger.info("Rules 插件已卸载")
    
    def on_enable(self):
        """插件启用"""
        self.logger.info("Rules 插件已启用")
    
    def on_disable(self):
        """插件禁用"""
        self.logger.info("Rules 插件已禁用")
    
    def _load_categories(self):
        """加载分类规则"""
        self._categories = self.config.get_categories()
    
    def _on_window_changed(self, **kwargs):
        """处理窗口切换事件"""
        if not self.enabled:
            return
        
        window_info = kwargs.get('window_info')
        if not window_info:
            return
        
        # 匹配分类
        result = self.classify(window_info.title, window_info.process_name)
        
        # 发送分类匹配事件
        self.event_bus.emit_to_main(
            Events.CATEGORY_MATCHED,
            category=result.category,
            icon=result.icon,
            color=result.color,
            title=window_info.title,
            process_name=window_info.process_name,
            matched_rule=result.matched_rule
        )
        
        self.logger.debug(f"Rules 插件: {window_info.title[:30]} -> {result.category}")
    
    def classify(self, title: str, process_name: str) -> ClassificationResult:
        """
        分类窗口
        
        Args:
            title: 窗口标题
            process_name: 进程名
        
        Returns:
            分类结果
        """
        # 遍历所有分类
        for category_name, category_info in self._categories.items():
            rules = category_info.get("rules", [])
            
            for rule in rules:
                if self._match_rule(rule, title, process_name):
                    return ClassificationResult(
                        category=category_name,
                        icon=category_info.get("icon", "💻"),
                        color=tuple(category_info.get("color", [149, 165, 166])),
                        matched_rule=f"{rule['type']}:{rule['pattern']}"
                    )
        
        # 默认分类
        return ClassificationResult(
            category="其他",
            icon="💻",
            color=(149, 165, 166)
        )
    
    def _match_rule(self, rule: dict, title: str, process_name: str) -> bool:
        """
        匹配单条规则
        
        Args:
            rule: 规则 {"type": "process"|"title", "pattern": "..."}
            title: 窗口标题
            process_name: 进程名
        
        Returns:
            是否匹配
        """
        rule_type = rule.get("type", "")
        pattern = rule.get("pattern", "")
        
        if rule_type == "process":
            # 进程名匹配（不区分大小写）
            return fnmatch.fnmatch(process_name.lower(), pattern.lower())
        
        elif rule_type == "title":
            # 窗口标题匹配（支持通配符）
            return fnmatch.fnmatch(title, pattern)
        
        return False
    
    def reload_rules(self):
        """重新加载规则"""
        self._load_categories()
        self.logger.info(f"Rules 插件: 规则已重新加载，{len(self._categories)} 个分类")
    
    def get_categories(self) -> Dict[str, dict]:
        """获取所有分类"""
        return self._categories.copy()
    
    def test_classify(self, title: str, process_name: str) -> ClassificationResult:
        """
        测试分类（用于调试）
        
        Args:
            title: 窗口标题
            process_name: 进程名
        
        Returns:
            分类结果
        """
        return self.classify(title, process_name)


# 约定：PluginClass 变量指向插件类
PluginClass = RulesPlugin
