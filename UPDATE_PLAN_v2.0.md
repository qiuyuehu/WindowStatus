# WindowStatus v3.0 更新方案

## 背景

v2.0 已完成**轻量重构**（方案一），实现了：
- 插件化架构（core/ + plugins/）
- 配置文件管理（~/.WindowStatus/config.json）
- 日志系统（~/.WindowStatus/window_status.log）
- 异常处理优化
- 插件可独立开关

当前架构仍然存在局限：
- 插件之间耦合度高，通过主应用直接调用
- 无法动态加载/卸载插件
- 没有事件总线，插件间通信依赖主应用中转
- 新增插件需要修改 main.py

**目标：** 演进到**完整插件化架构**（方案二），实现真正的插件系统。

---

## 架构设计

### 核心概念

```
┌─────────────────────────────────────────────────────────┐
│                    Application                          │
│  ┌─────────────────────────────────────────────────┐   │
│  │                  Kernel                         │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐     │   │
│  │  │ EventBus │  │ PluginMgr│  │ ConfigMgr│     │   │
│  │  └──────────┘  └──────────┘  └──────────┘     │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │                  Plugins                        │   │
│  │  ┌────────┐  ┌────────┐  ┌────────┐  ┌──────┐ │   │
│  │  │ Monitor│  │ Overlay│  │  Tray  │  │ Stats│ │   │
│  │  └────────┘  └────────┘  └────────┘  └──────┘ │   │
│  └─────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

### 事件总线（EventBus）

**关键设计：支持线程安全的事件分发**

```python
class EventBus:
    def __init__(self):
        self._handlers = {}
        self._main_thread = None  # 由 Kernel 设置为 QThread.currentThread()
    
    def emit(self, event, **kwargs):
        """同步发送，在调用线程执行"""
        if event not in self._handlers:
            return
        for handler in self._handlers[event]:
            handler(**kwargs)
    
    def emit_to_main(self, event, **kwargs):
        """发送到主线程执行（用于 GUI 插件）"""
        if self._main_thread and QThread.currentThread() != self._main_thread:
            QMetaObject.invokeMethod(
                self, "_emit_on_main", Qt.QueuedConnection,
                Q_ARG(str, event), Q_ARG(dict, kwargs)
            )
        else:
            self.emit(event, **kwargs)
```

**为什么需要 emit_to_main？**
- Monitor 插件的窗口钩子可能运行在非 GUI 线程
- Overlay 插件的 UI 更新**必须在主线程**执行
- 直接跨线程调用会导致随机崩溃

**事件类型定义：**

```python
class Events:
    WINDOW_CHANGED = "window.changed"    # 窗口切换
    CATEGORY_MATCHED = "category.matched" # 分类匹配
    STATS_RECORDED = "stats.recorded"     # 统计记录
    CONFIG_CHANGED = "config.changed"     # 配置变更
    PLUGIN_LOADED = "plugin.loaded"       # 插件加载
    PLUGIN_UNLOADED = "plugin.unloaded"   # 插件卸载
```

**使用方式：**

```python
# 监听窗口切换（在 Monitor 插件中）
event_bus.emit_to_main(Events.WINDOW_CHANGED, window_info=info, classification=result)

# 监听事件（在 Overlay 插件中）
event_bus.on(Events.WINDOW_CHANGED, self.handle_window_change)
```

**注意：v3.0 使用同步 EventBus，不做异步队列**
- 窗口切换是低频事件（每秒几次以内），同步调用完全够用
- 队列会增加调试难度（事件顺序、异常处理）
- v3.1/v4.0 有性能瓶颈时再加队列

### 插件接口（Plugin Interface）

所有插件实现统一接口：

```python
class Plugin:
    """插件基类"""
    
    name: str = "base"           # 插件名称
    version: str = "1.0.0"       # 插件版本
    enabled: bool = True         # 是否启用
    
    def __init__(self, kernel: 'Kernel'):
        self.kernel = kernel
        self.event_bus = kernel.event_bus
        self.config = kernel.config
    
    def on_load(self):
        """插件加载时调用"""
        pass
    
    def on_unload(self):
        """插件卸载时调用"""
        pass
    
    def on_enable(self):
        """插件启用时调用"""
        pass
    
    def on_disable(self):
        """插件禁用时调用"""
        pass
```

### 插件管理器（PluginManager）

**插件发现机制：约定优于配置**

```python
class PluginManager:
    """插件管理器"""
    
    def discover_plugins(self):
        """自动发现插件"""
        plugins_dir = os.path.join(os.path.dirname(__file__), '..', 'plugins')
        for item in os.listdir(plugins_dir):
            plugin_path = os.path.join(plugins_dir, item, 'plugin.py')
            if os.path.exists(plugin_path):
                # 动态导入
                spec = importlib.util.spec_from_file_location(f"plugins.{item}", plugin_path)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                # 约定：plugin.py 中必须定义 PluginClass 变量
                if hasattr(module, 'PluginClass'):
                    yield module.PluginClass
    
    def load_plugin(self, plugin_class: Type[Plugin]):
        """加载插件"""
        plugin = plugin_class(self.kernel)
        plugin.on_load()
        self.plugins[plugin.name] = plugin
    
    def unload_plugin(self, name: str):
        """卸载插件"""
        plugin = self.plugins[name]
        plugin.on_unload()
        del self.plugins[name]
    
    def enable_plugin(self, name: str):
        """启用插件"""
        plugin = self.plugins[name]
        plugin.enabled = True
        plugin.on_enable()
    
    def disable_plugin(self, name: str):
        """禁用插件"""
        plugin = self.plugins[name]
        plugin.enabled = False
        plugin.on_disable()
```

**插件目录结构约定：**

```
plugins/
├── monitor/
│   ├── __init__.py
│   └── plugin.py        # 必须定义 PluginClass = MonitorPlugin
├── overlay/
│   ├── __init__.py
│   └── plugin.py        # 必须定义 PluginClass = OverlayPlugin
└── ...
```

**配置文件中的插件启用列表：**

```json
{
  "enabled_plugins": ["monitor", "overlay", "tray", "stats"]
}
```

### Rules 插件设计

**职责分离：**

| 组件 | 职责 |
|------|------|
| Monitor 插件 | 只负责检测窗口切换，发出 `window.changed(process_name, window_title)` |
| Rules 插件 | 监听 `window.changed`，匹配规则，发出 `category.matched(category, icon, ...)` |
| Overlay / Stats 插件 | 监听 `category.matched`，不再关心规则逻辑 |

**收益：**
- 规则的热重载、多套规则切换变得容易
- Monitor 和 Overlay 进一步解耦

---

## 目录结构

```
WindowStatus/
├── kernel/
│   ├── __init__.py
│   ├── core.py              # Kernel 核心类
│   ├── event_bus.py         # 事件总线
│   ├── plugin_manager.py    # 插件管理器
│   └── config.py            # 配置管理（重构）
├── plugins/
│   ├── __init__.py
│   ├── base.py              # 插件基类
│   ├── monitor/
│   │   ├── __init__.py
│   │   └── plugin.py        # 窗口监控插件
│   ├── overlay/
│   │   ├── __init__.py
│   │   └── plugin.py        # 悬浮窗插件
│   ├── tray/
│   │   ├── __init__.py
│   │   └── plugin.py        # 系统托盘插件
│   ├── stats/
│   │   ├── __init__.py
│   │   └── plugin.py        # 统计插件
│   └── rules/
│       ├── __init__.py
│       └── plugin.py        # 规则触发插件（新增）
├── main.py                  # 程序入口（简化）
├── config.json              # 配置文件
├── build.py                 # 打包脚本
└── README.md
```

---

## 实施步骤

### 第一阶段：基础设施（1天）

**步骤 1：创建 Kernel 核心**
- 实现 EventBus（支持 emit + emit_to_main）
- 实现 PluginManager（加载/卸载/启用/禁用）
- 重构 Config 模块

**步骤 2：定义插件接口**
- 创建 Plugin 基类
- 定义标准生命周期方法
- 定义事件注册机制

**第一天结束时验证目标：**
- Monitor 插件发一个模拟事件 → Overlay 插件在主线程收到并打印日志

### 第二阶段：插件迁移（3-4天）

**步骤 3：迁移 Monitor 插件**
- 将 core/monitor.py 改造为插件
- 通过事件总线发送 WINDOW_CHANGED 事件
- 移除直接调用

**步骤 4：迁移 Overlay 插件**
- 监听 WINDOW_CHANGED 事件
- 更新悬浮窗显示
- 移除与主应用的耦合

**步骤 5：迁移 Tray 插件**
- 监听相关事件
- 通过事件总线发送用户操作
- 移除回调函数

**步骤 6：迁移 Stats 插件**
- 监听 WINDOW_CHANGED 事件
- 记录统计数据
- 发送 STATS_RECORDED 事件

### 第三阶段：增强功能（3-4天）

**步骤 7：实现 Rules 插件**
- 规则引擎独立为插件
- 支持自定义规则触发动作
- 事件驱动的规则匹配

**步骤 8：插件热加载**
- 运行时加载/卸载插件
- 插件状态持久化
- 插件配置独立管理

**步骤 9：插件发现机制**
- 扫描 plugins/ 子目录
- 自动加载 PluginClass
- 配置文件控制启用列表

### 第四阶段：测试和调试（1-2天）

- 线程相关 Bug 测试
- 边缘情况处理
- 性能测试

---

## 事件流设计

### 窗口切换流程

```
Monitor Plugin
    │
    ├─► emit_to_main(WINDOW_CHANGED, window_info)
    │
    ├─► Rules Plugin (监听)
    │   └─► 匹配规则，emit_to_main(CATEGORY_MATCHED, category, icon, ...)
    │
    ├─► Overlay Plugin (监听 CATEGORY_MATCHED)
    │   └─► 更新悬浮窗显示
    │
    ├─► Tray Plugin (监听 CATEGORY_MATCHED)
    │   └─► 更新托盘提示
    │
    └─► Stats Plugin (监听 CATEGORY_MATCHED)
        └─► 记录统计数据
            └─► emit(STATS_RECORDED, stats_data)
```

### 用户操作流程

```
Tray Plugin (用户点击)
    │
    ├─► emit(OPACITY_CHANGED, opacity)
    │   └─► Overlay Plugin (监听) → 更新透明度
    │
    ├─► emit(TOGGLE_TOP, enabled)
    │   └─► Overlay Plugin (监听) → 更新置顶状态
    │
    └─► emit(SHOW_STATS)
        └─► Stats Plugin (监听) → 显示统计窗口
```

---

## 对比 v2.0 vs v3.0

| 维度 | v2.0（当前） | v3.0（目标） |
|------|-------------|-------------|
| 插件通信 | 直接调用 | 事件总线 |
| 插件加载 | 静态导入 | 动态加载 |
| 耦合度 | 中等 | 低 |
| 可扩展性 | 好 | 优秀 |
| 新增插件 | 修改 main.py | 只需注册 |
| 插件复用 | 困难 | 容易 |
| 线程安全 | 未考虑 | 内置支持 |
| 开发复杂度 | 低 | 中等 |

---

## 兼容性考虑

1. **配置文件兼容**：v2.0 配置文件自动迁移到 v3.0 格式
2. **数据兼容**：SQLite 数据库结构不变
3. **API 兼容**：插件接口保持向后兼容
4. **打包兼容**：PyInstaller 打包方式不变

---

## 风险评估

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| 线程安全 | 高 | EventBus 内置 emit_to_main 支持 |
| 插件冲突 | 低 | 插件隔离，命名空间 |
| 调试困难 | 中 | 事件日志，插件状态监控 |
| 迁移成本 | 低 | 渐进式迁移，保留旧接口 |

---

## 时间估算

- 第一阶段（基础设施）：1 天
- 第二阶段（插件迁移）：3-4 天
- 第三阶段（增强功能）：3-4 天
- 第四阶段（测试调试）：1-2 天

**总计：8-12 天（按 10 天规划）**

---

## 决策建议

**v3.0 是否是当前最该做的事？**

| 情况 | 建议 |
|------|------|
| v2.0 刚发布不到一天，暂无用户反馈 | 先观察 1-2 周，收集真实需求 |
| 用户反馈集中在「加个 XXX 插件」「自定义触发动作」 | → 插件化是刚需，果断做 v3.0 |
| 用户反馈集中在「统计图表不好看」「某个游戏识别不准」 | → 先做功能迭代，v3.0 推迟 1 个月 |
| 做 v3.0 是为了架构洁癖 / 学习目的 | → 可以做的，但要接受时间成本和用户无感知 |

**核心原则：架构演进服务于业务需求，而不是反过来。**

---

## 如果决定开工，第一天的行动项

1. 实现 EventBus 类（支持同步 emit + emit_to_main）
2. 实现 Plugin 基类（定义生命周期方法）
3. 实现 PluginManager（只做加载/卸载/启用/禁用，暂不实现热加载的文件监听）
4. 改造 main.py 或新建 kernel/core.py，组装 Kernel
5. 写一个示例插件验证事件总线工作正常

**第一天结束时应该能跑通：**
Monitor 插件发一个模拟事件 → Overlay 插件在主线程收到并打印日志。

---

*方案由衾衾整理，参考资深原型师评审意见，等主人确认后开工。*
