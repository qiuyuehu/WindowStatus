import os
import subprocess
import shutil
import glob
import sys

print("=" * 50)
print("WindowStatus Build Script v3.0")
print("=" * 50)
print()

# Paths - 自动检测 Python 路径
def find_python():
    """自动检测 Python 可执行路径"""
    # 优先使用当前运行的 Python
    if sys.executable and os.path.exists(sys.executable):
        return sys.executable
    
    # 常见安装路径
    candidates = [
        shutil.which("python"),
        shutil.which("python3"),
        os.path.expandvars(r"%LOCALAPPDATA%\Programs\Python\Python311\python.exe"),
        os.path.expandvars(r"%LOCALAPPDATA%\Programs\Python\Python312\python.exe"),
        os.path.expandvars(r"%LOCALAPPDATA%\Programs\Python\Python310\python.exe"),
    ]
    
    for candidate in candidates:
        if candidate and os.path.exists(candidate):
            return candidate
    
    print("ERROR: 找不到 Python，请确保 Python 已安装并加入 PATH")
    sys.exit(1)

python_path = find_python()
print(f"Python: {python_path}")
build_env = r"C:\BuildEnv"
temp_build = r"C:\TempBuild"
project_dir = os.path.dirname(os.path.abspath(__file__))

# Clean
print("[1/6] Cleaning...")
for d in [build_env, temp_build]:
    if os.path.exists(d):
        shutil.rmtree(d)

# Create venv
print("[2/6] Creating virtual environment...")
subprocess.run([python_path, "-m", "venv", build_env], check=True)

# Install deps
print("[3/6] Installing dependencies...")
pip = os.path.join(build_env, "Scripts", "pip.exe")
subprocess.run([pip, "install", "PyQt5", "psutil", "pywin32", "pyinstaller", "-q"], check=True)

# Copy files
print("[4/6] Copying project files...")
os.makedirs(temp_build)

# 复制核心目录
for dir_name in ['kernel', 'plugins']:
    src_dir = os.path.join(project_dir, dir_name)
    dst_dir = os.path.join(temp_build, dir_name)
    if os.path.exists(src_dir):
        shutil.copytree(src_dir, dst_dir)

# 复制主程序和图标
for f in ['main.py', 'icon.ico', 'icon.svg']:
    src = os.path.join(project_dir, f)
    if os.path.exists(src):
        shutil.copy2(src, temp_build)

# Build
print("[5/6] Building...")
pyinstaller = os.path.join(build_env, "Scripts", "pyinstaller.exe")

# 收集所有需要打包的数据文件（素材等）
datas_entries = []
for root, dirs, files in os.walk(temp_build):
    for file in files:
        if not file.endswith('.py'):
            # 计算相对路径，保持目录结构
            rel_dir = os.path.relpath(root, temp_build)
            src_path = os.path.join(root, file)
            if rel_dir == '.':
                dst_dir = '.'
            else:
                dst_dir = rel_dir
            datas_entries.append(f"    ('{src_path.replace(os.sep, '/')}', '{dst_dir.replace(os.sep, '/')}'),")

datas_str = '\n'.join(datas_entries) if datas_entries else ''

# 使用 spec 文件打包
spec_content = f"""# -*- mode: python ; coding: utf-8 -*-
import os
import sys

a = Analysis(
    ['main.py'],
    pathex=['{temp_build}'],
    binaries=[],
    datas=[
{datas_str}
    ],
    hiddenimports=[
        'sqlite3', 'psutil', 'win32gui', 'win32process', 'win32con', 'PyQt5.sip',
        'kernel', 'kernel.event_bus', 'kernel.plugin_manager', 'kernel.config', 'kernel.core',
        'plugins', 'plugins.base', 'plugins.utils',
        'plugins.monitor', 'plugins.monitor.plugin',
        'plugins.overlay', 'plugins.overlay.plugin',
        'plugins.tray', 'plugins.tray.plugin',
        'plugins.stats', 'plugins.stats.plugin', 'plugins.stats.dialog',
        'plugins.rules', 'plugins.rules.plugin',
        'plugins.about', 'plugins.about.plugin',
        'plugins.settings', 'plugins.settings.plugin', 'plugins.settings.dialog',
        'plugins.reminders', 'plugins.reminders.plugin',
        'plugins.desktop_pet', 'plugins.desktop_pet.plugin',
        'plugins.desktop_pet.widget', 'plugins.desktop_pet.state_machine',
    ],
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='WindowStatus',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon.ico',
)
"""

spec_file = os.path.join(temp_build, 'WindowStatus.spec')
with open(spec_file, 'w', encoding='utf-8') as f:
    f.write(spec_content)

# 执行打包
subprocess.run([pyinstaller, spec_file], cwd=temp_build, check=True)

# Copy result
exe_path = os.path.join(temp_build, "dist", "WindowStatus.exe")
if os.path.exists(exe_path):
    print("[6/6] Copying exe...")
    shutil.copy2(exe_path, project_dir)
    print()
    print("=" * 50)
    print("Build successful!")
    print(f"File: {os.path.join(project_dir, 'WindowStatus.exe')}")
    print("=" * 50)
else:
    print()
    print("=" * 50)
    print("Build failed!")
    print("=" * 50)

# Cleanup
print("Cleaning up...")
for d in [build_env, temp_build]:
    if os.path.exists(d):
        shutil.rmtree(d)

input("\nPress Enter to exit...")