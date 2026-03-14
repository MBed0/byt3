"""
Byte v3.2.0 - Setup & Installation
"""
import subprocess, sys, os, platform
from pathlib import Path

BASE = Path(__file__).parent.resolve()
REQUIREMENTS = ["flask", "requests", "selenium"]

def install_deps():
    print("  Installing dependencies...")
    subprocess.run(
        [sys.executable, "-m", "pip", "install"] + REQUIREMENTS +
        ["--quiet", "--disable-pip-version-check"],
        check=False
    )
    print("  OK  Packages ready.")

def write_bat(path, content):
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="ascii", errors="replace")
        if path.exists() and path.stat().st_size > 10:
            print(f"  OK  Created: {path}")
            return True
        else:
            print(f"  FAIL  File empty or missing: {path}")
            return False
    except Exception as e:
        print(f"  FAIL  {path}: {e}")
        return False

def create_entry_point():
    system = platform.system()

    if system == "Windows":
        python_exe = str(Path(sys.executable).resolve())
        byte_py    = str((BASE / "byte.py").resolve())
        bat_content = f'@echo off\r\n"{python_exe}" "{byte_py}" %*\r\n'

        print(f"\n  Python : {python_exe}")
        print(f"  byte.py: {byte_py}\n")

        candidates = [
            Path(sys.prefix) / "Scripts" / "byte.bat",
            Path(sys.executable).parent / "byte.bat",
            BASE / "byte.bat",
        ]

        for bat_path in candidates:
            write_bat(bat_path, bat_content)

        print(f"\n  If 'byte' is not found after reopening CMD,")
        print(f"  run directly from byt3-en folder: byte.bat --cmd")

    elif system in ("Linux", "Darwin"):
        byte_py   = BASE / "byte.py"
        local_bin = Path.home() / ".local" / "bin"
        local_bin.mkdir(parents=True, exist_ok=True)
        sp = local_bin / "byte"
        sp.write_text(f'#!/bin/bash\n"{sys.executable}" "{byte_py}" "$@"\n')
        sp.chmod(0o755)
        path_env = os.environ.get("PATH", "")
        if str(local_bin) not in path_env:
            rc = Path.home() / (".bashrc" if system == "Linux" else ".zshrc")
            with open(rc, "a") as f:
                f.write(f'\n# Byte AI\nexport PATH="$PATH:{local_bin}"\n')
            print("  Added ~/.local/bin to PATH -- restart your terminal.")
        print(f"  OK  {sp}")

def main():
    print("\n  Byte v3.1 -- Installation\n  " + "-"*38)
    install_deps()
    print()
    create_entry_point()
    print("\n  Done!\n")
    print("  byte             ->  menu")
    print("  byte --cmd       ->  direct chat")
    print("  byte --web       ->  web GUI")
    print("  byte --quick Q   ->  one-shot answer\n")

if __name__ == "__main__":
    main()
