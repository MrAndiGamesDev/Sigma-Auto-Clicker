import subprocess
import sys
import logging
from time import sleep
from pathlib import Path
from typing import Optional

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger()

class VirtualEnvManager:
    """Manages creation and package installation for a virtual environment."""
    def __init__(self, venv_path: str, requirements_file: str = "requirements.txt"):
        """Initialize with virtual environment path and optional requirements file."""
        self.venv_path = Path(venv_path)
        self.requirements_file = Path(requirements_file)
        self.venv_python = self._get_venv_python()

    def _get_venv_python(self) -> Path:
        """Determine the virtual environment's Python executable path."""
        if sys.platform.startswith("win"):
            return self.venv_path / "Scripts" / "python.exe"
        return self.venv_path / "bin" / "python"

    def _run_subprocess(self, command: list, success_message: str, error_message: str) -> bool:
        """Helper method to execute a subprocess command with logging."""
        try:
            subprocess.check_call(command)
            logger.info(success_message)
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"{error_message}: {e}")
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
        return False

    def setup_venv(self) -> bool:
        """Create a virtual environment if it doesn't exist."""
        if self.venv_path.exists():
            logger.info(f"Virtual environment already exists at {self.venv_path}")
            return True

        logger.info(f"Creating virtual environment at {self.venv_path}...")
        return self._run_subprocess(
            [sys.executable, "-m", "venv", str(self.venv_path)],
            f"Virtual environment created at {self.venv_path}",
            "Failed to create virtual environment"
        )

    def install_requirements(self) -> bool:
        """Install requirements from the requirements file if it exists."""
        if not self.requirements_file.exists():
            logger.warning(f"Requirements file not found at {self.requirements_file}")
            return False

        if not self.venv_python.exists():
            logger.error(f"Virtual environment Python executable not found at {self.venv_python}")
            return False

        logger.info(f"Installing requirements from {self.requirements_file} using {self.venv_python}...")
        return self._run_subprocess(
            [str(self.venv_python), "-m", "pip", "install", "-r", str(self.requirements_file)],
            f"Requirements installed from {self.requirements_file}",
            "Failed to install requirements"
        )

    def manage_venv(self) -> bool:
        """Manage the virtual environment: create and install packages."""
        if not self.venv_path.exists():
            logger.info("Virtual environment not found. Setting up environment...")
            if not self.setup_venv():
                return False

        logger.info("Virtual environment detected. Proceeding with package installation...")
        if not self.install_requirements():
            return False

        # Provide instructions for manual activation
        if sys.platform.startswith("win"):
            activate_cmd = f"{self.venv_path}\\Scripts\\Activate.ps1"
            logger.info(f"To use the virtual environment, run in PowerShell: {activate_cmd}")
        else:
            activate_cmd = f"source {self.venv_path}/bin/activate"
            logger.info(f"To use the virtual environment, run in terminal: {activate_cmd}")
        return True

    def exit_script(self, duration: int, lvl: Optional[int] = 1):
        """Exit the script with a message."""
        logger.info("Exiting script.")
        sleep(duration)
        sys.exit(lvl)

def run(duration: Optional[int] = 2, env_name="Sigma-Auto-Clicker-Py"):
    """Main entry point for the script."""
    try:
        venv_manager = VirtualEnvManager(env_name)
        if not venv_manager.manage_venv():
            venv_manager.exit_script(duration)
    except Exception as e:
        logger.error(f"Unexpected error in main: {e}")
        venv_manager.exit_script(duration)

if __name__ == "__main__":
    run()  # Adjust duration as needed