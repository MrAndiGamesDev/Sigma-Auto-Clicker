import os
import sys
import ctypes
import requests
import subprocess
import tempfile
import argparse

# GitHub configuration
AUTHOR_NAME = "MrAndiGamesDev"
REPO_NAME = "Sigma-Auto-Clicker"
BRANCH = "stable"
BASE_RAW_URL = f"https://raw.githubusercontent.com/{AUTHOR_NAME}/{REPO_NAME}/{BRANCH}"
VERSION_URL = f"{BASE_RAW_URL}/version.txt"  # Try root first
VERSION_URL_SUBDIR = f"{BASE_RAW_URL}/VERSION.txt"  # Fallback to src/
SCRIPT_URL = f"{BASE_RAW_URL}/autoclicker.py"  # Primary script
SCRIPT_URL_SUBDIR = f"{BASE_RAW_URL}/src/autoclicker.py"  # Fallback to src/
SCRIPT_URL_DEV = f"{BASE_RAW_URL}/autoclickerdev.py"  # Fallback for renamed script

def is_admin():
    """Check if the script is running with admin privileges."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception:
        return False

def get_version():
    """Fetch the version number from version.txt (try root, then src/)."""
    for url in [VERSION_URL, VERSION_URL_SUBDIR]:
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            version = response.text.strip()
            if not version:
                print(f"❌ Error: version.txt at {url} is empty.")
                continue
            return version
        except Exception as e:
            print(f"❌ Error fetching version.txt from {url}: {e}")
    print("⚠️ No valid version.txt found in root or src/. Proceeding without version.")
    return None

def download_script():
    """Download the Python script content (try multiple URLs)."""
    urls = [SCRIPT_URL, SCRIPT_URL_SUBDIR, SCRIPT_URL_DEV]
    for url in urls:
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            script_content = response.text
            if not script_content.strip():
                print(f"❌ Error: Script at {url} is empty.")
                continue
            print(f"✅ Successfully downloaded script from {url}")
            return script_content
        except Exception as e:
            print(f"❌ Error downloading script from {url}: {e}")
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
    parser = argparse.ArgumentParser(description="Sigma Auto Clicker Launcher")
    parser.add_argument('--version-only', action='store_true', help="Print version and exit")
    args = parser.parse_args()

    if os.name != 'nt':
        print("❌ This script is intended for Windows only.")
        sys.exit(1)

    # Fetch version
    version = get_version()
    if args.version_only:
        if version:
            print(f"Sigma Auto Clicker version: {version}")
            sys.exit(0)
        else:
            print("❌ Failed to fetch version.txt.")
            sys.exit(1)

    if version:
        print(f"🔄 Fetching Sigma Auto Clicker version {version} from dev branch...")
    else:
        print("⚠️ Could not fetch version.txt. Attempting to download script from dev branch.")

    # Download and run the script
    script_content = download_script()
    if not script_content:
        print("❌ Failed to download autoclicker.py or autoclickerdev.py from dev branch.")
        print("ℹ️ Check the repository at https://github.com/MrAndiGamesDev/Sigma-Auto-Clicker/tree/dev for correct file paths.")
        sys.exit(1)

    run_python_script(script_content)

if __name__ == "__main__":
    main()