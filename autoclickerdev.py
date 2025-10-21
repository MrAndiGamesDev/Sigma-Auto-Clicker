import os
import sys
import ctypes
import requests
import subprocess
import tempfile

# GitHub configuration
AUTHOR_NAME = "MrAndiGamesDev"
REPO_NAME = "Sigma-Auto-Clicker"
VERSION_URL = f"https://raw.githubusercontent.com/{AUTHOR_NAME}/{REPO_NAME}/dev/version.txt"
SCRIPT_URL_TEMPLATE = "https://github.com/{AUTHOR_NAME}/{REPO_NAME}/releases/download/v{version}/autoclicker.py"
FALLBACK_SCRIPT_URL = f"https://raw.githubusercontent.com/{AUTHOR_NAME}/{REPO_NAME}/dev/autoclicker.py"

def is_admin():
    """Check if the script is running with admin privileges."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception:
        return False

def get_version():
    """Fetch the version number from version.txt on the dev branch."""
    try:
        response = requests.get(VERSION_URL, timeout=10)
        response.raise_for_status()
        version = response.text.strip()
        return version
    except Exception as e:
        print(f"❌ Error fetching version.txt: {e}")
        return None

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
            print("⚠️ Script needs to be run as Administrator. Attempting to relaunch with elevation.")
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

    # Fetch version
    version = get_version()
    if version:
        print(f"🔄 Fetching Sigma Auto Clicker version {version}...")
        script_url = SCRIPT_URL_TEMPLATE.format(version=version)
    else:
        print("⚠️ Could not fetch version.txt. Falling back to dev branch script.")
        script_url = FALLBACK_SCRIPT_URL

    # Download and run the script
    script_content = download_script(script_url)
    if not script_content:
        print(f"❌ Failed to download autoclicker.py from {script_url}.")
        if script_url != FALLBACK_SCRIPT_URL:
            print("🔄 Attempting fallback to dev branch script...")
            script_content = download_script(FALLBACK_SCRIPT_URL)
        if not script_content:
            print("❌ Failed to download fallback script.")
            sys.exit(1)

    run_python_script(script_content)

if __name__ == "__main__":
    main()