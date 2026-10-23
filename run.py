"""Create a local environment, install pinned dependencies, then launch Streamlit."""

from __future__ import annotations

import hashlib
import os
from pathlib import Path
import subprocess
import sys
import venv


def main() -> int:
    if not (3, 11) <= sys.version_info[:2] <= (3, 15):
        print("Please install Python 3.12 (or 3.11–3.15) from https://www.python.org/downloads/")
        return 1
    root = Path(__file__).resolve().parent
    os.chdir(root)
    env = root / ".venv"
    python = env / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    if not python.exists():
        print("Creating the project's .venv environment...")
        venv.EnvBuilder(with_pip=True).create(env)
    requirements = root / "requirements.txt"
    fingerprint = hashlib.sha256(requirements.read_bytes()).hexdigest()
    marker = env / ".reservoirviz-requirements"
    installed = marker.read_text().strip() if marker.exists() else ""
    if installed != fingerprint:
        print("Installing project dependencies from the Python package registry...")
        subprocess.run([str(python), "-m", "pip", "install", "-r", str(requirements)], check=True)
        marker.write_text(fingerprint)
    print("Starting ReservoirViz at http://localhost:8501 — press Ctrl+C to stop.")
    return subprocess.call([str(python), "-m", "streamlit", "run", "app.py", "--server.address=127.0.0.1"])


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        pass
    except (OSError, subprocess.CalledProcessError) as exc:
        print(f"Setup failed: {exc}\nSee README.md for manual installation steps.")
        raise SystemExit(1)
