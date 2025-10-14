import os
import shutil
import sys
import PyInstaller.__main__

def clean_build_dirs():
    folder_lists = ['build', 'dist']
    for folder in folder_lists:
        if os.path.exists(folder):
            print(f"Removing {folder} directory...")
            shutil.rmtree(folder)

def build_executable(script_file: str):
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
    build_executable(script)

if __name__ == "__main__":
    main()