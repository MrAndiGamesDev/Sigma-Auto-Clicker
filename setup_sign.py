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
    """Orchestrates download, extraction, and packaging of Windows SDK signing tools."""

    # ------------------------------------------------------------------
    # Life-cycle
    # ------------------------------------------------------------------

    def __init__(
        self,
        *,
        downloads_root: Path = Path("Downloads"),
        releases_root: Path = Path("Releases"),
        manifest_url: str = "https://aka.ms/vs/17/release/channel",
        msi_filename: str = "Windows SDK Signing Tools-x86_en-us.msi",
    ) -> None:
        """
        Configure working directories and upstream manifest.

        Parameters
        ----------
        downloads_root : Path
            Top-level folder for cached downloads.
        releases_root : Path
            Destination folder for produced ZIP archives.
        manifest_url : str
            Visual Studio channel manifest (JSON).
        msi_filename : str
            Exact MSI name inside the manifest payloads.
        """
        self.logger = Logging.Log
        self.downloads_root = downloads_root
        self.releases_root = releases_root
        self.archives_root = self.downloads_root / "Archives"
        self.manifest_url = manifest_url
        self.msi_filename = msi_filename

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _log(self, level: str, message: str, *args) -> None:
        """Thin wrapper around the injected logger."""
        self.logger(level, message % args if args else message)

    def _ensure_dirs(self) -> None:
        """Create missing working directories idempotently."""
        for folder in (self.downloads_root, self.releases_root, self.archives_root):
            folder.mkdir(parents=True, exist_ok=True)
            self._log("debug", "Ensured directory %s", folder)

    # ------------------------------------------------------------------
    # Network I/O
    # ------------------------------------------------------------------

    def _http_get(self, url: str) -> bytes:
        """Download arbitrary binary content."""
        self._log("info", "Downloading from %s ...", url)
        try:
            with urllib.request.urlopen(url) as resp:
                return resp.read()
        except Exception as exc:
            raise RuntimeError(f"Unable to download {url}") from exc

    def _fetch_json(self, url: str) -> dict:
        """Download and parse JSON document."""
        return json.loads(self._http_get(url))

    # ------------------------------------------------------------------
    # Manifest / payload resolution
    # ------------------------------------------------------------------

    def _fetch_manifest(self) -> dict:
        """Retrieve Visual Studio channel manifest."""
        return self._fetch_json(self.manifest_url)

    def _locate_sdk_payloads(self, channel_manifest: dict) -> Tuple[str, List[dict], str]:
        """
        Extract Windows 11 SDK version, payload list, and license URL.

        Returns
        -------
        version : str
            SDK build version string.
        payloads : List[dict]
            All payload entries for the SDK MSI/CABs.
        license_url : str
            Microsoft license URL for user acceptance.
        """
        try:
            channel_items = channel_manifest["channelItems"]
            vsman_url = channel_items[0]["payloads"][0]["url"]
            license_url = channel_items[1]["localizedResources"][0]["license"]
            vsman = self._fetch_json(vsman_url)

            for pkg in reversed(vsman["packages"]):
                pkg_id = pkg["id"]
                self._log("debug", "Found package %s", pkg_id)
                if pkg_id.startswith("Win11SDK_10.0."):
                    return pkg["version"], pkg["payloads"], license_url

            raise RuntimeError("Windows 11 SDK package not found in manifest.")
        except (KeyError, IndexError) as exc:
            raise RuntimeError("Malformed manifest structure.") from exc

    # ------------------------------------------------------------------
    # MSI / CAB helpers
    # ------------------------------------------------------------------

    def _iter_cab_names(self, msi_data: bytes) -> Generator[str, None, None]:
        """Yield CAB filenames referenced inside MSI binary."""
        for match in re.finditer(rb"([A-Za-z0-9_\-]+\.cab)", msi_data):
            cab_name = match.group(1).decode("ascii", errors="ignore")
            self._log("debug", "Found CAB %s", cab_name)
            yield cab_name

    # ------------------------------------------------------------------
    # Payload caching
    # ------------------------------------------------------------------

    def _cache_payload(self, filename: str, payloads: List[dict]) -> Path:
        """
        Download and store a single payload file.

        Returns
        -------
        Path
            Absolute path to the cached file.
        """
        target = self.downloads_root / filename

        for payload in payloads:
            if payload["fileName"] == f"Installers\\{filename}":
                data = self._http_get(payload["url"])
                target.write_bytes(data)
                self._log("debug", "Cached %s (%s bytes)", target, len(data))
                return target

        raise RuntimeError(f"Payload {filename!r} not listed in manifest.")

    # ------------------------------------------------------------------
    # MSI extraction
    # ------------------------------------------------------------------

    def _extract_msi(self, msi_path: Path, extract_to: Path) -> None:
        """Silently extract MSI to a directory using msiexec."""
        self._log("info", "Extracting %s -> %s", msi_path.name, extract_to)
        if extract_to.exists():
            shutil.rmtree(extract_to)

        cmd = [
            "msiexec.exe",
            "/a",
            str(msi_path),
            "/qn",
            f"TARGETDIR={extract_to.resolve()}",
        ]
        try:
            subprocess.run(cmd, check=True, capture_output=True, text=True)
        except subprocess.CalledProcessError as exc:
            raise RuntimeError(f"msiexec failed: {exc.stderr}") from exc

    # ------------------------------------------------------------------
    # Archive creation
    # ------------------------------------------------------------------

    def _zip_architectures(self, version: str) -> None:
        """
        Create architecture-specific ZIP archives from extracted SDK tree.

        Tree layout after extraction:
            Archives/Windows Kits/10/bin/<arch>/signtool.exe
        """
        windows_sdk_kits = "Windows Kits"
        windows_sdk_root = self.archives_root / windows_sdk_kits
        windows_sdk_bin = windows_sdk_root / "10" / "bin"
        if not windows_sdk_bin.is_dir():
            raise RuntimeError(f"SDK bin directory missing: {windows_sdk_bin}")

        arch_dirs = [d for d in windows_sdk_bin.iterdir() if d.is_dir()]
        if not arch_dirs:
            raise RuntimeError(f"No architecture folders under {windows_sdk_bin}")

        for arch_dir in arch_dirs:
            zip_name = self.releases_root / f"SignTool-{version}-{arch_dir.name}"
            self._log("info", "Creating %s.zip", zip_name)
            shutil.make_archive(zip_name, "zip", arch_dir)

    # ------------------------------------------------------------------
    # Public workflow
    # ------------------------------------------------------------------

    def manage_sdk(self) -> bool:
        """
        Run the complete workflow.

        Returns
        -------
        bool
            True  – success, archives created.
            False – user rejected license or fatal error logged.
        """
        try:
            self._ensure_dirs()
            manifest = self._fetch_manifest()
            version, payloads, license_url = self._locate_sdk_payloads(manifest)
            prompt = f"Accept Microsoft Visual Studio license? {license_url} [Y/N]: "
            if input(prompt).strip().upper() not in {"Y", "YES", ""}:
                self._log("error", "License rejected – aborting.")
                return False

            # Prime cache: MSI + CABs
            msi_path = self._cache_payload(self.msi_filename, payloads)
            for cab in self._iter_cab_names(msi_path.read_bytes()):
                self._cache_payload(cab, payloads)

            self._extract_msi(msi_path, self.archives_root)
            self._zip_architectures(version)

            self._log("info", "Windows SDK signing tools packaged successfully.")
            return True
        except Exception as exc:
            self._log("error", "Workflow failure: %s", exc)
            return False

    # ------------------------------------------------------------------
    # CLI helpers
    # ------------------------------------------------------------------

    def exit_with_delay(self, code: int = 1, seconds: int = 2) -> None:
        """Exit process after a short pause (allows reading logs)."""
        self._log("info", "Exiting with code %s", code)
        sleep(seconds)
        sys.exit(code)

    def run(self, exit_code_on_failure: Optional[int] = 1) -> None:
        """
        Console entry-point.

        Parameters
        ----------
        exit_code_on_failure : Optional[int]
            Exit code when `manage_sdk()` returns False or raises.
        """
        try:
            if not self.manage_sdk():
                self.exit_with_delay(exit_code_on_failure or 1)
        except Exception as exc:
            self._log("error", "Unhandled exception: %s", exc)
            self.exit_with_delay(exit_code_on_failure or 1)


# ------------------------------------------------------------------
# Module execution
# ------------------------------------------------------------------

if __name__ == "__main__":
    SDKManager = WindowsSDKManager()
    SDKManager.run(1)