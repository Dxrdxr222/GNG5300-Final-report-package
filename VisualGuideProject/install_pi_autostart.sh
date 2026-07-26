#!/usr/bin/env bash

set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AUTOSTART_DIR="$HOME/.config/autostart"
AUTOSTART_FILE="$AUTOSTART_DIR/visual-guide-robot.desktop"

chmod +x "$PROJECT_DIR/start_visual_guide_pi.sh"

mkdir -p "$AUTOSTART_DIR"

cat > "$AUTOSTART_FILE" <<DESKTOP
[Desktop Entry]
Type=Application
Name=Visual Guide Robot
Comment=Start Visual Guide Robot in standby camera-gate mode
Exec=$PROJECT_DIR/start_visual_guide_pi.sh
Path=$PROJECT_DIR
Terminal=true
X-GNOME-Autostart-enabled=true
DESKTOP

echo "Autostart installed:"
echo "$AUTOSTART_FILE"
echo ""
echo "It will start after Raspberry Pi desktop login."
echo "To test now, run:"
echo "$PROJECT_DIR/start_visual_guide_pi.sh"
