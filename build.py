import os
import subprocess
import shutil

print("=" * 50)
print("WindowStatus Build Script")
print("=" * 50)
print()

# Paths
python_path = r"C:\Users\秋月\AppData\Local\Programs\Python\Python311\python.exe"
build_env = r"C:\BuildEnv"
temp_build = r"C:\TempBuild"
project_dir = os.path.dirname(os.path.abspath(__file__))

# Clean
print("[1/5] Cleaning...")
for d in [build_env, temp_build]:
    if os.path.exists(d):
        shutil.rmtree(d)

# Create venv
print("[2/5] Creating virtual environment...")
subprocess.run([python_path, "-m", "venv", build_env], check=True)

# Install deps
print("[3/5] Installing dependencies...")
pip = os.path.join(build_env, "Scripts", "pip.exe")
subprocess.run([pip, "install", "PyQt5", "psutil", "pywin32", "pyinstaller", "-q"], check=True)

# Copy files
print("[4/5] Copying and building...")
os.makedirs(temp_build)
for f in os.listdir(project_dir):
    if f.endswith(('.py', '.ico')):
        shutil.copy2(os.path.join(project_dir, f), temp_build)

# Build
pyinstaller = os.path.join(build_env, "Scripts", "pyinstaller.exe")
subprocess.run([
    pyinstaller, "--onefile", "--windowed",
    "--icon", "icon.ico",
    "--name", "WindowStatus",
    "window_status.py"
], cwd=temp_build, check=True)

# Copy result
exe_path = os.path.join(temp_build, "dist", "WindowStatus.exe")
if os.path.exists(exe_path):
    print("[5/5] Copying exe...")
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