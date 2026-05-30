# 更新日志

## v3.3.2 (2026-05-30)

### 新功能
- **桌宠拖拽**：长按桌宠 200ms 进入拖拽模式，拖拽时同步气泡位置，支持屏幕边界检测
- **进程内重启**：重启功能改为进程内重载（Events.RESTART），不再使用 os.execv/subprocess

### 优化
- **长按延迟**：桌宠长按触发时间从 300ms 降低到 200ms，手感更流畅
- **状态保护**：长按/拖拽中禁止分类事件切换桌宠状态，避免状态闪烁

### 删除
- **气泡拖拽**：删除气泡拖拽功能及相关代码（OVERLAY_MOVED 事件、鼠标事件、长按定时器等）
- **临时测试脚本**：删除 test_v3.py、test_stats_data.py

### 文件变更
```
plugins/desktop_pet/widget.py   # 桌宠拖拽（长按、鼠标事件、边界检测）
plugins/desktop_pet/plugin.py   # 拖拽回调、反向定位气泡
plugins/overlay/plugin.py       # 删除气泡拖拽相关代码
kernel/event_bus.py             # 新增 RESTART 事件，删除 OVERLAY_MOVED
kernel/config.py                # 新增 reload() 方法
main.py                         # 进程内重启逻辑
plugins/tray/plugin.py          # 重启改为发 RESTART 事件
```

---

## v3.3.1 (2026-05-30)

### 优化
- **气泡+桌宠整体边界检测**：拖拽气泡时，气泡和桌宠作为整体受屏幕边界约束，不再各自独立限制导致分离
- **小气泡连接**：删除尾巴（三角形），改用小气泡（半径3px）连接大气泡和桌宠
- **屏幕边界扩展**：右边+20px、下方+20px余量，下方可无视任务栏
- **简化桌宠定位**：删除桌宠独立边界检测，完全由气泡侧统一约束
- **删除预设位置功能**：设置页面不再提供上下左右位置选项，完全由用户手动拖拽定位

### 架构修复
- **Config 线程安全**：所有公开方法加 `threading.RLock()`，防止多线程竞态条件
- **关闭顺序优化**：`unload_all()` 先清空所有事件监听再卸载插件，避免事件到达已卸载的 handler
- **God Object 重构**：`self.kernel` 改为 `self._kernel`（私有），提供 `get_plugin()`/`get_all_plugins()`/`main_window` 受限接口
- **插件解耦**：settings → rules/overlay 的直接调用改为事件（`RULES_RELOAD`、`OVERLAY_SET_THEME`）
- **代码清理**：删除死代码（`_match_rule`）、未使用的机制（`get_plugin_config`/`set_plugin_config`）、可变类默认值（`dependencies` 改为 tuple）
- **API 迁移**：`QDesktopWidget` 改为 `QApplication.primaryScreen()`
- **硬编码优化**：AboutDialog 版本号从 config 读取，desktop_pet 常量从 overlay widget 动态获取

### 文件变更
```
kernel/config.py                # 线程安全锁
kernel/event_bus.py             # 新增 RULES_RELOAD、OVERLAY_SET_THEME 事件
kernel/plugin_manager.py        # 关闭顺序优化
plugins/base.py                 # 受限接口、删除未使用方法
plugins/overlay/plugin.py       # 整体边界检测、小气泡绘制、删除预设位置
plugins/desktop_pet/plugin.py   # 动态获取常量、删除独立边界检测
plugins/rules/plugin.py         # 监听 RULES_RELOAD 事件、删除死代码
plugins/settings/dialog.py      # 删除位置选择 UI
plugins/settings/plugin.py      # 改为事件驱动
plugins/about/plugin.py         # 版本号从 config 读取
plugins/monitor/plugin.py       # 删除冗余 logger 赋值
plugins/reminders/plugin.py     # 删除冗余 logger 赋值
plugins/stats/plugin.py         # 删除冗余 logger 赋值
plugins/tray/plugin.py          # 删除冗余 logger 赋值
```

---

## v3.3.0 (2026-05-29)

### 新功能
- **气泡状态栏**：悬浮窗改为半透明圆角气泡样式（260x70），尾巴指向桌宠头顶
- **暗色/亮色主题**：支持切换气泡显示主题，设置页面可配置
- **数据备份**：启动时自动备份数据库（保留7天）
- **数据导出**：托盘菜单支持导出统计（CSV/JSON格式）
- **重启功能**：托盘菜单添加"重启"选项

### 优化
- **内存泄漏防护**：各插件 on_unload 正确清理资源
- **规则匹配优化**：按进程名建哈希表索引，匹配速度提升
- **拖拽边界检测**：气泡拖拽时自动检测屏幕边界

### 修复
- 修复双气泡 bug（删除桌宠 widget 中的旧 StatusBubble）
- 修复气泡尾巴位置（BUBBLE_WIDTH - BUBBLE_RADIUS = 240）

### 文件变更
```
plugins/overlay/plugin.py       # 气泡绘制（QPainter + 暗色亮色主题）
plugins/desktop_pet/plugin.py   # 桌宠跟随逻辑（尾巴尖端对准头顶）
plugins/desktop_pet/widget.py   # 删除旧 StatusBubble，只保留图片显示
plugins/settings/dialog.py      # 主题切换 UI
plugins/settings/plugin.py      # 主题配置保存
plugins/rules/plugin.py         # 规则匹配索引优化
plugins/stats/plugin.py         # 数据备份 + 导出功能
plugins/tray/plugin.py          # 重启功能 + 导出菜单
plugins/about/plugin.py         # 版本号 v3.3.0
```

---

## v3.2.0 (2026-05-28)

### 新功能
- 桌面宠物插件（像素风动画）
- 窗口规则自定义（支持通配符）
- 使用统计（时间线 + 分类时长）

### 优化
- 插件架构重构
- 事件总线优化

---

## v3.1.0 (2026-05-27)

### 新功能
- 系统托盘集成
- 分类图标显示
- 透明度调节

### 修复
- Windows 11 兼容性问题

---

## v3.0.0 (2026-05-26)

### 初始版本
- 窗口状态监测
- 自动分类（游戏/办公/摸鱼/开发/工具）
- 悬浮窗显示
- 插件系统架构

---

**作者**：qiuyuehu + 衾衾 (Hermes Agent)
