#!/usr/bin/env python3
"""Clears the menu bar inbox item for this session.

Triggered by PreToolUse / Stop hooks — meaning Claude is no longer waiting.
Standalone script, no dependencies beyond stdlib.
"""
import json
import sys
from pathlib import Path

INBOX_DIR = Path.home() / ".claude-menubar" / "inbox"


def main():
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        return

    session_id = data.get("session_id", "")
    if not session_id:
        return

    if not INBOX_DIR.is_dir():
        return

    for path in INBOX_DIR.glob("*.json"):
        try:
            existing = json.loads(path.read_text())
            if existing.get("session_id") == session_id:
                path.unlink()
        except (json.JSONDecodeError, OSError):
            pass


if __name__ == "__main__":
    main()
