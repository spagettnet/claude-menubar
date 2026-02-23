#!/usr/bin/env python3
"""Claude Code notification hook — writes notifications to the menu bar inbox.

This script is called by Claude Code's Notification hook event.
It receives JSON on stdin and writes a notification file to ~/.claude-menubar/inbox/.

This is a standalone script with no dependencies beyond the Python stdlib.
"""
import json
import os
import subprocess
import sys
import time
import uuid
from pathlib import Path

INBOX_DIR = Path.home() / ".claude-menubar" / "inbox"


def find_terminal_info() -> tuple[str, int]:
    """Walk up the process tree to find the terminal application."""
    known_terminals = {
        "iTerm2", "Terminal", "Alacritty", "kitty", "WezTerm",
        "Hyper", "Tabby", "Rio", "Ghostty",
    }

    pid = os.getpid()
    for _ in range(15):
        if pid <= 1:
            break
        try:
            result = subprocess.run(
                ["ps", "-o", "ppid=,comm=", "-p", str(pid)],
                capture_output=True, text=True, timeout=2,
            )
            if result.returncode != 0:
                break
            line = result.stdout.strip()
            if not line:
                break
            parts = line.split(None, 1)
            if len(parts) < 2:
                break
            ppid = int(parts[0])
            comm = parts[1].strip()
            app_name = comm.rsplit("/", 1)[-1]
            if app_name in known_terminals:
                return app_name, pid
            pid = ppid
        except (subprocess.TimeoutExpired, ValueError, OSError):
            break

    return "", 0


def get_claude_pid() -> int:
    """Find the Claude Code process in our ancestry."""
    pid = os.getppid()
    for _ in range(5):
        if pid <= 1:
            break
        try:
            result = subprocess.run(
                ["ps", "-o", "ppid=,comm=", "-p", str(pid)],
                capture_output=True, text=True, timeout=2,
            )
            if result.returncode != 0:
                break
            line = result.stdout.strip()
            if not line:
                break
            parts = line.split(None, 1)
            if len(parts) < 2:
                break
            comm = parts[1].strip().rsplit("/", 1)[-1]
            if "claude" in comm.lower() or "node" in comm.lower():
                return pid
            pid = int(parts[0])
        except (subprocess.TimeoutExpired, ValueError, OSError):
            break

    # Fallback: use direct parent
    return os.getppid()


def get_tty_for_pid(pid: int) -> str:
    """Get the TTY device path for a given PID."""
    try:
        result = subprocess.run(
            ["ps", "-o", "tty=", "-p", str(pid)],
            capture_output=True, text=True, timeout=2,
        )
        tty = result.stdout.strip()
        if tty and tty != "??":
            return f"/dev/{tty}"
    except (subprocess.TimeoutExpired, OSError):
        pass
    return ""


def main():
    INBOX_DIR.mkdir(parents=True, exist_ok=True)

    # Read notification data from stdin
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        data = {}

    message = data.get("message", "Claude needs attention")
    title = data.get("title", "Claude Code")
    notification_type = data.get("notification_type", "unknown")
    session_id = data.get("session_id", "")
    cwd = data.get("cwd", "")

    # Extra fields from PermissionRequest hooks
    tool_name = data.get("tool_name", "")
    tool_input = data.get("tool_input", "")
    if isinstance(tool_input, dict):
        # Summarize the tool input for display
        tool_input = json.dumps(tool_input, indent=2)

    # Detect terminal
    terminal_app, terminal_pid = find_terminal_info()
    claude_pid = get_claude_pid()
    tty = get_tty_for_pid(claude_pid)

    # Remove existing notification for this session (superseded)
    if session_id:
        for path in INBOX_DIR.glob("*.json"):
            try:
                existing = json.loads(path.read_text())
                if existing.get("session_id") == session_id:
                    path.unlink()
            except (json.JSONDecodeError, OSError):
                pass

    # Write new notification
    notif_id = str(uuid.uuid4())
    notification = {
        "id": notif_id,
        "message": message,
        "title": title,
        "notification_type": notification_type,
        "timestamp": time.time(),
        "claude_pid": claude_pid,
        "terminal_app": terminal_app,
        "terminal_pid": terminal_pid,
        "session_id": session_id,
        "cwd": cwd,
        "tty": tty,
        "tool_name": tool_name,
        "tool_input": tool_input if isinstance(tool_input, str) else "",
    }
    path = INBOX_DIR / f"{notif_id}.json"
    path.write_text(json.dumps(notification))


if __name__ == "__main__":
    main()
