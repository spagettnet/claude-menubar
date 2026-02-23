#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SETTINGS_FILE="$HOME/.claude/settings.json"
INBOX_DIR="$HOME/.claude-menubar/inbox"
PLIST_NAME="com.claude-menubar.app"
PLIST_PATH="$HOME/Library/LaunchAgents/$PLIST_NAME.plist"

echo "=== Claude Menubar Installer ==="
echo

# 1. Install dependencies with uv
echo "[1/4] Installing Python dependencies..."
cd "$SCRIPT_DIR"
uv sync
echo "  Done."
echo

# 2. Create inbox directory
echo "[2/4] Creating inbox directory..."
mkdir -p "$INBOX_DIR"
echo "  Created $INBOX_DIR"
echo

# 3. Configure Claude Code hooks (nondestructive — appends to existing hooks)
echo "[3/4] Configuring Claude Code hooks..."
if [ -f "$SETTINGS_FILE" ]; then
    python3 -c "
import json, sys

settings_path = '$SETTINGS_FILE'
script_dir = '$SCRIPT_DIR'

with open(settings_path) as f:
    settings = json.load(f)

hooks = settings.setdefault('hooks', {})

# Each entry: (event_name, hook_script, matcher)
hook_entries = [
    ('Notification', f'python3 {script_dir}/hooks/notify_hook.py', ''),
    ('Stop', f'python3 {script_dir}/hooks/stop_hook.py', ''),
    ('PreToolUse', f'python3 {script_dir}/hooks/clear_hook.py', ''),
]

added = []
skipped = []

for event_name, command, matcher in hook_entries:
    event_hooks = hooks.setdefault(event_name, [])

    # Check if this command is already registered
    already_exists = False
    for entry in event_hooks:
        for h in entry.get('hooks', []):
            if script_dir in h.get('command', ''):
                already_exists = True
                break
        if already_exists:
            break

    if already_exists:
        skipped.append(event_name)
    else:
        event_hooks.append({
            'matcher': matcher,
            'hooks': [{
                'type': 'command',
                'command': command,
            }]
        })
        added.append(event_name)

if added:
    with open(settings_path, 'w') as f:
        json.dump(settings, f, indent=2)
    print(f'  Added hooks: {', '.join(added)}')
if skipped:
    print(f'  Already configured: {', '.join(skipped)}')
if not added and not skipped:
    print('  No changes needed.')
"
else
    mkdir -p "$HOME/.claude"
    python3 -c "
import json

settings = {
    'hooks': {
        'Notification': [{
            'matcher': '',
            'hooks': [{'type': 'command', 'command': 'python3 $SCRIPT_DIR/hooks/notify_hook.py'}]
        }],
        'Stop': [{
            'matcher': '',
            'hooks': [{'type': 'command', 'command': 'python3 $SCRIPT_DIR/hooks/stop_hook.py'}]
        }],
        'PreToolUse': [{
            'matcher': '',
            'hooks': [{'type': 'command', 'command': 'python3 $SCRIPT_DIR/hooks/clear_hook.py'}]
        }],
    }
}

with open('$SETTINGS_FILE', 'w') as f:
    json.dump(settings, f, indent=2)
print('  Created $SETTINGS_FILE with hooks.')
"
fi
echo

# 4. Offer to create a LaunchAgent for auto-start
echo "[4/4] Auto-start on login..."

read -p "  Create a LaunchAgent to start on login? [y/N] " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    cat > "$PLIST_PATH" << PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>$PLIST_NAME</string>
    <key>ProgramArguments</key>
    <array>
        <string>$SCRIPT_DIR/.venv/bin/claude-menubar</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <false/>
    <key>WorkingDirectory</key>
    <string>$SCRIPT_DIR</string>
</dict>
</plist>
PLIST
    launchctl load "$PLIST_PATH" 2>/dev/null || true
    echo "  Created and loaded $PLIST_PATH"
else
    echo "  Skipped. You can run it manually with: cd $SCRIPT_DIR && uv run claude-menubar"
fi

echo
echo "=== Installation complete ==="
echo
echo "To start now:  cd $SCRIPT_DIR && uv run claude-menubar"
echo "To uninstall:  launchctl unload $PLIST_PATH 2>/dev/null; rm -f $PLIST_PATH"
