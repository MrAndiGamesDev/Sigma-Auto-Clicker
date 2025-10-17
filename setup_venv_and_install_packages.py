from time import sleep
from pathlib import Path
import subprocess
import sys
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger()

class VirtualEnvManager:
    """Manages creation, activation, and package installation for a virtual environment."""
    def __init__(self, venv_path: str, requirements_file: str = "requirements.txt"):
        """Initialize with virtual environment path and optional requirements file."""
        self.venv_path = Path(venv_path)
        self.requirements_file = Path(requirements_file)
        self.activate_script = self._get_activate_script()

    def _get_activate_script(self) -> Path:
        """Determine the appropriate activation script based on the platform."""
        script_path = self.venv_path / "Scripts" / "Activate.ps1" if sys.platform.startswith("win") else self.venv_path / "bin" / "activate"
        return script_path

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

    def activate_venv(self) -> bool:
        """Activate the virtual environment."""
        if not self.activate_script.exists():
            logger.warning(f"Activation script not found at {self.activate_script}")
            return False

        logger.info(f"Activating virtual environment at {self.venv_path}")
        if sys.platform.startswith("win"):
            return self._run_subprocess(
                ["powershell", "-ExecutionPolicy", "Bypass", str(self.activate_script)],
                f"Virtual environment activated at {self.venv_path}",
                "Failed to activate virtual environment"
            )
            
        return self._run_subprocess(
            ["bash", "-c", f"source {self.activate_script}"],
            f"Virtual environment activated at {self.venv_path}",
            "Failed to activate virtual environment"
        )

    def install_requirements(self) -> bool:
        """Install requirements from the requirements file if it exists."""
        if not self.requirements_file.exists():
            logger.warning(f"Requirements file not found at {self.requirements_file}")
            return False

        logger.info(f"Installing requirements from {self.requirements_file}...")
        return self._run_subprocess(
            [sys.executable, "-m", "pip", "install", "-r", str(self.requirements_file)],
            f"Requirements installed from {self.requirements_file}",
            "Failed to install requirements"
        )

    def manage_venv(self) -> bool:
        """Manage the virtual environment: create, activate, and install packages."""
        if not self.venv_path.exists():
            logger.info("Virtual environment not found. Setting up environment...")
            if not self.setup_venv():
                return False

        logger.info("Virtual environment detected. Proceeding with activation and installation...")
        if not self.activate_venv() or not self.install_requirements():
            return False
        return True

    def exit_script(self, duration: int, lvl=1):
        """Exit the script with a message."""
        logger.info("Exiting script.")
        sleep(duration)
        sys.exit(lvl)

def run(duration: int):
    """Main entry point for the script."""
    try:
        venv_manager = VirtualEnvManager("AutoClickerPy")
        if not venv_manager.manage_venv():
            venv_manager.exit_script(duration)
    except Exception as e:
        logger.error(f"Unexpected error in main: {e}")
        venv_manager.exit_script(duration)

if __name__ == "__main__":
    run(2)  # Adjust duration as needed
