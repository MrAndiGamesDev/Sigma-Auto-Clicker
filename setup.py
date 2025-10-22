import os
import shutil
import sys
import PyInstaller.__main__
from time import sleep
from typing import Optional, List
from src.Packages.CustomLogging import Logging # Replace this into a different module

class PyInstallerBuilder:
    """Manages the build process for creating executables using PyInstaller."""

    def __init__(self, script_file: Optional[str] = None):
        """
        Initialize the PyInstallerBuilder with script file and configuration.

        Args:
            script_file (Optional[str]): Path to the main script file to build.
                Defaults to sys.argv[1] or 'autoclicker.py'.
        """
        self.logger = Logging.Log
        self.script_file = script_file or (sys.argv[1] if len(sys.argv) > 1 else "sigma_auto_clicker.py")
        self.app_name = "Sigma Auto Clicker"
        self.version_file = "VERSION.txt"
        self.icon_path = "src/icons/mousepointer.ico"

        self._validate_script_file()
        self.pyinstaller_args = self._build_pyinstaller_args()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _validate_script_file(self) -> None:
        if not os.path.exists(self.script_file):
            self.logger("error", f"Script file '{self.script_file}' not found.")
            self._exit_script()

    def _load_version(self) -> str:
        try:
            if os.path.exists(self.version_file):
                with open(self.version_file, encoding="utf-8") as fh:
                    return fh.read().strip()
            self.logger("warning", f"Version file '{self.version_file}' not found.")
        except Exception as exc:
            self.logger("warning", f"Failed to load version from '{self.version_file}': {exc}")
        return ""

    def _get_executable_name(self) -> str:
        version = self._load_version()
        return f"{self.app_name} (v{version})" if version else self.app_name

    def _build_pyinstaller_args(self) -> List[str]:
        return [
            self.script_file,
            "--noconfirm",
            "--onefile",
            "--windowed",
            f"--name={self._get_executable_name()}",
            f"--icon={self.icon_path}",
            "--optimize=2",
            "--clean",
            f"--add-data={self.icon_path};src/icons/",
            f"--add-data={self.version_file};.",
            "--hidden-import=PySide6",
            "--hidden-import=pyautogui",
            "--hidden-import=keyboard",
            "--hidden-import=psutil",
            "--hidden-import=requests",
            "--hidden-import=sys",
            "--hidden-import=platform",
            "--hidden-import=threading",
            "--hidden-import=subprocess",
            "--hidden-import=urllib.request",
            "--hidden-import=webbrowser",
            "--hidden-import=socket",
            "--hidden-import=os",
            "--hidden-import=random",
            "--hidden-import=re",
        ]
        
    # ------------------------------------------------------------------
    # Cleanup
    # ------------------------------------------------------------------
    def _remove_directory(self, path: str) -> None:
        if not os.path.exists(path):
            self.logger("info", f"'{path}' directory not found — skipping.")
            return

        self.logger("info", f"Removing '{path}' directory...")
        try:
            shutil.rmtree(path, ignore_errors=True)
            self.logger("success", f"'{path}' directory removed successfully.")
        except Exception as exc:
            self.logger("warning", f"Failed to remove '{path}': {exc}")

    def _remove_file(self, file_path: str) -> bool:
        if not os.path.exists(file_path):
            return False

        self.logger("info", f"Removing '{file_path}'...")
        try:
            os.remove(file_path)
            self.logger("success", f"'{file_path}' removed successfully.")
            return True
        except Exception as exc:
            self.logger("warning", f"Failed to remove '{file_path}': {exc}")
            return False

    def cleanup_dirs(self) -> None:
        for folder in ("build", "dist"):
            self._remove_directory(folder)

        base_name = os.path.splitext(self.script_file)[0]
        possible_specs = [
            f"{base_name}.spec",
            "Sigma_Auto_Clicker.spec",
            "SigmaAutoClicker.spec",
            self._get_executable_name()
            .replace(" ", "_")
            .replace("(", "")
            .replace(")", "")
            + ".spec",
        ]

        removed = 0
        for spec in possible_specs:
            if self._remove_file(spec):
                removed += 1

        for entry in os.listdir("."):
            if entry.endswith(".spec") and entry not in possible_specs:
                if self._remove_file(entry):
                    removed += 1

        if not removed:
            self.logger("info", "No .spec files found to remove.")

    # ------------------------------------------------------------------
    # Build
    # ------------------------------------------------------------------
    def build_executable(self) -> None:
        self.logger("info", f"Building executable for '{self.script_file}'...")
        try:
            self.logger(
                "info", "Running PyInstaller with arguments: " + " ".join(self.pyinstaller_args)
            )
            PyInstaller.__main__.run(self.pyinstaller_args)
            self.logger(
                "success",
                f"Executable '{self._get_executable_name()}' built successfully in 'dist' folder.",
            )
        except Exception as exc:
            self.logger("error", f"PyInstaller build failed: {exc}")
            self._exit_script(2)

    # ------------------------------------------------------------------
    # Flow control
    # ------------------------------------------------------------------
    def _exit_script(self, duration: int = 1, exit_code: int = 1) -> None:
        self.logger("info", "Exiting script.")
        sleep(duration)
        sys.exit(exit_code)

    def run(self, cleanup_delay: float = 0.5) -> None:
        self.logger("info", f"Starting build process for '{self.script_file}'...")
        try:
            self.cleanup_dirs()
            sleep(cleanup_delay)
            self.build_executable()
            self.logger("success", "Build process completed successfully.")
        except Exception as exc:
            self.logger("error", f"Build process failed: {exc}")
            self._exit_script(cleanup_delay)

if __name__ == "__main__":
    PyBuilder = PyInstallerBuilder()
    PyBuilder.run()