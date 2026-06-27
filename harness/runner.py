"""
WindowStatus 测试入口

运行约束检查 + 单元测试，约束检查失败则阻塞测试运行。

使用方式：
    python harness/runner.py           # 运行检查 + 测试
    python harness/runner.py --checks  # 只运行约束检查
    python harness/runner.py --tests   # 只运行测试（跳过约束检查）
"""

import subprocess
import sys
from pathlib import Path

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent


def run_checks() -> bool:
    """
    运行约束检查

    Returns:
        bool: 检查是否通过
    """
    print("=" * 60)
    print("步骤 1/2：约束检查")
    print("=" * 60)

    result = subprocess.run(
        [sys.executable, str(Path(__file__).parent / "checks.py")],
        cwd=str(PROJECT_ROOT),
        capture_output=False
    )

    return result.returncode == 0


def run_tests() -> bool:
    """
    运行单元测试

    Returns:
        bool: 测试是否通过
    """
    print("\n" + "=" * 60)
    print("步骤 2/2：单元测试")
    print("=" * 60)

    result = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/", "-v"],
        cwd=str(PROJECT_ROOT),
        capture_output=False
    )

    return result.returncode == 0


def main():
    """命令行入口"""
    only_checks = "--checks" in sys.argv
    only_tests = "--tests" in sys.argv

    success = True

    # 运行约束检查
    if not only_tests:
        if not run_checks():
            success = False
            if not only_tests:
                print("\n约束检查失败，跳过测试运行。")
                sys.exit(1)

    # 运行测试
    if not only_checks:
        if not run_tests():
            success = False

    # 总结
    print("\n" + "=" * 60)
    if success:
        print("✓ 所有检查通过")
        sys.exit(0)
    else:
        print("✗ 存在失败项")
        sys.exit(1)


if __name__ == "__main__":
    main()
