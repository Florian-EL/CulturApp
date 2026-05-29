# ...existing code...
#!/usr/bin/env bash
set -e

# === CONFIG ===
APP_NAME="CulturApp"
PROJECT_DIR="/home/florian/Documents/Projets/Algo/CulturApp"
BUILD_DIR="$PROJECT_DIR/build/exe.linux-x86_64-3.13"
DESKTOP_FILE="$PROJECT_DIR/$APP_NAME.desktop"
DESKTOP_TARGET="$HOME/.local/share/applications/$APP_NAME.desktop"
EXEC_PATH="$BUILD_DIR/$APP_NAME"

# === BUILD ===
echo "Nettoyage de l'ancien build..."
rm -rf "$PROJECT_DIR/build"

PY_BIN="$(command -v python3 || command -v python || true)"

echo "Compilation avec cx_Freeze en utilisant : $PY_BIN"
"$PY_BIN" "$PROJECT_DIR/build.py" build


chmod +x "$DESKTOP_FILE"

# === INSTALLATION ===
echo "Copie du raccourci vers ~/.local/share/applications/ ..."
mkdir -p "$(dirname "$DESKTOP_TARGET")"
cp "$DESKTOP_FILE" "$DESKTOP_TARGET"
update-desktop-database ~/.local/share/applications/ >/dev/null 2>&1 || true

# === TRUST ===
echo "Marquage du .desktop comme fiable..."
gio set "$DESKTOP_TARGET" metadata::trusted true 2>/dev/null || true

echo "Build complet !"
echo "Lance ton application depuis le menu ou avec :"
echo "  $EXEC_PATH"
