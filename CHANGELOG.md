# 更新日志

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
