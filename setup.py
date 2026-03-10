"""
Byte v3.0 - Setup & Installation
"""
import subprocess, sys, os, platform
from pathlib import Path

BASE = Path(__file__).parent
REQUIREMENTS = ["flask", "requests", "selenium"]

def install_deps():
    print("Installing dependencies...")
    subprocess.run([sys.executable, "-m", "pip", "install"] + REQUIREMENTS, check=False)

def create_entry_point():
    system = platform.system()
    if system == "Windows":
        import ctypes
        scripts = Path(sys.prefix) / "Scripts"
        bat_path = scripts / "byte.bat"
        python_exe = str(sys.executable).replace("/", "\\")
        buf = ctypes.create_unicode_buffer(260)
        ctypes.windll.kernel32.GetShortPathNameW(str(BASE), buf, 260)
        short_dir = buf.value if buf.value else str(BASE).replace("/", "\\")
        bat_content = "@echo off\n\"{p}\" \"{d}\\byte.py\" %*\n".format(p=python_exe, d=short_dir)
        bat_path.write_text(bat_content, encoding="cp1252")
        print("OK: {}".format(bat_path))
    elif system in ("Linux", "Darwin"):
        byte_py = BASE / "byte.py"
        local_bin = Path.home() / ".local" / "bin"
        local_bin.mkdir(parents=True, exist_ok=True)
        sp = local_bin / "byte"
        sp.write_text('#!/bin/bash\n"{}" "{}" "$@"\n'.format(sys.executable, byte_py))
        sp.chmod(0o755)
        path_env = os.environ.get("PATH", "")
        if str(local_bin) not in path_env:
            rc = Path.home() / (".bashrc" if system == "Linux" else ".zshrc")
            with open(rc, "a") as f:
                f.write('\n# Byte AI\nexport PATH="$PATH:{}"\n'.format(local_bin))
            print("Added to PATH — restart terminal")
    print("   Run: byte")

def main():
    print("\nByte v3.0 — Installation\n" + "-"*40)
    install_deps()
    create_entry_point()
    print("\nDone!\n")
    print("   byte             -> menu (first run: setup wizard)")
    print("   byte --cmd       -> direct chat")
    print("   byte --web       -> web GUI")
    print("   byte --quick Q   -> one-shot answer\n")

if __name__ == "__main__":
    main()
