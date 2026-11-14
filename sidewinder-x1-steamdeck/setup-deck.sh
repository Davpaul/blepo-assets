#!/bin/bash
# setup-deck.sh - one-time Steam Deck setup for running an Artillery Sidewinder X1.
# Run from Desktop Mode in Konsole:   bash setup-deck.sh
# You need a sudo password set first (run: passwd).

set -e

echo "== 1/4  Checking Flathub =="
flatpak remote-add --user --if-not-exists flathub https://dl.flathub.org/repo/flathub.flatpakrepo

echo "== 2/4  Installing PrusaSlicer (slicer + firmware flasher) =="
flatpak install --user -y flathub com.prusa3d.PrusaSlicer

echo "== 3/4  Letting PrusaSlicer see USB devices (needed for flashing) =="
flatpak override --user --device=all com.prusa3d.PrusaSlicer

echo "== 4/4  Allowing your user to talk to USB printers (asks for sudo password) =="
RULE='KERNEL=="ttyUSB[0-9]*", MODE="0666"
KERNEL=="ttyACM[0-9]*", MODE="0666"'
echo "$RULE" | sudo tee /etc/udev/rules.d/99-3d-printer.rules > /dev/null
sudo udevadm control --reload-rules
sudo udevadm trigger

mkdir -p "$HOME/x1"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cp "$SCRIPT_DIR/x1tool.py" "$HOME/x1/" 2>/dev/null || true

echo
echo "All done."
echo "  PrusaSlicer is in the app menu (or run: flatpak run com.prusa3d.PrusaSlicer)"
echo "  Printer checker:  python3 ~/x1/x1tool.py check"
echo "If a SteamOS update ever removes the USB permission, just run this script again."
