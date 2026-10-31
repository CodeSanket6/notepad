"""
Windows 11 Notepad Settings Page.
Matches NotepadSettingsPage.xbf, ThemeSettingSection.xbf, and FontSettingSection.xbf.
"""

import json
import os
from gi.repository import Gtk, Adw, Gdk

CONFIG_PATH = os.path.expanduser("~/.config/notepad-linux/config.json")

def load_config():
    default_config = {
        "theme": "system",  # "system", "light", "dark"
        "font_family": "Consolas",
        "font_size": 11,
        "word_wrap": True,
        "open_in_tab": True,
    }
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                default_config.update(data)
        except Exception:
            pass
    return default_config

def save_config(cfg):
    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
    try:
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2)
    except Exception:
        pass

class SettingsDialog(Adw.PreferencesWindow):
    def __init__(self, parent_window, on_settings_changed):
        super().__init__(transient_for=parent_window, modal=True)
        self.set_title("Settings")
        self.set_default_size(560, 480)
        self.on_changed = on_settings_changed
        self.config = load_config()

        # Main Page
        page = Adw.PreferencesPage()
        self.add(page)

        # --- Appearance Group ---
        grp_appearance = Adw.PreferencesGroup(title="Appearance")
        page.add(grp_appearance)

        # App Theme ComboRow
        self.theme_row = Adw.ComboRow(title="App theme")
        self.theme_row.set_subtitle("Select which app theme to display")
        theme_model = Gtk.StringList.new(["Light", "Dark", "Use system setting"])
        self.theme_row.set_model(theme_model)

        theme_map = {"light": 0, "dark": 1, "system": 2}
        self.theme_row.set_selected(theme_map.get(self.config.get("theme", "system"), 2))
        self.theme_row.connect("notify::selected", self._on_theme_changed)
        grp_appearance.add(self.theme_row)

        # Font Expander
        grp_font = Adw.PreferencesGroup(title="Font")
        page.add(grp_font)

        # Font Family Row
        self.font_family_row = Adw.ActionRow(title="Font family")
        self.font_family_entry = Gtk.Entry()
        self.font_family_entry.set_text(self.config.get("font_family", "Consolas"))
        self.font_family_entry.set_valign(Gtk.Align.CENTER)
        self.font_family_entry.connect("changed", self._on_font_changed)
        self.font_family_row.add_suffix(self.font_family_entry)
        grp_font.add(self.font_family_row)

        # Font Size SpinRow
        self.font_size_row = Adw.SpinRow.new_with_range(8, 72, 1)
        self.font_size_row.set_title("Font size")
        self.font_size_row.set_value(self.config.get("font_size", 11))
        self.font_size_row.connect("notify::value", self._on_font_changed)
        grp_font.add(self.font_size_row)

        # Word Wrap Row
        self.wrap_row = Adw.SwitchRow(title="Word wrap")
        self.wrap_row.set_subtitle("Wrap long lines into multiple lines on display")
        self.wrap_row.set_active(self.config.get("word_wrap", True))
        self.wrap_row.connect("notify::active", self._on_wrap_changed)
        grp_font.add(self.wrap_row)

        # --- About Group ---
        grp_about = Adw.PreferencesGroup(title="About this app")
        page.add(grp_about)

        about_row = Adw.ActionRow(
            title="Notepad 11.2607.14.0",
            subtitle="Windows 11 Fluent Notepad ported to Linux with GtkSourceView 5"
        )
        icon_path = os.path.join(os.path.dirname(__file__), "../assets/notepad.png")
        if Gtk.IconTheme.get_for_display(self.get_display() or Gdk.Display.get_default()).has_icon("io.github.CodeSanket6.notepad"):
            about_img = Gtk.Image.new_from_icon_name("io.github.CodeSanket6.notepad")
        elif os.path.exists(icon_path):
            about_img = Gtk.Image.new_from_file(icon_path)
        else:
            about_img = Gtk.Image.new_from_icon_name("text-editor-symbolic")
        about_img.set_pixel_size(36)
        about_row.add_prefix(about_img)
        grp_about.add(about_row)

    def _on_theme_changed(self, row, pspec):
        idx = row.get_selected()
        idx_map = {0: "light", 1: "dark", 2: "system"}
        self.config["theme"] = idx_map.get(idx, "system")
        save_config(self.config)
        self.on_changed(self.config)

    def _on_font_changed(self, *args):
        self.config["font_family"] = self.font_family_entry.get_text() or "Consolas"
        self.config["font_size"] = int(self.font_size_row.get_value())
        save_config(self.config)
        self.on_changed(self.config)

    def _on_wrap_changed(self, row, pspec):
        self.config["word_wrap"] = row.get_active()
        save_config(self.config)
        self.on_changed(self.config)
