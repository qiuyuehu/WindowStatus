# 事件系统文档

WindowStatus 使用事件驱动架构，插件之间通过事件总线（EventBus）进行通信。

## 目录

- [概述](#概述)
- [事件列表](#事件列表)
- [事件流图](#事件流图)
- [使用方法](#使用方法)
- [线程安全](#线程安全)
- [自定义事件](#自定义事件)

---

## 概述

事件系统是 WindowStatus 插件架构的核心。所有插件通过监听和发送事件来通信，彼此不直接依赖。

```
┌─────────┐    WINDOW_CHANGED    ┌─────────┐    CATEGORY_MATCHED    ┌─────────┐
│ Monitor │ ──────────────────→  │  Rules  │ ────────────────────→  │ Overlay │
└─────────┘                      └─────────┘                        └─────────┘
                                      │                                  │
                                      │                                  │
                                      ↓                                  ↓
                                 ┌─────────┐                        ┌─────────┐
                                 │  Stats  │                        │Reminders│
                                 └─────────┘                        └─────────┘
```

---

## 事件列表

### 窗口事件

| 事件名 | 常量 | 触发时机 | 参数 |
|--------|------|----------|------|
| `window.changed` | `Events.WINDOW_CHANGED` | 窗口切换 | `window_info: WindowInfo` |
| `idle.detected` | `Events.IDLE_DETECTED` | 用户空闲超过阈值 | `idle_seconds: float` |
| `idle.resumed` | `Events.IDLE_RESUMED` | 用户从空闲状态回来 | 无 |

### 分类事件

| 事件名 | 常量 | 触发时机 | 参数 |
|--------|------|----------|------|
| `category.matched` | `Events.CATEGORY_MATCHED` | 窗口分类匹配完成 | `category: str`, `icon: str`, `color: tuple`, `title: str`, `process_name: str`, `matched_rule: str` |

### 统计事件

| 事件名 | 常量 | 触发时机 | 参数 |
|--------|------|----------|------|
| `stats.recorded` | `Events.STATS_RECORDED` | 统计记录完成 | `window_title: str`, `process_name: str`, `category: str`, `duration: int` |

### 配置事件

| 事件名 | 常量 | 触发时机 | 参数 |
|--------|------|----------|------|
| `config.changed` | `Events.CONFIG_CHANGED` | 配置变更 | `key: str`, `value: Any` |

### 插件事件

| 事件名 | 常量 | 触发时机 | 参数 |
|--------|------|----------|------|
| `plugin.loaded` | `Events.PLUGIN_LOADED` | 插件加载完成 | `plugin_name: str`, `plugin_version: str` |
| `plugin.unloaded` | `Events.PLUGIN_UNLOADED` | 插件卸载完成 | `plugin_name: str` |
| `plugin.enabled` | `Events.PLUGIN_ENABLED` | 插件启用 | `plugin_name: str` |
| `plugin.disabled` | `Events.PLUGIN_DISABLED` | 插件禁用 | `plugin_name: str` |

### 用户操作事件

| 事件名 | 常量 | 触发时机 | 参数 |
|--------|------|----------|------|
| `opacity.changed` | `Events.OPACITY_CHANGED` | 透明度变更 | `opacity: float` |
| `toggle.top` | `Events.TOGGLE_TOP` | 切换置顶 | `enabled: bool` |
| `show.stats` | `Events.SHOW_STATS` | 显示统计窗口 | 无 |
| `show.settings` | `Events.SHOW_SETTINGS` | 显示设置窗口 | 无 |
| `show.about` | `Events.SHOW_ABOUT` | 显示关于窗口 | 无 |
| `quit` | `Events.QUIT` | 退出应用 | 无 |

---

## 事件流图

### 窗口监控流程

```
用户切换窗口
    ↓
Monitor 检测到变化
    ↓
emit(WINDOW_CHANGED, window_info=...)
    ↓
Rules 接收事件
    ↓
匹配分类规则
    ↓
emit(CATEGORY_MATCHED, category=..., icon=..., ...)
    ↓
┌───────────────────────────────────────┐
│                                       │
↓                                       ↓
Stats 记录统计                      Overlay 更新显示
                                Reminders 检查提醒
                                Desktop Pet 更新状态
```

### 空闲检测流程

```
用户停止操作 60 秒
    ↓
Monitor 检测到空闲
    ↓
emit(IDLE_DETECTED, idle_seconds=...)
    ↓
┌───────────────────┐
│                   │
↓                   ↓
Stats 暂停统计  Reminders 暂停计时

用户继续操作
    ↓
Monitor 检测到活动
    ↓
emit(IDLE_RESUMED)
    ↓
┌───────────────────┐
│                   │
↓                   ↓
Stats 恢复统计  Reminders 重置计时
```

---

## 使用方法

### 注册事件监听

```python
def on_load(self):
    # 注册事件监听
    self.event_bus.on(Events.WINDOW_CHANGED, self._on_window_changed)

def _on_window_changed(self, **kwargs):
    """处理窗口切换事件"""
    window_info = kwargs.get('window_info')
    if window_info:
        self.logger.debug(f"窗口切换: {window_info.title}")
```

### 注销事件监听

```python
def on_unload(self):
    # 注销事件监听
    self.event_bus.off(Events.WINDOW_CHANGED, self._on_window_changed)
```

### 发送事件

```python
# 同步发送（在当前线程执行）
self.event_bus.emit(
    "custom.event",
    key1="value1",
    key2="value2"
)

# 发送到主线程（用于 GUI 插件，确保线程安全）
self.event_bus.emit_to_main(
    "custom.event",
    key1="value1",
    key2="value2"
)
```

---

## 线程安全

### 问题

PyQt5 的 UI 操作必须在主线程执行。如果从后台线程直接更新 UI，会导致程序崩溃。

### 解决方案

使用 `emit_to_main()` 而不是 `emit()`：

```python
# ❌ 错误：可能在后台线程执行
self.event_bus.emit(Events.CATEGORY_MATCHED, category="游戏")

# ✅ 正确：确保在主线程执行
self.event_bus.emit_to_main(Events.CATEGORY_MATCHED, category="游戏")
```

### 规则

- **UI 插件**（overlay, tray, stats dialog）：使用 `emit_to_main()`
- **非 UI 插件**（monitor, rules, stats）：可以使用 `emit()`

---

## 自定义事件

### 定义事件名

在 `kernel/event_bus.py` 的 `Events` 类中添加：

```python
class Events:
    # ... 现有事件
    
    # 自定义事件
    MY_CUSTOM_EVENT = "my.custom.event"
```

### 发送自定义事件

```python
self.event_bus.emit(
    Events.MY_CUSTOM_EVENT,
    param1="value1",
    param2=42
)
```

### 监听自定义事件

```python
def on_load(self):
    self.event_bus.on(Events.MY_CUSTOM_EVENT, self._on_my_event)

def _on_my_event(self, **kwargs):
    param1 = kwargs.get('param1')
    param2 = kwargs.get('param2')
    # 处理事件
```

---

## 最佳实践

### 1. 使用常量

始终使用 `Events` 类中的常量，不要硬编码字符串：

```python
# ❌ 错误
self.event_bus.on("window.changed", self._handler)

# ✅ 正确
self.event_bus.on(Events.WINDOW_CHANGED, self._handler)
```

### 2. 使用 **kwargs

事件处理函数应该使用 `**kwargs` 接收参数，这样即使参数变化也不会崩溃：

```python
def _on_window_changed(self, **kwargs):
    window_info = kwargs.get('window_info')
    if window_info:
        # 处理事件
        pass
```

### 3. 检查 enabled 状态

在事件处理函数中检查插件是否启用：

```python
def _on_window_changed(self, **kwargs):
    if not self.enabled:
        return
    # 处理事件
```

### 4. 避免循环监听

不要让插件监听自己发送的事件，否则会导致无限循环。

---

## 调试技巧

### 查看事件日志

在配置文件中设置日志级别为 DEBUG：

```json
{
    "logging": {
        "level": "DEBUG"
    }
}
```

### 监听所有事件

```python
def on_load(self):
    # 监听所有事件用于调试
    for attr in dir(Events):
        if not attr.startswith('_'):
            event = getattr(Events, attr)
            self.event_bus.on(event, lambda **kw: self.logger.debug(f"事件: {attr}, 参数: {kw}"))
```

---

更多信息请参考 `kernel/event_bus.py` 源代码。
