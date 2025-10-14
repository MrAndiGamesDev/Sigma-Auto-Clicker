import subprocess
import os
import sys

def setup_venv(venv_path):
    """Create a virtual environment if it doesn't exist."""
    if not os.path.exists(venv_path):
        print(f"Creating virtual environment at {venv_path}...")
        subprocess.check_call([sys.executable, '-m', 'venv', venv_path])
    else:
        print(f"Virtual environment already exists at {venv_path}")

def activate_venv(venv_path):
    """Activate the virtual environment using PowerShell."""
    activate_script = os.path.join(venv_path, 'Scripts', 'Activate.ps1')
    if os.path.exists(activate_script):
        print(f"Activating virtual environment at {venv_path}")
        subprocess.check_call(["powershell", "-ExecutionPolicy", "Bypass", activate_script])
    else:
        print(f"Activation script not found at {activate_script}. Please check the virtual environment setup.")

def install_requirements(requirements_file='requirements.txt'):
    """Install requirements from requirements.txt if it exists."""
    if os.path.exists(requirements_file):
        print("Installing requirements...")
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', requirements_file])
    else:
        print(f"{requirements_file} not found. Please provide the requirements file.")

def auto_execute_venv(project_folder):
    """Checks if the virtual environment exists. If so, activate and install packages."""
    venv_path = project_folder
    requirements_file = 'requirements.txt'
    
    # If the virtual environment exists, activate and install packages
    if os.path.exists(os.path.join(venv_path, 'Scripts', 'Activate.ps1')):
        print("Virtual environment detected. Activating and installing requirements...")
        activate_venv(venv_path)
        install_requirements(requirements_file)
    else:
        print("Virtual environment not found. Setting up environment and installing packages...")
        setup_venv(venv_path)
        activate_venv(venv_path)
        install_requirements(requirements_file)

if __name__ == "__main__":
    folder_name = "AutoClickerPy"  # Define your project folder
    auto_execute_venv(folder_name)