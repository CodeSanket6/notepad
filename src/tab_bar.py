"""
Windows 11 Fluent Tab Bar Widget.
Replicates WinUI 3 TabsBar from modern Windows 11 Notepad:
- App icon shown ONLY on active tab (left side of filename)
- Inactive tabs show title only (no icon)
- Close button always visible on active tab, visible on hover for inactive tabs
- Vertical divider lines between inactive tabs
- Unsaved indicator dot (•)
- New Tab (+) button immediately following tabs
- Fully responsive tab layout with smooth hover states
"""

import os
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, GObject, Pango, Gdk

class FluentTabItem(Gtk.Box):
    def __init__(self, tab_id, title, is_modified, on_select, on_close):
        super().__init__(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self.tab_id = tab_id
        self.on_select = on_select
        self.on_close = on_close
        self.is_active = False
        self.is_modified = is_modified
        self._is_hovered = False

        self.add_css_class("fluent-tab")
        self.set_valign(Gtk.Align.END)

        # Modified indicator dot (•)
        self.dot_label = Gtk.Label(label="•")
        self.dot_label.add_css_class("fluent-tab-dot")
        self.dot_label.set_valign(Gtk.Align.CENTER)
        self.dot_label.set_visible(is_modified)
        self.append(self.dot_label)

        # Tab Title Label (No logo on tab - logo is at left side of titlebar)
        self.title_label = Gtk.Label(label=title)
        self.title_label.add_css_class("fluent-tab-label")
        self.title_label.set_ellipsize(Pango.EllipsizeMode.END)
        self.title_label.set_max_width_chars(24)
        self.title_label.set_hexpand(True)
        self.title_label.set_halign(Gtk.Align.START)
        self.title_label.set_valign(Gtk.Align.CENTER)
        self.append(self.title_label)

        # Close Button (✕) - completely transparent by default, blends into tab
        self.close_btn = Gtk.Button.new_from_icon_name("window-close-symbolic")
        self.close_btn.add_css_class("fluent-tab-close")
        self.close_btn.set_has_frame(False)
        self.close_btn.set_tooltip_text("Close tab (Ctrl+W)")
        self.close_btn.set_valign(Gtk.Align.CENTER)
        self.close_btn.connect("clicked", self._on_close_clicked)
        # Inactive tabs hide close button until hover
        self.close_btn.set_visible(False)
        self.append(self.close_btn)

        # Click gesture to activate tab
        click_gesture = Gtk.GestureClick.new()
        click_gesture.connect("released", self._on_tab_clicked)
        self.add_controller(click_gesture)

        # Motion controller for hover state (to show close button on inactive tab)
        motion_ctrl = Gtk.EventControllerMotion.new()
        motion_ctrl.connect("enter", self._on_enter)
        motion_ctrl.connect("leave", self._on_leave)
        self.add_controller(motion_ctrl)

    def _on_tab_clicked(self, gesture, n_press, x, y):
        self.on_select(self.tab_id)

    def _on_close_clicked(self, btn):
        self.on_close(self.tab_id)

    def _on_enter(self, ctrl, x, y):
        self._is_hovered = True
        self.add_css_class("fluent-tab-hover")
        if not self.is_active:
            self.close_btn.set_visible(True)

    def _on_leave(self, ctrl):
        self._is_hovered = False
        self.remove_css_class("fluent-tab-hover")
        if not self.is_active:
            self.close_btn.set_visible(False)

    def set_active(self, active):
        self.is_active = active
        if active:
            self.add_css_class("fluent-tab-active")
            self.close_btn.set_visible(True)
        else:
            self.remove_css_class("fluent-tab-active")
            self.close_btn.set_visible(self._is_hovered)

    def update_title(self, title, is_modified):
        self.title_label.set_text(title)
        self.is_modified = is_modified
        self.dot_label.set_visible(is_modified)


class TabDivider(Gtk.Box):
    """Subtle 1px vertical separator line between inactive tabs."""
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self.add_css_class("fluent-tab-divider")
        self.set_valign(Gtk.Align.CENTER)


class FluentTabBar(Gtk.Box):
    __gsignals__ = {
        'tab-selected': (GObject.SignalFlags.RUN_FIRST, None, (str,)),
        'tab-close-requested': (GObject.SignalFlags.RUN_FIRST, None, (str,)),
        'new-tab-requested': (GObject.SignalFlags.RUN_FIRST, None, ()),
    }

    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        self.add_css_class("fluent-tab-bar")
        self.set_valign(Gtk.Align.END)

        # Scrollable container for tabs
        self.scrolled = Gtk.ScrolledWindow()
        self.scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.NEVER)
        self.scrolled.set_propagate_natural_width(True)
        self.scrolled.set_hexpand(False)
        self.scrolled.set_valign(Gtk.Align.END)

        self.tabs_container = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        self.tabs_container.set_valign(Gtk.Align.END)
        self.scrolled.set_child(self.tabs_container)
        self.append(self.scrolled)

        # New Tab (+) button immediately next to the tabs - transparent blending into titlebar
        self.btn_new_tab = Gtk.Button.new_from_icon_name("list-add-symbolic")
        self.btn_new_tab.add_css_class("fluent-tab-add")
        self.btn_new_tab.set_has_frame(False)
        self.btn_new_tab.set_tooltip_text("New tab (Ctrl+N)")
        self.btn_new_tab.set_valign(Gtk.Align.CENTER)
        self.btn_new_tab.connect("clicked", lambda b: self.emit('new-tab-requested'))
        self.append(self.btn_new_tab)

        self.tabs = {}  # tab_id -> FluentTabItem
        self.tab_ids = []  # ordered list of tab_ids
        self.dividers = {}  # index -> TabDivider
        self.active_tab_id = None

    def add_tab(self, tab_id, title, is_modified=False):
        tab_item = FluentTabItem(
            tab_id=tab_id,
            title=title,
            is_modified=is_modified,
            on_select=lambda tid: self.emit('tab-selected', tid),
            on_close=lambda tid: self.emit('tab-close-requested', tid)
        )
        self.tabs[tab_id] = tab_item
        self.tab_ids.append(tab_id)

        self._refresh_tab_display()
        self.set_active_tab(tab_id)
        return tab_item

    def remove_tab(self, tab_id):
        if tab_id in self.tabs:
            del self.tabs[tab_id]
            self.tab_ids.remove(tab_id)
            if self.active_tab_id == tab_id:
                self.active_tab_id = None
            self._refresh_tab_display()

    def _refresh_tab_display(self):
        # Clear container
        while True:
            child = self.tabs_container.get_first_child()
            if not child:
                break
            self.tabs_container.remove(child)

        self.dividers.clear()

        # Re-add tabs with separators
        for i, tid in enumerate(self.tab_ids):
            tab_item = self.tabs[tid]
            if i > 0:
                div = TabDivider()
                self.dividers[i] = div
                self.tabs_container.append(div)
            self.tabs_container.append(tab_item)

        self._update_divider_visibility()

    def set_active_tab(self, tab_id):
        self.active_tab_id = tab_id
        for tid, tab_item in self.tabs.items():
            tab_item.set_active(tid == tab_id)
        self._update_divider_visibility()

    def _update_divider_visibility(self):
        # Hide divider if adjacent to active tab
        active_idx = self.tab_ids.index(self.active_tab_id) if self.active_tab_id in self.tab_ids else -1
        for i, div in self.dividers.items():
            # i is divider before tab_ids[i] (between tab_ids[i-1] and tab_ids[i])
            if i == active_idx or i == active_idx + 1:
                div.set_visible(False)
            else:
                div.set_visible(True)

    def set_tab_title(self, tab_id, title, is_modified):
        if tab_id in self.tabs:
            self.tabs[tab_id].update_title(title, is_modified)

    def get_tab_count(self):
        return len(self.tabs)

    def get_active_tab_id(self):
        return self.active_tab_id

    def select_next_tab(self):
        if not self.tab_ids:
            return
        idx = self.tab_ids.index(self.active_tab_id) if self.active_tab_id in self.tab_ids else -1
        next_idx = (idx + 1) % len(self.tab_ids)
        self.emit('tab-selected', self.tab_ids[next_idx])

    def select_prev_tab(self):
        if not self.tab_ids:
            return
        idx = self.tab_ids.index(self.active_tab_id) if self.active_tab_id in self.tab_ids else -1
        prev_idx = (idx - 1) % len(self.tab_ids)
        self.emit('tab-selected', self.tab_ids[prev_idx])
