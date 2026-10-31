"""
Windows 11 Notepad Go To Line Dialog.
Matches GotoDialogContent.xbf component.
"""

from gi.repository import Gtk

class GotoDialog(Gtk.Window):
    def __init__(self, parent_window, active_tab):
        super().__init__(transient_for=parent_window, modal=True)
        self.set_title("Go to line")
        self.set_default_size(320, 160)
        self.set_resizable(False)

        self.tab = active_tab
        self.total_lines = active_tab.buffer.get_line_count()

        # Layout container
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        main_box.set_margin_top(16)
        main_box.set_margin_bottom(16)
        main_box.set_margin_start(16)
        main_box.set_margin_end(16)
        self.set_child(main_box)

        # Label
        label = Gtk.Label(label=f"Line number (1 - {self.total_lines}):")
        label.set_halign(Gtk.Align.START)
        main_box.append(label)

        # Entry
        cur_line, _, _, _ = self.tab.get_cursor_info()
        self.entry = Gtk.Entry()
        self.entry.set_text(str(cur_line))
        self.entry.select_region(0, -1)
        self.entry.connect("activate", lambda e: self._on_goto())
        main_box.append(self.entry)

        # Buttons Row
        btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        btn_box.set_halign(Gtk.Align.END)
        btn_box.set_margin_top(8)

        btn_cancel = Gtk.Button(label="Cancel")
        btn_cancel.connect("clicked", lambda b: self.close())
        btn_box.append(btn_cancel)

        btn_goto = Gtk.Button(label="Go to")
        btn_goto.add_css_class("suggested-action")
        btn_goto.connect("clicked", lambda b: self._on_goto())
        btn_box.append(btn_goto)

        main_box.append(btn_box)

    def _on_goto(self):
        text = self.entry.get_text().strip()
        if text.isdigit():
            target_line = max(1, min(int(text), self.total_lines))
            line_iter = self.tab.buffer.get_iter_at_line(target_line - 1)
            self.tab.buffer.place_cursor(line_iter)
            self.tab.view.scroll_to_iter(line_iter, 0.25, False, 0.0, 0.0)
            self.tab.view.grab_focus()
            self.close()
