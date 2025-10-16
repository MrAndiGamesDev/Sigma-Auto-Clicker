import json
import re
import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path
from time import sleep
from typing import Generator, List, Tuple, Optional
from src.Packages.CustomLogging import Logging

class WindowsSDKManager:
    """Manages downloading, extracting, and packaging Windows SDK signing tools."""
    def __init__(
        self,
        downloads_dir: str = "Downloads",
        releases_dir: str = "Releases",
        msi_filename: str = "Windows SDK Signing Tools-x86_en-us.msi",
        manifest_url: str = "https://aka.ms/vs/17/release/channel"
    ):
        """Initialize with directory paths and manifest URL."""
        self.logger = Logging.Log
        self.downloads_dir = Path(downloads_dir)
        self.releases_dir = Path(releases_dir)
        self.archives_dir = self.downloads_dir / "Archives"
        self.msi_filename = msi_filename
        self.manifest_url = manifest_url

    def _log(self, level: str, message: str) -> None:
        """Log a message using the custom logger."""
        self.logger(level, message)

    def _ensure_dirs(self) -> None:
        """Ensure required directories exist."""
        for folder in [self.downloads_dir, self.releases_dir, self.archives_dir]:
            folder.mkdir(parents=True, exist_ok=True)
            self._log("info", f"Ensured directory exists: {folder}")

    def _download(self, url: str) -> bytes:
        """Download a file from the given URL and return its content."""
        try:
            self._log("info", f"Downloading from {url}...")
            with urllib.request.urlopen(url) as resp:
                return resp.read()
        except Exception as e:
            raise RuntimeError(f"Failed to download {url}: {e}") from e

    def _get_msi_cabs(self, msi_data: bytes) -> Generator[str, None, None]:
        """Extract .cab filenames from MSI binary content."""
        for match in re.finditer(rb"([A-Za-z0-9_\-]+\.cab)", msi_data):
            yield match.group(1).decode("ascii", errors="ignore")

    def _get_sub_dirs(self, path: Path) -> List[Path]:
        """Return all subdirectories in a given path."""
        return [x for x in path.iterdir() if x.is_dir()]

    def _fetch_manifest(self) -> dict:
        """Fetch and parse the Visual Studio channel manifest."""
        self._log("info", "Fetching Visual Studio manifest...")
        data = self._download(self.manifest_url)
        return json.loads(data)

    def _get_sdk_package_info(self, channel_manifest: dict) -> Tuple[str, List[dict], str]:
        """Extract SDK package information and payload URLs."""
        try:
            vsman_url = channel_manifest["channelItems"][0]["payloads"][0]["url"]
            license_url = channel_manifest["channelItems"][1]["localizedResources"][0]["license"]
            vsman = json.loads(self._download(vsman_url))
            packages = vsman["packages"]

            for pkg in reversed(packages):
                if pkg["id"].startswith("Win11SDK_10.0."):
                    return pkg["version"], pkg["payloads"], license_url
            raise RuntimeError("Could not find Windows 11 SDK package info.")
        except (KeyError, IndexError) as e:
            raise RuntimeError("Invalid manifest structure.") from e

    def _download_payload(self, filename: str, payloads: List[dict]) -> Optional[bytes]:
        """Download a specific payload by its filename."""
        for p in payloads:
            if p["fileName"] == f"Installers\\{filename}":
                path = self.downloads_dir / filename
                data = self._download(p["url"])
                with open(path, "wb") as f:
                    f.write(data)
                return data
        raise RuntimeError(f"Payload {filename} not found in manifest.")

    def _extract_msi(self, msi_path: Path, target_dir: Path) -> None:
        """Extract an MSI file to a target directory."""
        self._log("info", f"Unpacking {msi_path.name}...")
        shutil.rmtree(target_dir, ignore_errors=True)
        try:
            result = subprocess.run(
                ["msiexec.exe", "/a", str(msi_path), "/qn", f"TARGETDIR={target_dir.resolve()}"],
                check=True,
                capture_output=True,
                text=True
            )
            self._log("info", f"MSI extraction completed: {result.stdout}")
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to extract MSI {msi_path}: {e.stderr}") from e

    def _create_archives(self, version: str) -> None:
        """Create ZIP archives for each architecture folder."""
        sdk_bin_path = self.archives_dir / "Windows Kits" / "10" / "bin"
        if not sdk_bin_path.exists():
            raise RuntimeError(f"SDK binary path not found: {sdk_bin_path}")
        
        sub_dirs = self._get_sub_dirs(sdk_bin_path)
        if not sub_dirs:
            raise RuntimeError(f"No architecture directories found in {sdk_bin_path}")
        
        for arch_dir in sub_dirs:
            out_name = self.releases_dir / f"SignTool-{version}-{arch_dir.name}"
            self._log("info", f"Creating archive: {out_name}.zip")
            shutil.make_archive(out_name, "zip", arch_dir)

    def manage_sdk(self) -> bool:
        """Manage the Windows SDK: download, extract, and package."""
        try:
            self._ensure_dirs()

            # Fetch manifests and SDK info
            chman = self._fetch_manifest()
            version, payloads, license_url = self._get_sdk_package_info(chman)

            # License acceptance
            user_input = input(f"Do you accept the Microsoft Visual Studio license ({license_url}) [Y/N]? ").strip().upper()
            if user_input not in ("Y", "YES", ""):
                self._log("error", "License not accepted. Exiting...")
                return False

            # Download and extract MSI
            msi_data = self._download_payload(self.msi_filename, payloads)
            for cab_name in self._get_msi_cabs(msi_data):
                self._download_payload(cab_name, payloads)

            self._extract_msi(self.downloads_dir / self.msi_filename, self.archives_dir)
            self._create_archives(version)
            self._log("info", "Windows SDK processing completed successfully.")
            return True
        except Exception as e:
            self._log("error", f"Failed to manage SDK: {e}")
            return False

    def exit_script(self, duration, lvl=1):
        """Exit the script with a message."""
        self._log("info", "Exiting script.")
        sleep(duration)
        sys.exit(lvl)

def run(duration):
    """Main entry point for the script."""
    try:
        sdk_manager = WindowsSDKManager()
        success = sdk_manager.manage_sdk()
        if not success:
            sdk_manager.exit_script(duration)
    except Exception as e:
        Logging.Log("error", f"Unexpected error in main: {e}")
        sdk_manager.exit_script(duration)

if __name__ == "__main__":
    run(2)