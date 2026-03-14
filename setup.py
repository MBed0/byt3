"""
Byte v3.0 - Setup & Installation
"""
import subprocess, sys, os, platform
from pathlib import Path

BASE = Path(__file__).parent.resolve()
REQUIREMENTS = ["flask", "requests", "selenium"]

def install_deps():
    print("Installing dependencies...")
    subprocess.run([sys.executable, "-m", "pip", "install"] + REQUIREMENTS, check=False)

def create_entry_point():
    system = platform.system()

    if system == "Windows":
        scripts = Path(sys.prefix) / "Scripts"
        scripts.mkdir(exist_ok=True)

        bat_path = scripts / "byte.bat"
        python_exe = str(Path(sys.executable).resolve())
        byte_py = str((BASE / "byte.py").resolve())

        bat_content = f'''@echo off
"{python_exe}" "{byte_py}" %*
'''

        bat_path.write_text(bat_content, encoding="utf-8")
        print(f"OK: {bat_path}")

    elif system in ("Linux", "Darwin"):
        byte_py = BASE / "byte.py"
        local_bin = Path.home() / ".local" / "bin"
        local_bin.mkdir(parents=True, exist_ok=True)

        sp = local_bin / "byte"
        sp.write_text(f'''#!/bin/bash
"{sys.executable}" "{byte_py}" "$@"
''')

        sp.chmod(0o755)

        path_env = os.environ.get("PATH", "")
        if str(local_bin) not in path_env:
            rc = Path.home() / (".bashrc" if system == "Linux" else ".zshrc")
            with open(rc, "a") as f:
                f.write(f'\n# Byte AI\nexport PATH="$PATH:{local_bin}"\n')
            print("Added to PATH — restart terminal")

    print("Run: byte")

def main():
    print("\nByte v3.0 — Installation\n" + "-"*40)
    install_deps()
    create_entry_point()

    print("\nDone!\n")
    print("byte             -> menu")
    print("byte --cmd       -> direct chat")
    print("byte --web       -> web GUI")
    print("byte --quick Q   -> one-shot answer\n")

if __name__ == "__main__":
    main()