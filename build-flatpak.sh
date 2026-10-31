#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

APP_ID="io.ninja.notepad"
BUNDLE_FILE="$APP_ID.flatpak"
BUILD_DIR="$SCRIPT_DIR/flatpak_build"
APP_DIR="$BUILD_DIR/app_dir"
REPO_DIR="$BUILD_DIR/repo"

echo "=== Building Flatpak Bundle for $APP_ID ==="

# Check flatpak
if ! command -v flatpak &> /dev/null; then
    echo "Error: flatpak is not installed."
    exit 1
fi

# Detect installed GNOME Platform runtime version
RUNTIME_VER=""
for v in 51 50 49 48 47; do
    if flatpak info "org.gnome.Platform//$v" &> /dev/null; then
        RUNTIME_VER="$v"
        break
    fi
done

if [ -z "$RUNTIME_VER" ]; then
    echo "Installing GNOME Platform 50 (User space)..."
    flatpak install --user -y flathub org.gnome.Platform//50
    RUNTIME_VER="50"
fi

echo "Using org.gnome.Platform branch $RUNTIME_VER"

# Clean build directory
rm -rf "$APP_DIR" "$REPO_DIR"
mkdir -p "$APP_DIR"

# Initialize application structure
echo "Initializing flatpak structure..."
flatpak build-init "$APP_DIR" "$APP_ID" org.gnome.Platform org.gnome.Platform "$RUNTIME_VER"

# Detect runtime python version
PY_VER=$(flatpak run --command=python3 "org.gnome.Platform//$RUNTIME_VER" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "Detected Flatpak Python version: $PY_VER"

FILES_DIR="$APP_DIR/files"
BIN_DIR="$FILES_DIR/bin"
PY_LIB_DIR="$FILES_DIR/lib/python$PY_VER/site-packages/notepad"
APPS_DIR="$FILES_DIR/share/applications"
META_DIR="$FILES_DIR/share/metainfo"
ICONS_DIR="$FILES_DIR/share/icons/hicolor"
STYLES_DIR="$FILES_DIR/share/notepad/styles"

mkdir -p "$BIN_DIR" "$PY_LIB_DIR" "$APPS_DIR" "$META_DIR" "$ICONS_DIR" "$STYLES_DIR"

# 1. Launcher script
cat << 'EOF' > "$BIN_DIR/notepad"
#!/bin/sh
export PKGDATADIR="/app/share/notepad"
exec python3 -m notepad.app "$@"
EOF
chmod +x "$BIN_DIR/notepad"

# 2. Python source modules
cp src/*.py "$PY_LIB_DIR/"

# 3. Desktop file & AppStream metadata
if [ -f "_build/data/$APP_ID.desktop" ]; then
    cp "_build/data/$APP_ID.desktop" "$APPS_DIR/"
else
    cp "data/$APP_ID.desktop.in" "$APPS_DIR/$APP_ID.desktop"
fi

if [ -f "_build/data/$APP_ID.metainfo.xml" ]; then
    cp "_build/data/$APP_ID.metainfo.xml" "$META_DIR/"
else
    cp "data/$APP_ID.metainfo.xml.in" "$META_DIR/$APP_ID.metainfo.xml"
fi

# 4. High-resolution icons
cp -r data/icons/hicolor/* "$ICONS_DIR/"

# 5. Stylesheet
cp data/styles/fluent.css "$STYLES_DIR/"

# 6. Build finish (permissions & exports)
echo "Finishing build with sandboxing permissions..."
flatpak build-finish \
  --command=notepad \
  --socket=wayland \
  --socket=fallback-x11 \
  --share=ipc \
  --device=dri \
  --filesystem=host \
  --talk-name=org.freedesktop.FileManager1 \
  "$APP_DIR"

# 7. Export repo and build single-file bundle
echo "Exporting repository and building $BUNDLE_FILE..."
mkdir -p "$REPO_DIR"
flatpak build-export "$REPO_DIR" "$APP_DIR"
flatpak build-bundle "$REPO_DIR" "$BUNDLE_FILE" "$APP_ID"

echo ""
echo "=== Success! ==="
echo "Flatpak bundle successfully built: $SCRIPT_DIR/$BUNDLE_FILE"
echo ""
echo "To test or install locally:"
echo "  flatpak install --user -y --reinstall $BUNDLE_FILE"
echo "To run:"
echo "  flatpak run $APP_ID"
