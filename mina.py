#!/usr/bin/env python3
"""SB3 Quest Completer — fast Discord game-library desktop UI."""
from __future__ import annotations

import io
import base64
import hashlib
import http.server
import json
import os
import queue
import secrets
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import webbrowser
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any, Callable
from urllib.parse import parse_qs, urlencode, urlparse

try:
    import tkinter as tk
    from tkinter import filedialog, messagebox, ttk
except ImportError as exc:
    raise SystemExit("Tkinter is required. Install Python with Tcl/Tk enabled.") from exc
try:
    import requests
except ImportError:
    requests = None
try:
    from PIL import Image, ImageDraw, ImageGrab, ImageOps, ImageTk
except ImportError:
    Image = ImageDraw = ImageGrab = ImageOps = ImageTk = None
try:
    from pypresence import Presence
except ImportError:
    Presence = None
try:
    import webview
except ImportError:
    webview = None

APP_NAME = "SB3 Quest Completer"
VERSION = "0.4.5"
# Set this to the raw URL of the public update.json file in your GitHub repository.
# Example: https://raw.githubusercontent.com/OWNER/REPO/main/update.json
UPDATE_MANIFEST_URL = os.getenv(
    "SB3_UPDATE_MANIFEST_URL",
    "https://raw.githubusercontent.com/awas123456awas-png/-SB3-Quest-Completer/main/update.json",
)
# Burgundy Minimal: هرم لوني هادئ وواضح، من دون تباين قاسٍ أو تأثيرات مشتّتة.
# الخلفية الداكنة الموحّدة تُبقي التركيز على محتوى المكتبة والقوائم.
BG = "#0E080A"              # خلفية خارجية هادئة ودافئة
PANEL = "#1B0C10"           # سطح اللوحات الرئيسية
CARD = "#251217"            # بطاقات الألعاب والمهام
CARD_HOVER = "#321A20"      # تمييز لطيف عند المرور
INPUT = "#160A0D"           # حقل البحث، أغمق بدرجة بسيطة لراحة العين
BORDER = "#3B2026"          # فواصل وحدود خافتة
TEXT = "#F7EFF0"            # نص رئيسي ناعم وعالي الوضوح
TEXT_DIM = "#CCB8BC"        # نص ثانوي
MUTED = "#967B81"           # نص مساعد وخافت
RED = "#A7474D"             # لون الإجراء الرئيسي
RED_HOVER = "#B9585E"       # تفاعل هادئ عند المرور
RED_DARK = "#3D161C"        # زر الإيقاف — أحمر داكن واضح
RED_DARK_HOVER = "#552128"  # تفاعل زر الإيقاف
SUCCESS = "#83A38B"         # حالة النجاح

# إعدادات مظهر محلية: الوضع الافتراضي الهادئ ووضع تباين أوضح للقراءة.
BURGUNDY_PALETTE = {
    "BG": "#0E080A", "PANEL": "#1B0C10", "CARD": "#251217", "CARD_HOVER": "#321A20",
    "INPUT": "#160A0D", "BORDER": "#3B2026", "TEXT": "#F7EFF0", "TEXT_DIM": "#CCB8BC",
    "MUTED": "#967B81", "RED": "#A7474D", "RED_HOVER": "#B9585E",
    "RED_DARK": "#3D161C", "RED_DARK_HOVER": "#552128", "SUCCESS": "#83A38B",
}
HIGH_CONTRAST_PALETTE = {
    "BG": "#090607", "PANEL": "#191014", "CARD": "#2A171D", "CARD_HOVER": "#43242C",
    "INPUT": "#120A0D", "BORDER": "#74414D", "TEXT": "#FFFFFF", "TEXT_DIM": "#E7D4D9",
    "MUTED": "#C5A8AF", "RED": "#CF5D67", "RED_HOVER": "#E16F78",
    "RED_DARK": "#571C26", "RED_DARK_HOVER": "#742635", "SUCCESS": "#9DC8A8",
}

UI_TEXT = {
    "en": {
        "settings": "Settings", "settings_title": "Settings", "settings_note": "Changes are saved locally and apply immediately.",
        "text_size": "Text size", "contrast": "Contrast", "language": "Language",
        "small": "Small", "default": "Default", "large": "Large", "xl": "XL",
        "calm": "Calm", "high_contrast": "High contrast", "support": "Support",
        "featured_games": "Featured Discord games", "preparing_library": "Preparing your library",
        "search_hint": "Search by game name or Discord task/application ID", "load_more": "Load more",
        "quest_queue": "Quest queue", "stop_all": "Stop all", "selected": "selected",
        "queue_help": "Add a game from the library. Only verified PC launchers for that game are shown.",
        "empty_queue": "Your queue is empty.", "add": "Add", "run": "Run", "stop": "Stop", "retry": "Retry",
        "library_loading": "Library · Loading", "ready": "● Ready", "no_results": "No games match your search.",
        "loading_games": "LOADING DISCORD GAMES", "loading_wait": "Please wait while the library is being prepared.",
        "library_ready": "● Discord library ready", "library_unavailable": "Library · Unavailable",
        "library_error": "Discord library could not be loaded.", "connection_retry": "Check your connection, then try loading the library again.",
        "showing": "Showing {shown:,} of {total:,}", "no_launcher_title": "No verified launcher",
        "no_launcher_message": "No verified PC launcher was found for {name}. Discord is not shown as a launcher option.",
        "available_platforms": "Available platforms", "choose_launcher": "Choose a verified launcher",
        "already_queue": "● Game is already in the queue", "added": "● Added: {name}",
        "stopped_tasks": "● Stopped {count} active task(s)",
        "support_title": "Sba3 Dev Support", "support_message": "Join our Discord server for support and updates.",
        "join_support": "Join Discord server", "logout": "Sign out",
        "auth_subtitle": "Discord access required", "login_title": "Sign in with Discord",
        "login_message": "Sign in with your Discord account to continue.", "login_button": "Sign in with Discord",
        "checking_session": "Checking saved Discord session...", "checking_updates": "Checking for updates...",
        "membership_subtitle": "Discord server access", "membership_title": "To use the app, join the SB3 server",
        "membership_message": "Click the button, join the server, then return to the app.",
        "membership_error": "There was an error joining. Please try again.", "join_button": "Join the server", "refresh_membership": "Refresh",
        "update_subtitle": "Application update", "update_title": "A new update is available",
        "current_version": "Current version: {version}", "new_version": "New version: {version}",
        "update_button": "Update now", "downloading_update": "Downloading update...",
        "cancel_update": "Cancel", "update_cancelled": "Update cancelled.",
        "update_error": "There was an error updating. Please try again.", "download_speed": "Speed: {speed}/s",
        "time_remaining": "Time remaining: {time}", "launching_update": "Launching the installer...",
        "installer_size": "Installer size: {size}",
    },
    "ar": {
        "settings": "الإعدادات", "settings_title": "الإعدادات", "settings_note": "تُحفظ التغييرات محليًا وتُطبّق فورًا.",
        "text_size": "حجم النص", "contrast": "التباين", "language": "اللغة",
        "small": "صغير", "default": "افتراضي", "large": "كبير", "xl": "كبير جدًا",
        "calm": "هادئ", "high_contrast": "تباين عالٍ", "support": "الدعم",
        "featured_games": "ألعاب Discord المميزة", "preparing_library": "يتم تجهيز المكتبة",
        "search_hint": "ابحث باسم اللعبة أو معرّف مهمة/تطبيق Discord", "load_more": "عرض المزيد",
        "quest_queue": "قائمة المهام", "stop_all": "إيقاف الكل", "selected": "محددة",
        "queue_help": "أضف لعبة من المكتبة. تظهر فقط منصات الكمبيوتر المعتمدة لهذه اللعبة.",
        "empty_queue": "قائمة المهام فارغة.", "add": "إضافة", "run": "تشغيل", "stop": "إيقاف", "retry": "إعادة المحاولة",
        "library_loading": "المكتبة · جارٍ التحميل", "ready": "● جاهز", "no_results": "لا توجد ألعاب مطابقة للبحث.",
        "loading_games": "جارٍ تحميل ألعاب Discord", "loading_wait": "يرجى الانتظار أثناء تجهيز المكتبة.",
        "library_ready": "● مكتبة Discord جاهزة", "library_unavailable": "المكتبة · غير متاحة",
        "library_error": "تعذر تحميل مكتبة Discord.", "connection_retry": "تحقق من الاتصال ثم حاول تحميل المكتبة مجددًا.",
        "showing": "عرض {shown:,} من {total:,}", "no_launcher_title": "لا توجد منصة معتمدة",
        "no_launcher_message": "لم يتم العثور على منصة كمبيوتر معتمدة للعبة {name}. لا يتم عرض Discord كمنصة تشغيل.",
        "available_platforms": "المنصات المتاحة", "choose_launcher": "اختر منصة تشغيل معتمدة",
        "already_queue": "● اللعبة موجودة في قائمة المهام", "added": "● تمت الإضافة: {name}",
        "stopped_tasks": "● تم إيقاف {count} من المهام النشطة",
        "support_title": "دعم Sba3 Dev", "support_message": "انضم إلى سيرفر Discord للدعم والحصول على آخر التحديثات.",
        "join_support": "انضم إلى سيرفر Discord", "logout": "تسجيل الخروج",
        "auth_subtitle": "تسجيل الدخول عبر Discord", "login_title": "تسجيل الدخول عبر Discord",
        "login_message": "سجّل دخولك بحساب Discord للمتابعة إلى الأداة.", "login_button": "تسجيل الدخول عبر Discord",
        "checking_session": "جارٍ فحص جلسة Discord المحفوظة...", "checking_updates": "جارٍ فحص التحديثات...",
        "membership_subtitle": "الوصول إلى سيرفر Discord", "membership_title": "لاستخدام الأداة يجب عليك الانضمام إلى سيرفر SB3",
        "membership_message": "اضغط الزر، انضم إلى السيرفر، ثم ارجع إلى الأداة.",
        "membership_error": "حدث خطأ في الانضمام، يرجى المحاولة مرة أخرى.", "join_button": "انضمام إلى السيرفر", "refresh_membership": "تحديث",
        "update_subtitle": "تحديث التطبيق", "update_title": "يتوفر تحديث جديد",
        "current_version": "النسخة الحالية: {version}", "new_version": "النسخة الجديدة: {version}",
        "update_button": "تحديث الآن", "downloading_update": "جارٍ تنزيل التحديث...",
        "cancel_update": "إلغاء", "update_cancelled": "تم إلغاء التحديث.",
        "update_error": "حدث خطأ في التحديث، يرجى المحاولة مرة أخرى.", "download_speed": "السرعة: {speed}/ث",
        "time_remaining": "الوقت المتبقي: {time}", "launching_update": "جارٍ تشغيل المثبت...",
        "installer_size": "حجم التثبيت: {size}",
    },
}


def rounded_photo(width: int, height: int, radius: int, fill: str, background: str,
                  underlay: Image.Image | None = None) -> object | None:
    """Render a supersampled rounded surface, optionally preserving the real pixels behind its corners."""
    if not (Image and ImageDraw and ImageTk) or width < 2 or height < 2:
        return None
    scale = 4
    pixel_width, pixel_height = width * scale, height * scale
    if underlay is not None:
        image = underlay.convert("RGB").resize((pixel_width, pixel_height), Image.Resampling.LANCZOS)
    else:
        image = Image.new("RGB", (pixel_width, pixel_height), background)
    draw = ImageDraw.Draw(image)
    # A small inset keeps corner pixels equal to the parent background. It also remains valid
    # during Tk's transient 1–2 px layout passes before the widget reaches its final size.
    inset = max(1, scale // 2)
    max_radius = max(1, min((pixel_width - 2 * inset) // 2, (pixel_height - 2 * inset) // 2))
    draw.rounded_rectangle((inset, inset, pixel_width - inset - 1, pixel_height - inset - 1),
                           radius=max(1, min(radius * scale, max_radius)), fill=fill)
    return ImageTk.PhotoImage(image.resize((width, height), Image.Resampling.LANCZOS))


class PillButton(tk.Canvas):
    """Small canvas button with fully rounded, low-contrast surfaces."""

    def __init__(self, parent: tk.Misc, text: str, command: Callable[[], None] | None = None,
                 fill: str = RED, hover_fill: str = RED_HOVER, text_color: str = "white",
                 font: tuple = ("Segoe UI", 9, "bold"), width: int = 104, height: int = 36,
                 background: str | None = None) -> None:
        self._text = text
        self._command = command
        self._fill = fill
        self._hover_fill = hover_fill
        self._text_color = text_color
        self._font = font
        self._hovered = False
        self._pressed = False
        self._radius = max(12, height // 2)
        try:
            canvas_bg = background or str(parent.cget("bg"))
        except tk.TclError:
            canvas_bg = BG
        self._canvas_bg = canvas_bg
        self._photo = None
        super().__init__(parent, width=width, height=height, bg=canvas_bg, bd=0,
                         highlightthickness=0, cursor="hand2", takefocus=1)
        self.bind("<Configure>", lambda _event: self._draw())
        self.bind("<Enter>", self._enter)
        self.bind("<Leave>", self._leave)
        self.bind("<ButtonPress-1>", self._press)
        self.bind("<ButtonRelease-1>", self._release)
        self.bind("<Return>", lambda _event: self.invoke())
        self.bind("<space>", lambda _event: self.invoke())
        self.after_idle(self._draw)

    def _draw(self) -> None:
        self.delete("pill")
        width, height = max(2, self.winfo_width()), max(2, self.winfo_height())
        fill = self._hover_fill if (self._hovered or self._pressed) else self._fill
        self._photo = rounded_photo(width, height, min(self._radius, height // 2), fill, self._canvas_bg)
        if self._photo:
            self.create_image(0, 0, image=self._photo, anchor="nw", tags="pill")
        else:
            self.create_rectangle(0, 0, width, height, fill=fill, outline="", tags="pill")
        self.create_text(width // 2, height // 2, text=self._text, fill=self._text_color,
                         font=self._font, tags="pill")

    def _enter(self, _event=None) -> None:
        self._hovered = True
        self._draw()

    def _leave(self, _event=None) -> None:
        self._hovered = False
        self._pressed = False
        self._draw()

    def _press(self, _event=None) -> None:
        self._pressed = True
        self._draw()

    def _release(self, event=None) -> None:
        was_pressed = self._pressed
        self._pressed = False
        self._draw()
        if was_pressed and event and 0 <= event.x <= self.winfo_width() and 0 <= event.y <= self.winfo_height():
            self.invoke()

    def invoke(self) -> None:
        if self._command:
            self._command()

    def set_canvas_background(self, color: str) -> None:
        self._canvas_bg = color
        self.configure(bg=color)
        self._draw()


class RoundedSurface(tk.Canvas):
    """Canvas-backed container that gives regular Tk content softly rounded edges."""

    def __init__(self, parent: tk.Misc, fill: str = PANEL, radius: int = 20,
                 width: int = 320, height: int = 200, background: str | None = None,
                 background_image: Image.Image | None = None) -> None:
        try:
            canvas_bg = background or str(parent.cget("bg"))
        except tk.TclError:
            canvas_bg = BG
        super().__init__(parent, width=width, height=height, bg=canvas_bg, bd=0,
                         highlightthickness=0, takefocus=0)
        self.canvas_bg = canvas_bg
        self.background_image = background_image
        self.fill = fill
        self.radius = radius
        # مساحة داخلية متوازنة تمنح العناصر تنفّسًا بلا تضخيم للواجهات.
        self.content_inset = max(10, min(radius // 2, 15))
        self._surface_photo = None
        self.content = tk.Frame(self, bg=fill, bd=0, highlightthickness=0)
        self._content_window = self.create_window(0, 0, anchor="nw", window=self.content)
        self.bind("<Configure>", self._resize)
        self.after_idle(self._resize)

    def _resize(self, _event=None) -> None:
        width, height = max(2, self.winfo_width()), max(2, self.winfo_height())
        radius = min(self.radius, max(2, width // 2), max(2, height // 2))
        inset = min(self.content_inset, max(1, width // 4), max(1, height // 4))
        self.coords(self._content_window, inset, inset)
        self.itemconfigure(self._content_window, width=max(1, width - 2 * inset), height=max(1, height - 2 * inset))
        self.delete("surface")
        self._surface_photo = rounded_photo(width, height, radius, self.fill, self.canvas_bg, self.background_image)
        if self._surface_photo:
            self.create_image(0, 0, image=self._surface_photo, anchor="nw", tags="surface")
        else:
            self.create_rectangle(0, 0, width, height, fill=self.fill, outline="", tags="surface")
        self.tag_lower("surface")

    def set_fill(self, color: str) -> None:
        self.fill = color
        self.content.configure(bg=color)
        self._resize()


class SoftScrollbar(tk.Canvas):
    """A discreet, arrow-free scrollbar with a softly rounded thumb."""

    def __init__(self, parent: tk.Misc, command: Callable[..., None], background: str = PANEL,
                 thumb: str = CARD, hover_thumb: str = CARD_HOVER) -> None:
        super().__init__(parent, width=8, bg=background, bd=0, highlightthickness=0,
                         cursor="hand2", takefocus=0)
        self.command = command
        self.background = background
        self.thumb = thumb
        self.hover_thumb = hover_thumb
        self.first = 0.0
        self.last = 1.0
        self.drag_offset = 0
        self.hovered = False
        self.bind("<Configure>", lambda _event: self._draw())
        self.bind("<Enter>", self._enter)
        self.bind("<Leave>", self._leave)
        self.bind("<Button-1>", self._press)
        self.bind("<B1-Motion>", self._drag)

    def set(self, first: str | float, last: str | float) -> None:
        self.first = max(0.0, min(1.0, float(first)))
        self.last = max(self.first, min(1.0, float(last)))
        self._draw()

    def _thumb_metrics(self) -> tuple[int, int, int]:
        height = max(1, self.winfo_height())
        thumb_height = max(34, int(height * (self.last - self.first)))
        thumb_height = min(height, thumb_height)
        available = max(0, height - thumb_height)
        y = int(available * self.first)
        return y, thumb_height, available

    def _draw(self) -> None:
        self.delete("all")
        if self.last - self.first >= 0.999 or self.winfo_height() < 4:
            return
        y, thumb_height, _available = self._thumb_metrics()
        color = self.hover_thumb if self.hovered else self.thumb
        self._thumb_photo = rounded_photo(8, thumb_height, 4, color, self.background)
        if self._thumb_photo:
            self.create_image(0, y, image=self._thumb_photo, anchor="nw")
        else:
            self.create_rectangle(2, y, 8, y + thumb_height, fill=color, outline="")

    def _enter(self, _event=None) -> None:
        self.hovered = True
        self._draw()

    def _leave(self, _event=None) -> None:
        self.hovered = False
        self._draw()

    def _press(self, event) -> None:
        y, thumb_height, available = self._thumb_metrics()
        if y <= event.y <= y + thumb_height:
            self.drag_offset = event.y - y
        else:
            self.drag_offset = thumb_height // 2
            self._move_to(event.y - self.drag_offset, available)

    def _drag(self, event) -> None:
        _y, _thumb_height, available = self._thumb_metrics()
        self._move_to(event.y - self.drag_offset, available)

    def _move_to(self, y: int, available: int) -> None:
        if available <= 0:
            return
        fraction = max(0.0, min(1.0, y / available))
        self.command("moveto", fraction)


DISCORD_DETECTABLE_URL = "https://discord.com/api/v10/applications/detectable"
DISCORD_ICON_URL = "https://cdn.discordapp.com/app-icons/{app_id}/{icon_hash}.png?size=64"
HEADERS = {"User-Agent": "SB3QuestCompleter/1.1", "Accept": "application/json"}
DISCORD_CLIENT_ID = os.getenv("SB3_DISCORD_CLIENT_ID", "1541619305592922162")
SUPPORT_DISCORD_URL = "https://discord.gg/WcknYK29Hq"
DISCORD_GUILD_ID = "1371820874293838004"
DISCORD_REDIRECT_URI = "http://127.0.0.1:53134/callback/SB3"
DISCORD_AUTH_WORKER_URL = "https://sb3-discord-auth.sb3-auth-2026-2136.workers.dev"
DISCORD_OAUTH_SCOPES = "identify guilds.members.read"
PAGE_SIZE = 60
FEATURED_LIMIT = 60


def resource_path(name: str) -> Path:
    return Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent)) / name


def discord_session_file() -> Path:
    return Path(os.getenv("LOCALAPPDATA", str(Path.home()))) / "Sba3Dev" / "discord_session.json"


def load_discord_session() -> dict[str, Any]:
    try:
        data = json.loads(discord_session_file().read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError, TypeError):
        return {}


def save_discord_session(data: dict[str, Any]) -> None:
    try:
        path = discord_session_file()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    except OSError:
        pass


def clear_discord_session() -> None:
    try:
        discord_session_file().unlink(missing_ok=True)
    except OSError:
        pass


def worker_json_post(endpoint: str, payload: dict[str, Any]) -> dict[str, Any]:
    if not requests:
        return {}
    response = requests.post(f"{DISCORD_AUTH_WORKER_URL}{endpoint}", json=payload, timeout=(5, 20))
    try:
        data = response.json()
    except ValueError:
        data = {}
    if not isinstance(data, dict):
        return {}
    return data


def check_saved_discord_session(force_refresh: bool = False) -> tuple[bool, str]:
    session = load_discord_session()
    refresh_token = str(session.get("refresh_token") or "")
    if not refresh_token:
        return False, "missing_session"
    try:
        result = worker_json_post("/session/check", {
            "refresh_token": refresh_token,
            "access_token": session.get("access_token") or "",
            "force_refresh": force_refresh,
        })
    except Exception:
        return False, "network"
    if result.get("ok") and result.get("member"):
        save_discord_session({"refresh_token": result.get("refresh_token", refresh_token),
                              "access_token": result.get("access_token") or session.get("access_token") or "",
                              "guild_id": DISCORD_GUILD_ID,
                              "user": result.get("user") or session.get("user") or {}})
        return True, "ok"
    rotated_token = str(result.get("refresh_token") or "")
    if rotated_token:
        save_discord_session({"refresh_token": rotated_token,
                              "access_token": result.get("access_token") or session.get("access_token") or "",
                              "guild_id": DISCORD_GUILD_ID,
                              "user": result.get("user") or session.get("user") or {}})
    return False, str(result.get("error") or "invalid_session")


def discord_login() -> tuple[bool, str]:
    if not DISCORD_CLIENT_ID:
        return False, "missing_client_id"
    result_queue: queue.Queue[tuple[str, str]] = queue.Queue()
    state = secrets.token_urlsafe(32)

    def close_embedded_window() -> None:
        if not webview:
            return
        try:
            for window in list(webview.windows):
                window.destroy()
        except Exception:
            pass

    class CallbackHandler(http.server.BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            parsed = urlparse(self.path)
            params = parse_qs(parsed.query)
            code = str((params.get("code") or [""])[0])
            returned_state = str((params.get("state") or [""])[0])
            error = str((params.get("error") or [""])[0])
            result_queue.put((code if returned_state == state else "", error or "state_error" if returned_state != state else ""))
            language = "en"
            try:
                settings_path = Path(os.getenv("LOCALAPPDATA", str(Path.home()))) / "Sba3Dev" / "settings.json"
                settings = json.loads(settings_path.read_text(encoding="utf-8"))
                language = str(settings.get("language", "en")) if isinstance(settings, dict) else "en"
            except (OSError, ValueError, TypeError):
                pass
            arabic = language == "ar"
            direction = "rtl" if arabic else "ltr"
            title = "تم تسجيل الدخول بنجاح" if arabic else "Signed in successfully"
            message = "يمكنك إغلاق هذه الصفحة والعودة إلى الأداة." if arabic else "You can close this page and return to the app."
            try:
                icon = base64.b64encode(resource_path("logo.ico").read_bytes()).decode("ascii")
            except OSError:
                icon = ""
            icon_html = f'<img src="data:image/x-icon;base64,{icon}" class="logo" alt="SB3">' if icon else '<div class="logo-fallback">SB3</div>'
            body = f'''<!doctype html><html lang="{'ar' if arabic else 'en'}" dir="{direction}"><head><meta charset="utf-8"><title>SB3</title>
            <style>body{{margin:0;background:#0e080a;color:#f7eff0;font-family:Segoe UI,Arial,sans-serif;display:flex;align-items:center;justify-content:center;min-height:100vh}}
            .card{{width:350px;padding:34px 28px;border:1px solid #3b2026;border-radius:24px;background:#1b0c10;text-align:center;box-shadow:0 18px 60px #0008}}
            .logo{{width:78px;height:78px;object-fit:contain;margin-bottom:16px}}.logo-fallback{{font-size:30px;font-weight:700;color:#a7474d;margin-bottom:16px}}
            h1{{font-size:20px;margin:0 0 12px}}p{{color:#ccb8bc;font-size:14px;line-height:1.6;margin:0}}</style></head>
            <body><main class="card">{icon_html}<h1>{title}</h1><p>{message}</p></main></body></html>'''.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            if webview:
                threading.Timer(1.8, close_embedded_window).start()

        def log_message(self, _format: str, *_args: Any) -> None:
            return

    try:
        server = http.server.HTTPServer(("127.0.0.1", 53134), CallbackHandler)
        server.timeout = 180
        auth_url = "https://discord.com/oauth2/authorize?" + urlencode({
            "response_type": "code", "client_id": DISCORD_CLIENT_ID,
            "scope": DISCORD_OAUTH_SCOPES, "state": state,
            "redirect_uri": DISCORD_REDIRECT_URI,
        })
        def serve_callback() -> None:
            server.handle_request()

        callback_thread = threading.Thread(target=serve_callback, daemon=True)
        callback_thread.start()
        if webview:
            try:
                webview.create_window("SB3 Discord Login", auth_url, width=480, height=760,
                                      resizable=True, min_size=(420, 620))
                webview.start(gui="edgechromium", debug=False)
            except Exception:
                # Older Windows installations may not have the WebView2 runtime yet.
                # Keep login usable there while newer installations remain fully embedded.
                webbrowser.open(auth_url)
                callback_thread.join(timeout=180)
        else:
            webbrowser.open(auth_url)
            callback_thread.join(timeout=180)
        callback_thread.join(timeout=5)
        server.server_close()
        code, error = result_queue.get_nowait()
    except (OSError, queue.Empty):
        return False, "callback_timeout"
    if error or not code:
        return False, error or "authorization_failed"
    try:
        result = worker_json_post("/oauth/exchange", {"code": code, "redirect_uri": DISCORD_REDIRECT_URI})
    except Exception:
        return False, "network"
    if result.get("ok") and result.get("member") and result.get("refresh_token"):
        save_discord_session({"refresh_token": result["refresh_token"],
                              "access_token": result.get("access_token") or "",
                              "guild_id": DISCORD_GUILD_ID,
                              "user": result.get("user") or {}})
        return True, "ok"
    return False, str(result.get("error") or "not_in_guild")


def ensure_discord_access(root: tk.Tk) -> bool:
    while True:
        valid, reason = check_saved_discord_session()
        if valid:
            return True
        if reason not in {"missing_session", "invalid_session", "network", "not_in_guild"}:
            clear_discord_session()
        if reason in {"not_in_guild", "invalid_session"}:
            webbrowser.open_new_tab(SUPPORT_DISCORD_URL)
            retry = messagebox.askretrycancel(
                "Discord server required",
                "You must be a member of the support Discord server to use SB3 Quest Completer.\n\n"
                "Join the server in your browser, then press Retry.", parent=root)
            if not retry:
                return False
            continue
        logged_in, login_reason = discord_login()
        if logged_in:
            return True
        if login_reason == "not_in_guild":
            webbrowser.open_new_tab(SUPPORT_DISCORD_URL)
            retry = messagebox.askretrycancel(
                "Discord server required",
                "Your Discord account is not in the required server.\n\n"
                "Join it, then press Retry.", parent=root)
            if retry:
                continue
            return False
        retry = messagebox.askretrycancel(
            "Discord login required",
            "Discord login could not be completed. Press Retry to try again.", parent=root)
        if not retry:
            return False


def win_executable(game: dict[str, Any]) -> str | None:
    for item in game.get("executables") or []:
        name = item.get("name")
        if item.get("os") == "win32" and isinstance(name, str) and name.lower().endswith(".exe"):
            return name
    return None


def display_name(name: Any) -> str:
    """Use Discord's public game name, without the leading internal # marker."""
    result = str(name or "").strip()
    return result[1:].strip() if result.startswith("#") else result


def newest_game_rank(game_id: Any) -> int:
    """Use Discord's Snowflake creation order as the best available recency signal."""
    try:
        return -int(str(game_id))
    except (TypeError, ValueError):
        return 0


# Official distributor values exposed by Discord's game data, plus common aliases found in legacy records.
# Discord itself is deliberately excluded: it is an activity source, not a PC game launcher choice.
LAUNCHER_DISTRIBUTORS = {
    "steam": "Steam",
    "epic": "Epic Games",
    "gog": "GOG Galaxy",
    "uplay": "Ubisoft Connect",
    "ubisoft": "Ubisoft Connect",
    "ubisoft_connect": "Ubisoft Connect",
    "battlenet": "Battle.net",
    "battle_net": "Battle.net",
    "origin": "EA app",
    "ea": "EA app",
    "ea_app": "EA app",
    "microsoft": "Microsoft Store",
    "xbox": "Xbox app",
    "xbox_title": "Xbox app",
    "xbox_game_pass": "Xbox app",
    "twitch": "Amazon Games",
    "amazon": "Amazon Games",
    "amazon_games": "Amazon Games",
    "itch": "itch.io",
    "itchio": "itch.io",
    "roblox": "Roblox",
    "nvidia_gdn_app": "GeForce NOW",
    "geforce_now": "GeForce NOW",
    "riot": "Riot Client",
    "rockstar": "Rockstar Games Launcher",
    "minecraft": "Minecraft Launcher",
    "gamejolt": "Game Jolt Client",
    "bethesda": "Bethesda.net Launcher",
    "wargaming": "Wargaming Game Center",
    "garena": "Garena",
    "arc": "Arc Games",
    "glyph": "Glyph",
    "paradox": "Paradox Launcher",
    "2k": "2K Launcher",
}
PLATFORM_ORDER = (
    "Steam", "Epic Games", "GOG Galaxy", "Ubisoft Connect", "EA app", "Battle.net",
    "Riot Client", "Rockstar Games Launcher", "Microsoft Store", "Xbox app", "Amazon Games",
    "itch.io", "Roblox", "Minecraft Launcher", "Game Jolt Client", "Bethesda.net Launcher",
    "Wargaming Game Center", "Garena", "Arc Games", "Glyph", "Paradox Launcher", "2K Launcher",
    "GeForce NOW",
)
LAUNCHER_URL_HINTS = {
    "steampowered.com": "Steam",
    "steamcommunity.com": "Steam",
    "epicgames.com": "Epic Games",
    "gog.com": "GOG Galaxy",
    "ubisoft.com": "Ubisoft Connect",
    "uplay.com": "Ubisoft Connect",
    "battle.net": "Battle.net",
    "blizzard.com": "Battle.net",
    "ea.com": "EA app",
    "origin.com": "EA app",
    "xbox.com": "Xbox app",
    "microsoft.com": "Microsoft Store",
    "amazon.com": "Amazon Games",
    "itch.io": "itch.io",
    "roblox.com": "Roblox",
    "riotgames.com": "Riot Client",
    "rockstargames.com": "Rockstar Games Launcher",
    "minecraft.net": "Minecraft Launcher",
    "gamejolt.com": "Game Jolt Client",
    "bethesda.net": "Bethesda.net Launcher",
    "wargaming.net": "Wargaming Game Center",
    "garena.com": "Garena",
    "arcgames.com": "Arc Games",
    "glyph.net": "Glyph",
    "paradoxplaza.com": "Paradox Launcher",
    "2k.com": "2K Launcher",
    "nvidia.com": "GeForce NOW",
}
LAUNCHER_EXECUTABLE_HINTS = (
    ("riotclient", "Riot Client"), ("leagueclient", "Riot Client"), ("valorant", "Riot Client"),
    ("battle.net", "Battle.net"), ("overwatch", "Battle.net"), ("hearthstone", "Battle.net"),
    ("wow", "Battle.net"), ("diablo", "Battle.net"), ("uplay", "Ubisoft Connect"),
    ("ubisoftconnect", "Ubisoft Connect"), ("eadesktop", "EA app"), ("origin", "EA app"),
    ("rockstar", "Rockstar Games Launcher"), ("gta5", "Rockstar Games Launcher"),
    ("reddead", "Rockstar Games Launcher"), ("minecraftlauncher", "Minecraft Launcher"),
    ("robloxplayer", "Roblox"), ("galaxyclient", "GOG Galaxy"), ("epicgameslauncher", "Epic Games"),
    ("gamejoltclient", "Game Jolt Client"), ("bethesdanetlauncher", "Bethesda.net Launcher"),
    ("wargaming.net game center", "Wargaming Game Center"), ("wgc.exe", "Wargaming Game Center"),
    ("garena", "Garena"), ("arc.exe", "Arc Games"), ("glyphclient", "Glyph"),
    ("paradox launcher", "Paradox Launcher"), ("2klauncher", "2K Launcher"),
)
# Only used when Discord provides neither a verified SKU nor a verified store URL/executable hint.
PUBLISHER_LAUNCHER_HINTS = (
    ("riot", "Riot Client"), ("blizzard", "Battle.net"), ("ubisoft", "Ubisoft Connect"),
    ("electronic arts", "EA app"), (" ea", "EA app"), ("rockstar", "Rockstar Games Launcher"),
    ("mojang", "Minecraft Launcher"), ("roblox", "Roblox"), ("bethesda", "Bethesda.net Launcher"),
    ("wargaming", "Wargaming Game Center"), ("garena", "Garena"), ("paradox", "Paradox Launcher"),
    ("2k games", "2K Launcher"),
)


def _platform_from_url(url: Any) -> str | None:
    """Resolve a known official launcher from an already-supplied game-store URL."""
    try:
        host = urlparse(str(url)).netloc.casefold().removeprefix("www.")
    except (TypeError, ValueError):
        return None
    return next((platform for domain, platform in LAUNCHER_URL_HINTS.items() if host == domain or host.endswith(f".{domain}")), None)


def platforms_for_game(game: dict[str, Any]) -> tuple[str, ...]:
    """Return only verified PC launchers for this game; never insert Discord as a launcher."""
    detected: set[str] = set()
    sku_lists = (game.get("third_party_skus"), game.get("thirdPartySkus"), game.get("skus"))
    for skus in sku_lists:
        for sku in skus or ():
            if isinstance(sku, dict):
                distributor = str(sku.get("distributor") or sku.get("store") or "").casefold().strip()
                platform = LAUNCHER_DISTRIBUTORS.get(distributor)
                if platform:
                    detected.add(platform)
    for websites in (game.get("websites"), game.get("third_party_urls"), game.get("thirdPartyUrls")):
        for website in websites or ():
            url = website.get("url") if isinstance(website, dict) else website
            platform = _platform_from_url(url)
            if platform:
                detected.add(platform)
    executable_names = " ".join(str(item.get("name", "")) for item in (game.get("executables") or ()) if isinstance(item, dict)).casefold()
    for hint, platform in LAUNCHER_EXECUTABLE_HINTS:
        if hint in executable_names:
            detected.add(platform)
    if not detected:
        people = tuple(game.get("publishers") or ()) + tuple(game.get("developers") or ()) + tuple(game.get("companies") or ())
        company_text = " ".join(str(person.get("name", "")) for person in people if isinstance(person, dict)).casefold()
        for hint, platform in PUBLISHER_LAUNCHER_HINTS:
            if hint in company_text:
                detected.add(platform)
    return tuple(platform for platform in PLATFORM_ORDER if platform in detected)


def run_game_process(game_name: str, platform: str, stop_signal: str = "") -> None:
    """Run a real hidden system window so the activity remains a detectable background process."""
    root = tk.Tk()
    root.title(f"Active: {game_name}")
    # Keep a genuine top-level window alive for the background task, but make it borderless and off-screen.
    # Unlike withdraw(), this preserves the OS window handle while never presenting a second UI to the user.
    root.overrideredirect(True)
    root.geometry("1x1-32000-32000")
    root.configure(bg=BG)
    root.update_idletasks()
    signal_path = Path(stop_signal) if stop_signal else None

    def stop_session() -> None:
        try:
            root.destroy()
        except tk.TclError:
            pass

    def watch_parent_stop() -> None:
        try:
            if signal_path and signal_path.exists():
                stop_session()
                return
            root.after(250, watch_parent_stop)
        except tk.TclError:
            pass

    root.protocol("WM_DELETE_WINDOW", stop_session)
    watch_parent_stop()
    root.mainloop()


class PlatformSelector(tk.Toplevel):
    def __init__(self, parent: tk.Misc, game_name: str, platforms: tuple[str, ...], callback: Callable[[str], None]):
        super().__init__(parent)
        self.title("Choose platform")
        surface_height = 190 + 52 * len(platforms)
        self.geometry(f"414x{surface_height + 24}")
        self.configure(bg=BG)
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        surface = RoundedSurface(self, fill=PANEL, radius=24, width=390, height=surface_height, background=BG)
        surface.pack(fill="both", expand=True, padx=12, pady=12)
        content = surface.content
        tk.Label(content, text="Available platforms", bg=PANEL, fg=TEXT, font=("Segoe UI", 13, "bold")).pack(pady=(22, 6))
        tk.Label(content, text=game_name, bg=PANEL, fg=TEXT_DIM, font=("Segoe UI", 10), wraplength=320).pack(pady=(0, 16))
        for name in platforms:
            button = PillButton(content, text=name, fill=CARD, hover_fill=RED, text_color=TEXT,
                                width=292, height=38, background=PANEL,
                                command=lambda p=name: self.choose(p, callback))
            button.pack(pady=4)

    def choose(self, platform: str, callback: Callable[[str], None]) -> None:
        self.destroy()
        callback(platform)


class QuestCompleterApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.base_tk_scaling = float(root.tk.call("tk", "scaling"))
        self.appearance_settings = self.load_appearance_settings()
        self._apply_appearance_palette()
        root.title(APP_NAME)
        root.geometry("1180x820")
        root.minsize(980, 640)
        root.configure(bg=BG)
        root.protocol("WM_DELETE_WINDOW", self.on_closing)
        icon_path = resource_path("logo.ico")
        if icon_path.exists():
            try: root.iconbitmap(str(icon_path))
            except tk.TclError: pass

        self.all_games: list[dict[str, Any]] = []
        self.filtered_games: list[dict[str, Any]] = []
        self.selected_quests: list[dict[str, Any]] = []
        self.active_simulations: dict[str, dict[str, Any]] = {}
        self.icon_cache: dict[tuple[str, int], Any] = {}
        self.icon_pending: set[tuple[str, int]] = set()
        self.icon_pool = ThreadPoolExecutor(max_workers=6, thread_name_prefix="sb3-icon")
        self.stop_event = threading.Event()
        self.filter_job: str | None = None
        self.rendered = 0
        self.spinner_job: str | None = None
        self.activity_timer_job: str | None = None
        self.activity_duration_labels: dict[str, tk.Label] = {}
        self.loading_active = False
        self.brand_logo = None
        self.in_app_overlay: tk.Frame | None = None
        self.queue_canvas: tk.Canvas | None = None
        self.local_game_paths = self.load_local_game_paths()
        self.featured_ranks = self.load_featured_ranks()
        self.auth_busy = False
        self.update_cancel_event = threading.Event()
        self.update_temp_path: Path | None = None
        self.latest_manifest: dict[str, Any] | None = None
        self.auth_screen = "login"
        self.membership_watch_active = False
        self.root.after(100, self.start_startup_gate)

    def _clear_root(self) -> None:
        if getattr(self, "splash_job", None):
            try:
                self.root.after_cancel(self.splash_job)
            except tk.TclError:
                pass
            self.splash_job = None
        for widget in self.root.winfo_children():
            widget.destroy()

    def _auth_header(self, subtitle: str) -> None:
        header = tk.Frame(self.root, bg=BG)
        header.pack(fill="x", padx=30, pady=(22, 15))
        logo_slot = tk.Frame(header, width=46, height=46, bg=BG)
        logo_slot.pack(side="left", padx=(0, 13))
        logo_slot.pack_propagate(False)
        logo = tk.Label(logo_slot, bg=BG)
        logo.pack(fill="both", expand=True)
        self.load_logo(logo)
        labels = tk.Frame(header, bg=BG)
        labels.pack(side="left", fill="x", expand=True)
        tk.Label(labels, text=APP_NAME, bg=BG, fg=TEXT, font=("Segoe UI", 19, "bold")).pack(anchor="w")
        tk.Label(labels, text=subtitle, bg=BG, fg=TEXT_DIM, font=("Segoe UI", 9)).pack(anchor="w", pady=(3, 0))

    def _auth_footer(self) -> None:
        footer = tk.Frame(self.root, bg=BG)
        footer.pack(fill="x", padx=30, pady=(0, 16))
        settings_button = PillButton(footer, text="⚙", command=self.open_settings_panel, fill=INPUT,
                                     hover_fill=CARD_HOVER, text_color=TEXT_DIM, font=("Segoe UI Symbol", 15),
                                     width=38, height=34, background=BG)
        settings_button.pack(side="right")

    def build_login_screen(self, note: str = "") -> None:
        self._clear_root()
        self._auth_header(self.tr("auth_subtitle"))
        surface = RoundedSurface(self.root, fill=PANEL, radius=24, width=520, height=420, background=BG)
        surface.pack(fill="both", expand=True, padx=260, pady=(35, 75))
        content = surface.content
        self._add_panel_logo(content, 92)
        tk.Label(content, text=self.tr("login_title"), bg=PANEL, fg=TEXT,
                 font=("Segoe UI", 14, "bold")).pack(pady=(0, 9))
        tk.Label(content, text=self.tr("login_message"), bg=PANEL,
                 fg=TEXT_DIM, font=("Segoe UI", 9), wraplength=350, justify="center").pack(pady=(0, 18))
        self.auth_note = tk.Label(content, text=note, bg=PANEL, fg=RED_HOVER,
                                  font=("Segoe UI", 9), wraplength=350, justify="center")
        self.auth_note.pack(pady=(0, 12))
        self.auth_button = PillButton(content, text=self.tr("login_button"), command=self.start_discord_login,
                                      fill=RED, hover_fill=RED_HOVER, width=250, height=42, background=PANEL)
        self.auth_button.pack(pady=6)
        self.auth_screen = "login"
        self._auth_footer()
        self._enable_feedback_tree(self.root)

    def build_membership_screen(self, error: bool = False) -> None:
        self._clear_root()
        self._auth_header(self.tr("membership_subtitle"))
        surface = RoundedSurface(self.root, fill=PANEL, radius=24, width=520, height=420, background=BG)
        surface.pack(fill="both", expand=True, padx=260, pady=(35, 75))
        content = surface.content
        self._add_panel_logo(content, 92)
        tk.Label(content, text=self.tr("membership_title"), bg=PANEL,
                 fg=TEXT, font=("Segoe UI", 13, "bold"), wraplength=355, justify="center").pack(pady=(0, 12))
        if error:
            tk.Label(content, text=self.tr("membership_error"), bg=PANEL,
                     fg=RED_HOVER, font=("Segoe UI", 9), wraplength=350, justify="center").pack(pady=(0, 12))
        else:
            tk.Label(content, text=self.tr("membership_message"), bg=PANEL,
                     fg=TEXT_DIM, font=("Segoe UI", 9), wraplength=350, justify="center").pack(pady=(0, 12))
        self.auth_button = PillButton(content, text=self.tr("join_button"), command=self.join_and_recheck,
                                      fill=RED, hover_fill=RED_HOVER, width=220, height=42, background=PANEL)
        self.auth_button.pack(pady=6)
        if getattr(self, "membership_join_pressed", False):
            self.refresh_membership_button = PillButton(content, text=self.tr("refresh_membership"),
                                                        command=self.refresh_membership,
                                                        fill=CARD, hover_fill=CARD_HOVER, text_color=TEXT,
                                                        width=220, height=38, background=PANEL)
            self.refresh_membership_button.pack(pady=(2, 6))
        self.auth_screen = "membership"
        self._auth_footer()
        self._enable_feedback_tree(self.root)

    def build_splash_screen(self) -> None:
        self._clear_root()
        self.auth_screen = "splash"
        self.splash_angle = 0
        self.splash_panel = tk.Frame(self.root, bg=BG)
        self.splash_panel.pack(fill="both", expand=True)
        center = tk.Frame(self.splash_panel, bg=BG)
        center.place(relx=0.5, rely=0.5, anchor="center")
        self._add_panel_logo(center, 180)
        tk.Label(center, text="Welcom To SB3 Tool", bg=BG, fg=TEXT,
                 font=("Segoe UI", 20, "bold")).pack(pady=(8, 24))
        self.splash_loader = tk.Canvas(center, width=58, height=58, bg=BG, highlightthickness=0, bd=0)
        self.splash_loader.pack()
        self.splash_loader.create_oval(5, 5, 53, 53, outline=BORDER, width=5)
        self.splash_arc = self.splash_loader.create_arc(5, 5, 53, 53, start=0, extent=95,
                                                        outline=RED_HOVER, width=5, style="arc")
        self._animate_splash()

    def _animate_splash(self) -> None:
        if self.auth_screen != "splash":
            return
        try:
            self.splash_angle = (self.splash_angle + 12) % 360
            self.splash_loader.itemconfigure(self.splash_arc, start=self.splash_angle)
            self.splash_job = self.root.after(35, self._animate_splash)
        except tk.TclError:
            self.splash_job = None

    def start_auth_gate(self) -> None:
        self.auth_busy = True
        if self.auth_screen != "splash":
            self.build_login_screen(self.tr("checking_session"))
            self.auth_button.configure(state="disabled")
        threading.Thread(target=self._auth_check_worker, daemon=True, name="sb3-auth-check").start()

    def start_startup_gate(self) -> None:
        """Check the update manifest before showing Discord login."""
        self.auth_busy = True
        self.build_splash_screen()
        threading.Thread(target=self._startup_update_worker, daemon=True, name="sb3-startup-update").start()

    def _startup_update_worker(self) -> None:
        if not UPDATE_MANIFEST_URL or not requests:
            self.root.after(0, self.start_auth_gate)
            return
        try:
            response = requests.get(UPDATE_MANIFEST_URL, headers=HEADERS, timeout=(5, 15))
            response.raise_for_status()
            manifest = response.json()
            latest = str(manifest.get("version", "")).strip()
            installer_url = str(manifest.get("installer_url", "")).strip()
            if latest and installer_url and self._version_tuple(latest) > self._version_tuple(VERSION):
                self.root.after(0, lambda: self.show_update_screen(manifest))
                return
        except Exception:
            pass
        self.root.after(0, self.start_auth_gate)

    def _auth_check_worker(self) -> None:
        valid, reason = check_saved_discord_session()
        self.root.after(0, lambda: self._finish_auth_check(valid, reason))

    def _finish_auth_check(self, valid: bool, reason: str) -> None:
        self.auth_busy = False
        if valid:
            self.open_main_interface()
        elif reason == "not_in_guild":
            self.build_membership_screen()
        else:
            self.build_login_screen()

    def start_discord_login(self) -> None:
        if self.auth_busy:
            return
        self.auth_busy = True
        self.build_login_screen(self.tr("checking_session"))
        threading.Thread(target=self._login_worker, daemon=True, name="sb3-auth-login").start()

    def _login_worker(self) -> None:
        valid, reason = discord_login()
        self.root.after(0, lambda: self._finish_auth_check(valid, reason))
        self.auth_busy = False

    def join_and_recheck(self) -> None:
        self.membership_join_pressed = True
        self.build_membership_screen()
        webbrowser.open_new_tab(SUPPORT_DISCORD_URL)
        if not self.membership_watch_active:
            self.membership_watch_active = True
            threading.Thread(target=self._membership_worker, daemon=True, name="sb3-membership-check").start()

    def refresh_membership(self) -> None:
        """Manually refresh the saved Discord session and membership state."""
        if self.auth_busy:
            return
        self.membership_watch_active = False
        self.auth_busy = True
        self.build_membership_screen()
        threading.Thread(target=self._refresh_membership_worker, daemon=True, name="sb3-membership-refresh").start()

    def _refresh_membership_worker(self) -> None:
        valid, _reason = check_saved_discord_session(force_refresh=True)
        if valid:
            self.root.after(0, lambda: self._finish_membership_check(True))
            return
        self.membership_watch_active = True
        self.auth_busy = False
        self._membership_worker()

    def _membership_worker(self) -> None:
        valid = False
        while self.membership_watch_active:
            valid, _reason = check_saved_discord_session()
            if valid:
                break
            time.sleep(0.5)
        if valid and self.membership_watch_active:
            self.root.after(0, lambda: self._finish_membership_check(True))

    def _finish_membership_check(self, valid: bool) -> None:
        self.membership_watch_active = False
        self.auth_busy = False
        if valid:
            self.membership_join_pressed = False
            self.open_main_interface()
        else:
            self.build_membership_screen(error=True)

    def open_main_interface(self) -> None:
        self.auth_busy = False
        self.auth_screen = "main"
        self._clear_root()
        self.build_ui()
        self._enable_feedback_tree(self.root)
        self.start_monitor()
        self.load_data()
        self.root.after(250, self.check_for_required_update)

    @staticmethod
    def _version_tuple(value: Any) -> tuple[int, ...]:
        """Convert a semantic-ish version to comparable numeric components."""
        parts = []
        for part in str(value or "0").strip().lstrip("vV").split("."):
            digits = "".join(char for char in part if char.isdigit())
            parts.append(int(digits or 0))
        return tuple(parts or [0])

    def check_for_required_update(self) -> None:
        """Show the latest available update in an in-app screen."""
        if not UPDATE_MANIFEST_URL or not requests:
            return
        threading.Thread(target=self._update_check_worker, daemon=True, name="sb3-update-check").start()

    def _update_check_worker(self) -> None:
        try:
            response = requests.get(UPDATE_MANIFEST_URL, headers=HEADERS, timeout=(5, 15))
            response.raise_for_status()
            manifest = response.json()
            latest = str(manifest.get("version", "")).strip()
            installer_url = str(manifest.get("installer_url", "")).strip()
            if not latest or not installer_url or self._version_tuple(latest) <= self._version_tuple(VERSION):
                return
        except Exception:
            return
        self.root.after(0, lambda: self.show_update_screen(manifest))

    def show_update_screen(self, manifest: dict[str, Any]) -> None:
        self.auth_busy = False
        self.latest_manifest = manifest
        latest = str(manifest.get("version", "")).strip()
        self._clear_root()
        self.auth_screen = "update"
        self._auth_header(self.tr("update_subtitle"))
        surface = RoundedSurface(self.root, fill=PANEL, radius=24, width=520, height=420, background=BG)
        surface.pack(fill="both", expand=True, padx=260, pady=(35, 75))
        content = surface.content
        self._add_panel_logo(content, 92)
        tk.Label(content, text=self.tr("update_title"), bg=PANEL, fg=TEXT,
                 font=("Segoe UI", 14, "bold")).pack(pady=(0, 18))
        versions = tk.Frame(content, bg=PANEL)
        versions.pack(pady=(0, 18))
        tk.Label(versions, text=self.tr("current_version", version=VERSION), bg=PANEL, fg=TEXT_DIM,
                 font=("Segoe UI", 10)).pack()
        tk.Label(versions, text=self.tr("new_version", version=latest), bg=PANEL, fg=SUCCESS,
                 font=("Segoe UI", 10, "bold")).pack(pady=(6, 0))
        self.update_status = tk.Label(content, text="", bg=PANEL, fg=TEXT_DIM,
                                      font=("Segoe UI", 9), wraplength=350, justify="center")
        self.update_status.pack(pady=(0, 12))
        size_value = manifest.get("package_size") or manifest.get("size")
        try:
            size_text = self._format_download_size(float(size_value)) if size_value else "--"
        except (TypeError, ValueError):
            size_text = "--"
        self.update_size_label = tk.Label(content, text=self.tr("installer_size", size=size_text), bg=PANEL, fg=TEXT_DIM,
                                          font=("Segoe UI", 9))
        self.update_size_label.pack(pady=(0, 10))
        self.update_progress_area = tk.Frame(content, bg=PANEL)
        progress_row = tk.Frame(self.update_progress_area, bg=PANEL)
        progress_row.pack(fill="x", padx=34, pady=(0, 4))
        self.update_percent_label = tk.Label(progress_row, text="0%", bg=PANEL, fg=TEXT_DIM,
                                             font=("Segoe UI", 9, "bold"))
        self.update_percent_label.pack(side="left")
        self.update_total_label = tk.Label(progress_row, text="%100", bg=PANEL, fg=MUTED,
                                           font=("Segoe UI", 9, "bold"))
        self.update_total_label.pack(side="right")
        self.update_progress_canvas = tk.Canvas(self.update_progress_area, bg=INPUT, highlightthickness=0, bd=0,
                                                width=360, height=12)
        self.update_progress_canvas.pack(fill="x", padx=34, pady=(0, 9))
        self.update_progress_fill = self.update_progress_canvas.create_rectangle(0, 0, 0, 12, fill=RED, outline="")
        self.update_stats_label = tk.Label(self.update_progress_area, text="", bg=PANEL, fg=MUTED,
                                           font=("Segoe UI", 8), wraplength=350, justify="center")
        self.update_stats_label.pack(pady=(0, 7))
        self.update_button = PillButton(content, text=self.tr("update_button"), command=self.install_latest_update,
                                        fill=RED, hover_fill=RED_HOVER, width=190, height=42, background=PANEL)
        self.update_button.pack(pady=6)
        self.cancel_button = PillButton(content, text=self.tr("cancel_update"), command=self.cancel_update,
                                        fill=INPUT, hover_fill=CARD_HOVER, text_color=TEXT, width=190, height=42,
                                        background=PANEL)
        self.cancel_button.pack_forget()
        self._auth_footer()
        self._enable_feedback_tree(self.root)

    @staticmethod
    def _format_download_size(value: float) -> str:
        amount = float(max(0.0, value))
        for unit in ("B", "KB", "MB", "GB"):
            if amount < 1024 or unit == "GB":
                return f"{amount:.1f} {unit}" if unit != "B" else f"{int(amount)} {unit}"
            amount /= 1024
        return f"{amount:.1f} GB"

    @staticmethod
    def _format_download_time(seconds: float | None) -> str:
        if seconds is None or seconds < 0 or seconds > 86400:
            return "--:--"
        total = int(seconds)
        return f"{total // 60:02d}:{total % 60:02d}"

    def _render_download_progress(self, received: int, total: int, speed: float, eta: float | None) -> None:
        try:
            ratio = min(1.0, max(0.0, received / total)) if total else 0.0
            bar_width = max(1, self.update_progress_canvas.winfo_width())
            self.update_progress_canvas.coords(self.update_progress_fill, 0, 0, bar_width * ratio, 12)
            self.update_percent_label.configure(text=f"{int(ratio * 100)}%")
            speed_text = self._format_download_size(speed)
            eta_text = self._format_download_time(eta)
            self.update_stats_label.configure(text=f"{self.tr('download_speed', speed=speed_text)}  ·  {self.tr('time_remaining', time=eta_text)}")
        except tk.TclError:
            pass

    def install_latest_update(self) -> None:
        if self.auth_busy or not self.latest_manifest:
            return
        self.auth_busy = True
        self.update_cancel_event.clear()
        self.update_temp_path = None
        self.update_size_label.pack_forget()
        self.update_button.pack_forget()
        self.update_size_label.pack(pady=(0, 7))
        self.update_progress_area.pack(fill="x", pady=(0, 4))
        self.cancel_button.pack(pady=6)
        self.cancel_button.configure(state="normal")
        self.update_status.configure(text=self.tr("downloading_update"))
        threading.Thread(target=self._download_update_worker, daemon=True, name="sb3-update-download").start()

    def cancel_update(self) -> None:
        if not self.auth_busy:
            return
        self.update_cancel_event.set()
        self.cancel_button.configure(state="disabled")
        self.update_status.configure(text=self.tr("update_cancelled"))

    def _download_update_worker(self) -> None:
        manifest = self.latest_manifest or {}
        try:
            package_url = str(manifest.get("package_url") or manifest["installer_url"])
            latest = str(manifest["version"])
            download = requests.get(package_url, timeout=(10, 120), stream=True)
            download.raise_for_status()
            total = int(download.headers.get("content-length") or 0)
            received = 0
            started = time.monotonic()
            suffix = Path(package_url.split("?", 1)[0]).suffix or ".zip"
            temp_path = Path(tempfile.gettempdir()) / f"SB3QuestCompleter-update-{latest}{suffix}"
            self.update_temp_path = temp_path
            with temp_path.open("wb") as target:
                for chunk in download.iter_content(chunk_size=1024 * 1024):
                    if chunk:
                        if self.update_cancel_event.is_set():
                            try: temp_path.unlink(missing_ok=True)
                            except OSError: pass
                            self.root.after(0, self._update_cancelled)
                            return
                        target.write(chunk)
                        received += len(chunk)
                        elapsed = max(0.001, time.monotonic() - started)
                        speed = received / elapsed
                        eta = (total - received) / speed if total and speed > 0 else None
                        self.root.after(0, self._render_download_progress, received, total, speed, eta)
            if self.update_cancel_event.is_set():
                try: temp_path.unlink(missing_ok=True)
                except OSError: pass
                self.root.after(0, self._update_cancelled)
                return
            expected_hash = str(manifest.get("package_sha256") or manifest.get("sha256", "")).strip().casefold()
            if expected_hash:
                digest = hashlib.sha256(temp_path.read_bytes()).hexdigest().casefold()
                if digest != expected_hash:
                    raise ValueError("update checksum mismatch")
            if os.name != "nt":
                raise RuntimeError("Windows installer can only run on Windows")
            if self.update_cancel_event.is_set():
                try: temp_path.unlink(missing_ok=True)
                except OSError: pass
                self.root.after(0, self._update_cancelled)
                return
            self.root.after(0, self._render_download_progress, max(received, total), total, max(0.0, received / max(0.001, time.monotonic() - started)), 0.0)
            self.root.after(0, lambda: self.update_status.configure(text=self.tr("launching_update")))
            install_dir = Path(sys.executable).resolve().parent
            app_path = Path(sys.executable).resolve()
            updater_path = install_dir / "SB3Updater.exe"
            if not updater_path.exists():
                updater_path = resource_path("SB3Updater.exe")
            if not updater_path.exists():
                raise FileNotFoundError("SB3Updater.exe is missing")
            subprocess.Popen([str(updater_path), str(temp_path), str(install_dir), str(os.getpid()), str(app_path)])
            self.root.after(50, self._exit_for_update)
        except Exception:
            temp_path = self.update_temp_path
            if temp_path:
                try: temp_path.unlink(missing_ok=True)
                except OSError: pass
            self.root.after(0, lambda: self._update_failed())

    def _exit_for_update(self) -> None:
        """Exit completely so the silent installer can replace the one-file executable safely."""
        try:
            self.root.destroy()
        finally:
            os._exit(0)

    def _update_cancelled(self) -> None:
        self.auth_busy = False
        self.update_temp_path = None
        self.update_progress_area.pack_forget()
        self.cancel_button.pack_forget()
        self.update_button.pack(pady=6)
        self.update_button.configure(state="normal", text=self.tr("update_button"), command=self.install_latest_update)
        self.update_status.configure(text=self.tr("update_cancelled"))

    def _update_failed(self) -> None:
        self.auth_busy = False
        self.cancel_button.pack_forget()
        self.update_button.pack(pady=6)
        self.update_button.configure(state="normal", text=self.tr("update_button"), command=self.install_latest_update)
        self.update_status.configure(text=self.tr("update_error"))

    # ---- Visual system ----
    def _enable_button_feedback(self, button: tk.Button) -> None:
        """Attach feedback to this exact widget, so it is reliable for static and dynamic buttons."""
        if not getattr(button, "_sb3_feedback_bound", False):
            button.bind("<ButtonPress-1>", self._flash_button_press, add="+")
            button._sb3_feedback_bound = True

    def _enable_feedback_tree(self, parent: tk.Misc) -> None:
        for child in parent.winfo_children():
            if isinstance(child, tk.Button):
                self._enable_button_feedback(child)
            self._enable_feedback_tree(child)

    def _flash_button_press(self, event) -> None:
        """Brief, low-key visual acknowledgement for every ordinary Tk button."""
        button = event.widget
        if not isinstance(button, tk.Button):
            return
        try:
            if str(button.cget("state")) == "disabled":
                return
            original_bg = button.cget("bg")
            original_relief = button.cget("relief")
            active_bg = button.cget("activebackground") or original_bg
            def apply_flash() -> None:
                try:
                    if not button.winfo_exists():
                        return
                    button.configure(bg=active_bg, relief="sunken")
                    def restore() -> None:
                        try:
                            if button.winfo_exists():
                                button.configure(bg=original_bg, relief=original_relief)
                        except tk.TclError:
                            pass
                    button.after(105, restore)
                except tk.TclError:
                    pass
            # Run after Tk's native click state so native bindings cannot overwrite the visual feedback.
            button.after_idle(apply_flash)
        except (tk.TclError, AttributeError):
            pass

    def panel(self, parent: tk.Misc, width: int, height: int) -> RoundedSurface:
        # حواف أكثر هدوءًا وبساطة للوحتي المكتبة وقائمة المهام.
        return RoundedSurface(parent, fill=PANEL, radius=20, width=width, height=height, background=BG)

    def build_ui(self) -> None:
        header = tk.Frame(self.root, bg=BG)
        header.pack(fill="x", padx=30, pady=(22, 15))
        self.build_account_widget(header)
        # شعار ثابت وواضح يسار اسم التطبيق في رأس النافذة.
        logo_slot = tk.Frame(header, width=46, height=46, bg=BG)
        logo_slot.pack(side="left", padx=(0, 13))
        logo_slot.pack_propagate(False)
        self.header_logo = tk.Label(logo_slot, bg=BG)
        self.header_logo.pack(fill="both", expand=True)
        self.load_logo(self.header_logo)
        labels = tk.Frame(header, bg=BG)
        labels.pack(side="left", fill="x", expand=True)
        tk.Label(labels, text=APP_NAME, bg=BG, fg=TEXT, font=("Segoe UI", 19, "bold")).pack(anchor="w")
        tk.Label(labels, text="Sba3 Dev - 2026", bg=BG, fg=TEXT_DIM, font=("Segoe UI", 9)).pack(anchor="w", pady=(3, 0))
        body = tk.Frame(self.root, bg=BG)
        body.pack(fill="both", expand=True, padx=28, pady=(0, 14))
        body.grid_columnconfigure(0, weight=3, minsize=570)
        body.grid_columnconfigure(1, weight=1, minsize=310)
        body.grid_rowconfigure(0, weight=1)
        self.library_surface = self.panel(body, 660, 570)
        self.library_surface.grid(row=0, column=0, sticky="nsew", padx=(0, 14))
        self.queue_surface = self.panel(body, 340, 570)
        self.queue_surface.grid(row=0, column=1, sticky="nsew")
        self.library_panel = self.library_surface.content
        self.queue_panel = self.queue_surface.content
        self.build_library()
        self.build_queue()
        footer = tk.Frame(self.root, bg=BG)
        footer.pack(fill="x", padx=30, pady=(0, 16))
        self.status = tk.Label(footer, text=self.tr("ready"), bg=BG, fg=MUTED, font=("Segoe UI", 9, "bold"), anchor="w")
        self.status.pack(side="left")
        self.library_count = tk.Label(footer, text=self.tr("featured_games"), bg=BG, fg=TEXT_DIM,
                                      font=("Segoe UI", 9, "bold"), anchor="e")
        self.library_count.pack(side="right")

    def build_account_widget(self, parent: tk.Frame) -> None:
        account = tk.Frame(parent, bg=BG)
        account.pack(side="right", padx=(18, 0))
        user_info = load_discord_session().get("user") or {}
        self.account_avatar = tk.Canvas(account, width=34, height=34, bg=BG,
                                       highlightthickness=0, bd=0, cursor="hand2")
        self.account_avatar.pack(side="left")
        self.account_avatar_item = self.account_avatar.create_image(17, 17, anchor="center", image="")
        self.account_avatar_fallback = self.account_avatar.create_text(
            17, 17, text=self._avatar_initials(user_info), fill=TEXT,
            font=("Segoe UI", 9, "bold"), anchor="center"
        )
        self.account_avatar.bind("<Button-1>", lambda _event: self.toggle_account_menu())
        self.account_avatar_image = None
        self.account_avatar_thumb_image = None
        self.load_account_avatar(user_info)

    @staticmethod
    def _avatar_initials(user: dict[str, Any]) -> str:
        name = str(user.get("global_name") or user.get("username") or "SB")
        letters = "".join(part[0] for part in name.split() if part)
        return (letters or name[:2] or "SB").upper()[:2]

    def load_account_avatar(self, user: dict[str, Any]) -> None:
        user_id = str(user.get("id") or "")
        avatar_hash = str(user.get("avatar") or "")
        if not user_id:
            return
        urls = []
        if avatar_hash:
            urls.append(f"https://cdn.discordapp.com/avatars/{user_id}/{avatar_hash}.png?size=128")
        try:
            urls.append(f"https://cdn.discordapp.com/embed/avatars/{int(user_id) % 5}.png")
        except ValueError:
            pass
        if not requests:
            return

        def worker() -> None:
            for url in urls:
                try:
                    response = requests.get(url, timeout=(5, 15))
                    response.raise_for_status()
                    self.root.after(0, self._apply_account_avatar, response.content)
                    return
                except Exception:
                    continue
        threading.Thread(target=worker, daemon=True, name="sb3-account-avatar").start()

    def _apply_account_avatar(self, raw: bytes) -> None:
        if not (Image and ImageDraw and ImageOps and ImageTk):
            return
        try:
            image = Image.open(io.BytesIO(raw)).convert("RGBA")
            image = ImageOps.fit(image, (34, 34), Image.Resampling.LANCZOS)
            mask = Image.new("L", (34, 34), 0)
            ImageDraw.Draw(mask).ellipse((0, 0, 33, 33), fill=255)
            image.putalpha(mask)
            self.account_avatar_image = ImageTk.PhotoImage(image, master=self.root)
            thumb = ImageOps.fit(image.convert("RGBA"), (34, 34), Image.Resampling.LANCZOS)
            thumb_mask = Image.new("L", (34, 34), 0)
            ImageDraw.Draw(thumb_mask).ellipse((0, 0, 33, 33), fill=255)
            thumb.putalpha(thumb_mask)
            self.account_avatar_thumb_image = ImageTk.PhotoImage(thumb, master=self.root)
            self.account_avatar.itemconfigure(self.account_avatar_item, image=self.account_avatar_image, state="normal")
            self.account_avatar.itemconfigure(self.account_avatar_fallback, state="hidden")
            popup = getattr(self, "account_popup_avatar", None)
            if popup and popup.winfo_exists():
                popup.itemconfigure(self.account_popup_image_item, image=self.account_avatar_thumb_image, state="normal")
                popup.itemconfigure(self.account_popup_fallback, state="hidden")
        except (OSError, tk.TclError):
            pass

    def toggle_account_menu(self) -> None:
        if getattr(self, "account_menu", None) and self.account_menu.winfo_exists():
            self.account_menu.destroy()
            self.account_menu = None
            return
        self.root.update_idletasks()
        menu = tk.Frame(self.root, bg=BG, highlightthickness=0, bd=0)
        x = max(8, self.account_avatar.winfo_rootx() - self.root.winfo_rootx() - 228)
        y = max(8, self.account_avatar.winfo_rooty() - self.root.winfo_rooty())
        menu.place(x=x, y=y, width=220, height=205)
        menu.lift()
        self.account_menu = menu
        surface = RoundedSurface(menu, fill=PANEL, radius=16, width=220, height=205, background=PANEL)
        surface.pack(fill="both", expand=True)
        content = surface.content
        user_info = load_discord_session().get("user") or {}
        top = tk.Frame(content, bg=PANEL, height=40)
        top.pack(fill="x", padx=12, pady=(12, 8))
        top.pack_propagate(False)
        popup_avatar = tk.Canvas(top, width=34, height=34, bg=PANEL, highlightthickness=0, bd=0)
        popup_avatar.pack(side="left")
        self.account_popup_avatar = popup_avatar
        self.account_popup_image_item = popup_avatar.create_image(17, 17, anchor="center", image="")
        self.account_popup_fallback = popup_avatar.create_text(
            17, 17, text=self._avatar_initials(user_info), fill=TEXT,
            font=("Segoe UI", 9, "bold"), anchor="center"
        )
        if getattr(self, "account_avatar_thumb_image", None):
            popup_avatar.itemconfigure(self.account_popup_image_item, image=self.account_avatar_thumb_image, state="normal")
            popup_avatar.itemconfigure(self.account_popup_fallback, state="hidden")
        username = str(user_info.get("global_name") or user_info.get("username") or "Discord user")
        tk.Label(top, text=username, bg=PANEL, fg=TEXT, font=("Segoe UI", 9, "bold"),
                 anchor="w").pack(side="left", fill="x", expand=True, padx=(9, 0))
        for label, command in ((self.tr("settings"), self.open_settings_panel),
                               (self.tr("support"), self.open_support_panel),
                               (self.tr("logout"), self.logout)):
            button = PillButton(content, text=label, command=lambda action=command: self._account_action(action),
                                fill=CARD, hover_fill=CARD_HOVER, text_color=TEXT, width=176, height=32,
                                background=PANEL)
            button.pack(pady=3)

    def _account_action(self, action: Callable[[], None]) -> None:
        if getattr(self, "account_menu", None) and self.account_menu.winfo_exists():
            self.account_menu.destroy()
            self.account_menu = None
        action()

    def logout(self) -> None:
        self.membership_watch_active = False
        self.stop_all_simulations()
        clear_discord_session()
        self.auth_busy = False
        self.build_login_screen(self.tr("login_message"))

    def load_logo(self, target: tk.Label) -> None:
        path = resource_path("logo.ico")
        if not (Image and path.exists()):
            target.configure(text="SB3", fg=RED, font=("Segoe UI", 18, "bold"))
            return
        try:
            with Image.open(path) as image:
                self.brand_logo = ImageTk.PhotoImage(image.convert("RGBA").resize((46, 46), Image.Resampling.LANCZOS))
            target.configure(image=self.brand_logo)
        except OSError:
            target.configure(text="SB3", fg=RED, font=("Segoe UI", 18, "bold"))

    def load_featured_ranks(self) -> dict[str, int]:
        """Load the bundled popular-game manifest; absence degrades gracefully."""
        try:
            manifest = json.loads(resource_path("assets/featured_games.json").read_text(encoding="utf-8"))
            return {str(item["id"]): int(item["rank"]) for item in manifest if "id" in item and "rank" in item}
        except (OSError, ValueError, TypeError):
            return {}

    def local_game_paths_file(self) -> Path:
        return Path(os.getenv("LOCALAPPDATA", str(Path.home()))) / "Sba3Dev" / "game_paths.json"

    def load_local_game_paths(self) -> dict[str, str]:
        try:
            data = json.loads(self.local_game_paths_file().read_text(encoding="utf-8"))
            return data if isinstance(data, dict) else {}
        except (OSError, ValueError, TypeError):
            return {}

    def save_local_game_paths(self) -> None:
        try:
            path = self.local_game_paths_file()
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(self.local_game_paths, ensure_ascii=False, indent=2), encoding="utf-8")
        except OSError:
            pass

    def settings_file(self) -> Path:
        return Path(os.getenv("LOCALAPPDATA", str(Path.home()))) / "Sba3Dev" / "settings.json"

    def load_appearance_settings(self) -> dict[str, Any]:
        defaults: dict[str, Any] = {"font_scale": 1.0, "contrast": "calm", "language": "en"}
        try:
            data = json.loads(self.settings_file().read_text(encoding="utf-8"))
            if not isinstance(data, dict):
                return defaults
            scale = float(data.get("font_scale", defaults["font_scale"]))
            contrast = str(data.get("contrast", defaults["contrast"]))
            language = str(data.get("language", defaults["language"]))
            return {"font_scale": min(1.25, max(0.9, scale)),
                    "contrast": contrast if contrast in {"calm", "high"} else "calm",
                    "language": language if language in {"en", "ar"} else "en"}
        except (OSError, ValueError, TypeError):
            return defaults

    def save_appearance_settings(self) -> None:
        try:
            path = self.settings_file()
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(self.appearance_settings, ensure_ascii=False, indent=2), encoding="utf-8")
        except OSError:
            pass

    def tr(self, key: str, **values: Any) -> str:
        text = UI_TEXT.get(self.appearance_settings.get("language", "en"), UI_TEXT["en"]).get(key, key)
        return text.format(**values)

    def _apply_appearance_palette(self) -> None:
        palette = HIGH_CONTRAST_PALETTE if self.appearance_settings.get("contrast") == "high" else BURGUNDY_PALETTE
        for key, value in palette.items():
            globals()[key] = value
        scale = float(self.appearance_settings.get("font_scale", 1.0))
        self.root.tk.call("tk", "scaling", self.base_tk_scaling * scale)

    def bundled_icon_path(self, app_id: str) -> Path:
        return resource_path(f"assets/icons/{app_id}.png")

    def runtime_icon_path(self, app_id: str) -> Path:
        base = Path(os.getenv("LOCALAPPDATA", str(Path.home()))) / "Sba3Dev" / "icons"
        return base / f"{app_id}.png"

    def read_local_icon(self, app_id: str) -> bytes | None:
        for path in (self.bundled_icon_path(app_id), self.runtime_icon_path(app_id)):
            try:
                if path.is_file():
                    return path.read_bytes()
            except OSError:
                pass
        return None

    def save_runtime_icon(self, app_id: str, raw: bytes) -> None:
        try:
            path = self.runtime_icon_path(app_id)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)
        except OSError:
            pass

    def build_library(self) -> None:
        top = tk.Frame(self.library_panel, bg=PANEL)
        top.pack(fill="x", padx=22, pady=(20, 10))
        self.results = tk.Label(top, text=self.tr("preparing_library"), bg=PANEL, fg=MUTED, font=("Segoe UI", 9))
        self.results.pack(side="left")
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", self._on_search_change)
        search_surface = RoundedSurface(self.library_panel, fill=INPUT, radius=14, width=580, height=56, background=PANEL)
        search_surface.pack(fill="x", padx=22, pady=(0, 4))
        search_box = search_surface.content
        tk.Label(search_box, text="⌕", bg=INPUT, fg=TEXT_DIM, font=("Segoe UI Symbol", 15, "bold"), width=2).pack(side="left", padx=(8, 3))
        search = tk.Entry(search_box, textvariable=self.search_var, bg=INPUT, fg=TEXT, insertbackground=TEXT,
                          selectbackground=RED, selectforeground="white", exportselection=False, relief="flat",
                          highlightthickness=0, font=("Segoe UI", 11))
        search.pack(side="left", fill="x", expand=True, ipady=7, pady=1)
        clear = PillButton(search_box, text="×", command=self.clear_search, fill=INPUT, hover_fill=CARD_HOVER,
                           text_color=TEXT_DIM, font=("Segoe UI", 13), width=30, height=30, background=INPUT)
        clear.pack(side="right", padx=(3, 7), pady=7)
        self.search_entry = search
        self.search_clear_button = clear
        # Keep bindings local to the search control so Arabic IME input is never intercepted globally.
        search.bind("<<Paste>>", self._paste_search)
        search.bind("<Control-KeyPress>", self._search_control_key)
        search.bind("<Shift-Insert>", self._paste_search)
        search.bind("<Button-3>", self._show_search_menu)
        search.bind("<Escape>", lambda _event: self.clear_search() or "break")
        tk.Label(self.library_panel, text=self.tr("search_hint"), bg=PANEL, fg=MUTED, font=("Segoe UI", 8)).pack(anchor="w", padx=24, pady=(0, 10))
        search.focus_set()
        outer = tk.Frame(self.library_panel, bg=PANEL)
        outer.pack(fill="both", expand=True, padx=17, pady=(0, 10))
        self.canvas = tk.Canvas(outer, bg=PANEL, highlightthickness=0, bd=0)
        self.canvas.pack(side="left", fill="both", expand=True)
        bar = SoftScrollbar(outer, command=self.canvas.yview, background=PANEL)
        bar.pack(side="right", fill="y", padx=(7, 2))
        self.canvas.configure(yscrollcommand=bar.set)
        self.cards = tk.Frame(self.canvas, bg=PANEL)
        self.card_window = self.canvas.create_window((0, 0), window=self.cards, anchor="nw")
        self.cards.bind("<Configure>", lambda _e: self._refresh_scroll_region(self.canvas))
        self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfigure(self.card_window, width=e.width))
        if not getattr(self, "_mousewheel_bound", False):
            self.root.bind_all("<MouseWheel>", self._route_mousewheel, add="+")
            self.root.bind_all("<Button-4>", lambda e: self._route_mousewheel(e, -1), add="+")
            self.root.bind_all("<Button-5>", lambda e: self._route_mousewheel(e, 1), add="+")
            self._mousewheel_bound = True
        self.more_btn = PillButton(self.library_panel, text=self.tr("load_more"), command=self.show_more, fill=INPUT,
                                   hover_fill=CARD_HOVER, text_color=TEXT_DIM, width=126, height=36, background=PANEL)
        self.show_library_loading()

    def build_queue(self) -> None:
        top = tk.Frame(self.queue_panel, bg=PANEL)
        top.pack(fill="x", padx=22, pady=(21, 9))
        tk.Label(top, text=self.tr("quest_queue"), bg=PANEL, fg=TEXT, font=("Segoe UI", 12, "bold")).pack(side="left")
        self.stop_all_button = PillButton(top, text=self.tr("stop_all"), command=self.stop_all_simulations,
                                          fill=RED_DARK, hover_fill=RED_DARK_HOVER, width=82, height=30,
                                          background=PANEL)
        self.queue_count = tk.Label(top, text=f"0 {self.tr('selected')}", bg=PANEL, fg=MUTED, font=("Segoe UI", 9, "bold"))
        self.queue_count.pack(side="right")
        tk.Label(self.queue_panel, text=self.tr("queue_help"), bg=PANEL, fg=TEXT_DIM,
                 font=("Segoe UI", 9), justify="left", wraplength=265).pack(anchor="w", padx=22, pady=(0, 14))
        queue_outer = tk.Frame(self.queue_panel, bg=PANEL)
        queue_outer.pack(fill="both", expand=True, padx=17, pady=(0, 17))
        self.queue_canvas = tk.Canvas(queue_outer, bg=PANEL, highlightthickness=0, bd=0)
        self.queue_canvas.pack(side="left", fill="both", expand=True)
        self.queue_scrollbar = SoftScrollbar(queue_outer, command=self.queue_canvas.yview, background=PANEL)
        self.queue_scrollbar.pack(side="right", fill="y", padx=(6, 1))
        self.queue_canvas.configure(yscrollcommand=self.queue_scrollbar.set)
        self.queue = tk.Frame(self.queue_canvas, bg=PANEL)
        self.queue_window = self.queue_canvas.create_window((0, 0), window=self.queue, anchor="nw")
        self.queue.bind("<Configure>", lambda _e: self._refresh_scroll_region(self.queue_canvas))
        self.queue_canvas.bind("<Configure>", lambda e: self.queue_canvas.itemconfigure(self.queue_window, width=e.width))
        self.render_queue()

    def _refresh_scroll_region(self, canvas: tk.Canvas | None) -> None:
        if canvas and canvas.winfo_exists():
            bounds = canvas.bbox("all")
            if bounds:
                canvas.configure(scrollregion=bounds)

    def _pointer_is_over(self, widget: tk.Widget, event) -> bool:
        try:
            pointer_x = getattr(event, "x_root", self.root.winfo_pointerx())
            pointer_y = getattr(event, "y_root", self.root.winfo_pointery())
            return (widget.winfo_rootx() <= pointer_x < widget.winfo_rootx() + widget.winfo_width()
                    and widget.winfo_rooty() <= pointer_y < widget.winfo_rooty() + widget.winfo_height())
        except tk.TclError:
            return False

    def _route_mousewheel(self, event, explicit_steps: int | None = None):
        if explicit_steps is None:
            delta = int(getattr(event, "delta", 0))
            steps = int(-delta / 120) if delta else 0
            if not steps and delta:
                steps = -1 if delta > 0 else 1
        else:
            steps = explicit_steps
        if not steps:
            return None
        for canvas in (self.queue_canvas, self.canvas):
            if canvas and self._pointer_is_over(canvas, event):
                canvas.yview_scroll(steps, "units")
                return "break"
        return None

    def _capture_dimmed_background(self) -> Image.Image | None:
        """Capture a dimmed image of the app; dialogs reuse its pixels in their rounded corners."""
        if not (Image and ImageGrab):
            return None
        try:
            self.root.update_idletasks()
            x, y = self.root.winfo_rootx(), self.root.winfo_rooty()
            width, height = self.root.winfo_width(), self.root.winfo_height()
            if width < 2 or height < 2:
                return None
            frame = ImageGrab.grab(bbox=(x, y, x + width, y + height), all_screens=True).convert("RGBA")
            dimmer = Image.new("RGBA", frame.size, (0, 0, 0, 150))
            return Image.alpha_composite(frame, dimmer)
        except Exception:
            return None

    def _show_in_app_panel(self, title: str, height: int) -> tk.Frame:
        """Show a rounded dialog with corners composited against the actual dimmed app behind it."""
        self._close_in_app_panel()
        dimmed_frame = self._capture_dimmed_background()
        overlay = tk.Frame(self.root, bg=BG)
        overlay.place(relx=0, rely=0, relwidth=1, relheight=1)
        dialog_width = 410
        dialog_underlay = None
        if dimmed_frame:
            backdrop_image = ImageTk.PhotoImage(dimmed_frame)
            backdrop = tk.Label(overlay, image=backdrop_image, bg=BG, bd=0)
            backdrop.image = backdrop_image
            backdrop.place(relx=0, rely=0, relwidth=1, relheight=1)
            left = max(0, (dimmed_frame.width - dialog_width) // 2)
            top = max(0, (dimmed_frame.height - height) // 2)
            dialog_underlay = dimmed_frame.crop((left, top, left + dialog_width, top + height))
        overlay.lift()
        surface = RoundedSurface(overlay, fill=PANEL, radius=26, width=dialog_width, height=height,
                                 background=BG, background_image=dialog_underlay)
        surface.place(relx=0.5, rely=0.5, anchor="center", width=dialog_width, height=height)
        panel = surface.content
        panel.surface = surface
        close = PillButton(panel, text="×", command=self._close_in_app_panel, fill=PANEL,
                           hover_fill=CARD_HOVER, text_color=TEXT_DIM, font=("Segoe UI", 15),
                           width=34, height=34, background=PANEL)
        close.place(relx=1.0, x=-13, y=13, anchor="ne")
        tk.Label(panel, text=title, bg=PANEL, fg=TEXT, font=("Segoe UI", 13, "bold")).pack(pady=(24, 9))
        self.in_app_overlay = overlay
        return panel

    def _close_in_app_panel(self) -> None:
        if self.in_app_overlay and self.in_app_overlay.winfo_exists():
            self.in_app_overlay.destroy()
        self.in_app_overlay = None

    def _on_search_change(self, *_args) -> None:
        """Schedule filtering once after normal typing, IME commits, or a pasted Unicode string."""
        self.schedule_filter()

    def clear_search(self) -> None:
        self.search_var.set("")
        self.search_entry.focus_set()

    def _search_control_key(self, event):
        """Windows keeps virtual-key code 86 for the physical V key even under Arabic layouts."""
        if getattr(event, "keycode", None) == 86 or str(getattr(event, "keysym", "")).lower() == "v":
            return self._paste_search()
        return None

    def _paste_search(self, _event=None):
        """Paste one Unicode string directly into this Entry, independent of keyboard layout or Tk class bindings."""
        try:
            text = self.root.clipboard_get()
            text = str(text).replace("\r\n", " ").replace("\r", " ").replace("\n", " ")
        except tk.TclError:
            return "break"
        entry = self.search_entry
        try:
            if entry.selection_present():
                start, end = entry.index(tk.SEL_FIRST), entry.index(tk.SEL_LAST)
            else:
                start = end = entry.index(tk.INSERT)
        except tk.TclError:
            start = end = entry.index(tk.INSERT)
        entry.delete(start, end)
        entry.insert(start, text)
        entry.icursor(start + len(text))
        entry.focus_set()
        return "break"

    def _show_search_menu(self, event):
        # قائمة مختصرة وهادئة: تباين لطيف، وحالة مرور لا تنافس زر الإجراء الرئيسي.
        menu = tk.Menu(self.root, tearoff=False, bg=CARD, fg=TEXT,
                       activebackground=CARD_HOVER, activeforeground=TEXT,
                       font=("Segoe UI", 9), bd=0, relief="flat", activeborderwidth=0)
        menu.add_command(label="Paste", command=self._paste_search)
        menu.add_separator()
        menu.add_command(label="Clear", command=self.clear_search)
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()
        return "break"

    def _add_panel_logo(self, panel: tk.Frame, size: int = 80) -> None:
        logo_label = tk.Label(panel, bg=str(panel.cget("bg")))
        logo_label.pack(pady=(4, 9))
        icon_path = resource_path("logo.ico")
        if Image and icon_path.exists():
            try:
                with Image.open(icon_path) as image:
                    panel.logo_image = ImageTk.PhotoImage(ImageOps.contain(image.convert("RGBA"), (size, size), Image.Resampling.LANCZOS))
                logo_label.configure(image=panel.logo_image)
                return
            except OSError:
                pass
        logo_label.configure(text="SB3", fg=RED, font=("Segoe UI", 24, "bold"))

    def open_support_panel(self) -> None:
        panel = self._show_in_app_panel(self.tr("support_title"), 365)
        self._add_panel_logo(panel, 82)
        tk.Label(panel, text=self.tr("support_message"), bg=PANEL, fg=TEXT_DIM,
                 font=("Segoe UI", 9), wraplength=275, justify="center").pack(pady=(0, 18))
        join = PillButton(panel, text=self.tr("join_support"), fill=RED, hover_fill=RED_HOVER,
                          width=192, height=40, background=PANEL,
                          command=lambda: webbrowser.open_new_tab(SUPPORT_DISCORD_URL))
        join.pack(pady=(0, 10))
        tk.Label(panel, text="https://discord.gg/WcknYK29Hq", bg=PANEL, fg=MUTED, font=("Segoe UI", 8)).pack()

    def _set_appearance(self, *, font_scale: float | None = None, contrast: str | None = None,
                        language: str | None = None) -> None:
        if font_scale is not None:
            self.appearance_settings["font_scale"] = min(1.25, max(0.9, float(font_scale)))
        if contrast in {"calm", "high"}:
            self.appearance_settings["contrast"] = contrast
        if language in {"en", "ar"}:
            self.appearance_settings["language"] = language
        self.save_appearance_settings()
        self._apply_appearance_palette()
        if self.auth_screen == "update" and self.auth_busy:
            return
        self._rebuild_interface()

    def _rebuild_interface(self) -> None:
        """Rebuild the visual layer so saved appearance choices apply consistently."""
        if self.auth_screen == "login":
            self.build_login_screen()
            return
        if self.auth_screen == "membership":
            self.build_membership_screen()
            return
        if self.auth_screen == "update" and self.latest_manifest:
            self.show_update_screen(self.latest_manifest)
            return
        query = self.search_var.get() if hasattr(self, "search_var") else ""
        if self.spinner_job:
            try:
                self.root.after_cancel(self.spinner_job)
            except tk.TclError:
                pass
            self.spinner_job = None
        self.loading_active = False
        self.in_app_overlay = None
        for widget in self.root.winfo_children():
            widget.destroy()
        self.root.configure(bg=BG)
        self.build_ui()
        self._enable_feedback_tree(self.root)
        if self.all_games:
            self.library_count.configure(text=f"Library · {len(self.all_games):,} games")
            self.search_var.set(query)
            self.filter_games()
        self.render_queue()

    def open_settings_panel(self) -> None:
        panel = self._show_in_app_panel(self.tr("settings_title"), 480)
        tk.Label(panel, text=self.tr("settings_note"), bg=PANEL, fg=TEXT_DIM,
                 font=("Segoe UI", 9), justify="center").pack(pady=(0, 14))
        tk.Label(panel, text=self.tr("text_size"), bg=PANEL, fg=TEXT, font=("Segoe UI", 10, "bold")).pack()
        size_row = tk.Frame(panel, bg=PANEL)
        size_row.pack(pady=(8, 16))
        sizes = (("small", 0.9), ("default", 1.0), ("large", 1.15), ("xl", 1.25))
        active_scale = float(self.appearance_settings.get("font_scale", 1.0))
        for key, value in sizes:
            selected = abs(active_scale - value) < 0.02
            button = PillButton(size_row, text=self.tr(key), width=66, height=32, background=PANEL,
                                fill=RED if selected else CARD, hover_fill=RED_HOVER if selected else CARD_HOVER,
                                text_color=TEXT, command=lambda scale=value: self._set_appearance(font_scale=scale))
            button.pack(side="left", padx=3)
        tk.Label(panel, text=self.tr("contrast"), bg=PANEL, fg=TEXT, font=("Segoe UI", 10, "bold")).pack()
        contrast_row = tk.Frame(panel, bg=PANEL)
        contrast_row.pack(pady=(8, 16))
        current_contrast = self.appearance_settings.get("contrast", "calm")
        for key, value in (("calm", "calm"), ("high_contrast", "high")):
            selected = current_contrast == value
            button = PillButton(contrast_row, text=self.tr(key), width=132, height=34, background=PANEL,
                                fill=RED if selected else CARD, hover_fill=RED_HOVER if selected else CARD_HOVER,
                                text_color=TEXT, command=lambda mode=value: self._set_appearance(contrast=mode))
            button.pack(side="left", padx=4)
        tk.Label(panel, text=self.tr("language"), bg=PANEL, fg=TEXT, font=("Segoe UI", 10, "bold")).pack()
        language_row = tk.Frame(panel, bg=PANEL)
        language_row.pack(pady=(8, 4))
        current_language = self.appearance_settings.get("language", "en")
        for label, value in (("العربية", "ar"), ("English", "en")):
            selected = current_language == value
            button = PillButton(language_row, text=label, width=132, height=34, background=PANEL,
                                fill=RED if selected else CARD, hover_fill=RED_HOVER if selected else CARD_HOVER,
                                text_color=TEXT, command=lambda lang=value: self._set_appearance(language=lang))
            button.pack(side="left", padx=4)

    def show_library_loading(self) -> None:
        """Make library loading obvious in the main content area, not only in the status corner."""
        self.loading_active = True
        self.more_btn.pack_forget()
        for widget in self.cards.winfo_children():
            widget.destroy()
        holder = tk.Frame(self.cards, bg=PANEL)
        holder.pack(fill="both", expand=True, pady=125)
        self.spinner_label = tk.Label(holder, text="◐", bg=PANEL, fg=RED, font=("Segoe UI Symbol", 32, "bold"))
        self.spinner_label.pack(pady=(0, 12))
        tk.Label(holder, text=self.tr("loading_games"), bg=PANEL, fg=TEXT, font=("Segoe UI", 11, "bold")).pack()
        tk.Label(holder, text=self.tr("loading_wait"), bg=PANEL, fg=MUTED,
                 font=("Segoe UI", 9)).pack(pady=(5, 0))
        frames = ("◐", "◓", "◑", "◒")
        def spin(index: int = 0) -> None:
            if not self.loading_active or not self.spinner_label.winfo_exists():
                return
            self.spinner_label.configure(text=frames[index % len(frames)])
            self.spinner_job = self.root.after(110, lambda: spin(index + 1))
        spin()

    def hide_library_loading(self) -> None:
        self.loading_active = False
        if self.spinner_job:
            try: self.root.after_cancel(self.spinner_job)
            except tk.TclError: pass
        self.spinner_job = None

    # ---- Discord library ----
    def load_data(self) -> None:
        self.set_status("● Loading Discord library", TEXT_DIM)
        threading.Thread(target=self.library_worker, daemon=True, name="sb3-library").start()

    def library_worker(self) -> None:
        if not requests:
            self.root.after(0, lambda: self.library_error("The requests package is missing."))
            return
        try:
            response = requests.get(DISCORD_DETECTABLE_URL, headers=HEADERS, timeout=(5, 30))
            response.raise_for_status()
            data = response.json()
            if isinstance(data, dict):
                data = data.get("applications") or data.get("games") or data.get("data") or []
            if not isinstance(data, list):
                raise ValueError("Unexpected Discord response")
            games = []
            for raw in data:
                if isinstance(raw, dict) and raw.get("id") and raw.get("name"):
                    item = dict(raw)
                    item["_public_name"] = display_name(item["name"])
                    item["_internal_name"] = str(item["name"]).startswith("#")
                    aliases = " ".join(str(alias) for alias in (item.get("aliases") or []))
                    item["_search"] = f"{item['_public_name']} {item['id']} {aliases}".casefold()
                    item["_exe"] = win_executable(item)
                    item["_platforms"] = platforms_for_game(item)
                    # Discord does not expose an added_at timestamp in this endpoint.
                    # Snowflake IDs contain creation time, so descending ID is the
                    # closest live approximation for newly added applications.
                    item["_featured_rank"] = newest_game_rank(item["id"])
                    games.append(item)
            games.sort(key=lambda item: (item["_featured_rank"], item["_public_name"].casefold()))
            self.root.after(0, lambda: self.apply_library(games))
        except Exception as exc:
            self.root.after(0, lambda: self.library_error(str(exc)))

    def apply_library(self, games: list[dict[str, Any]]) -> None:
        self.hide_library_loading()
        self.all_games = games
        self.library_count.configure(text=f"{self.tr('featured_games')} · {len(games):,}")
        self.set_status(self.tr("library_ready"), SUCCESS)
        self.filter_games()

    def retry_library_load(self) -> None:
        """إعادة المحاولة من الواجهة نفسها من دون الحاجة إلى إعادة تشغيل الأداة."""
        if self.loading_active:
            return
        self.show_library_loading()
        self.load_data()

    def library_error(self, error: str) -> None:
        self.hide_library_loading()
        self.library_count.configure(text=self.tr("library_unavailable"))
        self.set_status(self.tr("library_error"), RED_HOVER)
        self.clear_cards()
        holder = tk.Frame(self.cards, bg=PANEL)
        holder.pack(fill="both", expand=True, pady=112)
        tk.Label(holder, text=self.tr("library_error"), bg=PANEL, fg=TEXT,
                 font=("Segoe UI", 11, "bold"), justify="center").pack()
        tk.Label(holder, text=self.tr("connection_retry"), bg=PANEL, fg=MUTED,
                 font=("Segoe UI", 9), justify="center").pack(pady=(6, 16))
        PillButton(holder, text=self.tr("retry"), command=self.retry_library_load, fill=RED, hover_fill=RED_HOVER,
                   width=112, height=34, background=PANEL).pack()
        print("Discord library error:", error)

    def schedule_filter(self) -> None:
        if self.filter_job:
            try: self.root.after_cancel(self.filter_job)
            except tk.TclError: pass
        self.filter_job = self.root.after(100, self.filter_games)

    def filter_games(self) -> None:
        self.filter_job = None
        query = self.search_var.get().casefold().strip()
        if query:
            self.filtered_games = [game for game in self.all_games if query in game["_search"]]
        else:
            # The first screen is deliberately curated; all other games remain searchable by name or ID.
            self.filtered_games = [game for game in self.all_games if game.get("_featured_rank", FEATURED_LIMIT) < FEATURED_LIMIT]
        self.rendered = 0
        self.clear_cards()
        self.render_next_page()

    def clear_cards(self) -> None:
        for widget in self.cards.winfo_children(): widget.destroy()

    def render_next_page(self) -> None:
        total = len(self.filtered_games)
        end = min(self.rendered + PAGE_SIZE, total)
        for game in self.filtered_games[self.rendered:end]: self.create_game_card(game)
        self.rendered = end
        self.results.configure(text=self.tr("showing", shown=end, total=total) if total else "0")
        if not total:
            tk.Label(self.cards, text=self.tr("no_results"), bg=PANEL, fg=MUTED, font=("Segoe UI", 10)).pack(pady=45)
        if end < total:
            self.more_btn.pack(pady=(0, 12))
        else:
            self.more_btn.pack_forget()
        self._refresh_scroll_region(self.canvas)

    def show_more(self) -> None:
        self.render_next_page()

    def create_game_card(self, game: dict[str, Any]) -> None:
        surface = RoundedSurface(self.cards, fill=CARD, radius=14, width=560, height=88, background=PANEL)
        surface.pack(fill="x", padx=3, pady=5)
        card = surface.content
        card.surface = surface
        icon_slot = tk.Frame(card, width=54, height=54, bg=CARD)
        icon_slot.pack(side="left", padx=(14, 8), pady=8)
        icon_slot.pack_propagate(False)
        initials = game["_public_name"][:1].upper() or "?"
        icon = tk.Label(icon_slot, text=initials, bg=CARD, fg=RED, font=("Segoe UI", 18, "bold"))
        icon.pack(expand=True)
        info = tk.Frame(card, bg=CARD)
        info.pack(side="left", fill="x", expand=True, pady=8)
        tk.Label(info, text=game["_public_name"], bg=CARD, fg=TEXT, font=("Segoe UI", 10, "bold"), anchor="w").pack(fill="x")
        add = PillButton(card, text=self.tr("add"), command=lambda g=game: self.add_to_queue(g), fill=RED,
                         hover_fill=RED_HOVER, width=76, height=32, background=CARD)
        add.pack(side="right", padx=14, pady=16)
        for widget in (surface, card, icon_slot, icon, info):
            widget.bind("<Enter>", lambda _e, c=card: self.hover_card(c, CARD_HOVER))
            widget.bind("<Leave>", lambda _e, c=card: self.hover_card(c, CARD))
        self.request_icon(game, icon)

    def hover_card(self, card: tk.Frame, color: str) -> None:
        try:
            card.configure(bg=color)
            surface = getattr(card, "surface", None)
            if isinstance(surface, RoundedSurface):
                surface.set_fill(color)
            for child in card.winfo_children():
                if isinstance(child, PillButton):
                    child.set_canvas_background(color)
                else:
                    child.configure(bg=color)
                    for grandchild in child.winfo_children():
                        if isinstance(grandchild, PillButton):
                            grandchild.set_canvas_background(color)
                        else:
                            grandchild.configure(bg=color)
        except tk.TclError:
            pass

    def request_icon(self, game: dict[str, Any], target: tk.Label) -> None:
        app_id = str(game.get("id", ""))
        icon_hash = game.get("icon_hash") or game.get("icon")
        key = (app_id, 64)
        if key in self.icon_cache:
            target.configure(image=self.icon_cache[key], text="")
            return
        # Featured-game logos are bundled; runtime cache is checked next.
        local_raw = self.read_local_icon(app_id)
        if local_raw:
            self.apply_icon(key, local_raw, target)
            return
        if not (requests and Image and app_id and icon_hash) or key in self.icon_pending:
            return
        self.icon_pending.add(key)
        def worker() -> None:
            raw = None
            try:
                url = DISCORD_ICON_URL.format(app_id=app_id, icon_hash=icon_hash)
                response = requests.get(url, headers=HEADERS, timeout=(4, 12))
                if response.status_code == 200:
                    raw = response.content
                    self.save_runtime_icon(app_id, raw)
            except Exception:
                pass
            try: self.root.after(0, lambda: self.apply_icon(key, raw, target))
            except tk.TclError: pass
        self.icon_pool.submit(worker)

    def apply_icon(self, key: tuple[str, int], raw: bytes | None, target: tk.Label) -> None:
        self.icon_pending.discard(key)
        if not raw or not target.winfo_exists(): return
        try:
            with Image.open(io.BytesIO(raw)) as image:
                fitted = ImageOps.contain(image.convert("RGBA"), (42, 42), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(fitted)
            self.icon_cache[key] = photo
            target.configure(image=photo, text="")
        except (OSError, tk.TclError): pass

    # ---- Queue, launch and cleanup ----
    def add_to_queue(self, game: dict[str, Any]) -> None:
        game_id = str(game["id"])
        if any(str(item["id"]) == game_id for item in self.selected_quests):
            self.set_status(self.tr("already_queue"), TEXT_DIM)
            return
        item = dict(game)
        item["exe"] = {"name": item.get("_exe") or ""}
        self.selected_quests.append(item)
        self.render_queue()
        self.set_status(self.tr("added", name=item["_public_name"]), SUCCESS)

    def _active_duration_text(self, data: dict[str, Any]) -> str:
        started_at = float(data.get("started_at") or time.monotonic())
        elapsed = max(0, int(time.monotonic() - started_at))
        hours, remainder = divmod(elapsed, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    def _refresh_activity_durations(self) -> None:
        self.activity_timer_job = None
        for qid, label in list(self.activity_duration_labels.items()):
            data = self.active_simulations.get(qid)
            try:
                if data and label.winfo_exists():
                    label.configure(text=self._active_duration_text(data))
            except tk.TclError:
                pass
        if self.active_simulations:
            self.activity_timer_job = self.root.after(1000, self._refresh_activity_durations)

    def _schedule_activity_duration_refresh(self) -> None:
        if self.activity_timer_job:
            try:
                self.root.after_cancel(self.activity_timer_job)
            except tk.TclError:
                pass
            self.activity_timer_job = None
        if self.active_simulations:
            self.activity_timer_job = self.root.after(0, self._refresh_activity_durations)

    def render_queue(self) -> None:
        for widget in self.queue.winfo_children():
            widget.destroy()
        self.activity_duration_labels = {}
        self.queue_count.configure(text=f"{len(self.selected_quests)} {self.tr('selected')}")
        if self.active_simulations:
            self.stop_all_button.pack(side="right", padx=(0, 8))
        else:
            self.stop_all_button.pack_forget()
        if not self.selected_quests:
            tk.Label(self.queue, text=self.tr("empty_queue"), bg=PANEL, fg=MUTED, font=("Segoe UI", 10)).pack(pady=30)
            self._schedule_activity_duration_refresh()
            return
        for quest in self.selected_quests:
            qid = str(quest["id"])
            running = qid in self.active_simulations
            card_height = 86 if running else 76
            surface = RoundedSurface(self.queue, fill=CARD, radius=13, width=292, height=card_height, background=PANEL)
            surface.pack(fill="x", pady=5)
            row = surface.content
            details = tk.Frame(row, bg=CARD)
            details.pack(side="left", fill="x", expand=True, padx=(13, 4), pady=10)
            tk.Label(details, text=quest["_public_name"], bg=CARD, fg=TEXT, anchor="w", wraplength=145,
                     font=("Segoe UI", 9, "bold")).pack(fill="x", anchor="w")
            if running:
                duration = tk.Label(details, text=self._active_duration_text(self.active_simulations[qid]), bg=CARD,
                                    fg=SUCCESS, anchor="w", font=("Segoe UI", 8, "bold"))
                duration.pack(anchor="w", pady=(3, 0))
                self.activity_duration_labels[qid] = duration
                action = PillButton(row, text=self.tr("stop"), fill=RED_DARK, hover_fill=RED_DARK_HOVER, width=58, height=30,
                                    background=CARD, command=lambda key=qid: self.stop_single_simulation(key))
            else:
                action = PillButton(row, text=self.tr("run"), fill=RED, hover_fill=RED_HOVER, width=58, height=30,
                                    background=CARD, command=lambda item=quest: self.run_best_platform(item))
            action.pack(side="right", padx=(1, 4), pady=15)
            remove = PillButton(row, text="×", fill=CARD, hover_fill=CARD_HOVER, text_color=TEXT_DIM,
                                font=("Segoe UI", 13), width=30, height=30, background=CARD,
                                command=lambda key=qid: self.remove_from_queue(key))
            remove.pack(side="right", pady=15)
        self._refresh_scroll_region(self.queue_canvas)
        self._schedule_activity_duration_refresh()

    def remove_from_queue(self, game_id: str) -> None:
        name = next((item.get("_public_name", "Task") for item in self.selected_quests if str(item["id"]) == game_id), "Task")
        if game_id in self.active_simulations:
            self.stop_single_simulation(game_id, refresh=False, notify=False)
        self.selected_quests = [item for item in self.selected_quests if str(item["id"]) != game_id]
        self.render_queue()

    def open_platform_selector(self, quest: dict[str, Any]) -> None:
        """Compatibility entry point: run Discord's first verified/recommended launcher."""
        self.run_best_platform(quest)

    def run_best_platform(self, quest: dict[str, Any]) -> None:
        platforms = platforms_for_game(quest) or tuple(quest.get("_platforms") or ())
        if not platforms:
            messagebox.showinfo(self.tr("no_launcher_title"), self.tr("no_launcher_message", name=quest["_public_name"]))
            return
        # PLATFORM_ORDER is Discord's verified-launcher priority. The first detected
        # launcher is therefore selected silently, without interrupting Run.
        self.start_single_simulation(quest, platforms[0])

    def _start_from_in_app_panel(self, quest: dict[str, Any], platform: str) -> None:
        self._close_in_app_panel()
        self.start_single_simulation(quest, platform)

    def start_single_simulation(self, quest: dict[str, Any], platform: str) -> None:
        """Recreated from the original sb3_app.pyc start_single_simulation flow."""
        qid = str(quest["id"])
        full_path = str((quest.get("exe") or {}).get("name") or "").replace("\\", "/").lstrip("/")
        exe_dir, exe_file = os.path.split(full_path) if "/" in full_path else ("", full_path)
        if not exe_file:
            exe_file = "game.exe"
        session_id = str(int(time.time()))
        base_path = Path.cwd() / "games" / qid / session_id / exe_dir
        base_path.mkdir(parents=True, exist_ok=True)
        temp_exe = base_path / exe_file
        source = Path(sys.executable if getattr(sys, "frozen", False) else sys.argv[0]).resolve()
        try:
            shutil.copy2(source, temp_exe)
            icon_source = resource_path("logo.ico")
            if icon_source.exists():
                shutil.copy2(icon_source, base_path / "logo.ico")
            stop_signal = base_path / "stop.signal"
            command = ([str(temp_exe), "--run-game", quest["name"], platform, str(stop_signal)]
                       if getattr(sys, "frozen", False)
                       else [sys.executable, str(temp_exe), "--run-game", quest["name"], platform, str(stop_signal)])
            proc = subprocess.Popen(command, cwd=str(base_path))
        except OSError as exc:
            shutil.rmtree(base_path.parents[len(Path(exe_dir).parts)] if exe_dir else base_path, ignore_errors=True)
            messagebox.showerror("Launch failed", str(exc))
            return

        rpc = None
        if Presence:
            for _ in range(3):
                try:
                    rpc = Presence(str(quest["id"]))
                    rpc.connect()
                    rpc.update(state=f"Quest Active ({platform})", details=f"Playing {quest['name']}", start=int(time.time()), instance=False)
                    break
                except Exception:
                    rpc = None
                    time.sleep(1)
        # Keep the child process tracked even when the optional Discord RPC connection is unavailable.
        session_root = str(Path.cwd() / "games" / qid)
        self.active_simulations[qid] = {"rpc": rpc, "proc": proc, "platform": platform, "session_path": session_root,
                                        "stop_signal": str(stop_signal), "started_at": time.monotonic(),
                                        "display_name": quest["_public_name"]}
        self.render_queue()

        if rpc:
            def update_rpc_loop() -> None:
                while qid in self.active_simulations and proc.poll() is None:
                    try:
                        rpc.update(state=f"Quest Active ({platform})", details=f"Playing {quest['name']}", start=int(time.time()), instance=False)
                        time.sleep(15)
                    except Exception:
                        return
            threading.Thread(target=update_rpc_loop, daemon=True, name=f"sb3-rpc-{qid}").start()

    def start_monitor(self) -> None:
        def monitor() -> None:
            while not self.stop_event.wait(1.0):
                ended = []
                for qid, data in list(self.active_simulations.items()):
                    if data.get("proc") and data["proc"].poll() is not None:
                        self.dispose(data); ended.append(qid)
                for qid in ended: self.active_simulations.pop(qid, None)
                if ended:
                    try: self.root.after(0, self.render_queue)
                    except tk.TclError: pass
        threading.Thread(target=monitor, daemon=True, name="sb3-monitor").start()

    def dispose(self, data: dict[str, Any]) -> None:
        if data.get("rpc"):
            try: data["rpc"].close()
            except Exception: pass
        if data.get("session_path"): shutil.rmtree(data["session_path"], ignore_errors=True)

    def stop_single_simulation(self, qid: str, refresh: bool = True, notify: bool = True) -> None:
        data = self.active_simulations.pop(qid, None)
        if not data:
            return
        signal_path = data.get("stop_signal")
        if signal_path:
            try:
                Path(str(signal_path)).touch(exist_ok=True)
            except OSError:
                pass
        proc = data.get("proc")
        if proc and proc.poll() is None:
            # On Windows, /T ends every process below this task as well as the task itself.
            # This prevents a hidden activity process from surviving Stop or application shutdown.
            if os.name == "nt":
                try:
                    subprocess.run(["taskkill", "/F", "/T", "/PID", str(proc.pid)],
                                   capture_output=True, timeout=5)
                except (OSError, subprocess.TimeoutExpired):
                    pass
            else:
                try:
                    proc.kill()
                except OSError:
                    pass
            try:
                proc.wait(timeout=2)
            except (subprocess.TimeoutExpired, OSError):
                pass
        self.dispose(data)
        if refresh:
            self.render_queue()


    def stop_all_simulations(self) -> None:
        count = len(self.active_simulations)
        if not count:
            return
        for qid in list(self.active_simulations):
            self.stop_single_simulation(qid, refresh=False, notify=False)
        self.render_queue()
        self.set_status(self.tr("stopped_tasks", count=count), RED_HOVER)

    def _deep_cleanup(self) -> None:
        self.stop_event.set()
        if self.activity_timer_job:
            try:
                self.root.after_cancel(self.activity_timer_job)
            except tk.TclError:
                pass
            self.activity_timer_job = None
        for qid in list(self.active_simulations):
            self.stop_single_simulation(qid, refresh=False, notify=False)
        self.icon_pool.shutdown(wait=False, cancel_futures=True)
        shutil.rmtree(Path.cwd() / "games", ignore_errors=True)

    def on_closing(self) -> None:
        self._deep_cleanup()
        self.root.destroy()

    def set_status(self, text: str, color: str) -> None:
        try: self.status.configure(text=text, fg=color)
        except AttributeError: pass


def main() -> None:
    if "--run-game" in sys.argv:
        index = sys.argv.index("--run-game")
        stop_signal = sys.argv[index + 3] if len(sys.argv) > index + 3 else ""
        run_game_process(sys.argv[index + 1], sys.argv[index + 2], stop_signal)
        return

    root = tk.Tk()
    QuestCompleterApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
