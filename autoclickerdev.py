import os
import sys
import ctypes
import requests
import subprocess
import tempfile

# GitHub configuration for dev branch
AUTHER_NAME = "MrAndiGamesDev"
REPO_NAME = "Sigma-Auto-Clicker"
SCRIPT_URL = f"https://raw.githubusercontent.com/{AUTHER_NAME}/{REPO_NAME}/dev/autoclicker.py"

def is_admin():
    """Check if the script is running with admin privileges."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception:
        return False

def download_script(url):
    """Download the Python script content from the URL."""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.text
    except Exception as e:
        print(f"❌ Error downloading script: {e}")
        return None

def run_python_script(script_content):
    """Run the downloaded Python script."""
    with tempfile.NamedTemporaryFile("w", delete=False, suffix=".py") as tmpfile:
        tmpfile.write(script_content)
        tmpfile_path = tmpfile.name

    try:
        if not is_admin():
            print("⚠️  Script needs to be run as Administrator. Attempting to relaunch with elevation.")
            # Relaunch with admin rights
            ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, f'"{tmpfile_path}"', None, 1)
            sys.exit(0)
        else:
            print("🚀 Running downloaded Python script...")
            subprocess.run([sys.executable, tmpfile_path], check=True)
    finally:
        try:
            os.unlink(tmpfile_path)
        except Exception:
            pass

def main():
    if os.name != 'nt':
        print("❌ This script is intended for Windows only.")
        sys.exit(1)

    print("🔄 Fetching autoclicker.py from dev branch...")
    script_content = download_script(SCRIPT_URL)
    if not script_content:
        print("❌ Failed to download the Python script.")
        sys.exit(1)

    run_python_script(script_content)

if __name__ == "__main__":
    main()