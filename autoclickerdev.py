import os
import sys
import ctypes
import requests
import subprocess

GITHUB_API_RELEASES = "https://api.github.com/repos/MrAndiGamesDev/Sigma-Auto-Clicker/releases"
WINUTIL_SCRIPT_TEMPLATE = "https://github.com/MrAndiGamesDev/Sigma-Auto-Clicker/releases/download/{tag}/winutil.ps1"
WINUTIL_LATEST_FULL_RELEASE = "https://github.com/MrAndiGamesDev/Sigma-Auto-Clicker/releases/latest/download/winutil.ps1"

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
        print(f"Error fetching release data: {e}")
        return None

def download_script(url):
    """Download the winutil.ps1 script content from the URL."""
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        return r.text
    except Exception as e:
        print(f"Error downloading script: {e}")
        return None

def run_powershell_script(script_content):
    """Run the PowerShell script content in an elevated shell if needed."""
    # Save the script to a temporary file
    import tempfile
    with tempfile.NamedTemporaryFile("w", delete=False, suffix=".ps1") as tmpfile:
        tmpfile.write(script_content)
        tmpfile_path = tmpfile.name

    try:
        if not is_admin():
            print("Script needs to be run as Administrator. Attempting to relaunch with elevation.")
            # Relaunch PowerShell with admin privileges running the saved script file
            params = f'-NoProfile -ExecutionPolicy Bypass -File "{tmpfile_path}"'
            # Use ShellExecute to run as admin
            ctypes.windll.shell32.ShellExecuteW(None, "runas", "powershell.exe", params, None, 1)
            sys.exit(0)
        else:
            # Run the script directly
            subprocess.run(["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", tmpfile_path], check=True)
    finally:
        # Clean up the temp file after running
        try:
            os.unlink(tmpfile_path)
        except Exception:
            pass

def main():
    tag = get_latest_prerelease_tag()
    if tag:
        script_url = WINUTIL_SCRIPT_TEMPLATE.format(tag=tag)
        print(f"Using latest pre-release: {tag}")
    else:
        print("No pre-release found. Falling back to latest full release.")
        script_url = WINUTIL_LATEST_FULL_RELEASE

    script_content = download_script(script_url)
    if not script_content:
        print("Failed to download the PowerShell script. Exiting.")
        sys.exit(1)

    run_powershell_script(script_content)

if __name__ == "__main__":
    if os.name != 'nt':
        print("This script is intended to be run on Windows only.")
        sys.exit(1)
    main()