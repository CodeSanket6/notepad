"""
Windows 11 Notepad Application entry point.
"""

import sys
import os

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
gi.require_version('GtkSource', '5')

from gi.repository import Gtk, Adw, Gio, Gdk
from .window import NotepadWindow


class NotepadApp(Adw.Application):
    def __init__(self):
        super().__init__(
            application_id="io.github.CodeSanket6.notepad",
            flags=Gio.ApplicationFlags.HANDLES_OPEN | Gio.ApplicationFlags.NON_UNIQUE
        )
        self.css_provider = None

    def do_startup(self):
        Adw.Application.do_startup(self)
        self._load_css()

    def _load_css(self):
        pkgdatadir = os.environ.get("PKGDATADIR", "")
        home_local = os.path.expanduser("~/.local/share/notepad/styles/fluent.css")
        candidates = [
            os.path.join(pkgdatadir, "styles/fluent.css") if pkgdatadir else None,
            home_local,
            "/app/share/notepad/styles/fluent.css",
            "/usr/local/share/notepad/styles/fluent.css",
            "/usr/share/notepad/styles/fluent.css",
            os.path.join(os.path.dirname(__file__), "../data/styles/fluent.css"),
            os.path.join(os.path.dirname(__file__), "../styles/fluent.css"),
            os.path.join(os.path.dirname(__file__), "styles/fluent.css"),
            "/home/sanket/Downloads/notepad/notepad-linux/data/styles/fluent.css",
        ]
        css_file = None
        for c in candidates:
            if c and os.path.exists(c):
                css_file = c
                break

        if css_file:
            self.css_provider = Gtk.CssProvider()
            self.css_provider.load_from_path(css_file)
            display = Gdk.Display.get_default()
            if display:
                Gtk.StyleContext.add_provider_for_display(
                    display,
                    self.css_provider,
                    Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION + 100
                )
            print(f"[Notepad] Loaded Fluent CSS from: {css_file}")


    def do_activate(self):
        win = self.get_active_window()
        if not win:
            win = NotepadWindow(self)
        win.present()

    def do_open(self, files, n_files, hint):
        file_paths = [f.get_path() for f in files if f.get_path()]
        win = self.get_active_window()
        if win:
            for p in file_paths:
                win.open_file_path(p)
        else:
            win = NotepadWindow(self, open_files=file_paths)
        win.present()

def main():
    app = NotepadApp()
    # If file paths passed on sys.argv[1:], run Gio.Application.run
    return app.run(sys.argv)

if __name__ == "__main__":
    sys.exit(main())
