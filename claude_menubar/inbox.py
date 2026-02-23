"""Manage notification files in the inbox directory."""
import json
import os
import time
import uuid
from dataclasses import dataclass, asdict
from pathlib import Path

INBOX_DIR = Path.home() / ".claude-menubar" / "inbox"
CONFIG_PATH = Path.home() / ".claude-menubar" / "config.json"


@dataclass
class Notification:
    id: str
    message: str
    title: str
    notification_type: str
    timestamp: float
    claude_pid: int
    terminal_app: str
    terminal_pid: int
    session_id: str
    cwd: str
    tty: str = ""
    tool_name: str = ""
    tool_input: str = ""
    snoozed_until: float = 0.0


def ensure_inbox_dir():
    INBOX_DIR.mkdir(parents=True, exist_ok=True)


# --- Config (sound toggle, etc.) ---

def load_config() -> dict:
    try:
        return json.loads(CONFIG_PATH.read_text())
    except (json.JSONDecodeError, OSError):
        return {}


def save_config(config: dict):
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(json.dumps(config, indent=2))


def get_sound_enabled() -> bool:
    return load_config().get("sound_enabled", True)


def set_sound_enabled(enabled: bool):
    config = load_config()
    config["sound_enabled"] = enabled
    save_config(config)


# --- Notifications ---

def add_notification(
    message: str,
    title: str = "Claude Code",
    notification_type: str = "unknown",
    claude_pid: int = 0,
    terminal_app: str = "",
    terminal_pid: int = 0,
    session_id: str = "",
    cwd: str = "",
) -> Notification:
    """Write a new notification to the inbox."""
    ensure_inbox_dir()

    # Remove any existing notification for the same session
    if session_id:
        for path in INBOX_DIR.glob("*.json"):
            try:
                data = json.loads(path.read_text())
                if data.get("session_id") == session_id:
                    path.unlink()
            except (json.JSONDecodeError, OSError):
                pass

    notif = Notification(
        id=str(uuid.uuid4()),
        message=message,
        title=title,
        notification_type=notification_type,
        timestamp=time.time(),
        claude_pid=claude_pid,
        terminal_app=terminal_app,
        terminal_pid=terminal_pid,
        session_id=session_id,
        cwd=cwd,
    )
    path = INBOX_DIR / f"{notif.id}.json"
    path.write_text(json.dumps(asdict(notif)))
    return notif


def list_notifications(include_snoozed: bool = False) -> list[Notification]:
    """Read all notifications from the inbox, sorted by timestamp.

    By default, snoozed notifications are hidden until their snooze expires.
    """
    ensure_inbox_dir()
    now = time.time()
    notifications = []
    for path in INBOX_DIR.glob("*.json"):
        try:
            data = json.loads(path.read_text())
            # Fill defaults for fields that may be missing in older files
            for field in ("tty", "tool_name", "tool_input"):
                data.setdefault(field, "")
            data.setdefault("snoozed_until", 0.0)
            notif = Notification(**data)
            if not include_snoozed and notif.snoozed_until > now:
                continue
            notifications.append(notif)
        except (json.JSONDecodeError, OSError, TypeError):
            try:
                path.unlink()
            except OSError:
                pass
    notifications.sort(key=lambda n: n.timestamp)
    return notifications


def snooze(notification_id: str, duration_seconds: int):
    """Snooze a notification for the given duration."""
    path = INBOX_DIR / f"{notification_id}.json"
    try:
        data = json.loads(path.read_text())
        data["snoozed_until"] = time.time() + duration_seconds
        path.write_text(json.dumps(data))
    except (json.JSONDecodeError, OSError):
        pass


def dismiss(notification_id: str):
    """Remove a single notification."""
    path = INBOX_DIR / f"{notification_id}.json"
    try:
        path.unlink()
    except OSError:
        pass


def dismiss_all():
    """Remove all notifications."""
    ensure_inbox_dir()
    for path in INBOX_DIR.glob("*.json"):
        try:
            path.unlink()
        except OSError:
            pass


def cleanup_stale(max_age_seconds: int = 3600):
    """Remove notifications older than max_age or whose Claude process died."""
    ensure_inbox_dir()
    now = time.time()
    for path in INBOX_DIR.glob("*.json"):
        try:
            data = json.loads(path.read_text())
            # Remove if too old
            if now - data.get("timestamp", 0) > max_age_seconds:
                path.unlink()
                continue
            # Remove if Claude process is dead
            pid = data.get("claude_pid", 0)
            if pid > 0:
                try:
                    os.kill(pid, 0)
                except ProcessLookupError:
                    path.unlink()
                except PermissionError:
                    pass
        except (json.JSONDecodeError, OSError):
            try:
                path.unlink()
            except OSError:
                pass
