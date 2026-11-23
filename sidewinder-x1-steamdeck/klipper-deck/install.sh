#!/bin/bash
# install.sh - one-time setup of Klipper on a Steam Deck.
# Run in Desktop Mode, in Konsole, from this folder:   bash install.sh
# Takes 5-15 minutes (mostly the container build). Needs internet and your sudo password.

set -e
KIT="$(cd "$(dirname "$0")" && pwd)"
step() { printf '\n\033[1m== %s ==\033[0m\n' "$*"; }

step "1/6 Checking podman (ships with SteamOS 3.5 and newer)"
if ! command -v podman >/dev/null; then
    echo "podman isn't installed. Update SteamOS (Settings > System > Check for updates) and run this again."
    exit 1
fi
podman --version

step "2/6 Checking sudo password"
if ! sudo -v; then
    echo "Set a password first by running:  passwd"
    exit 1
fi

step "3/6 Container user ranges"
U=$(id -un)
if ! grep -q "^$U:" /etc/subuid 2>/dev/null || ! grep -q "^$U:" /etc/subgid 2>/dev/null; then
    sudo usermod --add-subuids 100000-165535 --add-subgids 100000-165535 "$U"
    podman system migrate || true
    echo "Added."
else
    echo "Already set."
fi

step "4/6 USB printer access + web page on port 80"
printf 'KERNEL=="ttyUSB[0-9]*", MODE="0666"\nKERNEL=="ttyACM[0-9]*", MODE="0666"\n' \
    | sudo tee /etc/udev/rules.d/99-3d-printer.rules >/dev/null
sudo udevadm control --reload-rules
sudo udevadm trigger
echo "net.ipv4.ip_unprivileged_port_start=80" | sudo tee /etc/sysctl.d/99-klipper-deck.conf >/dev/null
sudo sysctl -q -w net.ipv4.ip_unprivileged_port_start=80
# Stop USB power saving from switching hubs/printers off mid-print
echo 'ACTION=="add", SUBSYSTEM=="usb", TEST=="power/control", ATTR{power/control}="on"' \
    | sudo tee /etc/udev/rules.d/99-usb-no-autosuspend.rules >/dev/null
echo -1 | sudo tee /sys/module/usbcore/parameters/autosuspend >/dev/null
for c in /sys/bus/usb/devices/*/power/control; do echo on | sudo tee "$c" >/dev/null 2>&1 || true; done
# Software "unplug and replug the dock", used by auto-resume. Root-owned, and the
# only thing allowed to run without a password.
sudo install -d -m 755 /etc/klipper-deck
sudo install -m 755 -o root -g root "$KIT/usb-reset" /etc/klipper-deck/usb-reset
echo "$U ALL=(root) NOPASSWD: /etc/klipper-deck/usb-reset" > /tmp/klipper-deck-sudoers
if sudo visudo -cf /tmp/klipper-deck-sudoers >/dev/null; then
    # "zz-" so it's read last: SteamOS's own wheel rule would otherwise override it
    sudo rm -f /etc/sudoers.d/klipper-deck
    sudo install -m 440 -o root -g root /tmp/klipper-deck-sudoers /etc/sudoers.d/zz-klipper-deck
fi
rm -f /tmp/klipper-deck-sudoers
sudo -k
if sudo -n /etc/klipper-deck/usb-reset 2>&1 | grep -q usage; then
    echo "Software dock reset: works without a password. Good."
else
    echo "WARNING: software dock reset still needs a password. Send Claude a photo of this:"
    sudo -n -l 2>&1 | tail -5
fi
# SteamOS can have firewalld running, which blocks other devices from reaching the web page
if command -v firewall-cmd >/dev/null && sudo firewall-cmd --state >/dev/null 2>&1; then
    sudo firewall-cmd -q --permanent --add-service=http
    sudo firewall-cmd -q --permanent --add-port=8080/tcp
    sudo firewall-cmd -q --permanent --add-port=7125/tcp
    sudo firewall-cmd -q --reload
    echo "Opened firewall for the web page (80, 8080) and Moonraker (7125)."
fi
echo "Done."

step "5/6 Building the Klipper container (the slow bit, 5-15 min)"
podman build -t localhost/klipper-deck -f "$KIT/container/Containerfile" "$KIT/container"

step "6/6 Installing the klipper-deck command and desktop shortcut"
mkdir -p "$HOME/.local/bin" "$HOME/.config/klipper-deck" "$HOME/klipper-deck/printer_data" "$HOME/.local/share/applications"
install -m 755 "$KIT/klipper-deck" "$HOME/.local/bin/klipper-deck"
mkdir -p "$HOME/.local/share/klipper-deck"
install -m 755 "$KIT/guard.py" "$HOME/.local/share/klipper-deck/guard.py"
bash "$KIT/add-extras.sh" || true
echo "$KIT" > "$HOME/.config/klipper-deck/src"
if ! grep -q 'HOME/.local/bin' "$HOME/.bashrc" 2>/dev/null; then
    echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$HOME/.bashrc"
fi

DESKTOP_ENTRY="[Desktop Entry]
Type=Application
Name=Start Klipper
Comment=Run the 3D printer (Klipper + Mainsail)
Exec=konsole --hold -e $HOME/.local/bin/klipper-deck start
Icon=printer
Terminal=false
Categories=Utility;"
echo "$DESKTOP_ENTRY" > "$HOME/.local/share/applications/klipper-deck.desktop"
if [ -d "$HOME/Desktop" ]; then
    echo "$DESKTOP_ENTRY" > "$HOME/Desktop/Start Klipper.desktop"
    chmod +x "$HOME/Desktop/Start Klipper.desktop"
fi

printf '\n\033[1mInstalled.\033[0m\n'
echo "Next:"
echo "  1. Plug the printer in by USB and switch it on"
echo "  2. Flash Klipper onto it (first time only):   ~/.local/bin/klipper-deck flash"
echo "  3. Start it:                                  ~/.local/bin/klipper-deck start"
echo "     (or double-click 'Start Klipper' on the desktop)"
