# WindowStatus 代码约束

> 自动检查：checks.py 会验证以下约束，失败则阻塞测试运行。

---

## 1. PyQt5 约束

### 1.1 Widget 创建时机
- **约束**：`on_enable()` 时必须立即创建 Widget，不能延迟到事件触发
- **原因**：事件触发顺序问题（P14），延迟创建会导致 widget 未初始化就收到事件
- **检查**：`on_enable()` 方法中必须有 `self.xxx_widget =` 或 `self.xxx = ` 的 widget 创建

### 1.2 Qt.Tool 使用限制
- **约束**：需要拖拽的 Widget 不能加 `Qt.Tool` flag
- **原因**：Win11 上 Qt.Tool 导致鼠标事件失效（P1）
- **检查**：grep `Qt.Tool` + `mousePressEvent` 同文件 → 违规

### 1.3 QDesktopWidget 禁用
- **约束**：禁止使用 `QDesktopWidget`，改用 `QApplication.primaryScreen().geometry()`
- **原因**：QDesktopWidget 已废弃（P13）
- **检查**：grep `QDesktopWidget` → 违规

### 1.4 透明背景谨慎使用
- **约束**：`WA_TranslucentBackground` 必须配合 `Qt.FramelessWindowHint` 使用
- **原因**：单独使用会让 widget 完全不可见
- **检查**：grep `WA_TranslucentBackground` 附近无 `FramelessWindowHint` → 警告

---

## 2. 插件架构约束

### 2.1 EventBus 通信
- **约束**：插件之间禁止直接调用，只通过 EventBus 通信
- **例外**：`get_plugin(name)` 获取其他插件实例（受限接口）
- **检查**：grep `get_plugin(` 调用后直接访问非公开方法 → 警告

### 2.2 单一职责
- **约束**：一个 UI 元素只由一个插件负责
- **原因**：双气泡 bug（P8）
- **检查**：手动审查（难以自动化）

### 2.3 事件处理器 kwargs
- **约束**：所有 EventBus handler 必须有 `**kwargs` 参数
- **原因**：emit() 传递 kwargs 而 handler 不接收会 TypeError，被 try-except 静默吞没
- **检查**：grep `def on_` 或 `def _on_` 函数签名无 `**kwargs` → 违规

---

## 3. 线程安全约束

### 3.1 Config 访问
- **约束**：所有 Config 公开方法必须使用 `threading.RLock()`
- **原因**：多线程并发读写导致数据不一致（v3.3.1 修复）
- **检查**：Config 类的公开方法无 `with self._lock` → 违规

### 3.2 EventBus 线程安全
- **约束**：EventBus 公开方法必须使用 `threading.Lock()`
- **检查**：EventBus 类的公开方法无 `with self._lock` → 违规

---

## 4. 路径处理约束

### 4.1 打包路径
- **约束**：资源文件路径必须区分打包/开发模式
- **打包后**：`sys._MEIPASS`
- **开发模式**：`os.path.dirname(__file__)`
- **检查**：grep `os.path.dirname(__file__)` 在非 `if getattr(sys, 'frozen', False)` 上下文中 → 警告

### 4.2 用户数据路径
- **约束**：用户数据（config, db, log）必须用 `os.path.expanduser('~/.WindowStatus/')`
- **禁止**：`os.path.dirname(sys.executable)` 用于用户数据
- **检查**：grep `sys.executable` 用于数据路径 → 违规

---

## 5. 异常处理约束

### 5.1 禁止空 catch
- **约束**：`except` 块必须有日志或注释说明为什么忽略
- **检查**：grep `except` 后只有 `pass` → 违规

### 5.2 QTimer 回调异常
- **约束**：所有 QTimer.singleShot / QTimer.timeout 回调必须加 `try/except`
- **原因**：Qt 事件循环会静默吞掉异常，游戏/功能卡住无报错
- **检查**：grep `.singleShot(` 或 `.timeout.connect(` 附近无 `try` → 警告

---

## 6. 测试约束

### 6.1 测试文件命名
- **约束**：测试文件必须 `test_` 前缀，放在 `tests/` 目录
- **检查**：文件名不符合 → 跳过

### 6.2 测试必须独立
- **约束**：每个测试必须能独立运行，不依赖其他测试的执行顺序
- **检查**：手动审查

---

## 白名单

以下文件跳过部分历史约束检查：
- `plugins/stats/dialog.py` — 历史代码，逐步重构
- `plugins/settings/dialog.py` — 历史代码，逐步重构
- `plugins/desktop_pet/widget.py` — 特例：Qt.Tool 用于桌宠，鼠标事件通过长按检测处理（不是直接拖拽）

---

*基于 SPEC.md v3.4.0 踩坑记录整理*
*更新时间：2026-06-27*
