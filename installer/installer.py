"""
SoundVault Installer
A self-contained Windows installer that sets up SoundVault on the user's machine.
Compile with: python -m PyInstaller installer.py --onefile --windowed --icon=../icon.ico --name=SoundVault_Setup
"""

import os
import sys
import shutil
import subprocess
import winreg
import ctypes
from pathlib import Path

APP_NAME = "SoundVault"
APP_EXE = "SoundVault.exe"
COMPANY_NAME = "SoundVault"

SRC_DIR = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def run_as_admin():
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
    sys.exit()

def get_program_files():
    return os.environ.get('ProgramFiles', 'C:\\Program Files')

def get_apps_folder():
    return os.path.join(os.environ.get('LOCALAPPDATA', os.path.expanduser('~')), APP_NAME)

def create_shortcut(target, shortcut_path, description="", icon_path=""):
    try:
        import win32com.client
        shell = win32com.client.Dispatch("WScript.Shell")
        shortcut = shell.CreateShortCut(shortcut_path)
        shortcut.TargetPath = target
        shortcut.WorkingDirectory = os.path.dirname(target)
        shortcut.Description = description
        if icon_path:
            shortcut.IconLocation = icon_path
        shortcut.Save()
        return True
    except:
        pass
    try:
        powershell = f'''
        $WScriptShell = New-Object -ComObject WScript.Shell
        $Shortcut = $WScriptShell.CreateShortcut("{shortcut_path}")
        $Shortcut.TargetPath = "{target}"
        $Shortcut.WorkingDirectory = "{os.path.dirname(target)}"
        $Shortcut.Description = "{description}"
        {f'$Shortcut.IconLocation = "{icon_path}"' if icon_path else ''}
        $Shortcut.Save()
        '''
        subprocess.run(['powershell', '-Command', powershell], check=True, capture_output=True)
        return True
    except:
        return False

def install():
    install_dir = get_apps_folder()
    print(f"Installing {APP_NAME} to {install_dir}...")

    os.makedirs(install_dir, exist_ok=True)

    src_exe = os.path.join(SRC_DIR, APP_EXE)
    src_icon = os.path.join(SRC_DIR, "icon.ico")
    dst_exe = os.path.join(install_dir, APP_EXE)

    if os.path.exists(src_exe):
        shutil.copy2(src_exe, dst_exe)
        print(f"  Copied {APP_EXE}")
    else:
        print(f"  WARNING: {APP_EXE} not found alongside installer")

    if os.path.exists(src_icon):
        shutil.copy2(src_icon, os.path.join(install_dir, "icon.ico"))
        print(f"  Copied icon.ico")

    setup_exe = os.path.join(install_dir, "SoundVault_Setup.exe")
    if getattr(sys, 'frozen', False):
        shutil.copy2(sys.executable, setup_exe)
    elif os.path.exists(os.path.join(SRC_DIR, "SoundVault_Setup.exe")):
        shutil.copy2(os.path.join(SRC_DIR, "SoundVault_Setup.exe"), setup_exe)
    else:
        setup_exe = dst_exe

    desktop = os.path.join(os.path.expanduser('~'), 'Desktop')
    shortcut_path = os.path.join(desktop, f"{APP_NAME}.lnk")
    create_shortcut(dst_exe, shortcut_path, f"{APP_NAME} Tag Library Manager", dst_exe)
    print(f"  Created desktop shortcut")

    start_menu = os.path.join(os.environ.get('APPDATA', ''), 
                              'Microsoft', 'Windows', 'Start Menu', 'Programs', COMPANY_NAME)
    os.makedirs(start_menu, exist_ok=True)
    sm_shortcut = os.path.join(start_menu, f"{APP_NAME}.lnk")
    create_shortcut(dst_exe, sm_shortcut, f"{APP_NAME} Tag Library Manager", dst_exe)
    print(f"  Created Start Menu shortcut")

    try:
        key_path = f"Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\{APP_NAME}"
        with winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE if is_admin() else winreg.HKEY_CURRENT_USER, key_path) as key:
            winreg.SetValueEx(key, "DisplayName", 0, winreg.REG_SZ, APP_NAME)
            winreg.SetValueEx(key, "DisplayIcon", 0, winreg.REG_SZ, dst_exe)
            winreg.SetValueEx(key, "DisplayVersion", 0, winreg.REG_SZ, "1.0.0")
            winreg.SetValueEx(key, "Publisher", 0, winreg.REG_SZ, COMPANY_NAME)
            winreg.SetValueEx(key, "InstallLocation", 0, winreg.REG_SZ, install_dir)
            winreg.SetValueEx(key, "UninstallString", 0, winreg.REG_SZ,
                             f'"{setup_exe}" --uninstall')
            winreg.SetValueEx(key, "NoModify", 0, winreg.REG_DWORD, 1)
            winreg.SetValueEx(key, "NoRepair", 0, winreg.REG_DWORD, 1)
        print(f"  Registered for uninstall")
    except Exception as e:
        print(f"  Warning: Could not register uninstall: {e}")

    print(f"\n✓ {APP_NAME} installed successfully!")
    print(f"  Location: {install_dir}")
    print(f"  App data: %APPDATA%\\{APP_NAME}")
    
    run_app = input("\nLaunch SoundVault now? (Y/n): ").strip().lower()
    if run_app != 'n':
        subprocess.Popen([dst_exe], cwd=install_dir)

def uninstall():
    install_dir = get_apps_folder()
    print(f"Uninstalling {APP_NAME}...")

    if os.path.exists(install_dir):
        shutil.rmtree(install_dir, ignore_errors=True)
        print(f"  Removed {install_dir}")

    desktop_shortcut = os.path.join(os.path.expanduser('~'), 'Desktop', f"{APP_NAME}.lnk")
    if os.path.exists(desktop_shortcut):
        os.remove(desktop_shortcut)
        print(f"  Removed desktop shortcut")

    start_menu = os.path.join(os.environ.get('APPDATA', ''),
                              'Microsoft', 'Windows', 'Start Menu', 'Programs', COMPANY_NAME)
    sm_shortcut = os.path.join(start_menu, f"{APP_NAME}.lnk")
    if os.path.exists(sm_shortcut):
        os.remove(sm_shortcut)
        print(f"  Removed Start Menu shortcut")
    if os.path.exists(start_menu) and not os.listdir(start_menu):
        os.rmdir(start_menu)

    try:
        key_path = f"Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\{APP_NAME}"
        for root in [winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER]:
            try:
                winreg.DeleteKey(root, key_path)
            except:
                pass
    except:
        pass

    print(f"\n✓ {APP_NAME} uninstalled.")

if __name__ == '__main__':
    print("=" * 50)
    print(f"  {APP_NAME} Setup")
    print("=" * 50)

    args = [a.lower() for a in sys.argv[1:]]
    
    if '--uninstall' in args or '/uninstall' in args:
        uninstall()
        input("\nPress Enter to exit...")
        sys.exit()

    if not is_admin():
        print("Note: Installing for current user only (no admin needed).")
        print("      Some features (all-users Start Menu) may be limited.\n")

    install()
    input("\nPress Enter to exit...")
