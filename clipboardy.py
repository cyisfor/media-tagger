from gi.repository import GLib, Gtk, Gdk

seen = set()

handler = None

def check(clipboard, text, nun=None):
    if text and not text in seen:
        seen.add(text)
        handler(text)
    GLib.timeout_add(200,start,clipboard)

def start(clipboard):
    clipboard.request_text(check,None)
    return False

def monitor(_handler):
    global handler
    handler = _handler
    clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
    clipboard.set_text('',0)
    GLib.idle_add(lambda *a: start(clipboard))

def run(_handler):
    monitor(_handler)
    import signal
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    Gtk.main()
