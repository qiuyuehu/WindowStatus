<h1 align="center">🪟 WindowStatus</h1>

<p align="center"><b>一款轻量的 Windows 窗口状态显示器，参考 Discord/Steam 设计，实时显示当前活动窗口的分类状态。</b></p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.7+-blue?logo=python&logoColor=white" alt="Python 3.7+">
  <img src="https://img.shields.io/badge/Platform-Windows-0078d4?logo=windows&logoColor=white" alt="Windows">
  <img src="https://img.shields.io/badge/License-MIT-green" alt="License">
</p>

---

## 核心功能

- **气泡状态栏** — 半透明圆角气泡，显示当前窗口的分类、标题、进程名、使用时长
- **自动分类** — 智能识别游戏/办公/摸鱼/开发/工具/其他，支持自定义规则
- **桌面宠物** — 像素风桌宠，附着在气泡下方，跟随移动，支持待机/行走/坐下/睡眠动画
- **使用统计** — 今日时间线、分类使用时长统计
- **暗色/亮色主题** — 支持切换气泡显示主题

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
| 游戏 | 🎮 | Steam、Epic、原神、Wallpaper Engine |
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
