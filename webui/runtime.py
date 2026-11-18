"""Optional pywebview runtime for the HTML dashboard.

The legacy Tk frontend remains the fallback. This adapter keeps all system work
in Python and exposes only allow-listed UI operations to JavaScript.
"""
from __future__ import annotations

import os
import hashlib
import shutil
import subprocess
import sys
import threading
import tempfile
import time
import webbrowser
from pathlib import Path
from typing import Any

try:
    import requests
except ImportError:
    requests = None
try:
    import webview
except ImportError:
    webview = None

from .bridge import WebUiBridge


def _version_tuple(value: Any) -> tuple[int, ...]:
    parts = []
    for part in str(value or "0").strip().lstrip("vV").split("."):
        digits = "".join(char for char in part if char.isdigit())
        parts.append(int(digits or 0))
    return tuple(parts or [0])


def _module():
    import mina
    return mina


class WebRuntime:
    def __init__(self, window: Any) -> None:
        self.window = window
        self.mina = _module()
        self.games: list[dict[str, Any]] = []
        self.queue: list[dict[str, Any]] = []
        self.active: dict[str, dict[str, Any]] = {}
        self.lock = threading.RLock()
        self.closed = False
        self.health_state: dict[str, Any] = {"status": "splash", "version": self.mina.VERSION}
        self.health_checked_at = 0.0
        self.health_busy = False
        self.update_cancel_event = threading.Event()
        self.update_busy = False

    def bootstrap(self) -> dict[str, Any]:
        session = self.mina.load_discord_session()
        user = session.get("user") or {}
        user_id = str(user.get("id") or "")
        avatar_hash = str(user.get("avatar") or "")
        avatar = (f"https://cdn.discordapp.com/avatars/{user_id}/{avatar_hash}.png?size=128"
                  if user_id and avatar_hash else
                  f"https://cdn.discordapp.com/embed/avatars/{int(user_id) % 5 if user_id.isdigit() else 0}.png")
        return {
            "version": self.mina.VERSION,
            "authenticated": bool(session.get("access_token")),
            "user": user,
            "avatar": avatar,
            "games": self._public_games(),
            "queue": self._public_queue(),
        }

    def refresh_library(self) -> None:
        if not requests:
            self._notify("Requests is not installed")
            return
        threading.Thread(target=self._load_library, daemon=True, name="sb3-web-library").start()

    def health_check(self, full_check: bool = True) -> dict[str, Any]:
        """Return cached state every second; refresh network state at most every 15s."""
        if not full_check:
            return self._update_only_check()
        with self.lock:
            if self.queue or self.active:
                return {"status": "hold", "reason": "tasks_active"}
            now = time.monotonic()
            if self.health_busy or now - self.health_checked_at < 15:
                return dict(self.health_state)
            self.health_busy = True
            self.health_checked_at = now
            previous = dict(self.health_state)
        try:
            # Check the manifest first so an outdated installation is notified
            # before authentication or membership routing.
            if requests:
                try:
                    response = requests.get(self.mina.UPDATE_MANIFEST_URL,
                                            headers=self.mina.HEADERS, timeout=(3, 8))
                    response.raise_for_status()
                    manifest = response.json()
                    latest = str(manifest.get("version") or "").strip()
                    installer = str(manifest.get("installer_url") or "").strip()
                    if latest and installer and _version_tuple(latest) > _version_tuple(self.mina.VERSION):
                        state = {"status": "update", "version": self.mina.VERSION,
                                 "latest": latest, "manifest": manifest}
                        with self.lock:
                            self.health_state = state
                        return dict(state)
                except Exception:
                    pass
            valid, reason = self.mina.check_saved_discord_session(force_refresh=True)
            if not valid:
                status = "membership" if reason == "not_in_guild" else "login"
                if reason == "network" and previous.get("status") == "main":
                    status = "main"
                state = {"status": status, "reason": reason, "version": self.mina.VERSION}
            else:
                state = {"status": "main", "reason": "ok", "version": self.mina.VERSION}
            with self.lock:
                self.health_state = state
            return dict(state)
        finally:
            with self.lock:
                self.health_busy = False

    def _update_only_check(self) -> dict[str, Any]:
        """Check only the manifest; never re-check login or server membership."""
        with self.lock:
            now = time.monotonic()
            if self.health_busy or now - self.health_checked_at < 15:
                return dict(self.health_state)
            self.health_busy = True
            self.health_checked_at = now
            previous = dict(self.health_state)
        try:
            if requests:
                try:
                    response = requests.get(self.mina.UPDATE_MANIFEST_URL,
                                            headers=self.mina.HEADERS, timeout=(3, 8))
                    response.raise_for_status()
                    manifest = response.json()
                    latest = str(manifest.get("version") or "").strip()
                    installer = str(manifest.get("installer_url") or "").strip()
                    if latest and installer and _version_tuple(latest) > _version_tuple(self.mina.VERSION):
                        state = {"status": "update", "version": self.mina.VERSION,
                                 "latest": latest, "manifest": manifest}
                        with self.lock:
                            self.health_state = state
                        return dict(state)
                except Exception:
                    pass
            return previous
        finally:
            with self.lock:
                self.health_busy = False

    def open_login(self) -> None:
        threading.Thread(target=self._login_worker, daemon=True, name="sb3-web-login").start()

    def _login_worker(self) -> None:
        try:
            # Reuse the existing OAuth callback and token exchange, but force its
            # login helper to use the system browser rather than a nested WebView.
            old_webview = self.mina.webview
            self.mina.webview = None
            try:
                valid, reason = self.mina.discord_login()
            finally:
                self.mina.webview = old_webview
            if valid:
                self._evaluate("window.sb3Web.showScreen('main'); window.pywebview.api.bootstrap().then(window.sb3Web.bootstrap)")
                self.refresh_library()
            elif reason == "not_in_guild":
                self._evaluate("window.sb3Web.showScreen('membership')")
            else:
                self._notify("Discord login could not be completed")
        except Exception as exc:
            self._notify(f"Login failed: {exc}")

    def open_support(self) -> None:
        webbrowser.open_new_tab(self.mina.SUPPORT_DISCORD_URL)

    def refresh_membership(self) -> None:
        def worker() -> None:
            try:
                valid, _reason = self.mina.check_saved_discord_session(force_refresh=True)
                if valid:
                    self._evaluate("window.sb3Web.showScreen('main'); window.pywebview.api.bootstrap().then(window.sb3Web.bootstrap)")
                    self.refresh_library()
                else:
                    self._notify("You are not a member of the required server yet")
            except Exception as exc:
                self._notify(f"Membership check failed: {exc}")
        threading.Thread(target=worker, daemon=True, name="sb3-web-membership").start()

    def logout(self) -> None:
        self.stop_all()
        self.mina.clear_discord_session()
        self._evaluate("window.sb3Web.showScreen('login')")

    def install_update(self) -> None:
        with self.lock:
            if self.update_busy:
                return
            self.update_busy = True
        self.update_cancel_event.clear()
        with self.lock:
            manifest = dict(self.health_state.get("manifest") or {})
        if not manifest:
            with self.lock:
                self.update_busy = False
            self._notify("Update information is not ready yet")
            return
        self._evaluate("document.getElementById('update-button').hidden=true;document.getElementById('cancel-update').hidden=false")
        threading.Thread(target=self._download_update_worker, args=(manifest,),
                         daemon=True, name="sb3-web-update-download").start()

    def cancel_update(self) -> None:
        with self.lock:
            if self.update_busy:
                self.update_cancel_event.set()
        self._update_ui("Cancelling update…")

    def _update_ui(self, message: str, ratio: float | None = None) -> None:
        payload = self._json(str(message))
        progress = ""
        if ratio is not None:
            progress = f";document.getElementById('update-progress-fill').style.width='{max(0,min(100,ratio*100)):.1f}%'"
        self._evaluate(f"document.getElementById('update-status').textContent={payload}{progress}")

    def _download_update_worker(self, manifest: dict[str, Any]) -> None:
        temp_path: Path | None = None
        try:
            if os.name != "nt":
                raise RuntimeError("Windows installer can only run on Windows")
            package_url = str(manifest.get("package_url") or "").strip()
            latest = str(manifest.get("version") or "latest").strip()
            if not package_url:
                raise ValueError("update package URL is missing")
            self._evaluate("document.getElementById('update-button').disabled=true")
            self._update_ui("Downloading update…", 0.0)
            download = requests.get(package_url, timeout=(10, 120), stream=True)
            download.raise_for_status()
            total = int(download.headers.get("content-length") or manifest.get("package_size") or 0)
            received = 0
            temp_path = Path(tempfile.gettempdir()) / f"SB3QuestCompleter-update-{latest}.zip"
            with temp_path.open("wb") as target:
                for chunk in download.iter_content(chunk_size=1024 * 1024):
                    if not chunk:
                        continue
                    if self.update_cancel_event.is_set():
                        temp_path.unlink(missing_ok=True)
                        self._evaluate("document.getElementById('update-button').hidden=false;document.getElementById('cancel-update').hidden=true;document.getElementById('update-progress-fill').style.width='0%'")
                        self._update_ui("Update cancelled")
                        return
                    target.write(chunk)
                    received += len(chunk)
                    self._update_ui(f"Downloading update… {int(received / total * 100) if total else 0}%",
                                    received / total if total else None)
            expected_hash = str(manifest.get("package_sha256") or manifest.get("sha256") or "").strip().casefold()
            if expected_hash:
                digest = hashlib.sha256(temp_path.read_bytes()).hexdigest().casefold()
                if digest != expected_hash:
                    raise ValueError("update checksum mismatch")
            install_dir = Path(sys.executable).resolve().parent
            app_path = Path(sys.executable).resolve()
            updater_path = install_dir / "SB3Updater.exe"
            if not updater_path.exists():
                updater_path = self.mina.resource_path("SB3Updater.exe")
            if not updater_path.exists():
                raise FileNotFoundError("SB3Updater.exe is missing")
            self._update_ui("Installing update…", 1.0)
            subprocess.Popen([str(updater_path), str(temp_path), str(install_dir),
                              str(os.getpid()), str(app_path)], close_fds=True)
            threading.Timer(0.2, lambda: os._exit(0)).start()
        except Exception as exc:
            if temp_path:
                try:
                    temp_path.unlink(missing_ok=True)
                except OSError:
                    pass
            self._evaluate("document.getElementById('update-button').hidden=false;document.getElementById('cancel-update').hidden=true")
            self._update_ui(f"Update failed: {exc}")
        finally:
            with self.lock:
                self.update_busy = False

    def _load_library(self) -> None:
        try:
            response = requests.get(self.mina.DISCORD_DETECTABLE_URL,
                                    headers=self.mina.HEADERS, timeout=(5, 30))
            response.raise_for_status()
            data = response.json()
            if isinstance(data, dict):
                data = data.get("applications") or data.get("games") or data.get("data") or []
            games = []
            for raw in data if isinstance(data, list) else []:
                if not isinstance(raw, dict) or not raw.get("id") or not raw.get("name"):
                    continue
                item = dict(raw)
                item["_public_name"] = self.mina.display_name(item["name"])
                item["_exe"] = self.mina.win_executable(item)
                item["_platforms"] = self.mina.platforms_for_game(item)
                item["_featured_rank"] = self.mina.newest_game_rank(item["id"])
                games.append(item)
            games.sort(key=lambda item: (item["_featured_rank"], item["_public_name"].casefold()))
            with self.lock:
                self.games = games
            self._evaluate("window.sb3Web.setGames(%s)" % self._json(self._public_games()))
            self._notify("Discord library ready")
        except Exception as exc:
            self._notify(f"Library unavailable: {exc}")

    def add_to_queue(self, game_id: str) -> None:
        with self.lock:
            game = next((g for g in self.games if str(g.get("id")) == game_id), None)
            if not game or any(str(g.get("id")) == game_id for g in self.queue):
                return
            item = dict(game)
            item["exe"] = {"name": item.get("_exe") or ""}
            self.queue.append(item)
        self._sync_queue()

    def remove_from_queue(self, game_id: str) -> None:
        self.stop_quest(game_id)
        with self.lock:
            self.queue = [g for g in self.queue if str(g.get("id")) != game_id]
        self._sync_queue()

    def run_quest(self, game_id: str) -> bool:
        with self.lock:
            quest = next((g for g in self.queue if str(g.get("id")) == game_id), None)
        if not quest or game_id in self.active:
            return False
        platforms = self.mina.platforms_for_game(quest) or tuple(quest.get("_platforms") or ())
        if not platforms:
            self._notify("No verified PC launcher found")
            return False
        try:
            self._start_process(quest, platforms[0])
        except Exception as exc:
            self._notify(f"Launch failed: {exc}")
            return False
        return True

    def _start_process(self, quest: dict[str, Any], platform: str) -> None:
        qid = str(quest["id"])
        session_id = str(int(time.time()))
        full_path = str((quest.get("exe") or {}).get("name") or "game.exe").replace("\\", "/").lstrip("/")
        exe_dir, exe_file = os.path.split(full_path) if "/" in full_path else ("", full_path)
        base = Path.cwd() / "games" / qid / session_id / exe_dir
        base.mkdir(parents=True, exist_ok=True)
        temp_exe = base / (exe_file or "game.exe")
        source = Path(sys.executable if getattr(sys, "frozen", False) else sys.argv[0]).resolve()
        shutil.copy2(source, temp_exe)
        icon = self.mina.resource_path("logo.ico")
        if icon.exists():
            shutil.copy2(icon, base / "logo.ico")
        stop_signal = base / "stop.signal"
        command = ([str(temp_exe), "--run-game", quest["name"], platform, str(stop_signal)]
                   if getattr(sys, "frozen", False) else
                   [sys.executable, str(temp_exe), "--run-game", quest["name"], platform, str(stop_signal)])
        proc = subprocess.Popen(command, cwd=str(base))
        rpc = None
        presence = getattr(self.mina, "Presence", None)
        if presence:
            for _ in range(3):
                try:
                    rpc = presence(str(quest["id"]))
                    rpc.connect()
                    rpc.update(state=f"Quest Active ({platform})", details=f"Playing {quest['name']}",
                               start=int(time.time()), instance=False)
                    break
                except Exception:
                    rpc = None
                    time.sleep(1)
        with self.lock:
            self.active[qid] = {"proc": proc, "stop_signal": stop_signal,
                                 "session_path": Path.cwd() / "games" / qid,
                                 "started_at": time.monotonic(), "rpc": rpc,
                                 "started_epoch": int(time.time()),
                                 "platform": platform,
                                 "display_name": quest.get("_public_name") or quest.get("name")}
        self._sync_queue()
        threading.Thread(target=self._watch_process, args=(qid, proc), daemon=True,
                         name=f"sb3-web-watch-{qid}").start()
        if rpc:
            threading.Thread(target=self._rpc_loop, args=(qid, rpc, proc, quest, platform),
                             daemon=True, name=f"sb3-web-rpc-{qid}").start()

    def _rpc_loop(self, qid: str, rpc: Any, proc: Any, quest: dict[str, Any], platform: str) -> None:
        while True:
            with self.lock:
                if qid not in self.active:
                    return
                started_epoch = int(self.active[qid].get("started_epoch") or time.time())
            if proc.poll() is not None:
                return
            try:
                rpc.update(state=f"Quest Active ({platform})", details=f"Playing {quest['name']}",
                           start=started_epoch, instance=False)
            except Exception:
                return
            time.sleep(15)

    def _watch_process(self, qid: str, proc: Any) -> None:
        proc.wait()
        with self.lock:
            data = self.active.pop(qid, None)
        if data:
            rpc = data.get("rpc")
            if rpc:
                try:
                    rpc.close()
                except Exception:
                    pass
            shutil.rmtree(data["session_path"], ignore_errors=True)
        self._sync_queue()

    def stop_quest(self, game_id: str) -> None:
        with self.lock:
            data = self.active.pop(game_id, None)
        if not data:
            return
        try:
            Path(data["stop_signal"]).touch(exist_ok=True)
            proc = data.get("proc")
            if proc and proc.poll() is None:
                if os.name == "nt":
                    subprocess.run(["taskkill", "/F", "/T", "/PID", str(proc.pid)],
                                   capture_output=True, timeout=5)
                else:
                    proc.kill()
        except (OSError, subprocess.TimeoutExpired):
            pass
        rpc = data.get("rpc")
        if rpc:
            try:
                rpc.close()
            except Exception:
                pass
        shutil.rmtree(data["session_path"], ignore_errors=True)
        self._sync_queue()

    def stop_all(self) -> None:
        for game_id in list(self.active):
            self.stop_quest(str(game_id))

    def close(self) -> None:
        self.closed = True
        self.stop_all()

    def _public_games(self) -> list[dict[str, Any]]:
        with self.lock:
            result = []
            for g in self.games:
                icon_hash = g.get("icon_hash") or g.get("icon")
                icon = (self.mina.DISCORD_ICON_URL.format(app_id=g.get("id"), icon_hash=icon_hash)
                        if icon_hash else str(g.get("icon_url") or ""))
                result.append({"id": g.get("id"), "name": g.get("_public_name") or g.get("name"),
                               "platform": (g.get("_platforms") or [None])[0],
                               "icon": icon, "has_icon": bool(icon)})
            return result

    def _public_queue(self) -> list[dict[str, Any]]:
        with self.lock:
            return [{"id": g.get("id"), "name": g.get("_public_name") or g.get("name"),
                     "running": str(g.get("id")) in self.active,
                     "elapsed": int(max(0, time.monotonic() - self.active[str(g.get("id"))]["started_at"]))
                     if str(g.get("id")) in self.active else 0} for g in self.queue]

    def _sync_queue(self) -> None:
        self._evaluate("window.sb3Web.setQueue(%s)" % self._json(self._public_queue()))

    def _notify(self, message: str) -> None:
        self._evaluate("window.sb3Web.notify(%s)" % self._json(str(message)))

    def _evaluate(self, script: str) -> None:
        if self.closed:
            return
        try:
            self.window.evaluate_js(script)
        except Exception:
            pass

    @staticmethod
    def _json(value: Any) -> str:
        import json
        return json.dumps(value, ensure_ascii=False)


def launch_web_ui() -> bool:
    """Launch the HTML dashboard; Tk remains the fallback if WebView2 fails."""
    if not webview or os.getenv("SB3_WEB_UI", "1") != "1":
        return False
    mina = _module()
    runtime_holder: dict[str, WebRuntime] = {}

    bridge = WebUiBridge(
        state_provider=lambda: runtime_holder["runtime"].bootstrap() if "runtime" in runtime_holder else {},
        on_refresh=lambda: runtime_holder.get("runtime") and runtime_holder["runtime"].refresh_library(),
        on_health=lambda full_check=True: runtime_holder["runtime"].health_check(full_check) if "runtime" in runtime_holder else {},
        on_login=lambda: runtime_holder.get("runtime") and runtime_holder["runtime"].open_login(),
        on_support=lambda: runtime_holder.get("runtime") and runtime_holder["runtime"].open_support(),
        on_membership=lambda: runtime_holder.get("runtime") and runtime_holder["runtime"].refresh_membership(),
        on_logout=lambda: runtime_holder.get("runtime") and runtime_holder["runtime"].logout(),
        on_update=lambda: runtime_holder.get("runtime") and runtime_holder["runtime"].install_update(),
        on_cancel_update=lambda: runtime_holder.get("runtime") and runtime_holder["runtime"].cancel_update(),
        on_add=lambda game_id: runtime_holder.get("runtime") and runtime_holder["runtime"].add_to_queue(game_id),
        on_remove=lambda game_id: runtime_holder.get("runtime") and runtime_holder["runtime"].remove_from_queue(game_id),
        on_run=lambda game_id: runtime_holder.get("runtime") and runtime_holder["runtime"].run_quest(game_id),
        on_stop=lambda game_id: runtime_holder.get("runtime") and runtime_holder["runtime"].stop_quest(game_id),
        on_stop_all=lambda: runtime_holder.get("runtime") and runtime_holder["runtime"].stop_all(),
    )

    def on_loaded() -> None:
        runtime = runtime_holder.get("runtime")
        if runtime:
            runtime.refresh_library()

    def create() -> None:
        window = webview.create_window("SB3 Quest Completer", str(mina.resource_path("webui/index.html")),
                                       width=1180, height=820, min_size=(980, 640),
                                       js_api=bridge)
        runtime = WebRuntime(window)
        runtime_holder["runtime"] = runtime
        window.events.loaded += on_loaded
        window.events.closed += lambda: runtime.close()

    try:
        # A single webview event loop is used; no nested OAuth webview is created.
        create()
        webview.start(debug=False)
        return True
    except Exception:
        runtime = runtime_holder.get("runtime")
        if runtime:
            runtime.close()
        return False
