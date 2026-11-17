#!/usr/bin/env python3
"""Silent updater for SB3 Quest Completer. Used after the main process exits."""
from __future__ import annotations

import ctypes
import os
import shutil
import subprocess
import sys
import tempfile
import time
import zipfile
from pathlib import Path


def wait_for_process(pid: int) -> None:
    if os.name != "nt" or pid <= 0:
        time.sleep(0.8)
        return
    handle = ctypes.windll.kernel32.OpenProcess(0x00100000, False, pid)
    if handle:
        ctypes.windll.kernel32.WaitForSingleObject(handle, 120000)
        ctypes.windll.kernel32.CloseHandle(handle)
    else:
        time.sleep(1.0)


def replace_file(source: Path, destination: Path) -> None:
    last_error: OSError | None = None
    for attempt in range(120):
        try:
            os.replace(source, destination)
            return
        except PermissionError as error:
            last_error = error
            time.sleep(0.5 if attempt < 10 else 1.0)
    if last_error:
        raise last_error


def copy_tree(source: Path, target: Path) -> None:
    for item in source.iterdir():
        destination = target / item.name
        if item.is_dir():
            if destination.exists():
                shutil.rmtree(destination)
            shutil.copytree(item, destination)
        else:
            replace_file(item, destination)


def restart_app(pid: int, app_path: Path) -> int:
    """Restart a one-file PyInstaller app after its old process has fully exited."""
    wait_for_process(pid)
    time.sleep(1.0)
    env = os.environ.copy()
    env.pop("_MEIPASS2", None)
    env["PYINSTALLER_RESET_ENVIRONMENT"] = "1"
    subprocess.Popen([str(app_path)], cwd=str(app_path.parent), env=env, close_fds=True)
    return 0


def main() -> int:
    if len(sys.argv) == 4 and sys.argv[1] == "--restart":
        try:
            pid = int(sys.argv[2])
        except ValueError:
            pid = 0
        return restart_app(pid, Path(sys.argv[3]).resolve())
    if len(sys.argv) < 5:
        return 2
    package = Path(sys.argv[1]).resolve()
    install_dir = Path(sys.argv[2]).resolve()
    try:
        pid = int(sys.argv[3])
    except ValueError:
        pid = 0
    app_path = Path(sys.argv[4]).resolve()
    wait_for_process(pid)
    # Windows may release the executable handle just after the process signal.
    time.sleep(1.5)
    if not package.is_file() or not install_dir.is_dir():
        return 3

    stage = Path(tempfile.mkdtemp(prefix="sb3-update-"))
    try:
        with zipfile.ZipFile(package, "r") as archive:
            for member in archive.infolist():
                destination = (stage / member.filename).resolve()
                try:
                    if os.path.commonpath((str(stage), str(destination))) != str(stage):
                        return 4
                except ValueError:
                    return 4
            archive.extractall(stage)
        copy_tree(stage, install_dir)
        try:
            package.unlink(missing_ok=True)
        except OSError:
            pass
        subprocess.Popen([str(app_path)], cwd=str(install_dir), close_fds=True)
        return 0
    finally:
        shutil.rmtree(stage, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
