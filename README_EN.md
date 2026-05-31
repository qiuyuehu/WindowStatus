<h1 align="center">🪟 WindowStatus</h1>

<p align="center">
  <a href="README.md">中文</a> | <a href="README_EN.md">English</a>
</p>

<p align="center"><b>A lightweight Windows activity monitor inspired by Discord/Steam, showing real-time status of your active window.</b></p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.7+-blue?logo=python&logoColor=white" alt="Python 3.7+">
  <img src="https://img.shields.io/badge/Platform-Windows-0078d4?logo=windows&logoColor=white" alt="Windows">
  <img src="https://img.shields.io/badge/License-MIT-green" alt="License">
</p>

---

<p align="center">
  <img src="assets/桌宠.png" alt="WindowStatus Desktop Pet" width="400">
</p>

## Highlights

- **Apple Screen Time Style Stats** — Donut charts, color-coded progress bars, and category breakdowns across Today / This Week / This Month / Timeline
- **Customizable Desktop Pet** — Anime-style pet widget, long-press to drag (200ms), remembers position across restarts
- **Floating Status Bubble** — Semi-transparent rounded bubble showing current window category, title, and duration, with dark/light theme support
- **Smart Categorization** — Auto-detects Gaming / Office / Slacking / Dev / Tools / Other, with wildcard pattern customization
- **Data Export** — Export statistics in CSV or JSON format

## Customize the Desktop Pet

Replace the five character illustrations in `plugins/desktop_pet/assets/` to change the pet's appearance:

| Filename | State |
|----------|-------|
| `idle.png` | Idle |
| `sit.png` | Sitting |
| `sleep.png` | Sleeping |
| `walk.png` | Walking |
| `drag.png` | Being dragged |

Use transparent PNG images at 256x256 resolution. Keep all images the same size. Restart the program after replacing.

## Features

- **Status Bubble** — Semi-transparent rounded bubble showing current window category, title, process name, and usage duration, with dark/light theme support
- **Auto Categorization** — Smart detection for Gaming / Office / Slacking / Dev / Tools / Other, with custom rule support
- **Desktop Pet** — Anime-style pet attached below the bubble, long-press to drag (200ms), syncs bubble position while dragging, remembers position
- **Usage Statistics** — Apple Screen Time style, Today / This Week / This Month stats + Timeline, export to CSV/JSON
- **Auto Backup** — Database auto-backup on startup (retained for 7 days)

## Quick Start

### Download EXE (Recommended)

Go to the [Releases](https://github.com/qiuyuehu/WindowStatus/releases) page, download the latest `WindowStatus.exe`, and double-click to run.

### Run from Source

```bash
# Clone the repo
git clone https://github.com/qiuyuehu/WindowStatus.git
cd WindowStatus

# Install dependencies
pip install PyQt5 psutil pywin32

# Run
python main.py
```

## Custom Classification Rules

1. Right-click the tray icon → "Settings"
2. Select a category on the left, view/edit matching rules on the right
3. Supports process name (`process`) and window title (`title`) matching with wildcard `*`

## Default Categories

| Category | Icon | Included Software |
|----------|------|-------------------|
| Gaming | 🎮 | Steam, Epic, Wallpaper Engine |
| Office | 📊 | Office, QQ, WeChat, Telegram, DingTalk |
| Slacking | 🐟 | Chrome, Edge, Bilibili, Douyin, Zhihu |
| Dev | 💻 | VS Code, PyCharm, Git, Docker |
| Tools | 🔧 | Everything, 7-Zip, PowerToys |
| Other | 💻 | Unmatched windows |

## System Requirements

- **OS**: Windows 10 / 11
- **Python**: 3.7+ (not needed for the packaged EXE)

## Author

**qiuyuehu** — [GitHub](https://github.com/qiuyuehu)

**Qinqin (Hermes Agent)** — Development & Design

## License

[MIT](LICENSE)

---

<p align="center">
  If you find this useful, give it a ⭐ Star!
</p>
