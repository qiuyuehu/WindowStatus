"""
WindowStatus 约束自动检查

检查 CONSTRAINTS.md 中定义的约束，返回检查结果。
失败则阻塞测试运行。

使用方式：
    python harness/checks.py           # 运行所有检查
    python harness/checks.py --verbose # 详细输出
"""

import os
import re
import sys
from pathlib import Path
from typing import List, Tuple

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent

# 白名单文件（跳过部分历史约束检查）
WHITELIST_FILES = [
    "plugins/stats/dialog.py",
    "plugins/settings/dialog.py",
]

# 检查结果
CheckResult = Tuple[str, str, str]  # (文件, 行号, 问题描述)


def is_whitelisted(filepath: str) -> bool:
    """检查文件是否在白名单中"""
    rel_path = os.path.relpath(filepath, PROJECT_ROOT)
    return rel_path in WHITELIST_FILES


def find_python_files(root: Path) -> List[Path]:
    """查找所有 Python 文件"""
    return list(root.rglob("*.py"))


def check_widget_creation_timing(files: List[Path]) -> List[CheckResult]:
    """
    检查 1.1：on_enable() 时必须立即创建 Widget
    """
    results = []
    pattern = re.compile(r"def on_enable\(self\)")
    widget_pattern = re.compile(r"self\.\w+\s*=\s*(QWidget|QLabel|QFrame|QPainter|QDialog)")

    for filepath in files:
        if is_whitelisted(str(filepath)):
            continue

        try:
            content = filepath.read_text(encoding="utf-8")
        except Exception:
            continue

        # 查找 on_enable 方法
        match = pattern.search(content)
        if not match:
            continue

        # 检查 on_enable 中是否有 widget 创建
        start = match.end()
        # 找到下一个 def 或 class
        next_def = re.search(r"\n    def |\nclass ", content[start:])
        if next_def:
            on_enable_body = content[start:start + next_def.start()]
        else:
            on_enable_body = content[start:]

        if not widget_pattern.search(on_enable_body):
            results.append((
                str(filepath),
                str(content[:match.start()].count("\n") + 1),
                "on_enable() 中未发现 Widget 创建（约束 1.1）"
            ))

    return results


def check_qt_tool_drag(files: List[Path]) -> List[CheckResult]:
    """
    检查 1.2：需要拖拽的 Widget 不能加 Qt.Tool
    """
    results = []
    tool_pattern = re.compile(r"Qt\.Tool")
    drag_pattern = re.compile(r"def mousePressEvent|def mouseMoveEvent")

    for filepath in files:
        if is_whitelisted(str(filepath)):
            continue

        try:
            content = filepath.read_text(encoding="utf-8")
        except Exception:
            continue

        if tool_pattern.search(content) and drag_pattern.search(content):
            results.append((
                str(filepath),
                "0",
                "文件同时包含 Qt.Tool 和鼠标事件（约束 1.2）"
            ))

    return results


def check_qdesktop_widget(files: List[Path]) -> List[CheckResult]:
    """
    检查 1.3：禁止使用 QDesktopWidget
    """
    results = []
    pattern = re.compile(r"QDesktopWidget")

    for filepath in files:
        if is_whitelisted(str(filepath)):
            continue

        try:
            content = filepath.read_text(encoding="utf-8")
        except Exception:
            continue

        if pattern.search(content):
            lines = content.split("\n")
            for i, line in enumerate(lines, 1):
                if "QDesktopWidget" in line:
                    results.append((
                        str(filepath),
                        str(i),
                        "使用了废弃的 QDesktopWidget（约束 1.3）"
                    ))

    return results


def check_event_handler_kwargs(files: List[Path]) -> List[CheckResult]:
    """
    检查 2.3：所有 EventBus handler 必须有 **kwargs 参数
    """
    results = []
    handler_pattern = re.compile(r"def (on_\w+|_on_\w+)\(self[^)]*\)")

    for filepath in files:
        if is_whitelisted(str(filepath)):
            continue

        try:
            content = filepath.read_text(encoding="utf-8")
        except Exception:
            continue

        for match in handler_pattern.finditer(content):
            sig = match.group(0)
            if "**kwargs" not in sig and "**kw" not in sig:
                line_num = content[:match.start()].count("\n") + 1
                results.append((
                    str(filepath),
                    str(line_num),
                    f"事件处理器 {sig} 缺少 **kwargs（约束 2.3）"
                ))

    return results


def check_empty_except(files: List[Path]) -> List[CheckResult]:
    """
    检查 5.1：禁止空 catch 块
    """
    results = []
    except_pattern = re.compile(r"except.*:\s*\n\s*pass")

    for filepath in files:
        if is_whitelisted(str(filepath)):
            continue

        try:
            content = filepath.read_text(encoding="utf-8")
        except Exception:
            continue

        for match in except_pattern.finditer(content):
            line_num = content[:match.start()].count("\n") + 1
            results.append((
                str(filepath),
                str(line_num),
                "空的 except 块（约束 5.1）"
            ))

    return results


def run_checks(verbose: bool = False) -> dict:
    """
    运行所有约束检查

    Returns:
        dict: {
            "passed": bool,
            "total": int,
            "violations": list,
            "warnings": list
        }
    """
    files = find_python_files(PROJECT_ROOT)

    # 排除 harness 目录和 __pycache__
    files = [f for f in files if "harness" not in str(f) and "__pycache__" not in str(f)]

    violations = []
    warnings = []

    # 运行所有检查
    checks = [
        ("1.1 Widget 创建时机", check_widget_creation_timing),
        ("1.2 Qt.Tool 拖拽限制", check_qt_tool_drag),
        ("1.3 QDesktopWidget 禁用", check_qdesktop_widget),
        ("2.3 事件处理器 kwargs", check_event_handler_kwargs),
        ("5.1 空 catch 块", check_empty_except),
    ]

    for check_name, check_fn in checks:
        if verbose:
            print(f"运行检查：{check_name}")

        results = check_fn(files)

        for filepath, line, msg in results:
            rel_path = os.path.relpath(filepath, PROJECT_ROOT)
            violation = f"{rel_path}:{line} - {msg}"
            violations.append(violation)

            if verbose:
                print(f"  违规：{violation}")

    return {
        "passed": len(violations) == 0,
        "total": len(files),
        "violations": violations,
        "warnings": warnings
    }


def main():
    """命令行入口"""
    verbose = "--verbose" in sys.argv or "-v" in sys.argv

    print("=" * 60)
    print("WindowStatus 约束检查")
    print("=" * 60)

    result = run_checks(verbose)

    print(f"\n检查文件数：{result['total']}")
    print(f"违规数：{len(result['violations'])}")

    if result["violations"]:
        print("\n违规详情：")
        for v in result["violations"]:
            print(f"  ✗ {v}")
        print("\n约束检查失败，阻塞测试运行。")
        print("请修复上述违规后重试。")
        sys.exit(1)
    else:
        print("\n✓ 所有约束检查通过")
        sys.exit(0)


if __name__ == "__main__":
    main()
