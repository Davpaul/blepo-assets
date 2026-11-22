#!/bin/bash
# remote-access.sh - reach Mainsail (and the alert buttons) from anywhere, privately.
# Uses Tailscale's own Steam Deck installer (github.com/tailscale-dev/deck-tailscale).
# Your phone and the Deck join a private network only your devices are on.
# Nothing is opened to the public internet.
set -e
KIT="$(cd "$(dirname "$0")" && pwd)"
step() { printf '\n\033[1m== %s ==\033[0m\n' "$*"; }

step "1/4 Getting Tailscale's Steam Deck installer"
if [ -d "$HOME/deck-tailscale/.git" ]; then
    git -C "$HOME/deck-tailscale" pull -q
else
    git clone -q https://github.com/tailscale-dev/deck-tailscale.git "$HOME/deck-tailscale"
fi

step "2/4 Installing Tailscale (asks for your password; survives SteamOS updates)"
sudo bash -c "cd '$HOME/deck-tailscale' && bash tailscale.sh"

step "3/4 Logging the Deck into your Tailscale account"
echo "A QR code appears below. Scan it with your phone and sign in"
echo "(Google/Apple/Microsoft account is fine). Use the same account in the"
echo "Tailscale app on your phone."
sudo /opt/tailscale/tailscale up --qr --operator="$(id -un)"

step "4/4 Letting Klipper accept connections from your Tailscale devices"
bash "$KIT/add-extras.sh"
if command -v firewall-cmd >/dev/null && sudo firewall-cmd --state >/dev/null 2>&1; then
    sudo firewall-cmd -q --permanent --zone=trusted --add-interface=tailscale0 || true
    sudo firewall-cmd -q --reload || true
fi
IP=$(/opt/tailscale/tailscale ip -4 | head -1)
# point alert buttons at the Tailscale address
if [ -f "$HOME/.config/klipper-deck/notify.json" ]; then
    python3 "$HOME/.local/share/klipper-deck/guard.py" notify setup >/dev/null && echo "Alert buttons now use $IP"
fi

printf '\n\033[1mDone.\033[0m\n'
echo "On your phone: install the Tailscale app, sign in with the same account, turn it on."
echo "Then Mainsail works from anywhere at:   http://$IP"
echo "Restart Klipper (close the window and start it again) so it picks up the change."
