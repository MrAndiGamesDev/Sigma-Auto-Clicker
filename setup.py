import os
import shutil
import sys
import subprocess
import PyInstaller.__main__

def clean_build_dirs():
    for folder in ['build', 'dist']:
        if os.path.exists(folder):
            print(f"Removing {folder} directory...")
            shutil.rmtree(folder)

def install_requirements():
    req_file = 'requirements.txt'
    if os.path.exists(req_file):
        print("Installing requirements...")
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', req_file])

def build_executable(script_file):
    pyinstaller_args = [
        script_file,
        '--noconfirm',
        '--onefile',
        '--windowed',
        '--icon=src\\Assets\\icons\\mousepointer.ico',
        '--optimize=2',
        '--strip',
        '--clean',
    ]

    try:
        print("Building executable with PyInstaller...")
        PyInstaller.__main__.run(pyinstaller_args)
        print("Build completed successfully.")
    except Exception as e:
        print(f"PyInstaller failed: {e}")

def main():
    script = sys.argv[1] if len(sys.argv) > 1 else 'autoclicker.py'
    clean_build_dirs()
    install_requirements()
    build_executable(script)

if __name__ == "__main__":
    main()
