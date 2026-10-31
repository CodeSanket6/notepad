"""
Windows 11 Notepad Editor Tab implementation.
Uses GtkSourceView 5 for high-performance text buffer, undo/redo, and search.
"""

import os

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('GtkSource', '5')

from gi.repository import Gtk, GtkSource, GObject, Pango

class EditorTab(Gtk.Box):
    __gsignals__ = {
        'status-changed': (GObject.SignalFlags.RUN_FIRST, None, ()),
        'title-changed': (GObject.SignalFlags.RUN_FIRST, None, (str, bool)),
    }

    def __init__(self, file_path=None, title=None, default_wrap=True, default_font_family="Consolas", default_font_size=11):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)

        self.file_path = file_path
        self._title = title or (os.path.basename(file_path) if file_path else "Untitled")
        self.encoding = "UTF-8"
        self.line_endings = "Windows (CRLF)"
        self.zoom_level = 100  # Percentage
        self._is_modified = False
        self._wrap_mode = default_wrap
        self.font_family = default_font_family
        self.font_size = default_font_size
        self._font_provider = None

        # Create GtkSourceView and Buffer
        self.buffer = GtkSource.Buffer()
        self.view = GtkSource.View(buffer=self.buffer)
        
        # Configure View Appearance & Behavior
        self.view.add_css_class("notepad-editor-view")
        self.view.set_show_line_numbers(False)  # Win11 Notepad has line numbers off by default
        self.view.set_wrap_mode(Gtk.WrapMode.WORD if default_wrap else Gtk.WrapMode.NONE)
        self.view.set_monospace(True)
        self.view.set_top_margin(12)
        self.view.set_bottom_margin(16)
        self.view.set_left_margin(16)
        self.view.set_right_margin(16)
        self.view.set_tab_width(4)
        self.view.set_insert_spaces_instead_of_tabs(False)

        # Scrolled container
        self.scrolled = Gtk.ScrolledWindow()
        self.scrolled.set_hexpand(True)
        self.scrolled.set_vexpand(True)
        self.scrolled.set_child(self.view)
        self.append(self.scrolled)

        # Setup Search context
        self.search_settings = GtkSource.SearchSettings()
        self.search_settings.set_wrap_around(True)
        self.search_context = GtkSource.SearchContext(buffer=self.buffer, settings=self.search_settings)

        # Buffer event listeners
        self.buffer.connect("changed", self._on_buffer_changed)
        self.buffer.connect("notify::cursor-position", self._on_cursor_moved)
        self.buffer.connect("mark-set", self._on_mark_set)

        # Apply default font
        self.set_font(default_font_family, default_font_size)

        # Load file if provided
        if self.file_path and os.path.exists(self.file_path):
            self.load_file(self.file_path)

    @property
    def title(self):
        return self._title

    @property
    def is_modified(self):
        return self._is_modified

    @is_modified.setter
    def is_modified(self, val):
        if self._is_modified != val:
            self._is_modified = val
            self.emit('title-changed', self._title, self._is_modified)

    def _on_buffer_changed(self, buf):
        self.is_modified = True
        self.emit('status-changed')

    def _on_cursor_moved(self, buf, pspec):
        self.emit('status-changed')

    def _on_mark_set(self, buf, location, mark):
        if mark.get_name() in ("insert", "selection_bound"):
            self.emit('status-changed')

    def get_cursor_info(self):
        """Returns (line, col, selection_count, total_chars)"""
        insert_mark = self.buffer.get_insert()
        insert_iter = self.buffer.get_iter_at_mark(insert_mark)
        line = insert_iter.get_line() + 1
        col = insert_iter.get_line_offset() + 1
        total_chars = self.buffer.get_char_count()

        sel_count = 0
        if self.buffer.get_has_selection():
            start, end = self.buffer.get_selection_bounds()
            sel_count = abs(end.get_offset() - start.get_offset())

        return line, col, sel_count, total_chars

    def set_font(self, font_family, font_size):
        self.font_family = font_family
        self.font_size = font_size
        self._apply_font()

    def set_word_wrap(self, enable):
        self._wrap_mode = enable
        self.view.set_wrap_mode(Gtk.WrapMode.WORD if enable else Gtk.WrapMode.NONE)

    def zoom_in(self):
        if self.zoom_level < 500:
            self.zoom_level += 10
            self._apply_font()
            self.emit('status-changed')

    def zoom_out(self):
        if self.zoom_level > 20:
            self.zoom_level -= 10
            self._apply_font()
            self.emit('status-changed')

    def reset_zoom(self):
        self.zoom_level = 100
        self._apply_font()
        self.emit('status-changed')

    def _apply_font(self):
        scaled_size = max(6, int(self.font_size * (self.zoom_level / 100.0)))
        css = f"textview.notepad-editor-view text {{ font-family: '{self.font_family}', monospace; font-size: {scaled_size}pt; }}"
        if not self._font_provider:
            self._font_provider = Gtk.CssProvider()
            self.view.get_style_context().add_provider(
                self._font_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION + 1
            )
        self._font_provider.load_from_data(css.encode('utf-8'))


    def load_file(self, path):
        try:
            with open(path, 'rb') as f:
                raw = f.read()

            # Detect line endings
            if b'\r\n' in raw:
                self.line_endings = "Windows (CRLF)"
            elif b'\r' in raw and b'\n' not in raw:
                self.line_endings = "Macintosh (CR)"
            else:
                self.line_endings = "Unix (LF)"

            # Detect encoding
            encoding = "UTF-8"
            text = ""
            if raw.startswith(b'\xff\xfe'):
                encoding = "UTF-16 LE"
                text = raw[2:].decode('utf-16le', errors='replace')
            elif raw.startswith(b'\xfe\xff'):
                encoding = "UTF-16 BE"
                text = raw[2:].decode('utf-16be', errors='replace')
            elif raw.startswith(b'\xef\xbb\xbf'):
                encoding = "UTF-8 with BOM"
                text = raw[3:].decode('utf-8', errors='replace')
            else:
                try:
                    text = raw.decode('utf-8')
                    encoding = "UTF-8"
                except UnicodeDecodeError:
                    text = raw.decode('latin1', errors='replace')
                    encoding = "ANSI"

            self.encoding = encoding
            self.file_path = path
            self._title = os.path.basename(path)

            # Block modified flag during initial load
            self.buffer.handler_block_by_func(self._on_buffer_changed)
            self.buffer.set_text(text)
            self.buffer.handler_unblock_by_func(self._on_buffer_changed)

            self.is_modified = False
            self.emit('title-changed', self._title, False)
            self.emit('status-changed')
            return True, None
        except Exception as e:
            return False, str(e)

    def save_file(self, path=None):
        target_path = path or self.file_path
        if not target_path:
            return False, "No file path specified"

        try:
            start = self.buffer.get_start_iter()
            end = self.buffer.get_end_iter()
            text = self.buffer.get_text(start, end, True)

            # Adjust line endings if necessary
            if self.line_endings == "Windows (CRLF)":
                # Normalize to \n first then replace with \r\n
                text = text.replace('\r\n', '\n').replace('\n', '\r\n')
            elif self.line_endings == "Unix (LF)":
                text = text.replace('\r\n', '\n')
            elif self.line_endings == "Macintosh (CR)":
                text = text.replace('\r\n', '\r').replace('\n', '\r')

            # Encode
            if self.encoding == "UTF-8 with BOM":
                raw = b'\xef\xbb\xbf' + text.encode('utf-8')
            elif self.encoding == "UTF-16 LE":
                raw = b'\xff\xfe' + text.encode('utf-16le')
            elif self.encoding == "UTF-16 BE":
                raw = b'\xfe\xff' + text.encode('utf-16be')
            elif self.encoding == "ANSI":
                raw = text.encode('latin1', errors='replace')
            else:
                raw = text.encode('utf-8')

            with open(target_path, 'wb') as f:
                f.write(raw)

            self.file_path = target_path
            self._title = os.path.basename(target_path)
            self.is_modified = False
            self.emit('title-changed', self._title, False)
            self.emit('status-changed')
            return True, None
        except Exception as e:
            return False, str(e)
