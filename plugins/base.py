# -*- coding: utf-8 -*-
"""
插件基类 - 插件层
定义所有插件的统一接口和生命周期
"""

from typing import Dict, Any, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from kernel.core import Kernel
    from kernel.event_bus import EventBus
    from kernel.config import Config
    import logging


class Plugin:
    """
    插件基类
    
    所有插件必须继承此类，并实现生命周期方法。
    
    生命周期：
    1. __init__() - 构造函数，注入 Kernel
    2. on_load() - 插件加载时调用，注册事件监听
    3. on_enable() - 插件启用时调用
    4. on_disable() - 插件禁用时调用
    5. on_unload() - 插件卸载时调用，注销事件监听
    
    属性：
        name: 插件名称（子类必须覆盖）
        version: 插件版本（子类必须覆盖）
        description: 插件描述
        dependencies: 插件依赖列表（可选）
        kernel: Kernel 实例
        event_bus: EventBus 实例
        config: Config 实例
        enabled: 是否启用
        logger: 日志记录器
    
    配置：
        子类可以定义 DEFAULT_CONFIG 字典来声明默认配置。
        插件配置存储在 config.json 的 "<plugin_name>" 键下。
        使用 get_plugin_config() 获取合并后的配置。
    """
    
    # 插件元信息（子类必须覆盖）
    name: str = "base"
    version: str = "1.0.0"
    description: str = ""
    
    # 插件依赖（子类可以覆盖）
    dependencies: List[str] = []
    
    # 插件默认配置（子类可以覆盖）
    DEFAULT_CONFIG: Dict[str, Any] = {}
    
    def __init__(self, kernel: 'Kernel') -> None:
        """
        初始化插件
        
        Args:
            kernel: Kernel 实例，提供 event_bus、config 等核心服务
        """
        self.kernel: 'Kernel' = kernel
        self.event_bus: 'EventBus' = kernel.event_bus
        self.config: 'Config' = kernel.config
        self.logger: 'logging.Logger' = kernel.logger
        self.enabled: bool = True
        self._loaded: bool = False
    
    def get_plugin_config(self) -> Dict[str, Any]:
        """
        获取插件配置（合并默认配置）
        
        Returns:
            合并后的配置字典
        
        使用方法：
            config = self.get_plugin_config()
            opacity = config.get("opacity", 1.0)
        """
        user_config = self.config.get(self.name, {})
        return {**self.DEFAULT_CONFIG, **user_config}
    
    def set_plugin_config(self, key: str, value: Any) -> None:
        """
        设置插件配置项
        
        Args:
            key: 配置键
            value: 配置值
        """
        self.config.set(f"{self.name}.{key}", value)
    
    def on_load(self) -> None:
        """
        插件加载时调用
        
        在此方法中：
        - 注册事件监听器
        - 初始化插件资源
        - 读取配置
        """
        pass
    
    def on_unload(self) -> None:
        """
        插件卸载时调用
        
        在此方法中：
        - 注销事件监听器
        - 释放插件资源
        - 保存状态
        """
        pass
    
    def on_enable(self) -> None:
        """
        插件启用时调用
        
        在此方法中：
        - 恢复插件功能
        - 重新注册事件监听器
        """
        pass
    
    def on_disable(self) -> None:
        """
        插件禁用时调用
        
        在此方法中：
        - 暂停插件功能
        - 注销事件监听器（但不释放资源）
        """
        pass
    
    def __str__(self) -> str:
        return f"Plugin({self.name} v{self.version})"
    
    def __repr__(self) -> str:
        return self.__str__()
