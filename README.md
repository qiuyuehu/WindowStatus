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
- **自定义分类** — 支持自定义分类规则（进程名/窗口标题）
- **透明度设置** — 可调整悬浮窗透明度（50%~100%）
- **置顶/取消置顶** — 可切换是否显示在其他窗口上面
- **开机自启动** — 支持开机自动运行

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
python window_status.py
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
- **设置** — 管理自定义分类规则
- **开机自启动** — 开机自动运行

### 自定义分类规则

1. 右键托盘图标 → "设置"
2. 选择要编辑的分类
3. 点击"编辑规则"
4. 每行一条规则，格式：
   - `process:进程名.exe` — 匹配进程名
   - `title:*关键词*` — 匹配窗口标题（支持通配符）

### 配置文件位置

```
C:\Users\你的用户名\.WindowStatus\
├── config.json    # 分类规则配置
└── data.db        # 使用统计数据
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
├── window_status.py   # 主程序
├── build.py           # 打包脚本
├── icon.ico           # 程序图标
├── icon.svg           # 图标源文件
├── PLAN.md            # 项目规划
├── README.md          # 项目说明
└── LICENSE            # MIT 协议
```

## 常见问题

**Q：启动后看不到悬浮窗？**
A：检查右下角托盘图标，右键选择"显示悬浮窗"。

**Q：如何调整悬浮窗位置？**
A：左键拖拽悬浮窗即可移动位置。

**Q：如何添加自定义分类？**
A：右键托盘图标 → "设置" → "添加分类"。

**Q：统计数据在哪里？**
A：右键托盘图标 → "使用统计"，或查看 `C:\Users\你的用户名\.WindowStatus\data.db`。

**Q：杀毒软件报毒？**
A：这是 Python 打包的常见误报。代码完全开源，可自行审计后添加白名单。

## 更新日志

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