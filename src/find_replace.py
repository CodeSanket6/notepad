"""
Windows 11 Notepad Floating Find & Replace Bar.
Matches the WinUI 3 FindReplaceDialog component.
"""

from gi.repository import Gtk, Gdk

class FindReplaceBar(Gtk.Box):
    def __init__(self, tab_view_callback):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        self.add_css_class("find-replace-panel")
        self.set_halign(Gtk.Align.END)
        self.set_valign(Gtk.Align.START)
        self.set_margin_top(10)
        self.set_margin_end(16)

        self.get_active_tab = tab_view_callback
        self.is_replace_visible = False

        # --- Top Row: Search Controls ---
        top_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)

        self.search_entry = Gtk.SearchEntry()
        self.search_entry.add_css_class("find-input")
        self.search_entry.set_placeholder_text("Find")
        self.search_entry.set_width_chars(22)
        self.search_entry.connect("search-changed", self._on_search_changed)
        self.search_entry.connect("activate", lambda e: self.find_next())
        top_row.append(self.search_entry)

        # Match counter label
        self.count_label = Gtk.Label(label="")
        self.count_label.add_css_class("find-count-label")
        top_row.append(self.count_label)

        # Find Previous Button
        self.btn_prev = Gtk.Button.new_from_icon_name("go-up-symbolic")
        self.btn_prev.add_css_class("notepad-icon-btn")
        self.btn_prev.set_tooltip_text("Previous (Shift+F3)")
        self.btn_prev.connect("clicked", lambda b: self.find_prev())
        top_row.append(self.btn_prev)

        # Find Next Button
        self.btn_next = Gtk.Button.new_from_icon_name("go-down-symbolic")
        self.btn_next.add_css_class("notepad-icon-btn")
        self.btn_next.set_tooltip_text("Next (F3)")
        self.btn_next.connect("clicked", lambda b: self.find_next())
        top_row.append(self.btn_next)

        # Match Case Toggle Button
        self.btn_match_case = Gtk.ToggleButton(label="Aa")
        self.btn_match_case.add_css_class("pill-btn")
        self.btn_match_case.set_tooltip_text("Match Case")
        self.btn_match_case.connect("toggled", self._on_case_toggled)
        top_row.append(self.btn_match_case)

        # Toggle Replace Expand Button
        self.btn_expand = Gtk.Button.new_from_icon_name("pan-down-symbolic")
        self.btn_expand.add_css_class("notepad-icon-btn")
        self.btn_expand.set_tooltip_text("Toggle Replace")
        self.btn_expand.connect("clicked", self._on_toggle_replace)
        top_row.append(self.btn_expand)

        # Close Button
        self.btn_close = Gtk.Button.new_from_icon_name("window-close-symbolic")
        self.btn_close.add_css_class("notepad-icon-btn")
        self.btn_close.set_tooltip_text("Close (Esc)")
        self.btn_close.connect("clicked", lambda b: self.hide_bar())
        top_row.append(self.btn_close)

        self.append(top_row)

        # --- Bottom Row: Replace Controls ---
        self.replace_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self.replace_row.set_margin_top(4)

        self.replace_entry = Gtk.Entry()
        self.replace_entry.add_css_class("find-input")
        self.replace_entry.set_placeholder_text("Replace")
        self.replace_entry.set_width_chars(22)
        self.replace_entry.connect("activate", lambda e: self.replace_current())
        self.replace_row.append(self.replace_entry)

        # Replace Button
        self.btn_replace = Gtk.Button(label="Replace")
        self.btn_replace.add_css_class("pill-btn")
        self.btn_replace.connect("clicked", lambda b: self.replace_current())
        self.replace_row.append(self.btn_replace)

        # Replace All Button
        self.btn_replace_all = Gtk.Button(label="Replace all")
        self.btn_replace_all.add_css_class("pill-btn")
        self.btn_replace_all.connect("clicked", lambda b: self.replace_all())
        self.replace_row.append(self.btn_replace_all)

        self.append(self.replace_row)
        self.replace_row.set_visible(False)

        # Start hidden
        self.set_visible(False)

        # Key controller to handle Escape
        key_ctrl = Gtk.EventControllerKey()
        key_ctrl.connect("key-pressed", self._on_key_pressed)
        self.add_controller(key_ctrl)

    def _on_key_pressed(self, controller, keyval, keycode, state):
        if keyval == Gdk.KEY_Escape:
            self.hide_bar()
            return True
        return False

    def show_find(self):
        self.set_visible(True)
        self.search_entry.grab_focus()
        active_tab = self.get_active_tab()
        if active_tab and active_tab.buffer.get_has_selection():
            start, end = active_tab.buffer.get_selection_bounds()
            selected = active_tab.buffer.get_text(start, end, True)
            if selected and "\n" not in selected:
                self.search_entry.set_text(selected)
        self._update_matches()

    def show_replace(self):
        self.show_find()
        if not self.is_replace_visible:
            self._on_toggle_replace(None)
        self.replace_entry.grab_focus()

    def hide_bar(self):
        self.set_visible(False)
        active_tab = self.get_active_tab()
        if active_tab:
            active_tab.view.grab_focus()

    def _on_toggle_replace(self, btn):
        self.is_replace_visible = not self.is_replace_visible
        self.replace_row.set_visible(self.is_replace_visible)
        icon_name = "pan-up-symbolic" if self.is_replace_visible else "pan-down-symbolic"
        self.btn_expand.set_icon_name(icon_name)

    def _on_case_toggled(self, btn):
        active_tab = self.get_active_tab()
        if active_tab:
            active_tab.search_settings.set_case_sensitive(self.btn_match_case.get_active())
            self._update_matches()

    def _on_search_changed(self, entry):
        text = entry.get_text()
        active_tab = self.get_active_tab()
        if active_tab:
            active_tab.search_settings.set_search_text(text if text else None)
            self._update_matches()

    def _update_matches(self):
        active_tab = self.get_active_tab()
        text = self.search_entry.get_text()
        if not active_tab or not text:
            self.count_label.set_text("")
            return

        # Simple occurrences count
        buf = active_tab.buffer
        start = buf.get_start_iter()
        count = 0
        current_idx = 0
        insert_mark = buf.get_insert()
        cursor_offset = buf.get_iter_at_mark(insert_mark).get_offset()

        while True:
            found, m_start, m_end, _ = active_tab.search_context.forward(start)
            if not found:
                break
            count += 1
            if m_start.get_offset() <= cursor_offset <= m_end.get_offset():
                current_idx = count
            start = m_end
            if start.is_end():
                break

        if count == 0:
            self.count_label.set_text("No results")
        elif current_idx > 0:
            self.count_label.set_text(f"{current_idx} of {count}")
        else:
            self.count_label.set_text(f"{count} matches")

    def find_next(self):
        active_tab = self.get_active_tab()
        if not active_tab or not self.search_entry.get_text():
            return
        buf = active_tab.buffer
        insert_mark = buf.get_insert()
        cursor_iter = buf.get_iter_at_mark(insert_mark)
        found, start, end, wrapped = active_tab.search_context.forward(cursor_iter)
        if found:
            buf.select_range(start, end)
            active_tab.view.scroll_to_iter(start, 0.2, False, 0.0, 0.0)
            self._update_matches()

    def find_prev(self):
        active_tab = self.get_active_tab()
        if not active_tab or not self.search_entry.get_text():
            return
        buf = active_tab.buffer
        insert_mark = buf.get_insert()
        cursor_iter = buf.get_iter_at_mark(insert_mark)
        found, start, end, wrapped = active_tab.search_context.backward(cursor_iter)
        if found:
            buf.select_range(start, end)
            active_tab.view.scroll_to_iter(start, 0.2, False, 0.0, 0.0)
            self._update_matches()

    def replace_current(self):
        active_tab = self.get_active_tab()
        if not active_tab or not self.search_entry.get_text():
            return
        buf = active_tab.buffer
        if buf.get_has_selection():
            start, end = buf.get_selection_bounds()
            replace_text = self.replace_entry.get_text()
            try:
                active_tab.search_context.replace(start, end, replace_text, len(replace_text))
            except Exception:
                buf.delete(start, end)
                buf.insert(start, replace_text)
        self.find_next()

    def replace_all(self):
        active_tab = self.get_active_tab()
        if not active_tab or not self.search_entry.get_text():
            return
        replace_text = self.replace_entry.get_text()
        active_tab.search_context.replace_all(replace_text, len(replace_text))
        self._update_matches()
