"""
Windows 11 Notepad Main Window Implementation.
Matches exact layout from Windows 11 screenshots:
- Left-aligned tabs with Notepad icon inside the tab
- Menubar with File/Edit/View on left and Settings gear on far right
- Statusbar with Ln/Col and characters on left, and Zoom/CRLF/UTF-8 on right
"""

import os
import time

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Adw, Gio, Gdk
from .tab_bar import FluentTabBar
from .editor_tab import EditorTab
from .find_replace import FindReplaceBar
from .goto_dialog import GotoDialog
from .settings_dialog import SettingsDialog, load_config

class NotepadWindow(Adw.ApplicationWindow):
    def __init__(self, app, open_files=None):
        super().__init__(application=app)
        self.set_title("Notepad")
        self.set_default_size(980, 680)
        self.add_css_class("notepad-window")

        self.app = app
        self.config = load_config()
        self.untitled_counter = 1
        self.tab_seq = 0
        self.tab_widgets = {}  # tab_id -> EditorTab

        # Root vertical layout
        self.root_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.set_content(self.root_box)

        # --- Top Header & Custom Fluent Tabs ---
        self._build_header_and_tabs()

        # --- Menu Bar (with Settings Gear on right) ---
        self._build_menubar()

        # --- Editor Area (Overlay containing Gtk.Stack and FindReplaceBar) ---
        self.overlay = Gtk.Overlay()
        self.overlay.set_hexpand(True)
        self.overlay.set_vexpand(True)

        self.stack = Gtk.Stack()
        self.stack.set_transition_type(Gtk.StackTransitionType.NONE)
        self.stack.connect("notify::visible-child", self._on_visible_child_changed)
        self.overlay.set_child(self.stack)

        # Find & Replace floating bar overlay
        self.find_replace_bar = FindReplaceBar(self.get_active_tab)
        self.overlay.add_overlay(self.find_replace_bar)
        self.root_box.append(self.overlay)

        # --- Status Bar ---
        self._build_statusbar()

        # Setup Keyboard Shortcuts
        self._setup_shortcuts()

        # Apply Configuration (Theme, Font, Word wrap)
        self.apply_config(self.config)

        # Open initial tabs
        if open_files:
            for f in open_files:
                self.open_file_path(f)
        else:
            self.new_tab()

    def _build_header_and_tabs(self):
        # Title bar styled as Windows 11 title bar (Mica background)
        self.titlebar_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.titlebar_box.add_css_class("notepad-titlebar")

        # Notepad App Logo at the far left side of the titlebar
        icon_candidates = [
            os.path.expanduser("~/.local/share/icons/hicolor/24x24/apps/io.github.CodeSanket6.notepad.png"),
            "/app/share/icons/hicolor/24x24/apps/io.github.CodeSanket6.notepad.png",
            os.path.join(os.path.dirname(__file__), "../assets/notepad.png"),
            os.path.join(os.path.dirname(__file__), "../data/icons/hicolor/24x24/apps/io.github.CodeSanket6.notepad.png"),
            "/home/sanket/Downloads/notepad/notepad-linux/assets/notepad.png"
        ]
        found_icon = None
        for p in icon_candidates:
            if os.path.exists(p):
                found_icon = p
                break

        if found_icon:
            self.app_logo = Gtk.Image.new_from_file(found_icon)
        else:
            self.app_logo = Gtk.Image.new_from_icon_name("io.github.CodeSanket6.notepad")
        self.app_logo.set_pixel_size(18)
        self.app_logo.add_css_class("notepad-titlebar-logo")
        self.app_logo.set_margin_start(10)
        self.app_logo.set_margin_end(6)
        self.app_logo.set_valign(Gtk.Align.CENTER)
        self.titlebar_box.append(self.app_logo)

        # Tabs placed to the right of the app logo (no logo on tabs)
        self.tab_bar = FluentTabBar()
        self.tab_bar.set_margin_start(2)
        self.tab_bar.connect("tab-selected", lambda b, tid: self._on_tab_selected(tid))
        self.tab_bar.connect("tab-close-requested", lambda b, tid: self.close_tab_by_id(tid))
        self.tab_bar.connect("new-tab-requested", lambda b: self.new_tab())
        self.titlebar_box.append(self.tab_bar)

        # Draggable empty space across titlebar
        self.drag_handle = Gtk.WindowHandle()
        self.drag_handle.set_hexpand(True)
        self.titlebar_box.append(self.drag_handle)

        # Native Window Controls (Minimize, Maximize, Close)
        self.window_controls = Gtk.WindowControls(side=Gtk.PackType.END)
        self.window_controls.set_valign(Gtk.Align.CENTER)
        self.titlebar_box.append(self.window_controls)

        self.root_box.append(self.titlebar_box)

    def _build_menubar(self):
        # Menu bar row unified with editor background
        self.menubar_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=2)
        self.menubar_box.add_css_class("notepad-menubar")

        # Left: Menus Box
        menu_items_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=2)

        # File Menu
        menu_file = Gio.Menu()
        menu_file.append("New tab\t\tCtrl+N", "win.new_tab")
        menu_file.append("New window\t\tCtrl+Shift+N", "win.new_window")
        menu_file.append("Open...\t\tCtrl+O", "win.open_file")
        menu_file.append("Save\t\tCtrl+S", "win.save_file")
        menu_file.append("Save as...\t\tCtrl+Shift+S", "win.save_as_file")
        menu_file.append("Save all", "win.save_all")
        menu_file.append("Print...\t\tCtrl+P", "win.print_file")
        menu_file.append("Close tab\t\tCtrl+W", "win.close_current_tab")
        menu_file.append("Close window\tCtrl+Shift+W", "win.close_window")
        menu_file.append("Exit\t\tCtrl+Q", "win.exit_app")

        def _make_menu_btn(label, menu_model):
            btn = Gtk.Button(label=label)
            btn.add_css_class("notepad-menu-btn")
            btn.set_has_frame(False)
            popover = Gtk.PopoverMenu.new_from_model(menu_model)
            popover.set_has_arrow(False)
            popover.set_parent(btn)
            btn.connect("clicked", lambda b: popover.popup())
            return btn

        btn_file = _make_menu_btn("File", menu_file)
        menu_items_box.append(btn_file)

        # Edit Menu
        menu_edit = Gio.Menu()
        menu_edit.append("Undo\t\tCtrl+Z", "win.undo")
        menu_edit.append("Redo\t\tCtrl+Y", "win.redo")
        menu_edit.append("Cut\t\tCtrl+X", "win.cut")
        menu_edit.append("Copy\t\tCtrl+C", "win.copy")
        menu_edit.append("Paste\t\tCtrl+V", "win.paste")
        menu_edit.append("Delete\t\tDel", "win.delete_sel")
        menu_edit.append("Find\t\tCtrl+F", "win.find")
        menu_edit.append("Find next\t\tF3", "win.find_next")
        menu_edit.append("Find previous\tShift+F3", "win.find_prev")
        menu_edit.append("Replace\t\tCtrl+H", "win.replace")
        menu_edit.append("Go to...\t\tCtrl+G", "win.goto_line")
        menu_edit.append("Select all\t\tCtrl+A", "win.select_all")
        menu_edit.append("Time/Date\t\tF5", "win.insert_datetime")

        btn_edit = _make_menu_btn("Edit", menu_edit)
        menu_items_box.append(btn_edit)

        # View Menu
        menu_view = Gio.Menu()
        menu_zoom = Gio.Menu()
        menu_zoom.append("Zoom in\t\tCtrl+Plus", "win.zoom_in")
        menu_zoom.append("Zoom out\t\tCtrl+Minus", "win.zoom_out")
        menu_zoom.append("Restore default zoom\tCtrl+0", "win.reset_zoom")
        menu_view.append_submenu("Zoom", menu_zoom)
        menu_view.append("Status bar", "win.toggle_statusbar")
        menu_view.append("Word wrap", "win.toggle_word_wrap")

        btn_view = _make_menu_btn("View", menu_view)
        menu_items_box.append(btn_view)

        self.menubar_box.append(menu_items_box)

        # Center spacer pushes Settings Gear to far right
        spacer = Gtk.Box()
        spacer.set_hexpand(True)
        self.menubar_box.append(spacer)

        # Right: Settings Gear Button (matching Windows 11 screenshot)
        btn_settings = Gtk.Button.new_from_icon_name("emblem-system-symbolic")
        btn_settings.add_css_class("notepad-icon-btn")
        btn_settings.set_has_frame(False)
        btn_settings.set_tooltip_text("Settings")
        btn_settings.connect("clicked", lambda b: self.open_settings())
        self.menubar_box.append(btn_settings)

        self.root_box.append(self.menubar_box)

        # Register Actions
        self._setup_menu_actions()

    def _setup_menu_actions(self):
        actions = {
            "new_tab": lambda a, p: self.new_tab(),
            "new_window": lambda a, p: self.new_window(),
            "open_file": lambda a, p: self.open_file_dialog(),
            "save_file": lambda a, p: self.save_current_file(),
            "save_as_file": lambda a, p: self.save_as_current_file(),
            "save_all": lambda a, p: self.save_all_files(),
            "print_file": lambda a, p: self.print_file(),
            "close_current_tab": lambda a, p: self.close_active_tab(),
            "close_window": lambda a, p: self.close(),
            "exit_app": lambda a, p: self.app.quit(),
            "undo": lambda a, p: self._call_tab_action(lambda t: t.buffer.undo() if t.buffer.can_undo() else None),
            "redo": lambda a, p: self._call_tab_action(lambda t: t.buffer.redo() if t.buffer.can_redo() else None),
            "cut": lambda a, p: self._call_tab_action(lambda t: t.buffer.cut_clipboard(self.get_clipboard(), True)),
            "copy": lambda a, p: self._call_tab_action(lambda t: t.buffer.copy_clipboard(self.get_clipboard())),
            "paste": lambda a, p: self._call_tab_action(lambda t: t.buffer.paste_clipboard(self.get_clipboard(), None, True)),
            "delete_sel": lambda a, p: self._call_tab_action(lambda t: t.buffer.delete_selection(True, True)),
            "find": lambda a, p: self.find_replace_bar.show_find(),
            "find_next": lambda a, p: self.find_replace_bar.find_next(),
            "find_prev": lambda a, p: self.find_replace_bar.find_prev(),
            "replace": lambda a, p: self.find_replace_bar.show_replace(),
            "goto_line": lambda a, p: self.open_goto_dialog(),
            "select_all": lambda a, p: self._call_tab_action(lambda t: t.buffer.select_range(t.buffer.get_start_iter(), t.buffer.get_end_iter())),
            "insert_datetime": lambda a, p: self.insert_datetime(),
            "zoom_in": lambda a, p: self._call_tab_action(lambda t: t.zoom_in()),
            "zoom_out": lambda a, p: self._call_tab_action(lambda t: t.zoom_out()),
            "reset_zoom": lambda a, p: self._call_tab_action(lambda t: t.reset_zoom()),
            "toggle_statusbar": lambda a, p: self.toggle_statusbar(),
            "toggle_word_wrap": lambda a, p: self.toggle_word_wrap(),
        }
        for name, callback in actions.items():
            action = Gio.SimpleAction.new(name, None)
            action.connect("activate", callback)
            self.add_action(action)

    def _call_tab_action(self, fn):
        tab = self.get_active_tab()
        if tab:
            fn(tab)

    def _build_statusbar(self):
        self.statusbar_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.statusbar_box.add_css_class("notepad-statusbar")
        self.statusbar_box.set_hexpand(True)

        # Left Section: Line, Col, and Characters (as in Windows 11 screenshot)
        left_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=24)
        left_box.set_margin_start(16)

        self.lbl_pos = Gtk.Label(label="Ln 1, Col 1")
        self.lbl_pos.add_css_class("status-item")
        left_box.append(self.lbl_pos)

        self.lbl_chars = Gtk.Label(label="0 characters")
        self.lbl_chars.add_css_class("status-item")
        left_box.append(self.lbl_chars)

        self.statusbar_box.append(left_box)

        # Center Spacer
        spacer = Gtk.Box()
        spacer.set_hexpand(True)
        self.statusbar_box.append(spacer)

        # Right Section: Zoom, Line Endings, and Encoding
        right_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=24)
        right_box.set_margin_end(16)

        self.lbl_zoom = Gtk.Label(label="100%")
        self.lbl_zoom.add_css_class("status-item")
        right_box.append(self.lbl_zoom)

        self.lbl_endings = Gtk.Label(label="Windows (CRLF)")
        self.lbl_endings.add_css_class("status-item")
        right_box.append(self.lbl_endings)

        self.lbl_encoding = Gtk.Label(label="UTF-8")
        self.lbl_encoding.add_css_class("status-item")
        right_box.append(self.lbl_encoding)

        self.statusbar_box.append(right_box)

        self.root_box.append(self.statusbar_box)

    def _setup_shortcuts(self):
        key_ctrl = Gtk.EventControllerKey()
        key_ctrl.connect("key-pressed", self._on_key_pressed)
        self.add_controller(key_ctrl)

    def _on_key_pressed(self, controller, keyval, keycode, state):
        ctrl = bool(state & Gdk.ModifierType.CONTROL_MASK)
        shift = bool(state & Gdk.ModifierType.SHIFT_MASK)
        alt = bool(state & Gdk.ModifierType.ALT_MASK)

        # Tabs Navigation
        if ctrl and shift and keyval in (Gdk.KEY_Tab, Gdk.KEY_ISO_Left_Tab):
            self.tab_bar.select_prev_tab()
            return True
        elif ctrl and keyval == Gdk.KEY_Page_Up:
            self.tab_bar.select_prev_tab()
            return True
        elif ctrl and keyval in (Gdk.KEY_Tab, Gdk.KEY_Page_Down):
            self.tab_bar.select_next_tab()
            return True

        # Close Tab / Window
        if ctrl and (keyval == Gdk.KEY_F4 or keyval in (Gdk.KEY_w, Gdk.KEY_W)):
            self.close_active_tab()
            return True
        if ctrl and shift and keyval in (Gdk.KEY_W, Gdk.KEY_w):
            self.close()
            return True

        # New Tab / New Window
        if ctrl and shift and keyval in (Gdk.KEY_N, Gdk.KEY_n):
            self.new_window()
            return True
        if ctrl and keyval in (Gdk.KEY_N, Gdk.KEY_n, Gdk.KEY_T, Gdk.KEY_t):
            self.new_tab()
            return True

        # File Operations
        if ctrl and shift and keyval in (Gdk.KEY_S, Gdk.KEY_s):
            self.save_as_current_file()
            return True
        if ctrl and keyval in (Gdk.KEY_S, Gdk.KEY_s):
            self.save_current_file()
            return True
        if ctrl and keyval in (Gdk.KEY_O, Gdk.KEY_o):
            self.open_file_dialog()
            return True
        if ctrl and keyval in (Gdk.KEY_P, Gdk.KEY_p):
            self.print_file()
            return True
        if ctrl and keyval in (Gdk.KEY_Q, Gdk.KEY_q):
            self.app.quit()
            return True

        # Find & Replace
        if ctrl and keyval in (Gdk.KEY_F, Gdk.KEY_f):
            self.find_replace_bar.show_find()
            return True
        if ctrl and keyval in (Gdk.KEY_H, Gdk.KEY_h):
            self.find_replace_bar.show_replace()
            return True
        if ctrl and keyval in (Gdk.KEY_G, Gdk.KEY_g):
            self.open_goto_dialog()
            return True
        if keyval == Gdk.KEY_F3:
            if shift:
                self.find_replace_bar.find_prev()
            else:
                self.find_replace_bar.find_next()
            return True

        # Date / Time
        if keyval == Gdk.KEY_F5:
            self.insert_datetime()
            return True

        # Zoom
        if ctrl and keyval in (Gdk.KEY_plus, Gdk.KEY_equal, Gdk.KEY_KP_Add):
            self._call_tab_action(lambda t: t.zoom_in())
            return True
        if ctrl and keyval in (Gdk.KEY_minus, Gdk.KEY_underscore, Gdk.KEY_KP_Subtract):
            self._call_tab_action(lambda t: t.zoom_out())
            return True
        if ctrl and keyval in (Gdk.KEY_0, Gdk.KEY_KP_0):
            self._call_tab_action(lambda t: t.reset_zoom())
            return True

        # Fullscreen & Word Wrap
        if keyval == Gdk.KEY_F11:
            self.set_fullscreened(not self.is_fullscreen())
            return True
        if alt and keyval in (Gdk.KEY_Z, Gdk.KEY_z):
            self.toggle_word_wrap()
            return True
        elif ctrl and keyval == Gdk.KEY_0:
            self._call_tab_action(lambda t: t.reset_zoom())
            return True
        elif keyval == Gdk.KEY_F3:
            if shift:
                self.find_replace_bar.find_prev()
            else:
                self.find_replace_bar.find_next()
            return True
        elif keyval == Gdk.KEY_F5:
            self.insert_datetime()
            return True
        elif keyval == Gdk.KEY_Escape:
            if self.find_replace_bar.get_visible():
                self.find_replace_bar.hide_bar()
                return True
        return False

    def new_tab(self, file_path=None):
        self.tab_seq += 1
        tab_id = f"tab_{self.tab_seq}"

        title = None
        if not file_path:
            title = f"Untitled {self.untitled_counter}" if self.untitled_counter > 1 else "Untitled"
            self.untitled_counter += 1

        font_family = self.config.get('font_family', 'Consolas')
        font_size = self.config.get('font_size', 11)
        tab = EditorTab(
            file_path=file_path,
            title=title,
            default_wrap=self.config.get("word_wrap", True),
            default_font_family=font_family,
            default_font_size=font_size
        )

        tab.tab_id = tab_id
        self.tab_widgets[tab_id] = tab
        self.stack.add_named(tab, tab_id)
        self.tab_bar.add_tab(tab_id, tab.title, is_modified=False)

        tab.connect("title-changed", lambda t, tit, mod: self._on_tab_title_changed(tab_id, tit, mod))
        tab.connect("status-changed", lambda t: self._update_statusbar_from_tab(tab))

        self._on_tab_selected(tab_id)
        tab.view.grab_focus()
        return tab

    def _on_tab_selected(self, tab_id):
        if tab_id in self.tab_widgets:
            self.tab_bar.set_active_tab(tab_id)
            self.stack.set_visible_child_name(tab_id)
            tab = self.tab_widgets[tab_id]
            self._update_statusbar_from_tab(tab)
            display_title = f"• {tab.title}" if tab.is_modified else tab.title
            self.set_title(f"{display_title} - Notepad")

    def _on_visible_child_changed(self, stack, pspec):
        tab = self.get_active_tab()
        if tab:
            self._update_statusbar_from_tab(tab)

    def _on_tab_title_changed(self, tab_id, title, is_modified):
        self.tab_bar.set_tab_title(tab_id, title, is_modified)
        if self.tab_bar.active_tab_id == tab_id:
            display_title = f"• {title}" if is_modified else title
            self.set_title(f"{display_title} - Notepad")

    def close_active_tab(self):
        if self.tab_bar.active_tab_id:
            self.close_tab_by_id(self.tab_bar.active_tab_id)

    def close_tab_by_id(self, tab_id):
        if tab_id not in self.tab_widgets:
            return
        tab = self.tab_widgets[tab_id]
        if tab.is_modified:
            self._show_unsaved_dialog(tab_id, tab)
            return
        self._finish_close_tab(tab_id)

    def _show_unsaved_dialog(self, tab_id, tab):
        dialog = Adw.MessageDialog(
            transient_for=self,
            heading="Do you want to save changes?",
            body=f"Do you want to save changes to '{tab.title}'?"
        )
        dialog.add_response("cancel", "Cancel")
        dialog.add_response("discard", "Don't Save")
        dialog.add_response("save", "Save")
        dialog.set_response_appearance("save", Adw.ResponseAppearance.SUGGESTED)
        dialog.set_response_appearance("discard", Adw.ResponseAppearance.DESTRUCTIVE)

        def on_response(dlg, response):
            if response == "save":
                ok, _ = tab.save_file()
                if not ok:
                    self.save_as_current_file(on_saved=lambda: self._finish_close_tab(tab_id))
                    return
                self._finish_close_tab(tab_id)
            elif response == "discard":
                self._finish_close_tab(tab_id)

        dialog.connect("response", on_response)
        dialog.present()

    def _finish_close_tab(self, tab_id):
        if tab_id in self.tab_widgets:
            tab = self.tab_widgets.pop(tab_id)
            self.stack.remove(tab)
            self.tab_bar.remove_tab(tab_id)

            if len(self.tab_widgets) == 0:
                self.new_tab()
            else:
                remaining = list(self.tab_widgets.keys())
                self._on_tab_selected(remaining[-1])

    def get_active_tab(self):
        active_id = self.tab_bar.active_tab_id
        return self.tab_widgets.get(active_id)

    def _update_statusbar_from_tab(self, tab):
        line, col, sel_count, total_chars = tab.get_cursor_info()
        if sel_count > 0:
            self.lbl_pos.set_text(f"Ln {line}, Col {col}  ({sel_count} selected)")
        else:
            self.lbl_pos.set_text(f"Ln {line}, Col {col}")

        self.lbl_chars.set_text(f"{total_chars} characters")
        self.lbl_zoom.set_text(f"{tab.zoom_level}%")
        self.lbl_endings.set_text(tab.line_endings)
        self.lbl_encoding.set_text(tab.encoding)

    def open_file_dialog(self):
        file_dialog = Gtk.FileDialog()
        file_dialog.set_title("Open")
        
        filters = Gio.ListStore.new(Gtk.FileFilter)
        f_text = Gtk.FileFilter()
        f_text.set_name("Text Documents (*.txt)")
        f_text.add_pattern("*.txt")
        filters.append(f_text)

        f_all = Gtk.FileFilter()
        f_all.set_name("All Files (*.*)")
        f_all.add_pattern("*")
        filters.append(f_all)

        file_dialog.set_filters(filters)
        file_dialog.open(self, None, self._on_open_finish)

    def _on_open_finish(self, dialog, result):
        try:
            gfile = dialog.open_finish(result)
            if gfile:
                path = gfile.get_path()
                self.open_file_path(path)
        except Exception:
            pass

    def open_file_path(self, path):
        active_tab = self.get_active_tab()
        if active_tab and active_tab.title.startswith("Untitled") and not active_tab.is_modified and active_tab.buffer.get_char_count() == 0:
            active_tab.load_file(path)
            if self.tab_bar.active_tab_id:
                self.tab_bar.set_tab_title(self.tab_bar.active_tab_id, active_tab.title, False)
        else:
            self.new_tab(file_path=path)

    def save_current_file(self):
        tab = self.get_active_tab()
        if not tab:
            return
        if tab.file_path:
            tab.save_file()
        else:
            self.save_as_current_file()

    def save_as_current_file(self, on_saved=None):
        tab = self.get_active_tab()
        if not tab:
            return

        file_dialog = Gtk.FileDialog()
        file_dialog.set_title("Save As")
        initial_name = tab.title if not tab.title.startswith("Untitled") else f"{tab.title}.txt"
        file_dialog.set_initial_name(initial_name)

        def on_save_finish(dialog, result):
            try:
                gfile = dialog.save_finish(result)
                if gfile:
                    path = gfile.get_path()
                    tab.save_file(path)
                    if on_saved:
                        on_saved()
            except Exception:
                pass

        file_dialog.save(self, None, on_save_finish)

    def save_all_files(self):
        for tab in self.tab_widgets.values():
            if tab and tab.is_modified and tab.file_path:
                tab.save_file()

    def print_file(self):
        tab = self.get_active_tab()
        if not tab:
            return
        print_op = Gtk.PrintOperation()
        print_op.set_job_name(tab.title)
        print_op.run(Gtk.PrintOperationAction.PRINT_DIALOG, self)

    def insert_datetime(self):
        tab = self.get_active_tab()
        if tab:
            now_str = time.strftime("%I:%M %p %m/%d/%Y")
            tab.buffer.insert_at_cursor(now_str)

    def toggle_statusbar(self):
        vis = not self.statusbar_box.get_visible()
        self.statusbar_box.set_visible(vis)

    def toggle_word_wrap(self):
        tab = self.get_active_tab()
        if tab:
            new_mode = not tab._wrap_mode
            tab.set_word_wrap(new_mode)
            self.config["word_wrap"] = new_mode

    def open_goto_dialog(self):
        tab = self.get_active_tab()
        if tab:
            dlg = GotoDialog(self, tab)
            dlg.present()

    def open_settings(self):
        dlg = SettingsDialog(self, self.apply_config)
        dlg.present()

    def apply_config(self, cfg):
        self.config = cfg
        theme = cfg.get("theme", "system")
        style_manager = Adw.StyleManager.get_default()

        if theme == "light":
            style_manager.set_color_scheme(Adw.ColorScheme.FORCE_LIGHT)
            self.remove_css_class("notepad-dark")
            self.add_css_class("notepad-light")
        elif theme == "dark":
            style_manager.set_color_scheme(Adw.ColorScheme.FORCE_DARK)
            self.remove_css_class("notepad-light")
            self.add_css_class("notepad-dark")
        else:
            style_manager.set_color_scheme(Adw.ColorScheme.DEFAULT)
            if style_manager.get_dark():
                self.remove_css_class("notepad-light")
                self.add_css_class("notepad-dark")
            else:
                self.remove_css_class("notepad-dark")
                self.add_css_class("notepad-light")

        font_family = cfg.get('font_family', 'Consolas')
        font_size = cfg.get('font_size', 11)
        wrap = cfg.get("word_wrap", True)
        for tab in self.tab_widgets.values():
            if tab:
                tab.set_font(font_family, font_size)
                tab.set_word_wrap(wrap)

    def new_window(self):
        win = NotepadWindow(self.app)
        win.present()
