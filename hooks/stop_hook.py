#!/usr/bin/env python3
"""Creates a 'turn complete' notification when Claude's turn ends.

Triggered by the Stop hook — meaning Claude finished responding and it's
the user's turn. Replaces any existing notification for this session.
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
            comm = parts[1].strip().rsplit("/", 1)[-1]
            if comm in known_terminals:
                return comm, pid
            pid = ppid
        except (subprocess.TimeoutExpired, ValueError, OSError):
            break
    return "", 0


def get_claude_pid() -> int:
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
    return os.getppid()


def get_tty_for_pid(pid: int) -> str:
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

    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        data = {}

    session_id = data.get("session_id", "")
    cwd = data.get("cwd", "")

    if not session_id:
        return

    # Remove existing notification for this session
    for path in INBOX_DIR.glob("*.json"):
        try:
            existing = json.loads(path.read_text())
            if existing.get("session_id") == session_id:
                path.unlink()
        except (json.JSONDecodeError, OSError):
            pass

    # Detect terminal
    terminal_app, terminal_pid = find_terminal_info()
    claude_pid = get_claude_pid()
    tty = get_tty_for_pid(claude_pid)

    # Write "turn complete" notification
    notif_id = str(uuid.uuid4())
    notification = {
        "id": notif_id,
        "message": "Claude finished — your turn",
        "title": "Claude Code",
        "notification_type": "turn_complete",
        "timestamp": time.time(),
        "claude_pid": claude_pid,
        "terminal_app": terminal_app,
        "terminal_pid": terminal_pid,
        "session_id": session_id,
        "cwd": cwd,
        "tty": tty,
        "tool_name": "",
        "tool_input": "",
        "snoozed_until": 0.0,
    }
    path = INBOX_DIR / f"{notif_id}.json"
    path.write_text(json.dumps(notification))


if __name__ == "__main__":
    main()
