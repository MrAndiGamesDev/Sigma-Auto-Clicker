import os
import shutil
import sys
import subprocess
from time import sleep
from typing import Optional, List

class Config:
    optmization_lvl = 2
    app_name = "Sigma Auto Clicker"
    version_file = "VERSION.txt"
    collect_modules = "Sigma-Auto-Clicker-Py/"
    icon_path = "src/icons/mousepointer.ico"
    debug_mode = True

# Fallback logger if CustomLogging import fails
class _FallbackLogger:
    @staticmethod
    def Log(level: str, message: str) -> str:
        return f"[{level.upper()}] {message}"

# Debugging logger wrapper
class _DebugLogger:
    def __init__(self, base_logger):
        self.base_logger = base_logger
        self.debug_enabled = False

    def enable_debug(self, can_debug: bool):
        self.debug_enabled = can_debug

    def Log(self, level: str, message: str) -> str:
        if self.debug_enabled or level.lower() != "debug":
            return self.base_logger(level, message)
        return ""

try:
    from src.Packages.CustomLogging import Logging
    logger = _DebugLogger(Logging.Log)
except Exception:
    logger = _DebugLogger(_FallbackLogger.Log)

class PyInstallerBuilder:
    """Manages the build process for creating executables using PyInstaller."""

    # ------------------------------------------------------------------
    # Initialize helpers
    # ------------------------------------------------------------------
    def __init__(self, script_file: Optional[str] = None, enable_debug: bool = False):
        """
        Initialize the PyInstallerBuilder with script file and configuration.

        Args:
            script_file (Optional[str]): Path to the main script file to build.
                Defaults to sys.argv[1] or 'run.py'.
            enable_debug (bool): Enable debug logging.
        """
        self.logger = logger
        self.script_file = script_file or (sys.argv[1] if len(sys.argv) > 1 else "run.py")
        self.optmization_lvl = Config.optmization_lvl
        self.app_name = Config.app_name
        self.version_file = Config.version_file
        self.collect_modules = Config.collect_modules
        self.icon_path = Config.icon_path

        self.logger.enable_debug(Config.debug_mode)
        self._validate_script_file()
        self.pyinstaller_args = self._build_pyinstaller_args()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _validate_script_file(self) -> None:
        self.logger.Log("debug", f"Validating script file: {self.script_file}")
        if not os.path.exists(self.script_file):
            self.logger.Log("error", f"Script file '{self.script_file}' not found.")
            self._exit_script()

    def _load_version(self) -> str:
        self.logger.Log("debug", f"Loading version from: {self.version_file}")
        try:
            if os.path.exists(self.version_file):
                with open(self.version_file, encoding="utf-8") as fh:
                    version = fh.read().strip()
                    self.logger.Log("debug", f"Version loaded: {version}")
                    return version
            self.logger.Log("warning", f"Version file '{self.version_file}' not found.")
        except Exception as exc:
            self.logger.Log("warning", f"Failed to load version from '{self.version_file}': {exc}")
        return ""

    def _get_executable_name(self) -> str:
        version = self._load_version()
        name = f"{self.app_name} (v{version})" if version else self.app_name
        self.logger.Log("debug", f"Executable name determined: {name}")
        return name

    def _build_pyinstaller_args(self) -> List[str]:
        args = [
            self.script_file,
            "--noconfirm",
            "--noconsole",
            "--clean",
            f"--name={self._get_executable_name()}",
            f"--icon={self.icon_path}",
            f"--optimize={self.optmization_lvl}",
            f"--add-data={self.icon_path};src/icons/",
            f"--add-data={self.version_file};.",
            f"--collect-submodules={self.collect_modules}",
        ]
        self.logger.Log("debug", f"PyInstaller arguments built: {args}")
        return args

    # ------------------------------------------------------------------
    # Cleanup
    # ------------------------------------------------------------------
    def _remove_directory(self, path: str) -> None:
        self.logger.Log("debug", f"Attempting to remove directory: {path}")
        if not os.path.exists(path):
            self.logger.Log("info", f"'{path}' directory not found — skipping.")
            return
        self.logger.Log("info", f"Removing '{path}' directory...")
        try:
            shutil.rmtree(path, ignore_errors=True)
            self.logger.Log("success", f"'{path}' directory removed successfully.")
        except Exception as exc:
            self.logger.Log("warning", f"Failed to remove '{path}': {exc}")

    def _remove_file(self, file_path: str) -> bool:
        self.logger.Log("debug", f"Attempting to remove file: {file_path}")
        if not os.path.exists(file_path):
            return False
        self.logger.Log("info", f"Removing '{file_path}'...")
        try:
            os.remove(file_path)
            self.logger.Log("success", f"'{file_path}' removed successfully.")
            return True
        except Exception as exc:
            self.logger.Log("warning", f"Failed to remove '{file_path}': {exc}")
            return False

    def cleanup_dirs(self) -> None:
        self.logger.Log("debug", "Starting cleanup of directories and spec files")
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
            self.logger.Log("info", "No .spec files found to remove.")

    # ------------------------------------------------------------------
    # Build
    # ------------------------------------------------------------------
    def build_executable(self) -> None:
        self.logger.Log("info", f"Building executable for '{self.script_file}'...")
        try:
            self.logger.Log(
                "info", "Running PyInstaller with arguments: " + " ".join(self.pyinstaller_args)
            )
            # Use subprocess to ensure the build runs in a fresh interpreter
            cmd = ([sys.executable, "-m", "PyInstaller"] + self.pyinstaller_args)
            self.logger.Log("debug", f"Executing command: {cmd}")
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                self.logger.Log("error", f"PyInstaller build failed:\n{result.stderr}")
                self._exit_script(2)
            self.logger.Log(
                "success",
                f"Executable '{self._get_executable_name()}' built successfully in 'dist' folder.",
            )
        except Exception as exc:
            self.logger.Log("error", f"PyInstaller build failed: {exc}")
            self._exit_script(2)

    # ------------------------------------------------------------------
    # Flow control
    # ------------------------------------------------------------------
    def _exit_script(self, duration: Optional[int] = 1, exit_code: Optional[int] = 1) -> None:
        self.logger.Log("info", "Exiting script.")
        sleep(duration)
        sys.exit(exit_code)

    def run(self, cleanup_delay: float = 0.5) -> None:
        self.logger.Log("info", f"Starting build process for '{self.script_file}'...")
        try:
            self.cleanup_dirs()
            sleep(cleanup_delay)
            self.build_executable()
            self.logger.Log("success", "Build process completed successfully.")
        except Exception as exc:
            self.logger.Log("error", f"Build process failed: {exc}")
            self._exit_script(cleanup_delay)

if __name__ == "__main__":
    # Enable debug logging if --debug flag is provided
    enable_debug = "--debug" in sys.argv
    if enable_debug:
        sys.argv.remove("--debug")
    PyBuilder = PyInstallerBuilder(enable_debug=enable_debug)
    PyBuilder.run()