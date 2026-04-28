#!/usr/bin/env bash
# =============================================================================
# install.sh — ColorFlow installer
# Installs ColorFlow as a desktop application for the current user.
# Run with: bash install.sh
# =============================================================================

set -e

BOLD="\033[1m"
GREEN="\033[32m"
YELLOW="\033[33m"
RESET="\033[0m"

ok()   { echo -e "  ${GREEN}✓${RESET} $1"; }
info() { echo -e "  ${YELLOW}→${RESET} $1"; }

echo ""
echo -e "${BOLD}Installing ColorFlow...${RESET}"
echo ""

# Directories
BIN_DIR="$HOME/.local/bin"
ICON_DIR="$HOME/.local/share/icons"
APP_DIR="$HOME/.local/share/applications"

mkdir -p "$BIN_DIR" "$ICON_DIR" "$APP_DIR"

# Copy files
info "Copying colorflow.py to $BIN_DIR"
cp colorflow.py "$BIN_DIR/colorflow.py"
chmod +x "$BIN_DIR/colorflow.py"
ok "colorflow.py installed"

info "Copying icon to $ICON_DIR"
cp colorflow.svg "$ICON_DIR/colorflow.svg"
ok "Icon installed"

# Write desktop file with correct paths
info "Creating desktop entry"
cat > "$APP_DIR/colorflow.desktop" << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=ColorFlow
Comment=Color management overview for photographers and video professionals
Exec=python3 $BIN_DIR/colorflow.py
Icon=$ICON_DIR/colorflow.svg
Terminal=false
Categories=Graphics;Photography;
Keywords=color;icc;profile;display;printer;calibration;
StartupNotify=true
EOF
ok "Desktop entry created"

# Update desktop database
if command -v update-desktop-database &>/dev/null; then
    update-desktop-database "$APP_DIR" 2>/dev/null
    ok "Desktop database updated"
fi

echo ""
echo -e "${BOLD}ColorFlow is installed!${RESET}"
echo ""
echo "  You can now find ColorFlow in your applications menu,"
echo "  or run it directly with:"
echo ""
echo "    python3 ~/.local/bin/colorflow.py"
echo ""
