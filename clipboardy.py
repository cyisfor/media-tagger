try: 
    import pgi
    pgi.install_as_gi()
except ImportError: pass

from gi.repository import GLib, Gtk, Gdk

seen = set()

handler = None
check = None

def gotClip(clipboard, text, nun=None):
    if check:
        res = check(text)
        if res is not True:
            text = res
    if text and not text in seen:
        seen.add(text)
        handler(text)
    GLib.timeout_add(200,start,clipboard)

def start(clipboard):
    clipboard.request_text(gotClip,None)
    return False

def monitor(_handler,_check=None):
    global handler,check
    handler = _handler
    check = _check
    clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
    clipboard.set_text('',0)
    GLib.idle_add(lambda *a: start(clipboard))

def run(_handler,_check=None):
    monitor(_handler,_check)
    import signal
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    Gtk.main()
