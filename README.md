<h1 align="center">🪟 WindowStatus</h1>

<p align="center"><b>一款轻量的 Windows 窗口状态显示器，参考 Discord/Steam 设计，实时显示当前活动窗口的分类状态。</b></p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.7+-blue?logo=python&logoColor=white" alt="Python 3.7+">
  <img src="https://img.shields.io/badge/Platform-Windows-0078d4?logo=windows&logoColor=white" alt="Windows">
  <img src="https://img.shields.io/badge/License-MIT-green" alt="License">
  <img src="https://img.shields.io/github/stars/qiuyuehu/WindowStatus?style=social" alt="Stars">
</p>

---

## 功能亮点

- **实时监控** — 监控当前活动窗口，切换窗口时自动更新
- **自动分类** — 智能识别游戏/办公/摸鱼/开发/工具/其他
- **悬浮窗显示** — 深色主题、圆角、半透明、可拖拽
- **使用时长** — 实时显示当前窗口已使用时长
- **使用统计** — 今日时间线、分类使用时长统计
- **自定义分类** — 可视化规则编辑器，支持进程名/窗口标题匹配（含通配符）
- **透明度设置** — 可调整悬浮窗透明度（50%~100%）
- **置顶/取消置顶** — 可切换是否显示在其他窗口上面
- **开机自启动** — 支持开机自动运行
- **桌面宠物** — 像素风桌宠，附着在悬浮窗下方，跟随移动，支持待机/行走/坐下/睡眠/拖拽动画
- **关闭到托盘** — 关闭窗口时最小化到系统托盘，不退出程序

## 界面预览

<p align="center">
  <img src="preview.png" alt="WindowStatus 界面预览" width="400">
</p>

## 快速开始

### 方式一：下载 EXE（推荐）

前往 [Releases](https://github.com/qiuyuehu/WindowStatus/releases) 页面，下载最新版本的 `WindowStatus.exe`，双击直接运行。

### 方式二：命令行运行

```bash
# 1. 克隆仓库
git clone https://github.com/qiuyuehu/WindowStatus.git
cd WindowStatus

# 2. 安装依赖
pip install PyQt5 psutil pywin32

# 3. 运行
python main.py
```

### 方式三：自行打包

```bash
# 1. 克隆仓库
git clone https://github.com/qiuyuehu/WindowStatus.git
cd WindowStatus

# 2. 运行打包脚本
python build.py
```

打包完成后，`WindowStatus.exe` 会出现在项目目录中。

## 使用说明

### 基本功能

1. **启动程序** — 运行后会在桌面显示悬浮窗，右下角显示托盘图标
2. **查看状态** — 悬浮窗显示当前窗口的分类、标题、进程名、使用时长
3. **拖拽移动** — 左键拖拽悬浮窗可移动位置
4. **右键菜单** — 右键托盘图标可访问所有功能

### 右键菜单功能

- **显示/隐藏悬浮窗** — 切换悬浮窗显示状态
- **置顶/取消置顶** — 切换是否显示在其他窗口上面
- **透明度** — 调整悬浮窗透明度（50%~100%）
- **使用统计** — 查看今日使用时间线和分类统计
- **设置** — 可视化编辑分类规则（增删改分类和匹配规则）
- **关于** — 查看应用信息和作者署名
- **开机自启动** — 开机自动运行
- **关闭到托盘** — 关闭窗口时最小化到托盘，不退出程序

### 自定义分类规则

1. 右键托盘图标 → "设置"
2. 左侧选择分类，右侧查看/编辑该分类的匹配规则
3. 点击"添加规则"新增规则：
   - **进程名** (`process`) — 匹配进程名，如 `chrome.exe`
   - **窗口标题** (`title`) — 匹配窗口标题，如 `*YouTube*`
4. 支持通配符 `*`，不区分大小写（进程名）
5. 点击"保存"生效，规则插件会自动重新加载

### 配置文件位置

```
C:\Users\你的用户名\.WindowStatus\
├── config.json    # 分类规则配置
├── data.db        # 使用统计数据
└── window_status.log  # 运行日志
```

## 默认分类

| 分类 | 图标 | 包含软件 |
|------|------|----------|
| 游戏 | 🎮 | Steam、Epic、360游戏大厅、MuMu模拟器、原神、Wallpaper Engine |
| 办公 | 📊 | Office、TIM、QQ、微信、Telegram、钉钉、飞书、夸克、阿里云盘 |
| 摸鱼 | 🐟 | Chrome、Edge、B站、抖音、微博、知乎、网易云音乐、豆包 |
| 开发 | 💻 | VS Code、PyCharm、Git、Node.js、Python、Ollama、Docker |
| 工具 | 🔧 | Everything、7-Zip、PowerToys、Clash Verge、Logitech G HUB |
| 其他 | 💻 | 未匹配的窗口 |

## 系统要求

- **操作系统**：Windows 10 / 11
- **Python**：3.7 及以上（打包后不需要）
- **依赖**：PyQt5、psutil、pywin32

## 项目结构

```
WindowStatus/
├── kernel/                  # 核心框架
│   ├── __init__.py
│   ├── core.py              # Kernel 核心类
│   ├── event_bus.py         # 事件总线（线程安全）
│   ├── plugin_manager.py    # 插件管理器（动态加载/卸载）
│   └── config.py            # 配置管理（支持批量更新）
├── plugins/                 # 插件层
│   ├── __init__.py
│   ├── base.py              # 插件基类（生命周期定义）
│   ├── utils.py             # 公共工具函数
│   ├── monitor/             # 窗口监控插件
│   ├── overlay/             # 悬浮窗插件
│   ├── tray/                # 系统托盘插件
│   ├── stats/               # 使用统计插件（含弹窗）
│   ├── rules/               # 规则匹配插件
│   ├── settings/            # 设置插件（规则编辑器）
│   ├── desktop_pet/         # 桌面宠物插件（像素风动画）
│   └── about/               # 关于窗口插件
├── main.py                  # 程序入口（仅组装逻辑）
├── build.py                 # 打包脚本（自动检测 Python）
├── test_v3.py               # 测试脚本
├── .gitignore
├── README.md
└── LICENSE
```

## 架构设计

```
┌─────────────────────────────────────────────┐
│                  main.py                     │
│         组装 Kernel + 启动 Qt 事件循环        │
└──────────────────┬──────────────────────────┘
                   │
         ┌─────────▼─────────┐
         │      Kernel       │
         │  (EventBus +       │
         │   PluginManager +  │
         │   Config)          │
         └─────────┬─────────┘
                   │
    ┌──────────────┼──────────────────┐
    │              │                  │
┌───▼───┐   ┌─────▼─────┐   ┌───────▼───────┐
│monitor│──▶│  rules    │──▶│ overlay/tray/ │
│ (监控) │   │  (分类)   │   │ stats/settings│
└───────┘   └───────────┘   │   /about      │
                            └───────────────┘
事件流: window.changed → category.matched → UI 更新 / 数据记录
```

## 常见问题

**Q：启动后看不到悬浮窗？**
A：检查右下角托盘图标，右键选择"显示悬浮窗"。

**Q：如何调整悬浮窗位置？**
A：左键拖拽悬浮窗即可移动位置。

**Q：如何添加自定义分类？**
A：右键托盘图标 → "设置" → 左下角"+ 添加分类"。

**Q：统计数据在哪里？**
A：右键托盘图标 → "使用统计"，或查看 `C:\Users\你的用户名\.WindowStatus\data.db`。

**Q：杀毒软件报毒？**
A：这是 Python 打包的常见误报。代码完全开源，可自行审计后添加白名单。

## 更新日志

### v3.2.0（2026-05-29）

- ✨ 新增桌面宠物插件 — 像素风桌宠，附着悬浮窗下方，跟随移动，支持待机/行走/坐下/睡眠/拖拽动画
- ✨ 新增关闭到托盘 — 关闭窗口时最小化到系统托盘，不退出程序
- ✨ 新增窗口标题栏图标和托盘图标（使用 icon.ico）
- 🔧 修复桌宠在屏幕外时的边界检测和自动翻转
- 🔧 修复取消置顶对桌宠无效的问题
- 🔧 修复隐藏悬浮窗时桌宠不跟随隐藏的问题
- 🔧 修复打包后桌宠不显示、任务栏图标残留、插件开关保存等问题
- 🔧 优化桌宠跟随拖拽的实时性（moveEvent 实时触发）
- 🔧 修复 About 对话框文字裁剪
- 🏗️ 代码审查与重构：提取公共 Win32 方法、统一错误处理、修复资源泄漏
- 🏗️ config 浅拷贝改 deepcopy，防止污染默认配置
- 🏗️ 调试日志降级为 DEBUG，减少生产环境日志噪音

### v3.1.0（2026-05-28）

- ✨ 新增设置插件 — 可视化规则编辑器（增删改分类和匹配规则）
- ✨ 新增关于窗口插件 — 独立展示应用信息和作者署名
- 🏗️ main.py 瘦身（274 行 → 109 行），UI 代码回归对应插件
- 🏗️ 去掉 enabled_plugins 冗余，统一使用 plugins 字典
- 🏗️ EventBus 改进错误报告（handler 签名不匹配时精确报错）
- 🏗️ Config 新增 batch_update 上下文管理器
- 🔧 提取公共工具函数到 plugins/utils.py
- 🔧 build.py 自动检测 Python 路径，不再硬编码
- 🔧 修复裸 except、import 位置等代码质量问题
- 📦 添加 .gitignore

### v3.0.0（2026-05-28）

- 🏗️ 完整插件化架构重构（事件总线驱动）
- ✨ 事件总线（EventBus）支持线程安全
- ✨ 插件动态加载/卸载
- ✨ Rules 插件独立负责分类匹配
- ✨ 插件发现机制（约定优于配置）
- 📦 更新打包脚本

### v2.0.0（2026-05-28）

- 🏗️ 插件化架构重构（core/ + plugins/）
- ✨ 配置文件管理（~/.WindowStatus/config.json）
- ✨ 日志系统（~/.WindowStatus/window_status.log）
- ✨ 异常处理优化，不会闪退
- ✨ 插件可独立开关
- 📦 更新打包脚本

### v1.0.0（2026-05-28）

- 🎉 初始发布
- ✨ 实时监控当前活动窗口
- ✨ 自动分类（游戏/办公/摸鱼/开发/工具/其他）
- ✨ 悬浮窗显示（深色主题、圆角、半透明、可拖拽）
- ✨ 使用时长实时显示
- ✨ 使用统计（今日时间线、分类时长）
- ✨ 自定义分类规则
- ✨ 透明度设置
- ✨ 置顶/取消置顶
- ✨ 开机自启动

## 作者

**qiuyuehu** — [GitHub](https://github.com/qiuyuehu)

**衾衾 (Hermes Agent)** — 开发与设计

## License

[MIT](LICENSE)

---

<p align="center">
  如果觉得有用，点个 ⭐ Star 支持一下吧！
</p>
