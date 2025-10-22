import os
import shutil
import sys
import subprocess
import pkg_resources
from time import sleep
from typing import Optional, List
from pathlib import Path
from importlib.metadata import distributions

# Fallback logger if CustomLogging import fails
class _FallbackLogger:
    @staticmethod
    def Log(level: str, message: str) -> None:
        print(f"[{level.upper()}] {message}")

try:
    from src.Packages.CustomLogging import Logging
    logger = Logging.Log
except Exception:
    logger = _FallbackLogger.Log


class PyInstallerBuilder:
    """Manages the build process for creating executables using PyInstaller."""

    def __init__(self, script_file: Optional[str] = None):
        """
        Initialize the PyInstallerBuilder with script file and configuration.

        Args:
            script_file (Optional[str]): Path to the main script file to build.
                Defaults to sys.argv[1] or 'sigma_auto_clicker.py'.
        """
        self.logger = logger
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
        def _collect_required_imports() -> List[str]:
            """
            Discover all top-level packages/modules that are *not* installed
            in the current environment and therefore must be explicitly
            hidden-imported so PyInstaller bundles them.
            """
            # 1. Build a set of everything that is importable from site-packages
            try:
                installed_dists = {d.metadata["Name"].lower() for d in distributions()}
            except ImportError:
                # fallback for Python < 3.8
                installed_dists = {d.project_name.lower() for d in pkg_resources.working_set}

            # Also add standard-library modules (they are always available)
            stdlib_names = {
                "sys", "platform", "threading", "subprocess", "urllib", "webbrowser",
                "socket", "os", "random", "re", "importlib", "typing", "pathlib",
                "shutil", "time", "pkg_resources"
            }

            # 2. Walk through the project folder and collect every Python file
            project_root = Path(__file__).resolve().parent
            local_modules = set()
            for py_file in project_root.rglob("*.py"):
                if py_file.name.startswith("__"):
                    continue
                relative = py_file.relative_to(project_root).with_suffix("")
                dotted = str(relative).replace(os.sep, ".")
                local_modules.add(dotted.split(".")[0])  # top-level only

            # 3. Filter out what is already satisfied (installed or stdlib)
            required = [
                mod for mod in local_modules
                if mod.lower() not in installed_dists and mod not in stdlib_names
            ]
            return required

        hidden_imports = [f"--hidden-import={m}" for m in _collect_required_imports()]

        return [
            self.script_file,
            "--noconfirm",
            "--onefile",
            "--noconsole",
            "--clean",
            f"--name={self._get_executable_name()}",
            f"--icon={self.icon_path}",
            "--optimize=2",
            f"--add-data={self.icon_path};src/icons/",
            f"--add-data={self.version_file};.",
            "--additional-hooks-dir=hooks",
            *hidden_imports
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
            # Use subprocess to ensure the build runs in a fresh interpreter
            cmd = [sys.executable, "-m", "PyInstaller"] + self.pyinstaller_args
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                self.logger("error", f"PyInstaller build failed:\n{result.stderr}")
                self._exit_script(2)
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