# -*- coding: utf-8 -*-
"""扫描已安装的软件列表"""
import winreg
import os

def get_installed_software():
    """获取已安装的软件列表"""
    software_list = []
    
    # 注册表路径
    paths = [
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"),
        (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
    ]
    
    for hive, path in paths:
        try:
            key = winreg.OpenKey(hive, path, 0, winreg.KEY_READ)
            i = 0
            while True:
                try:
                    subkey_name = winreg.EnumKey(key, i)
                    subkey = winreg.OpenKey(key, subkey_name, 0, winreg.KEY_READ)
                    try:
                        name, _ = winreg.QueryValueEx(subkey, "DisplayName")
                        try:
                            exe_path, _ = winreg.QueryValueEx(subkey, "InstallLocation")
                        except:
                            exe_path = ""
                        if name and not name.startswith("KB"):  # 过滤 Windows 更新
                            software_list.append({"name": name, "path": exe_path})
                    except:
                        pass
                    winreg.CloseKey(subkey)
                    i += 1
                except OSError:
                    break
            winreg.CloseKey(key)
        except:
            pass
    
    return software_list

def get_running_processes():
    """获取正在运行的进程"""
    import psutil
    processes = set()
    for proc in psutil.process_iter(['name']):
        try:
            processes.add(proc.info['name'].lower())
        except:
            pass
    return processes

if __name__ == '__main__':
    print("=" * 60)
    print("已安装的软件列表")
    print("=" * 60)
    
    software = get_installed_software()
    for s in sorted(software, key=lambda x: x['name']):
        print(f"  {s['name']}")
    
    print("\n" + "=" * 60)
    print("正在运行的进程")
    print("=" * 60)
    
    processes = get_running_processes()
    for p in sorted(processes):
        print(f"  {p}")
    
    print("\n" + "=" * 60)
    print("请把以上内容复制发给我，我来适配你的软件")
    print("=" * 60)
    input("\n按回车键退出...")