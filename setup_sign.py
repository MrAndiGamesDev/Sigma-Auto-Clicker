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

    def __init__(self):
        """Initialize with directory paths and manifest URL."""
        self.logger = Logging.Log
        self.downloads_dir = Path("Downloads")
        self.releases_dir = Path("Releases")
        self.archives_dir = self.downloads_dir / "Archives"
        self.msi_filename = "Windows SDK Signing Tools-x86_en-us.msi"
        self.manifest_url = "https://aka.ms/vs/17/release/channel"

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _log(self, level: str, message: str) -> None:
        """Log a message using the custom logger."""
        self.logger(level, message)

    def _ensure_dirs(self) -> None:
        """Ensure required directories exist."""
        for folder in (self.downloads_dir, self.releases_dir, self.archives_dir):
            folder.mkdir(parents=True, exist_ok=True)
            self._log("info", f"Ensured directory exists: {folder}")

    def _download(self, url: str) -> bytes:
        """Download a file from the given URL and return its content."""
        self._log("info", f"Downloading from {url}...")
        try:
            with urllib.request.urlopen(url) as resp:
                return resp.read()
        except Exception as exc:
            raise RuntimeError(f"Failed to download {url}: {exc}") from exc

    def _fetch_json(self, url: str) -> dict:
        """Download and parse JSON from a URL."""
        return json.loads(self._download(url))

    # ------------------------------------------------------------------
    # Manifest / payload handling
    # ------------------------------------------------------------------

    def _fetch_manifest(self) -> dict:
        """Fetch and parse the Visual Studio channel manifest."""
        self._log("info", "Fetching Visual Studio manifest...")
        return self._fetch_json(self.manifest_url)

    def _get_sdk_package_info(self, channel_manifest: dict) -> Tuple[str, List[dict], str]:
        """Extract SDK package information and payload URLs."""
        try:
            channel_items = channel_manifest["channelItems"]
            vsman_url = channel_items[0]["payloads"][0]["url"]
            license_url = channel_items[1]["localizedResources"][0]["license"]
            vsman = self._fetch_json(vsman_url)
            for pkg in reversed(vsman["packages"]):
                if pkg["id"].startswith("Win11SDK_10.0."):
                    return pkg["version"], pkg["payloads"], license_url
            raise RuntimeError("Could not find Windows 11 SDK package info.")
        except (KeyError, IndexError) as exc:
            raise RuntimeError("Invalid manifest structure.") from exc

    # ------------------------------------------------------------------
    # MSI / CAB helpers
    # ------------------------------------------------------------------

    def _iter_cab_names(self, msi_data: bytes) -> Generator[str, None, None]:
        """Yield .cab filenames found in MSI binary content."""
        for match in re.finditer(rb"([A-Za-z0-9_\-]+\.cab)", msi_data):
            yield match.group(1).decode("ascii", errors="ignore")

    def _download_payload(self, filename: str, payloads: List[dict]) -> Path:
        """Download a specific payload by its filename; return saved Path."""
        target_path = self.downloads_dir / filename
        for payload in payloads:
            if payload["fileName"] == f"Installers\\{filename}":
                data = self._download(payload["url"])
                target_path.write_bytes(data)
                return target_path
        raise RuntimeError(f"Payload {filename} not found in manifest.")

    def _extract_msi(self, msi_path: Path, target_dir: Path) -> None:
        """Extract an MSI file to a target directory."""
        self._log("info", f"Unpacking {msi_path.name}...")
        shutil.rmtree(target_dir, ignore_errors=True)
        cmd = [
            "msiexec.exe",
            "/a",
            str(msi_path),
            "/qn",
            f"TARGETDIR={target_dir.resolve()}",
        ]
        try:
            completed = subprocess.run(cmd, check=True, capture_output=True, text=True)
            self._log("info", f"MSI extraction completed: {completed.stdout}")
        except subprocess.CalledProcessError as exc:
            raise RuntimeError(f"Failed to extract MSI {msi_path}: {exc.stderr}") from exc

    # ------------------------------------------------------------------
    # Archive creation
    # ------------------------------------------------------------------

    def _create_archives(self, version: str) -> None:
        """Create ZIP archives for each architecture folder."""
        sdk_bin_path = self.archives_dir / "Windows Kits" / "10" / "bin"
        if not sdk_bin_path.exists():
            raise RuntimeError(f"SDK binary path not found: {sdk_bin_path}")

        arch_dirs = [d for d in sdk_bin_path.iterdir() if d.is_dir()]
        if not arch_dirs:
            raise RuntimeError(f"No architecture directories found in {sdk_bin_path}")

        for arch_dir in arch_dirs:
            out_name = self.releases_dir / f"SignTool-{version}-{arch_dir.name}"
            self._log("info", f"Creating archive: {out_name}.zip")
            shutil.make_archive(out_name, "zip", arch_dir)

    # ------------------------------------------------------------------
    # Public workflow
    # ------------------------------------------------------------------

    def manage_sdk(self) -> bool:
        """Download, extract, and package the Windows SDK signing tools."""
        try:
            self._ensure_dirs()

            # Fetch manifests and SDK info
            chman = self._fetch_manifest()
            version, payloads, license_url = self._get_sdk_package_info(chman)

            # License acceptance
            prompt = f"Do you accept the Microsoft Visual Studio license ({license_url}) [Y/N]? "
            if input(prompt).strip().upper() not in {"Y", "YES", ""}:
                self._log("error", "License not accepted. Exiting...")
                return False

            # Download MSI and related CABs
            msi_path = self._download_payload(self.msi_filename, payloads)
            for cab_name in self._iter_cab_names(msi_path.read_bytes()):
                self._download_payload(cab_name, payloads)

            # Extract and package
            self._extract_msi(msi_path, self.archives_dir)
            self._create_archives(version)

            self._log("info", "Windows SDK processing completed successfully.")
            return True
        except Exception as exc:
            self._log("error", f"Failed to manage SDK: {exc}")
            return False

    def exit_script(self, duration: int = 2, level: int = 1) -> None:
        """Exit the script after a short delay."""
        self._log("info", "Exiting script.")
        sleep(duration)
        sys.exit(level)

    def run(self, duration: Optional[int] = 2) -> None:
        """Main entry point."""
        try:
            if not self.manage_sdk():
                self.exit_script(duration)
        except Exception as exc:
            Logging.Log("error", f"Unexpected error in main: {exc}")
            self.exit_script(duration)

if __name__ == "__main__":
    SDKManager = WindowsSDKManager()
    SDKManager.run()