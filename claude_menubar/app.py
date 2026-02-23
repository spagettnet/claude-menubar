"""Claude Code menu bar app — popover UI with notification cards."""
import objc

from AppKit import (
    NSApplication,
    NSApplicationActivationPolicyAccessory,
    NSImage,
    NSMakeRect,
    NSMinYEdge,
    NSObject,
    NSPopover,
    NSPopoverBehaviorTransient,
    NSSound,
    NSStatusBar,
    NSTimer,
    NSVariableStatusItemLength,
    NSViewController,
)
from WebKit import WKUserContentController, WKWebView, WKWebViewConfiguration

from claude_menubar.inbox import (
    Notification,
    cleanup_stale,
    dismiss,
    dismiss_all,
    get_sound_enabled,
    list_notifications,
    set_sound_enabled,
    snooze,
)
from claude_menubar.icons import generate_icons
from claude_menubar.terminal import focus_terminal
from claude_menubar.html_template import render_html


WKScriptMessageHandler = objc.protocolNamed("WKScriptMessageHandler")


class WebViewMessageHandler(NSObject, protocols=[WKScriptMessageHandler]):
    """Handles messages sent from JavaScript in the WKWebView."""

    def initWithApp_(self, app):
        self = objc.super(WebViewMessageHandler, self).init()
        if self is None:
            return None
        self._app = app
        return self

    def userContentController_didReceiveScriptMessage_(self, controller, message):
        body = message.body()
        if hasattr(body, "get"):
            action = body.get("action", "") or ""
            notif_id = body.get("id", "") or ""
        else:
            return

        if action == "dismiss":
            dismiss(str(notif_id))
            self._app.refresh()
        elif action == "dismiss_all":
            dismiss_all()
            self._app.refresh()
        elif action == "focus":
            for n in self._app.current_notifications:
                if n.id == str(notif_id):
                    focus_terminal(n.terminal_app, n.terminal_pid, n.tty)
                    break
            dismiss(str(notif_id))
            self._app.refresh()
            self._app.popover.close()
        elif action == "snooze":
            duration = int(body.get("duration", 300) or 300)
            snooze(str(notif_id), duration)
            self._app.refresh()
        elif action == "toggle_sound":
            enabled = not get_sound_enabled()
            set_sound_enabled(enabled)
            self._app.refresh()


class PopoverViewController(NSViewController):
    def initWithWebView_(self, webview):
        self = objc.super(PopoverViewController, self).init()
        if self is None:
            return None
        self._webview = webview
        return self

    def loadView(self):
        self.setView_(self._webview)


class AppDelegate(NSObject):
    def initWithApp_(self, app):
        self = objc.super(AppDelegate, self).init()
        if self is None:
            return None
        self._app = app
        return self

    def togglePopover_(self, sender):
        self._app.togglePopover_(sender)

    def pollTick_(self, timer):
        self._app._poll()

    def flashTick_(self, timer):
        self._app._flash()


class ClaudeMenuBarApp:
    POPOVER_WIDTH = 380
    POPOVER_HEIGHT = 460

    def __init__(self):
        self.app = NSApplication.sharedApplication()
        self.app.setActivationPolicy_(NSApplicationActivationPolicyAccessory)

        # Icons (colored, not template — so the roof light can glow)
        idle_path, active_path = generate_icons()
        self.idle_icon = NSImage.alloc().initWithContentsOfFile_(idle_path)
        self.idle_icon.setSize_((29, 18))
        self.active_icon = NSImage.alloc().initWithContentsOfFile_(active_path)
        self.active_icon.setSize_((29, 18))

        # Notification sound
        self._ding = NSSound.soundNamed_("Glass")

        # Delegate
        self._delegate = AppDelegate.alloc().initWithApp_(self)

        # Status bar item
        self.status_item = NSStatusBar.systemStatusBar().statusItemWithLength_(
            NSVariableStatusItemLength
        )
        self.status_item.button().setImage_(self.idle_icon)
        self.status_item.button().setTarget_(self._delegate)
        self.status_item.button().setAction_(
            objc.selector(self._delegate.togglePopover_, signature=b"v@:@")
        )

        # WKWebView with message handler
        config = WKWebViewConfiguration.alloc().init()
        content_controller = WKUserContentController.alloc().init()
        self.message_handler = WebViewMessageHandler.alloc().initWithApp_(self)
        content_controller.addScriptMessageHandler_name_(self.message_handler, "bridge")
        config.setUserContentController_(content_controller)

        self.webview = WKWebView.alloc().initWithFrame_configuration_(
            NSMakeRect(0, 0, self.POPOVER_WIDTH, self.POPOVER_HEIGHT), config
        )
        self.webview.setValue_forKey_(False, "drawsBackground")

        # Popover
        self.popover = NSPopover.alloc().init()
        self.popover.setBehavior_(NSPopoverBehaviorTransient)
        self.popover.setContentSize_((self.POPOVER_WIDTH, self.POPOVER_HEIGHT))
        vc = PopoverViewController.alloc().initWithWebView_(self.webview)
        self.popover.setContentViewController_(vc)

        # State
        self.current_notifications: list[Notification] = []
        self._flash_state = False
        self._prev_ids: set[str] = set()

        # Timers
        self._poll_timer = (
            NSTimer.scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(
                2.0, self._delegate,
                objc.selector(self._delegate.pollTick_, signature=b"v@:@"),
                None, True,
            )
        )
        self._flash_timer = (
            NSTimer.scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(
                0.5, self._delegate,
                objc.selector(self._delegate.flashTick_, signature=b"v@:@"),
                None, True,
            )
        )

    def run(self):
        self.app.run()

    def refresh(self):
        cleanup_stale()
        self.current_notifications = list_notifications()
        self._prev_ids = {n.id for n in self.current_notifications}
        self._update_webview()
        self._update_icon()

    def _update_webview(self):
        sound_on = get_sound_enabled()
        html = render_html(self.current_notifications, sound_enabled=sound_on)
        self.webview.loadHTMLString_baseURL_(html, None)

    def _update_icon(self):
        if self.current_notifications:
            icon = self.active_icon if self._flash_state else self.idle_icon
            self.status_item.button().setImage_(icon)
        else:
            self.status_item.button().setImage_(self.idle_icon)
            self._flash_state = False

    def _play_ding(self):
        if get_sound_enabled() and self._ding:
            self._ding.stop()
            self._ding.play()

    def togglePopover_(self, sender):
        if self.popover.isShown():
            self.popover.close()
        else:
            self.refresh()
            self.popover.showRelativeToRect_ofView_preferredEdge_(
                self.status_item.button().bounds(),
                self.status_item.button(),
                NSMinYEdge,
            )

    def _poll(self):
        cleanup_stale()
        notifications = list_notifications()
        new_ids = {n.id for n in notifications}

        # Detect genuinely new notifications (not just unsnoozed ones returning)
        appeared = new_ids - self._prev_ids
        if appeared:
            self._play_ding()

        if new_ids != self._prev_ids:
            self.current_notifications = notifications
            self._prev_ids = new_ids
            if self.popover.isShown():
                self._update_webview()
        self._update_icon()

    def _flash(self):
        if self.current_notifications:
            self._flash_state = not self._flash_state
            self._update_icon()


def main():
    app = ClaudeMenuBarApp()
    app.run()


if __name__ == "__main__":
    main()
