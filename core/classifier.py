# -*- coding: utf-8 -*-
"""
分类引擎模块 - 核心层
负责根据窗口标题和进程名判断分类
"""

from typing import Dict, List, Tuple, Optional


class ClassificationResult:
    """分类结果数据类"""
    def __init__(self, category: str, icon: str, color: List[int]):
        self.category = category
        self.icon = icon
        self.color = color
    
    def __str__(self):
        return f"{self.icon} {self.category}"


class Rule:
    """分类规则"""
    def __init__(self, rule_type: str, pattern: str):
        self.rule_type = rule_type  # 'process' or 'title'
        self.pattern = pattern
    
    def match(self, title: str, process_name: str) -> bool:
        """
        匹配规则
        
        Args:
            title: 窗口标题
            process_name: 进程名
        
        Returns:
            bool: 是否匹配
        """
        if self.rule_type == "process":
            return process_name.lower() == self.pattern.lower()
        elif self.rule_type == "title":
            return self._match_title(title)
        return False
    
    def _match_title(self, title: str) -> bool:
        """匹配窗口标题（支持通配符）"""
        pattern = self.pattern
        title_lower = title.lower()
        
        if pattern.startswith("*") and pattern.endswith("*"):
            return pattern[1:-1].lower() in title_lower
        elif pattern.startswith("*"):
            return title_lower.endswith(pattern[1:].lower())
        elif pattern.endswith("*"):
            return title_lower.startswith(pattern[:-1].lower())
        else:
            return pattern.lower() in title_lower


class Category:
    """分类定义"""
    def __init__(self, name: str, icon: str, color: List[int], rules: List[Rule]):
        self.name = name
        self.icon = icon
        self.color = color
        self.rules = rules
    
    def match(self, title: str, process_name: str) -> bool:
        """检查是否匹配此分类"""
        for rule in self.rules:
            if rule.match(title, process_name):
                return True
        return False


# 智能识别关键词
SMART_KEYWORDS = {
    "游戏": ["游戏", "game", "play", "steam", "epic", "origin", "育碧", "暴雪", 
             "原神", "崩坏", "星穹", "火影", "英雄联盟", "LOL", "DOTA", "CS", "VALORANT",
             "启动器", "launcher", "加速器", "模拟器", "emulator"],
    "办公": ["办公", "office", "文档", "表格", "演示", "会议", "邮件", "outlook", 
             "teams", "zoom", "腾讯会议", "钉钉", "飞书", "企业微信", "云盘", "网盘"],
    "摸鱼": ["视频", "音乐", "社交", "微博", "b站", "bilibili", "抖音", "快手", 
             "小红书", "知乎", "贴吧", "豆瓣", "twitter", "facebook", "instagram", 
             "youtube", "直播", "游戏", "漫画", "小说"],
    "开发": ["开发", "code", "编程", "ide", "editor", "terminal", "cmd", "powershell", 
             "git", "github", "vscode", "pycharm", "intellij", "node", "python", 
             "npm", "docker", "database", "数据库", "redis", "mysql", "postgres"],
    "工具": ["工具", "tool", "管理", "manager", "设置", "settings", "系统", "system",
             "截图", "录屏", "代理", "proxy", "vpn", "外设", "驱动", "driver"],
}


class Classifier:
    """
    分类引擎
    
    根据窗口标题和进程名判断分类
    支持自定义规则和智能识别
    """
    
    def __init__(self):
        self._categories: Dict[str, Category] = {}
        self._default_result = ClassificationResult("其他", "💻", [149, 165, 166])
    
    def load_categories(self, categories_config: Dict):
        """
        加载分类配置
        
        Args:
            categories_config: 分类配置字典
        """
        self._categories.clear()
        
        for name, info in categories_config.items():
            rules = []
            for rule_data in info.get("rules", []):
                rule = Rule(rule_data["type"], rule_data["pattern"])
                rules.append(rule)
            
            category = Category(
                name=name,
                icon=info.get("icon", "📋"),
                color=info.get("color", [149, 165, 166]),
                rules=rules
            )
            self._categories[name] = category
    
    def classify(self, title: str, process_name: str) -> ClassificationResult:
        """
        分类窗口
        
        Args:
            title: 窗口标题
            process_name: 进程名
        
        Returns:
            ClassificationResult: 分类结果
        """
        # 先匹配自定义规则
        for category in self._categories.values():
            if category.match(title, process_name):
                return ClassificationResult(category.name, category.icon, category.color)
        
        # 再尝试智能识别
        smart_result = self._smart_classify(title, process_name)
        if smart_result and smart_result in self._categories:
            category = self._categories[smart_result]
            return ClassificationResult(category.name, category.icon, category.color)
        
        return self._default_result
    
    def _smart_classify(self, title: str, process_name: str) -> Optional[str]:
        """智能识别分类"""
        title_lower = title.lower()
        process_lower = process_name.lower()
        
        for category, keywords in SMART_KEYWORDS.items():
            for keyword in keywords:
                if keyword.lower() in title_lower or keyword.lower() in process_lower:
                    return category
        return None
    
    def get_categories(self) -> Dict[str, Category]:
        """获取所有分类"""
        return self._categories.copy()
    
    def add_category(self, name: str, icon: str, color: List[int], rules: List[Dict]):
        """
        添加分类
        
        Args:
            name: 分类名称
            icon: 分类图标
            color: 分类颜色
            rules: 规则列表
        """
        rule_objects = [Rule(r["type"], r["pattern"]) for r in rules]
        category = Category(name, icon, color, rule_objects)
        self._categories[name] = category
    
    def remove_category(self, name: str):
        """删除分类"""
        if name in self._categories:
            del self._categories[name]