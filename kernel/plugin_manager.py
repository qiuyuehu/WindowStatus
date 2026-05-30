# -*- coding: utf-8 -*-
"""
插件管理器 - 核心层
负责插件的发现、加载、卸载、启用、禁用
"""

import os
import sys
import traceback
import importlib
import importlib.util
from typing import Dict, List, Type, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from kernel.core import Kernel
    from plugins.base import Plugin


class PluginManager:
    """
    插件管理器
    
    支持：
    - 自动发现 plugins/ 目录下的插件
    - 动态加载/卸载插件
    - 启用/禁用插件
    - 插件状态查询
    """
    
    def __init__(self, kernel: 'Kernel'):
        self.kernel = kernel
        self._plugins: Dict[str, 'Plugin'] = {}
        self._plugin_classes: Dict[str, Type['Plugin']] = {}
        
        # 检测是否在 PyInstaller 环境中
        self._is_frozen = getattr(sys, 'frozen', False)
        
        # 设置插件目录路径
        if self._is_frozen:
            # PyInstaller 打包后，文件在 _MEIPASS 目录
            self._plugins_dir = os.path.join(sys._MEIPASS, 'plugins')
        else:
            # 开发环境
            self._plugins_dir = os.path.join(os.path.dirname(__file__), '..', 'plugins')
    
    def _log(self, level: str, msg: str):
        """统一日志输出，优先用 logger，fallback 到 print"""
        logger = getattr(self.kernel, 'logger', None)
        if logger:
            getattr(logger, level)(msg)
        else:
            print(f"[{level.upper()}] {msg}")
    
    def discover_plugins(self) -> List[Type['Plugin']]:
        """
        自动发现插件
        
        扫描 plugins/ 目录下的子目录，每个子目录必须包含 plugin.py，
        plugin.py 中必须定义 PluginClass 变量（指向插件类）。
        
        Returns:
            发现的插件类列表
        """
        plugin_classes = []
        
        # PyInstaller 打包后，使用直接导入方式
        if self._is_frozen:
            return self._discover_frozen_plugins()
        
        # 开发环境，使用文件发现方式
        return self._discover_dev_plugins()
    
    def _discover_frozen_plugins(self) -> List[Type['Plugin']]:
        """
        PyInstaller 打包后发现插件
        
        优先从 sys.modules 获取（hiddenimports 已预加载），
        失败则尝试 importlib 导入。
        """
        plugin_classes = []
        
        # 预定义的插件模块列表
        plugin_modules = [
            'plugins.monitor.plugin',
            'plugins.overlay.plugin',
            'plugins.tray.plugin',
            'plugins.stats.plugin',
            'plugins.rules.plugin',
            'plugins.about.plugin',
            'plugins.settings.plugin',
            'plugins.reminders.plugin',
            'plugins.desktop_pet.plugin',
        ]
        
        # 确保 plugins 包可用
        if 'plugins' not in sys.modules:
            self._log('warning', 'PluginManager: plugins 包不在 sys.modules 中')
        
        for module_name in plugin_modules:
            module = None
            
            # 方式1: 直接从 sys.modules 获取（hiddenimports 预加载的）
            if module_name in sys.modules:
                module = sys.modules[module_name]
                self._log('debug', f'PluginManager: 从 sys.modules 获取 [{module_name}]')
            
            # 方式2: importlib 导入
            if module is None:
                try:
                    module = importlib.import_module(module_name)
                    self._log('debug', f'PluginManager: importlib 导入成功 [{module_name}]')
                except Exception as e:
                    self._log('error', f'PluginManager: 导入失败 [{module_name}]: {e}')
                    self._log('error', f'PluginManager: {traceback.format_exc()}')
                    continue
            
            # 获取 PluginClass
            if module is not None:
                if hasattr(module, 'PluginClass'):
                    plugin_class = getattr(module, 'PluginClass')
                    plugin_classes.append(plugin_class)
                    self._plugin_classes[plugin_class.name] = plugin_class
                    self._log('info', f'PluginManager: 发现插件 [{plugin_class.name}]')
                else:
                    self._log('warning', f'PluginManager: 模块 [{module_name}] 没有 PluginClass')
        
        return plugin_classes
    
    def _discover_dev_plugins(self) -> List[Type['Plugin']]:
        """
        开发环境发现插件
        
        扫描 plugins/ 目录下的子目录
        """
        plugin_classes = []
        
        if not os.path.exists(self._plugins_dir):
            self._log('warning', f'PluginManager: 插件目录不存在 [{self._plugins_dir}]')
            return plugin_classes
        
        for item in os.listdir(self._plugins_dir):
            # 跳过特殊文件和目录
            if item.startswith('_') or item.startswith('.'):
                continue
            
            plugin_dir = os.path.join(self._plugins_dir, item)
            if not os.path.isdir(plugin_dir):
                continue
            
            plugin_path = os.path.join(plugin_dir, 'plugin.py')
            if not os.path.exists(plugin_path):
                continue
            
            try:
                # 动态导入
                module_name = f"plugins.{item}.plugin"
                spec = importlib.util.spec_from_file_location(module_name, plugin_path)
                if spec is None or spec.loader is None:
                    continue
                
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                # 约定：plugin.py 中必须定义 PluginClass 变量
                if hasattr(module, 'PluginClass'):
                    plugin_class = getattr(module, 'PluginClass')
                    plugin_classes.append(plugin_class)
                    self._plugin_classes[plugin_class.name] = plugin_class
                    
            except Exception as e:
                self._log('error', f'PluginManager: 发现插件失败 [{item}]: {e}')
        
        return plugin_classes
    
    def load_plugin(self, plugin_class: Type['Plugin']) -> Optional['Plugin']:
        """
        加载插件
        
        Args:
            plugin_class: 插件类
            
        Returns:
            加载的插件实例，失败返回 None
        """
        try:
            # 检查是否已加载
            if plugin_class.name in self._plugins:
                self._log('info', f'PluginManager: 插件已加载 [{plugin_class.name}]')
                return self._plugins[plugin_class.name]
            
            # 创建插件实例
            plugin = plugin_class(self.kernel)
            
            # 调用加载生命周期
            plugin.on_load()
            plugin._loaded = True
            
            # 注册到管理器
            self._plugins[plugin.name] = plugin
            
            # 发送插件加载事件
            self.kernel.event_bus.emit(
                "plugin.loaded",
                plugin_name=plugin.name,
                plugin_version=plugin.version
            )
            
            self._log('info', f'PluginManager: 插件已加载 [{plugin.name} v{plugin.version}]')
            return plugin
            
        except Exception as e:
            self._log('error', f'PluginManager: 加载插件失败 [{plugin_class.name}]: {e}')
            self._log('error', f'PluginManager: {traceback.format_exc()}')
            return None
    
    def unload_plugin(self, name: str) -> bool:
        """
        卸载插件
        
        Args:
            name: 插件名称
            
        Returns:
            是否成功卸载
        """
        plugin = self._plugins.get(name)
        if plugin is None:
            self._log('warning', f'PluginManager: 插件未找到 [{name}]')
            return False
        
        try:
            # 先禁用
            if plugin.enabled:
                self.disable_plugin(name)
            
            # 调用卸载生命周期
            plugin.on_unload()
            plugin._loaded = False
            
            # 从管理器移除
            del self._plugins[name]
            
            # 发送插件卸载事件
            self.kernel.event_bus.emit(
                "plugin.unloaded",
                plugin_name=name
            )
            
            self._log('info', f'PluginManager: 插件已卸载 [{name}]')
            return True
            
        except Exception as e:
            self._log('error', f'PluginManager: 卸载插件失败 [{name}]: {e}')
            return False
    
    def enable_plugin(self, name: str) -> bool:
        """
        启用插件
        
        Args:
            name: 插件名称
            
        Returns:
            是否成功启用
        """
        plugin = self._plugins.get(name)
        if plugin is None:
            self._log('warning', f'PluginManager: 插件未找到 [{name}]')
            return False
        
        if plugin.enabled:
            return True
        
        try:
            plugin.enabled = True
            plugin.on_enable()
            
            # 发送插件启用事件
            self.kernel.event_bus.emit(
                "plugin.enabled",
                plugin_name=name
            )
            
            self._log('info', f'PluginManager: 插件已启用 [{name}]')
            return True
            
        except Exception as e:
            self._log('error', f'PluginManager: 启用插件失败 [{name}]: {e}')
            return False
    
    def disable_plugin(self, name: str) -> bool:
        """
        禁用插件
        
        Args:
            name: 插件名称
            
        Returns:
            是否成功禁用
        """
        plugin = self._plugins.get(name)
        if plugin is None:
            self._log('warning', f'PluginManager: 插件未找到 [{name}]')
            return False
        
        if not plugin.enabled:
            return True
        
        try:
            plugin.enabled = False
            plugin.on_disable()
            
            # 发送插件禁用事件
            self.kernel.event_bus.emit(
                "plugin.disabled",
                plugin_name=name
            )
            
            self._log('info', f'PluginManager: 插件已禁用 [{name}]')
            return True
            
        except Exception as e:
            self._log('error', f'PluginManager: 禁用插件失败 [{name}]: {e}')
            return False
    
    def get_plugin(self, name: str) -> Optional['Plugin']:
        """获取插件实例"""
        return self._plugins.get(name)
    
    def get_all_plugins(self) -> List['Plugin']:
        """获取所有已加载的插件"""
        return list(self._plugins.values())
    
    def get_enabled_plugins(self) -> List['Plugin']:
        """获取所有已启用的插件"""
        return [p for p in self._plugins.values() if p.enabled]
    
    def is_loaded(self, name: str) -> bool:
        """检查插件是否已加载"""
        return name in self._plugins
    
    def is_enabled(self, name: str) -> bool:
        """检查插件是否已启用"""
        plugin = self._plugins.get(name)
        return plugin is not None and plugin.enabled
    
    def load_all_discovered(self, enabled_plugins: Optional[List[str]] = None):
        """
        加载所有发现的插件
        
        Args:
            enabled_plugins: 启用的插件名称列表，None 表示全部启用
        """
        # 先发现插件
        self.discover_plugins()
        
        # 按依赖顺序排序插件
        sorted_plugins = self._sort_plugins_by_dependency()
        
        # 加载插件
        for name in sorted_plugins:
            plugin_class = self._plugin_classes.get(name)
            if plugin_class is None:
                continue
            
            # 检查是否在启用列表中
            if enabled_plugins is not None and name not in enabled_plugins:
                continue
            
            # 检查依赖是否已加载
            if not self._check_dependencies(plugin_class):
                self._log('warning', f'PluginManager: 插件 [{name}] 的依赖未满足，跳过加载')
                continue
            
            plugin = self.load_plugin(plugin_class)
            
            # 加载成功后，调用 on_enable
            if plugin is not None:
                plugin.enabled = True
                try:
                    plugin.on_enable()
                except Exception as e:
                    self._log('error', f'PluginManager: 启用插件失败 [{name}]: {e}')
    
    def _sort_plugins_by_dependency(self) -> List[str]:
        """按依赖顺序排序插件（拓扑排序）"""
        # 构建依赖图
        graph = {}
        for name, plugin_class in self._plugin_classes.items():
            dependencies = getattr(plugin_class, 'dependencies', [])
            graph[name] = dependencies
        
        # 拓扑排序
        sorted_plugins = []
        visited = set()
        visiting = set()
        
        def dfs(node):
            if node in visiting:
                # 循环依赖
                self._log('error', f'PluginManager: 检测到循环依赖 [{node}]')
                return
            if node in visited:
                return
            
            visiting.add(node)
            for dep in graph.get(node, []):
                if dep in self._plugin_classes:
                    dfs(dep)
            visiting.remove(node)
            visited.add(node)
            sorted_plugins.append(node)
        
        for name in graph:
            dfs(name)
        
        return sorted_plugins
    
    def _check_dependencies(self, plugin_class) -> bool:
        """检查插件的依赖是否已加载"""
        dependencies = getattr(plugin_class, 'dependencies', [])
        for dep in dependencies:
            if dep not in self._plugins:
                return False
        return True
    
    def unload_all(self):
        """卸载所有插件"""
        # 先清空所有事件监听，避免卸载过程中事件到达已卸载的 handler
        self.kernel.event_bus.off_all_handlers()
        
        # 再逐个卸载（禁用 + on_unload）
        plugin_names = list(self._plugins.keys())
        for name in plugin_names:
            self.unload_plugin(name)
