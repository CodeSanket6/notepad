# Notepad (Linux Flatpak Edition)

[![Flathub](https://img.shields.io/badge/Flathub-Ready-blue.svg)](https://flathub.org)
[![Platform](https://img.shields.io/badge/Platform-Linux%20(GTK4%20%2F%20Libadwaita)-green.svg)]()
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A modern, responsive Linux text editor port of the **Windows 11 Fluent Notepad** (version 11.2607.14.0). Built with **GTK 4**, **Libadwaita**, and **GtkSourceView 5**, it brings the exact visual styling and feature set to Linux desktops.

---

## ✨ Features

- **Fluent Multi-Tab Bar (`TabsBar`)**:
  - Integrated header tab bar with New Tab (`+`) button (`Ctrl+N` / `Ctrl+T`)
  - Unsaved change indicator dot (`•`) on modified tabs
  - Per-tab close buttons (`✕`) and close confirmation dialogs
- **Floating Find & Replace Panel (`FindReplaceDialog`)**:
  - Overlaid in the top-right corner of the editor
  - Live match counting (`x of y matches`)
  - Next (`F3`) and Previous (`Shift+F3`) navigation
  - Match case toggle (`Aa`), Wrap around
  - Expandable Replace section with Replace and Replace All
- **Go To Line Dialog (`GotoDialogContent`)**:
  - Quick jump to any line number with `Ctrl+G`
- **Appearance & Fluent Theming (`NotepadSettingsPage`)**:
  - Light, Dark, and System theme matching Fluent Mica aesthetics
  - Live font family and font size customization
  - Configurable Word Wrap and Status Bar display
- **Full Encoding & Line-Ending Support**:
  - Windows (`\r\n` CRLF), Unix (`\n` LF), and Macintosh (`\r` CR) detection and preservation
  - UTF-8, UTF-8 with BOM, UTF-16 LE, UTF-16 BE, and ANSI
- **Status Bar (`StatusBar`)**:
  - Real-time line and column numbers (`Ln X, Col Y`)
  - Selection character count
  - Document character count
  - Zoom percentage (`Ctrl++`, `Ctrl+-`, `Ctrl+0`)
  - Detected line-ending format and encoding

---

## 🚀 Building & Running Locally

### Direct Execution
You can run Notepad immediately without installation:
```bash
./notepad [optional_files...]
```

### Build with Meson
```bash
meson setup _build --prefix=/usr
ninja -C _build
sudo ninja -C _build install
```

---

## 📦 Building the Flatpak

The repository is pre-configured with complete AppStream metadata, multi-size hicolor icons (16px to 256px), desktop entry, and Flatpak manifests.

### 1. Build and Install Locally
```bash
./build-flatpak.sh
```
Or manually using `flatpak-builder`:
```bash
flatpak-builder --user --install --force-clean build-dir io.github.sanket.Notepad.yaml
```

### 2. Run the Flatpak
```bash
flatpak run io.github.sanket.Notepad
```

### 3. Create a Standalone Single-File Bundle (`.flatpak`)
```bash
flatpak-builder --repo=repo --force-clean build-dir io.github.sanket.Notepad.yaml
flatpak build-bundle repo Notepad.flatpak io.github.sanket.Notepad
```

---

## 🌐 Publishing to Flathub

This project strictly conforms to the [Flathub Quality Guidelines](https://docs.flathub.org/docs/for-app-authors/submission):
- Reverse-DNS application ID: `io.github.sanket.Notepad`
- Standard Meson build system
- Validated AppStream metadata (`io.github.sanket.Notepad.metainfo.xml`)
- Validated Desktop entry (`io.github.sanket.Notepad.desktop`)
- Full hicolor icon set (16x16, 24x24, 32x32, 48x48, 64x64, 128x128, 256x256)

### Steps to Submit to Flathub:

1. **Push this source repository to GitHub**:
   ```bash
   git init
   git add .
   git commit -m "Initial commit of Windows 11 Notepad for Linux"
   git remote add origin https://github.com/sanket/notepad-linux.git
   git push -u origin main
   ```

2. **Create a release tag**:
   ```bash
   git tag -a v11.2607.14.0 -m "Release v11.2607.14.0"
   git push origin v11.2607.14.0
   ```

3. **Submit to Flathub**:
   - Fork [https://github.com/flathub/flathub](https://github.com/flathub/flathub)
   - Create a new branch: `git checkout -b add-notepad`
   - In your manifest (`io.github.sanket.Notepad.yaml`), replace the local directory source with your git repository:
     ```yaml
     modules:
       - name: notepad
         buildsystem: meson
         sources:
           - type: git
             url: https://github.com/sanket/notepad-linux.git
             tag: v11.2607.14.0
             commit: <git-commit-hash>
     ```
   - Commit and open a Pull Request against the `flathub/flathub` repository.
   - The Flathub automated bot will build and verify the package, providing test builds before publication!

---

## ⌨️ Keyboard Shortcuts

| Shortcut | Action |
| :--- | :--- |
| `Ctrl + N` / `Ctrl + T` | New Tab |
| `Ctrl + Shift + N` | New Window |
| `Ctrl + O` | Open File |
| `Ctrl + S` | Save |
| `Ctrl + Shift + S` | Save As |
| `Ctrl + W` | Close Tab |
| `Ctrl + Shift + W` | Close Window |
| `Ctrl + Q` | Exit Application |
| `Ctrl + F` | Find |
| `F3` / `Shift + F3` | Find Next / Previous |
| `Ctrl + H` | Replace |
| `Ctrl + G` | Go to Line |
| `F5` | Insert Current Time & Date |
| `Ctrl + +` / `Ctrl + =` | Zoom In |
| `Ctrl + -` | Zoom Out |
| `Ctrl + 0` | Restore Default Zoom (100%) |

---

## 📜 License
Distributed under the MIT License.
