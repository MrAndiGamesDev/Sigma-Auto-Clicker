import json
import re
import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path
from typing import Generator, List

# ---------- Constants ----------
DOWNLOADS = Path("Downloads")
RELEASES = Path("Releases")
ARCHIVES = DOWNLOADS / "Archives"
MANIFEST_URL = "https://aka.ms/vs/17/release/channel"
MSI_FILENAME = "Windows SDK Signing Tools-x86_en-us.msi"

# ---------- Utility Functions ----------
def log(msg: str):
    print(f"[+] {msg}")

def download(url: str) -> bytes:
    """Download a file from the given URL and return its content."""
    try:
        with urllib.request.urlopen(url) as resp:
            return resp.read()
    except Exception as e:
        sys.exit(f"Error: Failed to download {url}\n{e}")

def get_msi_cabs(msi_data: bytes) -> Generator[str, None, None]:
    """Extract .cab filenames from the MSI binary content."""
    for match in re.finditer(rb"([A-Za-z0-9_\-]+\.cab)", msi_data):
        yield match.group(1).decode("ascii", errors="ignore")

def get_sub_dirs(path: Path) -> List[Path]:
    """Return all subdirectories in a given path."""
    return [x for x in path.iterdir() if x.is_dir()]

def ensure_dirs():
    """Ensure required directories exist."""
    for folder in [DOWNLOADS, RELEASES]:
        folder.mkdir(parents=True, exist_ok=True)

# ---------- Main Download Logic ----------
def fetch_manifest() -> dict:
    """Fetch and parse the Visual Studio channel manifest."""
    log("Checking Visual Studio manifest...")
    data = download(MANIFEST_URL)
    return json.loads(data)

def get_sdk_package_info(channel_manifest: dict):
    """Extract SDK package information and payload URLs."""
    vsman_url = channel_manifest["channelItems"][0]["payloads"][0]["url"]
    license_url = channel_manifest["channelItems"][1]["localizedResources"][0]["license"]

    vsman = json.loads(download(vsman_url))
    packages = vsman["packages"]

    for pkg in reversed(packages):
        if pkg["id"].startswith("Win11SDK_10.0."):
            return pkg["version"], pkg["payloads"], license_url

    sys.exit("Error: Could not find Windows 11 SDK package info.")

def download_payload(filename: str, payloads: list) -> bytes:
    """Download a specific payload by its filename."""
    for p in payloads:
        if p["fileName"] == f"Installers\\{filename}":
            url = p["url"]
            path = DOWNLOADS / filename
            log(f"Downloading {filename}...")
            data = download(url)
            with open(path, "wb") as f:
                f.write(data)
            return data
    sys.exit(f"Error: Payload {filename} not found in manifest.")

# ---------- Extraction and Packaging ----------
def extract_msi(msi_path: Path, target_dir: Path):
    """Extract an MSI file to a target directory."""
    log(f"Unpacking {msi_path.name}...")
    shutil.rmtree(target_dir, ignore_errors=True)
    subprocess.run(
        ["msiexec.exe", "/a", str(msi_path), "/qn", f"TARGETDIR={target_dir.resolve()}"],
        check=False
    )

def create_archives(version: str):
    """Create ZIP archives for each architecture folder."""
    sdk_dir = get_sub_dirs(ARCHIVES / "Windows Kits/10/bin")[0]
    for arch_dir in get_sub_dirs(sdk_dir):
        out_name = RELEASES / f"SignTool-{version}-{arch_dir.name}"
        log(f"Creating archive: {out_name}.zip")
        shutil.make_archive(out_name, "zip", arch_dir)

# ---------- Entry Point ----------
def main():
    ensure_dirs()

    # Fetch manifests and SDK info
    chman = fetch_manifest()
    version, payloads, license_url = get_sdk_package_info(chman)

    # License acceptance
    user_input = input(f"Do you accept the Microsoft Visual Studio license ({license_url}) [Y/N]? ")
    if user_input.strip().upper() not in ("Y", "YES", ""):
        sys.exit("License not accepted. Exiting...")

    # Download and extract MSI
    msi_data = download_payload(MSI_FILENAME, payloads)
    for cab_name in get_msi_cabs(msi_data):
        download_payload(cab_name, payloads)

    extract_msi(DOWNLOADS / MSI_FILENAME, ARCHIVES)
    create_archives(version)

    log("Done!")

if __name__ == "__main__":
    main()