"""Detect the terminal app from a process tree and focus terminal windows/tabs."""
import subprocess


def find_terminal_info(start_pid: int) -> tuple[str, int]:
    """Walk up the process tree from start_pid to find the terminal application.

    Returns (terminal_app_name, terminal_pid). Falls back to ("", 0) if not found.
    """
    known_terminals = {
        "iTerm2", "Terminal", "Alacritty", "kitty", "WezTerm",
        "Hyper", "Tabby", "Rio", "Ghostty",
    }

    pid = start_pid
    for _ in range(10):
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


def focus_terminal(terminal_app: str, terminal_pid: int = 0, tty: str = ""):
    """Bring the exact terminal tab to the foreground.

    Uses TTY-based tab matching for iTerm2 and Terminal.app.
    Falls back to just activating the app if TTY is unavailable.
    """
    if not terminal_app:
        return

    app_names = {
        "iTerm2": "iTerm2",
        "Terminal": "Terminal",
        "Alacritty": "Alacritty",
        "kitty": "kitty",
        "WezTerm": "WezTerm",
        "Hyper": "Hyper",
        "Tabby": "Tabby",
        "Rio": "Rio",
        "Ghostty": "Ghostty",
    }
    app = app_names.get(terminal_app, terminal_app)

    if tty and app == "iTerm2":
        _focus_iterm2_tab(tty)
        return

    if tty and app == "Terminal":
        _focus_terminal_app_tab(tty)
        return

    # Fallback: just activate the app
    try:
        subprocess.run(
            ["osascript", "-e", f'tell application "{app}" to activate'],
            capture_output=True, timeout=5,
        )
    except (subprocess.TimeoutExpired, OSError):
        pass


def _focus_iterm2_tab(tty: str):
    """Focus the exact iTerm2 tab/session matching the given TTY."""
    script = f'''
    tell application "iTerm2"
        activate
        repeat with w in windows
            repeat with t in tabs of w
                repeat with s in sessions of t
                    if tty of s is "{tty}" then
                        select w
                        tell t to select
                        return
                    end if
                end repeat
            end repeat
        end repeat
    end tell
    '''
    try:
        subprocess.run(
            ["osascript", "-e", script],
            capture_output=True, timeout=5,
        )
    except (subprocess.TimeoutExpired, OSError):
        pass


def _focus_terminal_app_tab(tty: str):
    """Focus the exact Terminal.app tab matching the given TTY."""
    script = f'''
    tell application "Terminal"
        activate
        repeat with w in windows
            repeat with t in tabs of w
                if tty of t is "{tty}" then
                    set selected tab of w to t
                    set index of w to 1
                    return
                end if
            end repeat
        end repeat
    end tell
    '''
    try:
        subprocess.run(
            ["osascript", "-e", script],
            capture_output=True, timeout=5,
        )
    except (subprocess.TimeoutExpired, OSError):
        pass
