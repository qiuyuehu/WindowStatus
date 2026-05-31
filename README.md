<h1 align="center">🪟 WindowStatus</h1>

<p align="center">
  <a href="README.md">中文</a> | <a href="README_EN.md">English</a>
</p>

<p align="center"><b>一款轻量的 Windows 窗口状态显示器，参考 Discord/Steam 设计，实时显示当前活动窗口的分类状态。</b></p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.7+-blue?logo=python&logoColor=white" alt="Python 3.7+">
  <img src="https://img.shields.io/badge/Platform-Windows-0078d4?logo=windows&logoColor=white" alt="Windows">
  <img src="https://img.shields.io/badge/License-MIT-green" alt="License">
</p>

---

<p align="center">
  <img src="assets/桌宠.png" alt="WindowStatus 桌宠" width="400">
</p>

## 亮点功能

- **Apple Screen Time 风格统计** — 环形占比图 + 彩色进度条 + 分类时长对比，支持今日/本周/本月/时间线四个维度
- **可自定义桌宠** — 长按可拖拽，自动记住位置，重启后自动恢复
- **半透明气泡状态栏** — 圆角气泡显示当前窗口分类、标题、时长，支持暗色/亮色主题
- **智能分类** — 自动识别游戏/办公/摸鱼/开发/工具/其他，支持通配符自定义规则
- **数据导出** — CSV/JSON 格式导出统计数据

## 自定义桌宠

替换 `plugins/desktop_pet/assets/` 下的五张立绘即可更换桌宠形象：

| 文件名 | 用途 |
|--------|------|
| `idle.png` | 待机状态 |
| `sit.png` | 坐下状态 |
| `sleep.png` | 睡觉状态 |
| `walk.png` | 行走状态 |
| `drag.png` | 被拖拽时 |

图片建议使用透明背景的 PNG，分辨率 256x256，尺寸保持一致。替换后重启程序生效。

## 核心功能

- **气泡状态栏** — 半透明圆角气泡，显示当前窗口的分类、标题、进程名、使用时长，支持暗色/亮色主题
- **自动分类** — 智能识别游戏/办公/摸鱼/开发/工具/其他，支持自定义规则
- **桌面宠物** — 二次元风格桌宠，附着在气泡下方，支持长按拖拽（200ms），拖拽时同步气泡位置，记住位置
- **使用统计** — Apple Screen Time 风格，今日/本周/本月统计 + 时间线，支持 CSV/JSON 导出
- **数据备份** — 启动时自动备份数据库（保留 7 天）

## 快速开始

### 下载 EXE（推荐）

前往 [Releases](https://github.com/qiuyuehu/WindowStatus/releases) 页面，下载最新版本的 `WindowStatus.exe`，双击直接运行。

### 命令行运行

```bash
# 克隆仓库
git clone https://github.com/qiuyuehu/WindowStatus.git
cd WindowStatus

# 安装依赖
pip install PyQt5 psutil pywin32

# 运行
python main.py
```

## 自定义分类规则

1. 右键托盘图标 → "设置"
2. 左侧选择分类，右侧查看/编辑匹配规则
3. 支持进程名 (`process`) 和窗口标题 (`title`) 匹配，支持通配符 `*`

## 默认分类

| 分类 | 图标 | 包含软件 |
|------|------|----------|
| 游戏 | 🎮 | Steam、Epic、异环、Wallpaper Engine |
| 办公 | 📊 | Office、QQ、微信、Telegram、钉钉 |
| 摸鱼 | 🐟 | Chrome、Edge、B站、抖音、知乎 |
| 开发 | 💻 | VS Code、PyCharm、Git、Docker |
| 工具 | 🔧 | Everything、7-Zip、PowerToys |
| 其他 | 💻 | 未匹配的窗口 |

## 系统要求

- **操作系统**：Windows 10 / 11
- **Python**：3.7+（打包后不需要）

## 作者

**qiuyuehu** — [GitHub](https://github.com/qiuyuehu)

**衾衾 (Hermes Agent)** — 开发与设计

## License

[MIT](LICENSE)

---

<p align="center">
  如果觉得有用，点个 ⭐ Star 支持一下吧！
</p>
