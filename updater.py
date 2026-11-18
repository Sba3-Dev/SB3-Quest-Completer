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


def write_log(message: str) -> None:
    try:
        log_dir = Path(os.getenv("LOCALAPPDATA", tempfile.gettempdir())) / "Sba3Dev"
        log_dir.mkdir(parents=True, exist_ok=True)
        with (log_dir / "updater.log").open("a", encoding="utf-8") as stream:
            stream.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} {message}\n")
    except OSError:
        pass


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
        # The updater is running from the installation directory. Windows
        # cannot replace a running executable; the current updater remains
        # compatible and can safely launch the newly updated application.
        if os.name == "nt" and item.name.casefold() == "sb3updater.exe":
            continue
        destination = target / item.name
        if item.is_dir():
            if destination.exists():
                shutil.rmtree(destination)
            shutil.copytree(item, destination)
        else:
            replace_file(item, destination)


def launch_app(app_path: Path) -> bool:
    if not app_path.is_file():
        write_log(f"launch skipped; app missing: {app_path}")
        return False
    env = os.environ.copy()
    env.pop("_MEIPASS2", None)
    env["PYINSTALLER_RESET_ENVIRONMENT"] = "1"
    try:
        child = subprocess.Popen([str(app_path)], cwd=str(app_path.parent), env=env,
                                 close_fds=True)
        time.sleep(0.8)
        if child.poll() is None:
            write_log(f"launch succeeded: {app_path}")
            return True
        write_log(f"launch exited immediately with code {child.returncode}")
    except OSError as error:
        write_log(f"direct launch failed: {error}")
    if os.name == "nt":
        try:
            os.startfile(str(app_path))
            write_log(f"launch fallback succeeded: {app_path}")
            return True
        except OSError as error:
            write_log(f"launch fallback failed: {error}")
    return False


def restart_app(pid: int, app_path: Path) -> int:
    """Restart a one-file PyInstaller app after its old process has fully exited."""
    wait_for_process(pid)
    time.sleep(1.0)
    return 0 if launch_app(app_path) else 5


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
        return 0 if launch_app(app_path) else 5
    finally:
        shutil.rmtree(stage, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
