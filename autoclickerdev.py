import os
import sys
import ctypes
import requests
import subprocess
import tempfile

# GitHub configuration
GITHUB_API_RELEASES = "https://api.github.com/repos/MrAndiGamesDev/Sigma-Auto-Clicker/releases"
SCRIPT_NAME = "autoclicker.py"  # <-- This is the file we expect to find in releases
SCRIPT_URL_TEMPLATE = "https://github.com/MrAndiGamesDev/Sigma-Auto-Clicker/releases/download/{tag}/" + SCRIPT_NAME
SCRIPT_URL_LATEST = "https://github.com/MrAndiGamesDev/Sigma-Auto-Clicker/releases/latest/download/" + SCRIPT_NAME

def is_admin():
    """Check if the script is running with admin privileges."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception:
        return False

def get_latest_prerelease_tag():
    """Get the latest pre-release tag from GitHub API."""
    try:
        response = requests.get(GITHUB_API_RELEASES, timeout=10)
        response.raise_for_status()
        releases = response.json()

        for release in releases:
            if release.get('prerelease'):
                return release.get('tag_name')
        return None
    except Exception as e:
        print(f"❌ Error fetching release data: {e}")
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

    tag = get_latest_prerelease_tag()
    if tag:
        script_url = SCRIPT_URL_TEMPLATE.format(tag=tag)
        print(f"🔄 Using latest pre-release: {tag}")
    else:
        print("ℹ️  No pre-release found. Falling back to latest full release.")
        script_url = SCRIPT_URL_LATEST

    script_content = download_script(script_url)
    if not script_content:
        print("❌ Failed to download the Python script.")
        sys.exit(1)

    run_python_script(script_content)

if __name__ == "__main__":
    main()