# -*- coding: utf-8 -*-
"""
配置管理模块 - 核心层
负责加载、保存、管理配置文件
"""

import json
import os
import copy
import logging
import threading
from typing import Dict, Any, Optional, List
from contextlib import contextmanager

logger = logging.getLogger("WindowStatus.config")


# 默认分类规则
DEFAULT_CATEGORIES = {
    "游戏": {
        "icon": "🎮",
        "color": [255, 107, 107],
        "rules": [
            {"type": "process", "pattern": "steam.exe"},
            {"type": "process", "pattern": "steamwebhelper.exe"},
            {"type": "process", "pattern": "EpicGamesLauncher.exe"},
            {"type": "process", "pattern": "360game.exe"},
            {"type": "process", "pattern": "NarutoOnline.exe"},
            {"type": "title", "pattern": "*Naruto Online*"},
            {"type": "title", "pattern": "*火影忍者*"},
            {"type": "process", "pattern": "MuMuPlayer.exe"},
            {"type": "process", "pattern": "NemuPlayer.exe"},
            {"type": "process", "pattern": "OurPlay.exe"},
            {"type": "title", "pattern": "*MuMu*"},
            {"type": "title", "pattern": "*OurPlay*"},
            {"type": "process", "pattern": "cloudGenshin.exe"},
            {"type": "title", "pattern": "*云·原神*"},
            {"type": "process", "pattern": "GamePP.exe"},
            {"type": "process", "pattern": "Wallpaper64.exe"},
            {"type": "process", "pattern": "Wallpaper32.exe"},
            {"type": "title", "pattern": "*Wallpaper Engine*"},
            {"type": "process", "pattern": "miHoYoLauncher.exe"},
            {"type": "title", "pattern": "*米哈游*"},
            {"type": "title", "pattern": "*原神*"},
            {"type": "title", "pattern": "*崩坏*"},
            {"type": "title", "pattern": "*星穹铁道*"},
            {"type": "process", "pattern": "guiguai.exe"},
            {"type": "title", "pattern": "*古怪加速器*"},
        ]
    },
    "办公": {
        "icon": "📊",
        "color": [78, 205, 196],
        "rules": [
            {"type": "process", "pattern": "EXCEL.EXE"},
            {"type": "process", "pattern": "WINWORD.EXE"},
            {"type": "process", "pattern": "POWERPNT.EXE"},
            {"type": "process", "pattern": "ONENOTE.EXE"},
            {"type": "process", "pattern": "OUTLOOK.EXE"},
            {"type": "process", "pattern": "officeclicktorun.exe"},
            {"type": "process", "pattern": "TIM.exe"},
            {"type": "process", "pattern": "QQ.exe"},
            {"type": "process", "pattern": "WeChat.exe"},
            {"type": "process", "pattern": "telegram.exe"},
            {"type": "process", "pattern": "DingTalk.exe"},
            {"type": "process", "pattern": "Feishu.exe"},
            {"type": "process", "pattern": "Lark.exe"},
            {"type": "title", "pattern": "*钉钉*"},
            {"type": "title", "pattern": "*飞书*"},
            {"type": "process", "pattern": "123Pan.exe"},
            {"type": "process", "pattern": "AliyunPan.exe"},
            {"type": "process", "pattern": "Quark.exe"},
            {"type": "title", "pattern": "*123云盘*"},
            {"type": "title", "pattern": "*阿里云盘*"},
            {"type": "title", "pattern": "*夸克*"},
            {"type": "process", "pattern": "UURemote.exe"},
            {"type": "title", "pattern": "*UU远程*"},
            # 浏览器标题细分：办公类网站
            {"type": "title", "pattern": "*Google Docs*"},
            {"type": "title", "pattern": "*Google Sheets*"},
            {"type": "title", "pattern": "*Google Slides*"},
            {"type": "title", "pattern": "*腾讯文档*"},
            {"type": "title", "pattern": "*Notion*"},
            {"type": "title", "pattern": "*飞书文档*"},
            {"type": "title", "pattern": "*语雀*"},
            {"type": "title", "pattern": "*Confluence*"},
            {"type": "title", "pattern": "*Jira*"},
            {"type": "title", "pattern": "*DeepSeek*"},
            {"type": "title", "pattern": "*AI Studio*"},
            {"type": "title", "pattern": "*Gemini*"},
            {"type": "title", "pattern": "*超星*"},
            {"type": "title", "pattern": "*学习通*"},
            {"type": "title", "pattern": "*豆包*"},
        ]
    },
    "摸鱼": {
        "icon": "🐟",
        "color": [255, 230, 109],
        "rules": [
            {"type": "process", "pattern": "chrome.exe"},
            {"type": "process", "pattern": "msedge.exe"},
            {"type": "process", "pattern": "firefox.exe"},
            {"type": "process", "pattern": "FlashBrowser.exe"},
            {"type": "process", "pattern": "bilibili.exe"},
            {"type": "process", "pattern": "哔哩哔哩直播姬.exe"},
            {"type": "process", "pattern": "必剪.exe"},
            {"type": "title", "pattern": "*B站*"},
            {"type": "title", "pattern": "*bilibili*"},
            {"type": "title", "pattern": "*哔哩哔哩*"},
            {"type": "title", "pattern": "*抖音*"},
            {"type": "title", "pattern": "*快手*"},
            {"type": "title", "pattern": "*YouTube*"},
            {"type": "title", "pattern": "*微博*"},
            {"type": "title", "pattern": "*知乎*"},
            {"type": "title", "pattern": "*贴吧*"},
            {"type": "title", "pattern": "*豆瓣*"},
            {"type": "title", "pattern": "*小红书*"},
            {"type": "process", "pattern": "YesPlayMusic.exe"},
            {"type": "process", "pattern": "cloudmusic.exe"},
            {"type": "process", "pattern": "QQMusic.exe"},
            {"type": "title", "pattern": "*网易云音乐*"},
            {"type": "title", "pattern": "*QQ音乐*"},
            {"type": "process", "pattern": "doubao.exe"},
            {"type": "title", "pattern": "*Discord*"},
            {"type": "title", "pattern": "*起点*"},
            {"type": "title", "pattern": "*Apple Music*"},
        ]
    },
    "开发": {
        "icon": "💻",
        "color": [168, 230, 207],
        "rules": [
            {"type": "process", "pattern": "Code.exe"},
            {"type": "process", "pattern": "devenv.exe"},
            {"type": "process", "pattern": "pycharm64.exe"},
            {"type": "process", "pattern": "idea64.exe"},
            {"type": "process", "pattern": "webstorm64.exe"},
            {"type": "process", "pattern": "sublime_text.exe"},
            {"type": "title", "pattern": "*Visual Studio*"},
            {"type": "title", "pattern": "*PyCharm*"},
            {"type": "title", "pattern": "*IntelliJ*"},
            {"type": "title", "pattern": "*WebStorm*"},
            {"type": "title", "pattern": "*VS Code*"},
            {"type": "process", "pattern": "WindowsTerminal.exe"},
            {"type": "process", "pattern": "cmd.exe"},
            {"type": "process", "pattern": "powershell.exe"},
            {"type": "process", "pattern": "pwsh.exe"},
            {"type": "process", "pattern": "Hyper.exe"},
            {"type": "process", "pattern": "wt.exe"},
            {"type": "process", "pattern": "git.exe"},
            {"type": "process", "pattern": "GitHubDesktop.exe"},
            {"type": "process", "pattern": "node.exe"},
            {"type": "process", "pattern": "npm.exe"},
            {"type": "process", "pattern": "npx.exe"},
            {"type": "process", "pattern": "python.exe"},
            {"type": "process", "pattern": "pythonw.exe"},
            {"type": "process", "pattern": "pip.exe"},
            {"type": "process", "pattern": "ollama.exe"},
            {"type": "process", "pattern": "Ollama App.exe"},
            {"type": "title", "pattern": "*Ollama*"},
            {"type": "process", "pattern": "mysqld.exe"},
            {"type": "process", "pattern": "postgres.exe"},
            {"type": "process", "pattern": "redis-server.exe"},
            {"type": "process", "pattern": "Docker Desktop.exe"},
            {"type": "process", "pattern": "docker.exe"},
            # 浏览器标题细分：开发类网站
            {"type": "title", "pattern": "*GitHub*"},
            {"type": "title", "pattern": "*Stack Overflow*"},
            {"type": "title", "pattern": "*localhost*"},
            {"type": "title", "pattern": "*MDN Web Docs*"},
            {"type": "title", "pattern": "*npm*"},
            {"type": "title", "pattern": "*PyPI*"},
            {"type": "title", "pattern": "*Docker Hub*"},
            {"type": "title", "pattern": "*Vercel*"},
            {"type": "title", "pattern": "*Netlify*"},
            {"type": "title", "pattern": "*Hugging Face*"},
            {"type": "title", "pattern": "*/*: *"},
        ]
    },
    "工具": {
        "icon": "🔧",
        "color": [149, 165, 166],
        "rules": [
            {"type": "process", "pattern": "explorer.exe"},
            {"type": "process", "pattern": "taskmgr.exe"},
            {"type": "process", "pattern": "regedit.exe"},
            {"type": "process", "pattern": "msconfig.exe"},
            {"type": "process", "pattern": "control.exe"},
            {"type": "process", "pattern": "Everything.exe"},
            {"type": "process", "pattern": "7zFM.exe"},
            {"type": "process", "pattern": "WinRAR.exe"},
            {"type": "title", "pattern": "*Everything*"},
            {"type": "process", "pattern": "SnippingTool.exe"},
            {"type": "process", "pattern": "i_view64.exe"},
            {"type": "title", "pattern": "*IrfanView*"},
            {"type": "process", "pattern": "PowerToys.AdvancedPaste.exe"},
            {"type": "process", "pattern": "PowerToys.ColorPickerUI.exe"},
            {"type": "process", "pattern": "PowerToys.Peek.UI.exe"},
            {"type": "process", "pattern": "clash-verge.exe"},
            {"type": "process", "pattern": "verge-mihomo.exe"},
            {"type": "title", "pattern": "*Clash*"},
            {"type": "process", "pattern": "lghub.exe"},
            {"type": "process", "pattern": "lghub_agent.exe"},
            {"type": "title", "pattern": "*Logitech G HUB*"},
            {"type": "process", "pattern": "i4Tools.exe"},
            {"type": "title", "pattern": "*爱思助手*"},
        ]
    }
}

# 默认配置
DEFAULT_CONFIG = {
    "version": "3.0.0",
    "opacity": 0.9,
    "always_on_top": True,
    "position": "top-right",
    "minimize_to_tray": True,
    "categories": DEFAULT_CATEGORIES,
    "plugins": {
        "monitor": True,
        "overlay": True,
        "tray": True,
        "stats": True,
        "rules": True,
        "about": True,
        "settings": True,
        "desktop_pet": False
    },
    "logging": {
        "level": "INFO",
        "file": "window_status.log",
        "max_size": 10485760,  # 10MB
        "backup_count": 3
    }
}


class Config:
    """
    配置管理器
    
    负责加载、保存、管理配置文件
    支持点号分隔的键路径（如 "plugins.overlay"）
    """
    
    def __init__(self, config_path: str):
        """
        初始化配置管理器
        
        Args:
            config_path: 配置文件路径
        """
        self.config_path = config_path
        self._config: Dict[str, Any] = {}
        self._batch_mode = False
        self._lock = threading.RLock()  # 可重入锁，保护多线程访问
        self._ensure_dir()
        self.load()
    
    def _ensure_dir(self):
        """确保配置目录存在"""
        config_dir = os.path.dirname(self.config_path)
        if config_dir:
            os.makedirs(config_dir, exist_ok=True)
    
    def load(self):
        """加载配置文件"""
        with self._lock:
            if os.path.exists(self.config_path):
                try:
                    with open(self.config_path, 'r', encoding='utf-8') as f:
                        self._config = json.load(f)
                    # 合并默认配置（确保新增的配置项存在）
                    self._merge_defaults()
                    # 迁移旧版本配置
                    self._migrate_config()
                    # 合并后保存，持久化新增规则
                    self.save()
                except (json.JSONDecodeError, IOError, OSError) as e:
                    logger.error(f"加载配置失败: {e}")
                    self._config = copy.deepcopy(DEFAULT_CONFIG)
            else:
                self._config = copy.deepcopy(DEFAULT_CONFIG)
                self.save()
    
    def reload(self):
        """重新加载配置文件（重启时用）"""
        self.load()
    
    def _merge_defaults(self):
        """合并默认配置（支持三层嵌套：categories -> 分类 -> rules 列表追加）"""
        for key, value in DEFAULT_CONFIG.items():
            if key not in self._config:
                self._config[key] = value
            elif isinstance(value, dict) and isinstance(self._config[key], dict):
                for k, v in value.items():
                    if k not in self._config[key]:
                        self._config[key][k] = v
                    elif key == "categories" and isinstance(v, dict) and isinstance(self._config[key][k], dict):
                        # 分类内部合并：icon/color 保留用户值，rules 追加新增规则
                        user_cat = self._config[key][k]
                        for cat_key, cat_val in v.items():
                            if cat_key not in user_cat:
                                user_cat[cat_key] = cat_val
                            elif cat_key == "rules" and isinstance(cat_val, list):
                                # rules 列表：追加用户没有的规则（按 pattern 去重）
                                user_patterns = {
                                    r.get("pattern") for r in user_cat[cat_key]
                                    if isinstance(r, dict)
                                }
                                for rule in cat_val:
                                    if rule.get("pattern") not in user_patterns:
                                        user_cat[cat_key].append(rule)
    
    def _migrate_config(self):
        """迁移旧版本配置"""
        # v2.0 -> v3.0: 旧版用 enabled_plugins 列表，新版统一用 plugins 字典
        if "enabled_plugins" in self._config:
            old_enabled = self._config.pop("enabled_plugins")
            # 将列表转换为字典，确保默认插件不丢失
            default_plugins = DEFAULT_CONFIG.get("plugins", {})
            plugins_dict = self._config.get("plugins", {})
            # 旧列表中的插件标记为启用
            for name in old_enabled:
                plugins_dict[name] = True
            # 合并默认插件（保留旧配置中已有的 True/False）
            for name, default_val in default_plugins.items():
                if name not in plugins_dict:
                    plugins_dict[name] = default_val
            self._config["plugins"] = plugins_dict
        
        # 更新版本号
        self._config["version"] = "3.1.0"
    
    @contextmanager
    def batch_update(self):
        """
        批量更新上下文管理器

        在此上下文内，所有修改操作不会触发磁盘写入。
        退出时统一保存一次。

        用法：
            with config.batch_update():
                config.set("opacity", 0.8)
                config.set("always_on_top", False)
                # ... 多次修改 ...
            # 退出时自动 save()
        """
        self._batch_mode = True
        try:
            yield
        finally:
            self._batch_mode = False
            self.save()

    def save(self):
        """保存配置文件"""
        with self._lock:
            if self._batch_mode:
                return
            try:
                with open(self.config_path, 'w', encoding='utf-8') as f:
                    json.dump(self._config, f, ensure_ascii=False, indent=2)
            except Exception as e:
                logger.error(f"保存配置失败: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置项
        
        Args:
            key: 配置键（支持点号分隔，如 "plugins.overlay"）
            default: 默认值
        
        Returns:
            配置值
        """
        with self._lock:
            keys = key.split('.')
            value = self._config
            
            for k in keys:
                if isinstance(value, dict) and k in value:
                    value = value[k]
                else:
                    return default
            
            return value
    
    def set(self, key: str, value: Any):
        """
        设置配置项
        
        Args:
            key: 配置键（支持点号分隔）
            value: 配置值
        """
        with self._lock:
            keys = key.split('.')
            config = self._config
            
            for k in keys[:-1]:
                if k not in config:
                    config[k] = {}
                config = config[k]
            
            config[keys[-1]] = value
            self.save()
    
    def get_categories(self) -> Dict:
        """获取分类配置"""
        with self._lock:
            return self._config.get("categories", {})
    
    def set_categories(self, categories: Dict):
        """设置分类配置"""
        with self._lock:
            self._config["categories"] = categories
            self.save()
    
    def get_opacity(self) -> float:
        """获取透明度"""
        with self._lock:
            return self._config.get("opacity", 0.9)
    
    def set_opacity(self, opacity: float):
        """设置透明度"""
        with self._lock:
            self._config["opacity"] = opacity
            self.save()
    
    def is_always_on_top(self) -> bool:
        """是否置顶"""
        with self._lock:
            return self._config.get("always_on_top", True)
    
    def set_always_on_top(self, enabled: bool):
        """设置置顶"""
        with self._lock:
            self._config["always_on_top"] = enabled
            self.save()
    
    def get_position(self) -> str:
        """获取启动位置（top-left/top-right/bottom-left/bottom-right/custom）"""
        with self._lock:
            return self._config.get("position", "top-right")
    
    def set_position(self, position: str):
        """设置启动位置"""
        with self._lock:
            self._config["position"] = position
            self.save()
    
    def is_minimize_to_tray(self) -> bool:
        """关闭时是否最小化到托盘"""
        with self._lock:
            return self._config.get("minimize_to_tray", True)
    
    def set_minimize_to_tray(self, enabled: bool):
        """设置关闭时最小化到托盘"""
        with self._lock:
            self._config["minimize_to_tray"] = enabled
            self.save()
    
    def is_plugin_enabled(self, plugin_name: str) -> bool:
        """检查插件是否启用"""
        with self._lock:
            plugins = self._config.get("plugins", {})
            return plugins.get(plugin_name, True)
    
    def enable_plugin(self, plugin_name: str):
        """启用插件"""
        with self._lock:
            if "plugins" not in self._config:
                self._config["plugins"] = {}
            self._config["plugins"][plugin_name] = True
            self.save()
    
    def disable_plugin(self, plugin_name: str):
        """禁用插件"""
        with self._lock:
            if "plugins" not in self._config:
                self._config["plugins"] = {}
            self._config["plugins"][plugin_name] = False
            self.save()
    
    def get_enabled_plugins(self) -> List[str]:
        """获取启用的插件列表（从 plugins 字典推导）"""
        with self._lock:
            plugins = self._config.get("plugins", {})
            return [name for name, enabled in plugins.items() if enabled]
