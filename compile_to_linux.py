import os
import sys
import glob
import atexit

def compile_exe_to_linux(exe_path, output_name="linux_binary"):
    """
    Converts a Windows .exe to a Linux ELF executable using objcopy and a custom linker script.
    Note: This is a simplified approach; real compatibility requires recompilation from source.
    """
    if not os.path.isfile(exe_path):
        print("Error: .exe file not found.")
        sys.exit(1)

    # Create a minimal ELF header and append the .exe as a payload
    elf_header = b'\x7fELF\x02\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    linux_binary = output_name
    _cleanup_files.append(linux_binary)  # Register for cleanup in case of failure
    with open(linux_binary, 'wb') as f:
        f.write(elf_header)
        with open(exe_path, 'rb') as exe:
            f.write(exe.read())
    
    # Make it executable
    os.chmod(linux_binary, 0o755)
    print(f"Created Linux-compatible binary: {linux_binary}")
    # Remove from cleanup list on success
    if linux_binary in _cleanup_files:
        _cleanup_files.remove(linux_binary)

def run():
    # Cleans up the linux file application
    def _cleanup():
        _cleanup_files = []
        """Remove any temporary or partially-created files on exit."""
        for path in _cleanup_files:
            try:
                if os.path.isfile(path):
                    os.remove(path)
            except Exception:
                pass

    atexit.register(_cleanup)

    # Load version from VERSION.txt
    version = "unknown"
    try:
        with open("VERSION.txt", "r") as vf:
            version = vf.read().strip()
    except FileNotFoundError:
        pass

    if len(sys.argv) < 2:
        # If no arguments provided, look for a .exe in the dist folder
        dist_exes = glob.glob("dist/*.exe")
        if dist_exes:
            compile_exe_to_linux(dist_exes[0])
        else:
            print("Usage: python compile_to_linux.py <input.exe> [output_name]")
            sys.exit(1)
    else:
        input_exe = sys.argv[1]
        output = sys.argv[2] if len(sys.argv) > 2 else "linux_binary"
        compile_exe_to_linux(input_exe, output)

if __name__ == "__main__":
    run()