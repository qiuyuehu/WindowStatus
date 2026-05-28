# -*- coding: utf-8 -*-
"""
插件基类 - 插件层
定义所有插件的统一接口和生命周期
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from kernel.core import Kernel
    from kernel.event_bus import EventBus
    from kernel.config import Config


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
    """
    
    # 插件元信息（子类必须覆盖）
    name: str = "base"
    version: str = "1.0.0"
    description: str = ""
    
    def __init__(self, kernel: 'Kernel'):
        """
        初始化插件
        
        Args:
            kernel: Kernel 实例，提供 event_bus、config 等核心服务
        """
        self.kernel = kernel
        self.event_bus: 'EventBus' = kernel.event_bus
        self.config: 'Config' = kernel.config
        self.enabled: bool = True
        self._loaded: bool = False
    
    def on_load(self):
        """
        插件加载时调用
        
        在此方法中：
        - 注册事件监听器
        - 初始化插件资源
        - 读取配置
        """
        pass
    
    def on_unload(self):
        """
        插件卸载时调用
        
        在此方法中：
        - 注销事件监听器
        - 释放插件资源
        - 保存状态
        """
        pass
    
    def on_enable(self):
        """
        插件启用时调用
        
        在此方法中：
        - 恢复插件功能
        - 重新注册事件监听器
        """
        pass
    
    def on_disable(self):
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
