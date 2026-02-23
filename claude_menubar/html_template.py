"""HTML template for the popover card UI."""
import html
import time

from claude_menubar.inbox import Notification

CSS = """
* { margin: 0; padding: 0; box-sizing: border-box; }

:root {
    color-scheme: dark;
}

body {
    font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", "Helvetica Neue", sans-serif;
    background: #1c1c1e;
    color: #f5f5f7;
    padding: 12px;
    -webkit-user-select: none;
    overflow-y: auto;
    height: 100vh;
}

.header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 4px 4px 12px 4px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    margin-bottom: 12px;
}

.header-left h1 {
    font-size: 14px;
    font-weight: 600;
    letter-spacing: -0.01em;
    color: #ffffff;
}

.header-left .count {
    font-size: 11px;
    font-weight: 500;
    color: #98989d;
    margin-top: 2px;
}

.header-right {
    display: flex;
    align-items: center;
    gap: 6px;
}

.sound-toggle {
    background: none;
    border: none;
    cursor: pointer;
    padding: 4px 6px;
    border-radius: 6px;
    transition: background 0.15s, color 0.15s;
    line-height: 0;
    color: #636366;
    display: flex;
    align-items: center;
}
.sound-toggle:hover { background: rgba(255, 255, 255, 0.08); color: #98989d; }
.sound-toggle.on { color: #e5e5ea; }

.dismiss-all-btn {
    font-size: 11px;
    color: #64d2ff;
    background: none;
    border: none;
    cursor: pointer;
    font-weight: 500;
    padding: 4px 8px;
    border-radius: 6px;
    transition: background 0.15s;
}
.dismiss-all-btn:hover { background: rgba(100, 210, 255, 0.12); }

.empty {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    height: 300px;
    color: #636366;
}
.empty .icon { font-size: 36px; margin-bottom: 12px; opacity: 0.4; }
.empty p { font-size: 13px; }

.card {
    background: #2c2c2e;
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 12px;
    padding: 14px;
    margin-bottom: 10px;
    transition: background 0.15s, border-color 0.15s;
}
.card:hover {
    background: #3a3a3c;
    border-color: rgba(255, 255, 255, 0.14);
}

.card-top {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 8px;
}

.badge {
    display: inline-block;
    font-size: 10px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    padding: 3px 8px;
    border-radius: 100px;
    white-space: nowrap;
}
.badge.permission {
    background: rgba(255, 159, 10, 0.2);
    color: #ffb340;
}
.badge.idle {
    background: rgba(100, 210, 255, 0.15);
    color: #64d2ff;
}
.badge.complete {
    background: rgba(48, 209, 88, 0.18);
    color: #30d158;
}
.badge.other {
    background: rgba(255, 255, 255, 0.08);
    color: #98989d;
}

.timestamp {
    font-size: 11px;
    color: #636366;
    white-space: nowrap;
    margin-left: 8px;
    flex-shrink: 0;
}

.message {
    font-size: 13px;
    line-height: 1.5;
    margin-bottom: 8px;
    word-wrap: break-word;
    overflow-wrap: break-word;
    color: #e5e5ea;
}

.tool-name {
    font-size: 11px;
    font-weight: 600;
    color: #b4a0d6;
    margin-bottom: 4px;
}

.tool-input {
    font-size: 11px;
    color: #a1a1a6;
    font-family: "SF Mono", Menlo, monospace;
    background: rgba(255, 255, 255, 0.04);
    padding: 8px 10px;
    border-radius: 8px;
    margin-bottom: 8px;
    white-space: pre-wrap;
    word-break: break-all;
    max-height: 80px;
    overflow-y: auto;
    line-height: 1.4;
    border: 1px solid rgba(255, 255, 255, 0.05);
}

.cwd {
    font-size: 11px;
    color: #8e8e93;
    font-family: "SF Mono", Menlo, monospace;
    margin-bottom: 12px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    background: rgba(255, 255, 255, 0.04);
    padding: 4px 8px;
    border-radius: 6px;
}

.card-actions {
    display: flex;
    gap: 6px;
    align-items: center;
}

.card-actions button {
    font-size: 12px;
    font-weight: 500;
    padding: 7px 10px;
    border-radius: 8px;
    border: none;
    cursor: pointer;
    transition: background 0.15s, transform 0.1s;
}
.card-actions button:active { transform: scale(0.97); }

.btn-focus {
    flex: 1;
    background: #0a84ff;
    color: #ffffff;
}
.btn-focus:hover { background: #409cff; }

.btn-dismiss {
    flex: 1;
    background: rgba(255, 255, 255, 0.07);
    color: #98989d;
    border: 1px solid rgba(255, 255, 255, 0.06);
}
.btn-dismiss:hover {
    background: rgba(255, 255, 255, 0.12);
    color: #c7c7cc;
}

/* Snooze icon + hover menu */
.snooze-wrap {
    position: relative;
    display: flex;
    align-items: center;
}

.snooze-icon {
    width: 30px;
    height: 30px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: none;
    border: none;
    color: #636366;
    cursor: pointer;
    border-radius: 8px;
    transition: background 0.15s, color 0.15s;
    padding: 0;
}
.snooze-icon:hover {
    background: rgba(255, 255, 255, 0.08);
    color: #98989d;
}

.snooze-menu {
    display: none;
    position: absolute;
    top: 100%;
    right: 0;
    padding-top: 2px;
    z-index: 10;
}
.snooze-menu-inner {
    background: #2c2c2e;
    border: 1px solid rgba(255, 255, 255, 0.12);
    border-radius: 10px;
    padding: 4px;
    min-width: 130px;
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.5);
}
.snooze-wrap:hover .snooze-menu {
    display: block;
}

.snooze-option {
    display: block;
    width: 100%;
    padding: 7px 12px;
    background: none;
    border: none;
    color: #e5e5ea;
    font-size: 12px;
    font-weight: 400;
    text-align: left;
    cursor: pointer;
    border-radius: 6px;
    transition: background 0.1s;
    white-space: nowrap;
}
.snooze-option:hover {
    background: rgba(255, 255, 255, 0.1);
}

.snooze-custom-row {
    display: flex;
    align-items: center;
    gap: 4px;
    padding: 4px 8px;
}
.snooze-custom-row input {
    width: 40px;
    padding: 4px 6px;
    font-size: 11px;
    background: rgba(255, 255, 255, 0.08);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 5px;
    color: #e5e5ea;
    text-align: center;
    -webkit-appearance: none;
}
.snooze-custom-row input:focus { outline: 1px solid #0a84ff; }
.snooze-custom-row span {
    font-size: 11px;
    color: #98989d;
}
.snooze-custom-row button {
    padding: 4px 8px;
    font-size: 11px;
    font-weight: 500;
    background: #0a84ff;
    color: white;
    border: none;
    border-radius: 5px;
    cursor: pointer;
}
.snooze-custom-row button:hover { background: #409cff; }
"""

JS = """
function send(action, id, extra) {
    var msg = {action: action, id: id || ""};
    if (extra) { for (var k in extra) msg[k] = extra[k]; }
    window.webkit.messageHandlers.bridge.postMessage(msg);
}

function doSnooze(id, seconds) {
    send('snooze', id, {duration: seconds});
}

function customSnooze(id, inputEl) {
    var mins = parseInt(inputEl.value, 10);
    if (mins > 0) {
        send('snooze', id, {duration: mins * 60});
    }
}
"""


def _relative_time(ts: float) -> str:
    diff = time.time() - ts
    if diff < 5:
        return "just now"
    if diff < 60:
        return f"{int(diff)}s ago"
    if diff < 3600:
        return f"{int(diff / 60)}m ago"
    return f"{int(diff / 3600)}h ago"


def _badge_class(notification_type: str) -> str:
    if "permission" in notification_type:
        return "permission"
    if "idle" in notification_type:
        return "idle"
    if "turn_complete" in notification_type or "stop" in notification_type:
        return "complete"
    return "other"


def _badge_label(notification_type: str) -> str:
    if "permission" in notification_type:
        return "Needs Approval"
    if "idle" in notification_type:
        return "Waiting"
    if "turn_complete" in notification_type or "stop" in notification_type:
        return "Your Turn"
    return "Notification"


def _render_card(n: Notification) -> str:
    badge_cls = _badge_class(n.notification_type)
    badge_label = _badge_label(n.notification_type)
    rel_time = _relative_time(n.timestamp)
    msg = html.escape(n.message)
    cwd = html.escape(n.cwd) if n.cwd else ""

    cwd_html = f'<div class="cwd">{cwd}</div>' if cwd else ""

    tool_html = ""
    if n.tool_name:
        tool_name_escaped = html.escape(n.tool_name)
        tool_html = f'<div class="tool-name">Tool: {tool_name_escaped}</div>'
        if n.tool_input:
            preview = n.tool_input
            if len(preview) > 200:
                preview = preview[:197] + "..."
            preview_escaped = html.escape(preview)
            tool_html += f'<pre class="tool-input">{preview_escaped}</pre>'

    return f"""
    <div class="card">
        <div class="card-top">
            <span class="badge {badge_cls}">{badge_label}</span>
            <span class="timestamp">{rel_time}</span>
        </div>
        <div class="message">{msg}</div>
        {tool_html}
        {cwd_html}
        <div class="card-actions">
            <button class="btn-focus" onclick="send('focus', '{n.id}')">Focus</button>
            <button class="btn-dismiss" onclick="send('dismiss', '{n.id}')">Dismiss</button>
            <div class="snooze-wrap">
                <button class="snooze-icon" title="Snooze">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor"
                         stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <circle cx="12" cy="12" r="10"/>
                        <polyline points="12 6 12 12 16 14"/>
                    </svg>
                </button>
                <div class="snooze-menu"><div class="snooze-menu-inner">
                    <button class="snooze-option" onclick="doSnooze('{n.id}', 60)">1 min</button>
                    <button class="snooze-option" onclick="doSnooze('{n.id}', 300)">5 min</button>
                    <button class="snooze-option" onclick="doSnooze('{n.id}', 1800)">30 min</button>
                    <button class="snooze-option" onclick="doSnooze('{n.id}', 3600)">1 hour</button>
                    <button class="snooze-option" onclick="doSnooze('{n.id}', 86400)">1 day</button>
                    <div class="snooze-custom-row">
                        <input type="number" min="1" value="10" id="custom-{n.id}"
                               onclick="event.stopPropagation()">
                        <span>min</span>
                        <button onclick="customSnooze('{n.id}', document.getElementById('custom-{n.id}'))">Go</button>
                    </div>
                </div></div>
            </div>
        </div>
    </div>
    """


def render_html(notifications: list[Notification], sound_enabled: bool = True) -> str:
    count = len(notifications)
    sound_cls = "on" if sound_enabled else ""
    # Inline SVG bell icons — filled when on, slashed when off
    if sound_enabled:
        bell_svg = (
            '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
            'stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
            '<path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/>'
            '<path d="M13.73 21a2 2 0 0 1-3.46 0"/></svg>'
        )
    else:
        bell_svg = (
            '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
            'stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
            '<path d="M13.73 21a2 2 0 0 1-3.46 0"/>'
            '<path d="M18.63 13A17.89 17.89 0 0 1 18 8"/>'
            '<path d="M6.26 6.26A5.86 5.86 0 0 0 6 8c0 7-3 9-3 9h14"/>'
            '<path d="M18 8a6 6 0 0 0-9.33-5"/>'
            '<line x1="1" y1="1" x2="23" y2="23"/></svg>'
        )
    sound_btn = (
        f'<button class="sound-toggle {sound_cls}" onclick="send(\'toggle_sound\')" '
        f'title="{"Sound on" if sound_enabled else "Sound off"}">{bell_svg}</button>'
    )

    if count == 0:
        body = f"""
        <div class="header">
            <div class="header-left">
                <h1>Claude Code</h1>
                <span class="count">No notifications</span>
            </div>
            <div class="header-right">
                {sound_btn}
            </div>
        </div>
        <div class="empty">
            <div class="icon">&#9671;</div>
            <p>No pending notifications</p>
        </div>
        """
    else:
        cards = "\n".join(_render_card(n) for n in notifications)
        dismiss_btn = (
            f'<button class="dismiss-all-btn" onclick="send(\'dismiss_all\')">Dismiss All</button>'
            if count > 1
            else ""
        )
        body = f"""
        <div class="header">
            <div class="header-left">
                <h1>Claude Code</h1>
                <span class="count">{count} waiting</span>
            </div>
            <div class="header-right">
                {sound_btn}
                {dismiss_btn}
            </div>
        </div>
        {cards}
        """

    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>{CSS}</style>
</head>
<body>
{body}
<script>{JS}</script>
</body>
</html>"""
