import os
import sys
import subprocess

if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

def get_active_desktop_paths():
    paths = set()
    
    # 1. Query Windows Shell Special Folders (Handles OneDrive / Custom Redirects)
    try:
        cmd = ["powershell", "-NoProfile", "-Command", "[Environment]::GetFolderPath('Desktop')"]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode == 0 and res.stdout.strip():
            ps_path = res.stdout.strip()
            if os.path.exists(ps_path):
                paths.add(ps_path)
    except Exception:
        pass

    # 2. Standard User Home Desktop
    user_desktop = os.path.join(os.path.expanduser("~"), "Desktop")
    if os.path.exists(user_desktop):
        paths.add(user_desktop)

    # 3. OneDrive Desktop fallback
    onedrive_desktop = os.path.join(os.path.expanduser("~"), "OneDrive", "Desktop")
    if os.path.exists(onedrive_desktop):
        paths.add(onedrive_desktop)

    return list(paths)

def create_desktop_shortcut():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    target_path = os.path.join(current_dir, "Run_YTFetch.bat")
    
    icon_path = os.path.join(current_dir, "icon.ico")
    has_icon = os.path.exists(icon_path)

    desktop_paths = get_active_desktop_paths()
    print("Found Desktop locations:", desktop_paths)

    success_count = 0
    for desktop_dir in desktop_paths:
        shortcut_path = os.path.join(desktop_dir, "YTFetch.lnk")
        print(f"Creating shortcut at: {shortcut_path}")

        # PowerShell WScript.Shell shortcut creation
        ps_cmd = (
            f'$WshShell = New-Object -ComObject WScript.Shell; '
            f'$Shortcut = $WshShell.CreateShortcut("{shortcut_path}"); '
            f'$Shortcut.TargetPath = "{target_path}"; '
            f'$Shortcut.WorkingDirectory = "{current_dir}"; '
            f'$Shortcut.Description = "YTFetch - YouTube Media Downloader & Trimmer"; '
        )
        if has_icon:
            ps_cmd += f'$Shortcut.IconLocation = "{icon_path}"; '
        ps_cmd += '$Shortcut.Save()'

        cmd = ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps_cmd]
        res = subprocess.run(cmd, capture_output=True, text=True)

        if res.returncode == 0 and os.path.exists(shortcut_path):
            print(f"[SUCCESS] Shortcut created at {shortcut_path}")
            success_count += 1
        else:
            print(f"[ERROR] Failed at {shortcut_path}:", res.stderr)

    if success_count > 0:
        print("✅ Shortcut YTFetch berhasil dibuat di Desktop layar Anda!")
        return True
    return False

if __name__ == "__main__":
    create_desktop_shortcut()
