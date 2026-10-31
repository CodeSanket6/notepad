#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "Installing Windows 11 Notepad for Linux..."

# Install executable symlink to ~/.local/bin
mkdir -p "$HOME/.local/bin"
ln -sf "$SCRIPT_DIR/notepad" "$HOME/.local/bin/notepad"

# Install Icon
mkdir -p "$HOME/.local/share/icons/hicolor/256x256/apps"
cp "$SCRIPT_DIR/assets/notepad.png" "$HOME/.local/share/icons/hicolor/256x256/apps/com.microsoft.notepad.png"

# Install Desktop Entry
mkdir -p "$HOME/.local/share/applications"
sed -e "s|/home/sanket/Downloads/notepad/notepad-linux/notepad|$HOME/.local/bin/notepad|g" \
    -e "s|/home/sanket/Downloads/notepad/notepad-linux/assets/notepad.png|com.microsoft.notepad|g" \
    "$SCRIPT_DIR/com.microsoft.notepad.desktop" > "$HOME/.local/share/applications/com.microsoft.notepad.desktop"

# Update desktop database
update-desktop-database "$HOME/.local/share/applications" 2>/dev/null || true

echo "Installation complete! You can now run 'notepad' from the terminal or launch Notepad from your application menu."
