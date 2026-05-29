# 插件开发指南

本指南将帮助你为 WindowStatus 开发自定义插件。

## 目录

- [快速开始](#快速开始)
- [插件生命周期](#插件生命周期)
- [事件系统](#事件系统)
- [配置管理](#配置管理)
- [最佳实践](#最佳实践)
- [示例插件](#示例插件)

---

## 快速开始

### 1. 创建插件目录

在 `plugins/` 目录下创建新的插件目录：

```
plugins/
└── my_plugin/
    ├── __init__.py
    └── plugin.py
```

### 2. 编写 __init__.py

```python
# -*- coding: utf-8 -*-
```

### 3. 编写 plugin.py

```python
# -*- coding: utf-8 -*-
"""
My Plugin - 插件层
"""

from plugins.base import Plugin
from kernel.event_bus import Events


class MyPlugin(Plugin):
    """我的自定义插件"""
    
    name = "my_plugin"
    version = "1.0.0"
    description = "这是一个自定义插件"
    
    def on_load(self):
        """插件加载"""
        self.logger = self.kernel.logger
        self.event_bus.on(Events.WINDOW_CHANGED, self._on_window_changed)
        self.logger.info("My Plugin 已加载")
    
    def on_unload(self):
        """插件卸载"""
        self.event_bus.off(Events.WINDOW_CHANGED, self._on_window_changed)
        self.logger.info("My Plugin 已卸载")
    
    def on_enable(self):
        """插件启用"""
        self.logger.info("My Plugin 已启用")
    
    def on_disable(self):
        """插件禁用"""
        self.logger.info("My Plugin 已禁用")
    
    def _on_window_changed(self, **kwargs):
        """处理窗口切换事件"""
        window_info = kwargs.get('window_info')
        if window_info:
            self.logger.debug(f"窗口切换: {window_info.title}")


# 约定：PluginClass 变量指向插件类
PluginClass = MyPlugin
```

### 4. 注册插件

在 `kernel/config.py` 的 `DEFAULT_CONFIG["plugins"]` 中添加：

```python
"plugins": {
    # ... 其他插件
    "my_plugin": True,  # True 表示默认启用
}
```

在 `kernel/plugin_manager.py` 的 `_discover_frozen_plugins` 中添加：

```python
plugin_modules = [
    # ... 其他插件
    'plugins.my_plugin.plugin',
]
```

---

## 插件生命周期

插件有 5 个生命周期方法：

### __init__(self, kernel)

构造函数，注入 Kernel 实例。

```python
def __init__(self, kernel):
    super().__init__(kernel)
    # 初始化插件属性
```

### on_load(self)

插件加载时调用，用于：
- 注册事件监听器
- 初始化资源
- 读取配置

```python
def on_load(self):
    self.logger = self.kernel.logger
    self.event_bus.on(Events.WINDOW_CHANGED, self._on_window_changed)
```

### on_enable(self)

插件启用时调用，用于：
- 恢复插件功能
- 显示 UI 元素

### on_disable(self)

插件禁用时调用，用于：
- 暂停插件功能
- 隐藏 UI 元素

### on_unload(self)

插件卸载时调用，用于：
- 注销事件监听器
- 释放资源
- 保存状态

---

## 事件系统

### 可用事件

| 事件名 | 触发时机 | 参数 |
|--------|----------|------|
| `WINDOW_CHANGED` | 窗口切换 | `window_info: WindowInfo` |
| `CATEGORY_MATCHED` | 分类匹配完成 | `category`, `icon`, `color`, `title`, `process_name` |
| `IDLE_DETECTED` | 用户空闲 | `idle_seconds: float` |
| `IDLE_RESUMED` | 用户回来 | 无 |
| `STATS_RECORDED` | 统计记录完成 | `window_title`, `process_name`, `category`, `duration` |
| `CONFIG_CHANGED` | 配置变更 | `key`, `value` |
| `PLUGIN_LOADED` | 插件加载 | `plugin_name`, `plugin_version` |
| `PLUGIN_UNLOADED` | 插件卸载 | `plugin_name` |
| `QUIT` | 应用退出 | 无 |

### 注册事件

```python
def on_load(self):
    self.event_bus.on(Events.WINDOW_CHANGED, self._on_window_changed)
```

### 注销事件

```python
def on_unload(self):
    self.event_bus.off(Events.WINDOW_CHANGED, self._on_window_changed)
```

### 发送事件

```python
# 同步发送（在当前线程执行）
self.event_bus.emit("custom.event", data="value")

# 发送到主线程（用于 GUI 插件）
self.event_bus.emit_to_main("custom.event", data="value")
```

---

## 配置管理

### 读取配置

```python
# 读取单个值
opacity = self.config.get("opacity", 0.9)

# 读取嵌套配置
interval = self.config.get("reminders.摸鱼.interval_minutes", 30)

# 读取分类配置
categories = self.config.get_categories()
```

### 写入配置

```python
# 写入单个值
self.config.set("opacity", 0.8)

# 批量更新（只保存一次）
with self.config.batch_update():
    self.config.set("opacity", 0.8)
    self.config.set("always_on_top", False)
```

---

## 最佳实践

### 1. 单一职责

每个插件只负责一个功能，不要把所有逻辑都塞进一个插件。

### 2. 事件驱动

插件之间通过事件通信，不要直接调用其他插件的方法。

### 3. 资源清理

在 `on_unload` 中释放所有资源，避免内存泄漏。

### 4. 错误处理

使用 try/except 包裹可能出错的代码，避免插件崩溃影响主程序。

```python
def _do_something(self):
    try:
        # 可能出错的代码
        pass
    except Exception as e:
        self.logger.error(f"操作失败: {e}")
```

### 5. 日志记录

使用 `self.logger` 记录日志，不要使用 print。

```python
self.logger.info("插件已加载")
self.logger.debug("调试信息")
self.logger.error("出错了")
```

---

## 示例插件

### 简单的计数器插件

```python
# -*- coding: utf-8 -*-
"""
Counter Plugin - 统计窗口切换次数
"""

from plugins.base import Plugin
from kernel.event_bus import Events


class CounterPlugin(Plugin):
    name = "counter"
    version = "1.0.0"
    description = "统计窗口切换次数"
    
    def __init__(self, kernel):
        super().__init__(kernel)
        self._count = 0
    
    def on_load(self):
        self.logger = self.kernel.logger
        self.event_bus.on(Events.WINDOW_CHANGED, self._on_window_changed)
        self.logger.info("Counter 插件已加载")
    
    def on_unload(self):
        self.event_bus.off(Events.WINDOW_CHANGED, self._on_window_changed)
        self.logger.info(f"Counter 插件已卸载，共切换 {self._count} 次")
    
    def on_enable(self):
        self.logger.info("Counter 插件已启用")
    
    def on_disable(self):
        self.logger.info("Counter 插件已禁用")
    
    def _on_window_changed(self, **kwargs):
        if self.enabled:
            self._count += 1
            self.logger.debug(f"窗口切换次数: {self._count}")
    
    def get_count(self) -> int:
        return self._count


PluginClass = CounterPlugin
```

---

## 常见问题

### Q: 插件加载失败怎么办？

A: 检查日志文件 `~/.WindowStatus/window_status.log`，查看具体错误信息。

### Q: 如何调试插件？

A: 使用 `self.logger.debug()` 输出调试信息，确保配置文件中日志级别为 DEBUG。

### Q: 插件之间如何通信？

A: 通过事件总线（EventBus）通信，不要直接引用其他插件。

### Q: 如何添加 UI？

A: 使用 PyQt5 创建窗口，在 `on_load` 中创建，在 `on_unload` 中关闭。

---

更多信息请参考源代码中的现有插件实现。
